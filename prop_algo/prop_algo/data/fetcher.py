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

logger = logging.getLogger(__name__)


def fetch_ohlcv(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance.

    Args:
        ticker: Yahoo Finance ticker symbol
        period: Data period (1mo, 3mo, 6mo, 1y, 2y, 5y)
        interval: Candle interval (1m, 5m, 15m, 1h, 4h, 1d)
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)

    Returns:
        DataFrame with columns: open, high, low, close, volume
    """
    logger.info(f"Fetching {ticker} | period={period} | interval={interval}")

    try:
        ticker_obj = yf.Ticker(ticker)

        if start and end:
            df = ticker_obj.history(start=start, end=end, interval=interval)
        else:
            df = ticker_obj.history(period=period, interval=interval)

        if df.empty:
            logger.warning(f"No data returned for {ticker}")
            return pd.DataFrame()

        # Standardize column names
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]

        # Keep only OHLCV
        keep_cols = ["open", "high", "low", "close", "volume"]
        available = [c for c in keep_cols if c in df.columns]
        df = df[available].copy()

        # Remove timezone info for consistency
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df.dropna(inplace=True)
        logger.info(f"Fetched {len(df)} bars for {ticker}")
        return df

    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()


def add_technical_indicators(df: pd.DataFrame, config) -> pd.DataFrame:
    """
    Add all required technical indicators to OHLCV data.

    Indicators added:
        - EMA 50, EMA 200 (trend filter)
        - ATR (dynamic stop loss)
        - Previous day high/low (breakout levels)
        - Volume SMA (volume confirmation)
        - Candle body metrics (engulfing detection)

    Args:
        df: OHLCV DataFrame
        config: StrategyConfig instance

    Returns:
        DataFrame with indicator columns added
    """
    df = df.copy()

    # ─── Exponential Moving Averages ──────────────────────────
    df["ema_fast"] = df["close"].ewm(span=config.ema_fast_period, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=config.ema_slow_period, adjust=False).mean()

    # ─── Trend Direction ──────────────────────────────────────
    df["trend"] = np.where(df["close"] > df["ema_slow"], 1,
                  np.where(df["close"] < df["ema_slow"], -1, 0))

    df["ema_alignment"] = np.where(df["ema_fast"] > df["ema_slow"], 1,
                          np.where(df["ema_fast"] < df["ema_slow"], -1, 0))

    # ─── ATR (Average True Range) ─────────────────────────────
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = true_range.rolling(window=config.atr_period).mean()

    # ─── Previous Day High / Low (Breakout Levels) ────────────
    df["prev_high"] = df["high"].rolling(window=config.lookback_period).max().shift(1)
    df["prev_low"] = df["low"].rolling(window=config.lookback_period).min().shift(1)

    # More useful: just previous candle's high/low for intraday
    df["prev_candle_high"] = df["high"].shift(1)
    df["prev_candle_low"] = df["low"].shift(1)

    # ─── Volume ───────────────────────────────────────────────
    df["volume_sma"] = df["volume"].rolling(window=20).mean()
    df["volume_ratio"] = df["volume"] / df["volume_sma"]

    # ─── Candle Body Metrics ──────────────────────────────────
    df["body"] = (df["close"] - df["open"]).abs()
    df["candle_range"] = df["high"] - df["low"]
    df["body_pct"] = np.where(
        df["candle_range"] > 0,
        df["body"] / df["candle_range"],
        0
    )
    df["is_bullish"] = df["close"] > df["open"]
    df["is_bearish"] = df["close"] < df["open"]

    # Previous candle body
    df["prev_body"] = df["body"].shift(1)
    df["prev_is_bullish"] = df["is_bullish"].shift(1)
    df["prev_is_bearish"] = df["is_bearish"].shift(1)

    # ─── Support/Resistance via Rolling Pivots ────────────────
    df["resistance"] = df["high"].rolling(window=config.lookback_period).max()
    df["support"] = df["low"].rolling(window=config.lookback_period).min()

    # ─── Price relative to key levels ─────────────────────────
    df["dist_to_resistance_pct"] = (df["resistance"] - df["close"]) / df["close"] * 100
    df["dist_to_support_pct"] = (df["close"] - df["support"]) / df["close"] * 100

    return df


def resample_to_timeframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    Resample intraday data to higher timeframe.

    Args:
        df: Source OHLCV DataFrame
        timeframe: Target timeframe (4h, 1d, etc.)

    Returns:
        Resampled DataFrame
    """
    rule_map = {
        "15m": "15min", "30m": "30min",
        "1h": "1h", "4h": "4h", "1d": "1D",
    }
    rule = rule_map.get(timeframe, timeframe)

    resampled = df.resample(rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna()

    return resampled


def validate_data(df: pd.DataFrame, min_bars: int = 250) -> bool:
    """Check if data is sufficient for strategy calculations."""
    if df.empty:
        logger.error("DataFrame is empty")
        return False
    if len(df) < min_bars:
        logger.warning(f"Only {len(df)} bars. Need at least {min_bars}.")
        return False
    null_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))
    if null_pct > 0.05:
        logger.warning(f"Data has {null_pct:.1%} null values")
        return False
    return True
