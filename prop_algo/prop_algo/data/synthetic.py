"""
Synthetic Data Generator
========================
Generates realistic OHLCV data for testing when live feeds are unavailable.
Uses geometric Brownian motion with regime changes to simulate real market behavior.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Realistic parameters per asset
ASSET_PARAMS = {
    "XAUUSD": {
        "start_price": 2050.0,
        "daily_vol": 0.012,        # ~1.2% daily volatility
        "drift": 0.0003,           # Slight upward drift (gold in uptrend)
        "volume_base": 180000,
        "pip_size": 0.01,
    },
    "BTCUSD": {
        "start_price": 65000.0,
        "daily_vol": 0.035,        # ~3.5% daily (crypto volatility)
        "drift": 0.0005,
        "volume_base": 25000000000,
        "pip_size": 1.0,
    },
    "XRPUSD": {
        "start_price": 0.62,
        "daily_vol": 0.04,         # ~4% daily (altcoin)
        "drift": 0.0002,
        "volume_base": 1500000000,
        "pip_size": 0.0001,
    },
    "EURUSD": {
        "start_price": 1.0850,
        "daily_vol": 0.005,        # ~0.5% daily (forex majors)
        "drift": -0.0001,          # Slight downward drift
        "volume_base": 500000,
        "pip_size": 0.0001,
    },
}


def generate_synthetic_ohlcv(
    symbol: str,
    n_bars: int = 365,
    interval: str = "1d",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate realistic synthetic OHLCV data using geometric Brownian motion
    with trend regimes, mean reversion zones, and breakout patterns.

    Args:
        symbol: Asset symbol (must be in ASSET_PARAMS)
        n_bars: Number of bars to generate
        interval: Candle interval
        seed: Random seed for reproducibility

    Returns:
        DataFrame with open, high, low, close, volume
    """
    np.random.seed(seed + hash(symbol) % 1000)

    params = ASSET_PARAMS.get(symbol, ASSET_PARAMS["EURUSD"])
    price = params["start_price"]
    vol = params["daily_vol"]
    drift = params["drift"]
    vol_base = params["volume_base"]

    # Generate dates
    end_date = datetime(2026, 2, 25)
    if interval == "1d":
        dates = pd.bdate_range(end=end_date, periods=n_bars)
    elif interval == "4h":
        dates = pd.date_range(end=end_date, periods=n_bars, freq="4h")
    elif interval == "1h":
        dates = pd.date_range(end=end_date, periods=n_bars, freq="1h")
    else:
        dates = pd.bdate_range(end=end_date, periods=n_bars)

    opens, highs, lows, closes, volumes = [], [], [], [], []

    # Regime state: trending (0.6), ranging (0.3), volatile (0.1)
    regime = "trending"
    regime_length = 0
    trend_dir = 1 if drift >= 0 else -1

    for i in range(n_bars):
        # ─── Regime Switching ─────────────────────────────────
        regime_length += 1
        if regime_length > np.random.randint(20, 60):
            regime = np.random.choice(
                ["trending", "ranging", "volatile"],
                p=[0.50, 0.35, 0.15]
            )
            regime_length = 0
            if regime == "trending":
                trend_dir = np.random.choice([1, -1])

        # ─── Generate Returns Based on Regime ─────────────────
        if regime == "trending":
            daily_return = drift * trend_dir + vol * np.random.randn()
            intraday_vol = vol * 0.8
        elif regime == "ranging":
            # Mean revert around current price
            daily_return = vol * 0.5 * np.random.randn()
            intraday_vol = vol * 0.5
        else:  # volatile
            daily_return = drift + vol * 2.0 * np.random.randn()
            intraday_vol = vol * 1.5

        # ─── Generate OHLC ───────────────────────────────────
        open_price = price
        close_price = price * (1 + daily_return)

        # Intraday range
        intraday_move = abs(price * intraday_vol * np.random.randn())
        wick_up = abs(price * intraday_vol * np.random.exponential(0.5))
        wick_down = abs(price * intraday_vol * np.random.exponential(0.5))

        high_price = max(open_price, close_price) + wick_up
        low_price = min(open_price, close_price) - wick_down

        # Ensure valid OHLC
        low_price = max(low_price, price * 0.9)  # Prevent negative/extreme
        high_price = max(high_price, max(open_price, close_price))
        low_price = min(low_price, min(open_price, close_price))

        # ─── Volume ───────────────────────────────────────────
        vol_multiplier = 1.0
        if regime == "volatile":
            vol_multiplier = np.random.uniform(1.5, 3.0)
        elif regime == "ranging":
            vol_multiplier = np.random.uniform(0.5, 0.9)
        else:
            vol_multiplier = np.random.uniform(0.8, 1.5)

        # Breakout bars get higher volume
        if abs(daily_return) > vol * 1.5:
            vol_multiplier *= 1.8

        volume = int(vol_base * vol_multiplier * np.random.uniform(0.7, 1.3))

        opens.append(round(open_price, 5))
        highs.append(round(high_price, 5))
        lows.append(round(low_price, 5))
        closes.append(round(close_price, 5))
        volumes.append(volume)

        price = close_price

    df = pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    }, index=dates)

    logger.info(f"Generated {len(df)} synthetic bars for {symbol} "
                f"({df['close'].iloc[0]:.2f} → {df['close'].iloc[-1]:.2f})")

    return df
