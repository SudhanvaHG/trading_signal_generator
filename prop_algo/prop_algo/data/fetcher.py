"""
Data Fetcher Module
Downloads OHLCV data from Yahoo Finance and prepares it for strategy use.
Supports multiple timeframes and assets.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)
# yfinance >= 0.2.50 manages its own curl_cffi session internally.
# Do NOT pass a requests.Session — yfinance will raise an error if you do.


def fetch_ohlcv(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
    start: Optional[str] = None,
    end: Optional[str] = None,
    retries: int = 3,
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance.

    Uses yf.download() which is more robust than Ticker.history() in
    containerised environments (handles Yahoo Finance API changes better).

    Args:
        ticker:   Yahoo Finance ticker symbol (e.g. "BTC-USD", "GC=F")
        period:   Data window — "1mo" "3mo" "6mo" "1y" "2y" "5y"
        interval: Candle size  — "1m" "5m" "15m" "1h" "4h" "1d"
        start:    Start date YYYY-MM-DD (overrides period if provided with end)
        end:      End date   YYYY-MM-DD
        retries:  Number of attempts before giving up

    Returns:
        DataFrame with columns: open, high, low, close, volume (all lower-case)
        Empty DataFrame on failure.
    """
    logger.info(f"Fetching {ticker} | period={period} | interval={interval}")

    for attempt in range(1, retries + 1):
        try:
            if start and end:
                df = yf.download(
                    tickers=ticker,
                    start=start,
                    end=end,
                    interval=interval,
                    progress=False,
                    auto_adjust=True,
                    threads=False,
                )
            else:
                df = yf.download(
                    tickers=ticker,
                    period=period,
                    interval=interval,
                    progress=False,
                    auto_adjust=True,
                    threads=False,
                )

            if df.empty:
                logger.warning(f"No data returned for {ticker} (attempt {attempt})")
                if attempt < retries:
                    time.sleep(2 * attempt)   # back-off before retry
                continue

            # yf.download with a single ticker can return a MultiIndex
            # (ticker, field) — flatten it to just field names
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Standardise column names to lower-case
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]

            # Keep only OHLCV columns that exist
            keep_cols = ["open", "high", "low", "close", "volume"]
            available = [c for c in keep_cols if c in df.columns]
            df = df[available].copy()

            # Drop timezone so everything is naive UTC
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            df.dropna(inplace=True)
            logger.info(f"Fetched {len(df)} bars for {ticker} "
                        f"({df['close'].iloc[0]:.4f} → {df['close'].iloc[-1]:.4f})")
            return df

        except Exception as e:
            logger.error(f"Error fetching {ticker} (attempt {attempt}): {e}")
            if attempt < retries:
                time.sleep(2 * attempt)

    logger.error(f"All {retries} attempts failed for {ticker}")
    return pd.DataFrame()


def add_technical_indicators(df: pd.DataFrame, config) -> pd.DataFrame:
    """
    Add all required technical indicators to OHLCV data.

    Indicators added:
        - EMA 50, EMA 200 (trend filter)
        - ATR 14 (dynamic stop loss sizing)
        - Previous candle / rolling high-low (breakout levels)
        - Volume SMA 20 + ratio (volume confirmation)
        - Candle body metrics (engulfing / confirmation detection)
        - Support / Resistance pivots

    Args:
        df:     OHLCV DataFrame
        config: StrategyConfig instance

    Returns:
        DataFrame with indicator columns added in-place copy
    """
    df = df.copy()

    # ─── Exponential Moving Averages ──────────────────────────────────
    df["ema_fast"] = df["close"].ewm(span=config.ema_fast_period, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=config.ema_slow_period, adjust=False).mean()

    # ─── Trend Direction ──────────────────────────────────────────────
    df["trend"] = np.where(df["close"] > df["ema_slow"],  1,
                  np.where(df["close"] < df["ema_slow"], -1, 0))

    df["ema_alignment"] = np.where(df["ema_fast"] > df["ema_slow"],  1,
                          np.where(df["ema_fast"] < df["ema_slow"], -1, 0))

    # ─── ATR (Average True Range) ─────────────────────────────────────
    high_low   = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close  = (df["low"]  - df["close"].shift(1)).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"]  = true_range.rolling(window=config.atr_period).mean()

    # ─── Previous Day High / Low (Breakout Levels) ────────────────────
    df["prev_high"]       = df["high"].rolling(window=config.lookback_period).max().shift(1)
    df["prev_low"]        = df["low"].rolling(window=config.lookback_period).min().shift(1)
    df["prev_candle_high"] = df["high"].shift(1)
    df["prev_candle_low"]  = df["low"].shift(1)

    # ─── Volume ───────────────────────────────────────────────────────
    df["volume_sma"]   = df["volume"].rolling(window=20).mean()
    df["volume_ratio"] = df["volume"] / df["volume_sma"]

    # ─── Candle Body Metrics ──────────────────────────────────────────
    df["body"]         = (df["close"] - df["open"]).abs()
    df["candle_range"] = df["high"] - df["low"]
    df["body_pct"]     = np.where(
        df["candle_range"] > 0,
        df["body"] / df["candle_range"],
        0,
    )
    df["is_bullish"] = df["close"] > df["open"]
    df["is_bearish"] = df["close"] < df["open"]

    df["prev_body"]       = df["body"].shift(1)
    df["prev_is_bullish"] = df["is_bullish"].shift(1)
    df["prev_is_bearish"] = df["is_bearish"].shift(1)

    # ─── Support / Resistance (Rolling Pivots) ────────────────────────
    df["resistance"] = df["high"].rolling(window=config.lookback_period).max()
    df["support"]    = df["low"].rolling(window=config.lookback_period).min()

    df["dist_to_resistance_pct"] = (df["resistance"] - df["close"]) / df["close"] * 100
    df["dist_to_support_pct"]    = (df["close"] - df["support"])    / df["close"] * 100

    return df


def resample_to_timeframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample intraday data to a higher timeframe (4h, 1d, etc.)."""
    rule_map = {
        "15m": "15min", "30m": "30min",
        "1h": "1h", "4h": "4h", "1d": "1D",
    }
    rule = rule_map.get(timeframe, timeframe)
    return df.resample(rule).agg({
        "open":   "first",
        "high":   "max",
        "low":    "min",
        "close":  "last",
        "volume": "sum",
    }).dropna()


def validate_data(df: pd.DataFrame, min_bars: int = 250) -> bool:
    """Check if DataFrame has sufficient, clean data for strategy use."""
    if df.empty:
        logger.error("DataFrame is empty")
        return False
    if len(df) < min_bars:
        logger.warning(f"Only {len(df)} bars — need at least {min_bars}.")
        return False
    null_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))
    if null_pct > 0.05:
        logger.warning(f"Data has {null_pct:.1%} null values")
        return False
    return True
