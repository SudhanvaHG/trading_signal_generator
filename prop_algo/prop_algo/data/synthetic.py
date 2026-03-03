"""
Synthetic Data Generator
========================
Generates realistic OHLCV data for testing when live feeds are unavailable.

Uses Geometric Brownian Motion (GBM) with:
  - Regime switching  (trending / ranging / volatile)
  - Daily return caps (±3σ) to prevent price explosion
  - Hard price floor/ceiling per asset so output looks realistic
  - Current approximate prices (updated March 2026)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ─── Per-Asset Parameters ─────────────────────────────────────────────────────
# start_price : approximate current market price (update as needed)
# daily_vol   : realistic 1-day % volatility (1σ)
# drift       : tiny per-bar drift (annualised / 252)
# price_floor : absolute minimum price (circuit-breaker)
# price_ceil  : absolute maximum price (circuit-breaker)
# volume_base : approximate daily volume units
ASSET_PARAMS = {
    "XAUUSD": {
        "start_price":  2900.0,          # Gold ~$2,900/oz (Mar 2026)
        "daily_vol":    0.010,            # ~1.0% daily (gold is calmer than crypto)
        "drift":        0.0002,           # Slight upward bias (long-term gold trend)
        "price_floor":  1800.0,
        "price_ceil":   4000.0,
        "volume_base":  180_000,
    },
    "BTCUSD": {
        "start_price":  67_000.0,         # Bitcoin ~$67,000 (Mar 2026, per user)
        "daily_vol":    0.030,            # ~3.0% daily (crypto volatility)
        "drift":        0.0003,
        "price_floor":  20_000.0,
        "price_ceil":  200_000.0,
        "volume_base":  25_000_000_000,
    },
    "XRPUSD": {
        "start_price":  2.30,             # XRP ~$2.30 (Mar 2026)
        "daily_vol":    0.040,            # ~4.0% daily (altcoin)
        "drift":        0.0002,
        "price_floor":  0.20,
        "price_ceil":   20.0,
        "volume_base":  4_000_000_000,
    },
    "EURUSD": {
        "start_price":  1.0500,           # EUR/USD ~1.05 (Mar 2026)
        "daily_vol":    0.004,            # ~0.4% daily (forex major)
        "drift":       -0.00005,          # Slight USD-strong bias
        "price_floor":  0.90,
        "price_ceil":   1.30,
        "volume_base":  500_000,
    },
}


def generate_synthetic_ohlcv(
    symbol: str,
    n_bars: int = 252,
    interval: str = "1d",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate realistic synthetic OHLCV data.

    Uses GBM with regime switching (trending / ranging / volatile) and
    daily-return caps to keep prices in a believable range.

    Args:
        symbol:   Asset key (must be in ASSET_PARAMS)
        n_bars:   Number of candles to generate
        interval: Candle size ("1d", "4h", "1h")
        seed:     Random seed — same seed + symbol = reproducible data

    Returns:
        DataFrame with columns: open, high, low, close, volume
    """
    # Deterministic but different per symbol
    np.random.seed(seed + abs(hash(symbol)) % 10_000)

    params     = ASSET_PARAMS.get(symbol, ASSET_PARAMS["EURUSD"])
    price      = params["start_price"]
    vol        = params["daily_vol"]
    drift      = params["drift"]
    vol_base   = params["volume_base"]
    floor      = params["price_floor"]
    ceil_      = params["price_ceil"]

    # ─── Build date index ────────────────────────────────────────────
    end_date = datetime(2026, 3, 3)   # "today" in the simulation
    if interval == "1d":
        dates = pd.bdate_range(end=end_date, periods=n_bars)
    elif interval == "4h":
        dates = pd.date_range(end=end_date, periods=n_bars, freq="4h")
    elif interval == "1h":
        dates = pd.date_range(end=end_date, periods=n_bars, freq="1h")
    else:
        dates = pd.bdate_range(end=end_date, periods=n_bars)

    opens, highs, lows, closes, volumes = [], [], [], [], []

    # ─── Regime state machine ────────────────────────────────────────
    regime         = "trending"
    regime_length  = 0
    trend_dir      = 1 if drift >= 0 else -1

    for _ in range(n_bars):
        # Switch regime every 20-60 bars
        regime_length += 1
        if regime_length > np.random.randint(20, 60):
            regime = np.random.choice(
                ["trending", "ranging", "volatile"],
                p=[0.50, 0.35, 0.15],
            )
            regime_length = 0
            if regime == "trending":
                trend_dir = np.random.choice([1, -1])

        # ─── Daily return by regime ───────────────────────────────
        if regime == "trending":
            raw_return = drift * trend_dir + vol * np.random.randn()
            intraday_vol = vol * 0.8
        elif regime == "ranging":
            raw_return = vol * 0.4 * np.random.randn()   # mean-reverting, calmer
            intraday_vol = vol * 0.5
        else:  # volatile
            raw_return = drift + vol * 1.8 * np.random.randn()
            intraday_vol = vol * 1.4

        # ─── Hard cap: clip to ±3σ so no single day is absurd ────
        max_move = vol * 3.0
        daily_return = float(np.clip(raw_return, -max_move, max_move))

        # ─── Build OHLC ───────────────────────────────────────────
        open_price  = price
        close_price = price * (1.0 + daily_return)

        # Intraday wicks (exponential distribution for realistic tails)
        wick_up   = abs(price * intraday_vol * float(np.random.exponential(0.4)))
        wick_down = abs(price * intraday_vol * float(np.random.exponential(0.4)))

        high_price = max(open_price, close_price) + wick_up
        low_price  = min(open_price, close_price) - wick_down

        # Clamp to floor / ceiling BEFORE storing
        close_price = float(np.clip(close_price, floor, ceil_))
        high_price  = float(np.clip(high_price,  floor, ceil_))
        low_price   = float(np.clip(low_price,   floor, ceil_))
        open_price  = float(np.clip(open_price,  floor, ceil_))

        # Ensure OHLC invariant: low ≤ open,close ≤ high
        high_price = max(high_price, max(open_price, close_price))
        low_price  = min(low_price,  min(open_price, close_price))

        # ─── Volume ───────────────────────────────────────────────
        if regime == "volatile":
            vol_mult = float(np.random.uniform(1.5, 3.0))
        elif regime == "ranging":
            vol_mult = float(np.random.uniform(0.5, 0.9))
        else:
            vol_mult = float(np.random.uniform(0.8, 1.5))

        # Breakout bars get a volume spike
        if abs(daily_return) > vol * 1.5:
            vol_mult *= 1.8

        volume = int(vol_base * vol_mult * float(np.random.uniform(0.7, 1.3)))

        # Round prices to the natural precision of the asset
        decimals = 2 if price > 10 else (4 if price > 0.1 else 6)
        opens.append(round(open_price,  decimals))
        highs.append(round(high_price,  decimals))
        lows.append(round(low_price,    decimals))
        closes.append(round(close_price, decimals))
        volumes.append(volume)

        price = close_price   # carry forward for next bar

    df = pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes},
        index=dates,
    )

    logger.info(
        f"Generated {len(df)} synthetic bars for {symbol} "
        f"({df['close'].iloc[0]:.4f} → {df['close'].iloc[-1]:.4f})"
    )
    return df
