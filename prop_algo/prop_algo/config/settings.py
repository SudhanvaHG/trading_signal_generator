"""
Optimized Configuration Module
Balanced for prop firm compliance, realistic market noise tolerance, and optimized momentum capture.
Centralized config — change here, applies everywhere.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class RiskConfig:
    """Risk management parameters — Golden Rules from handbook."""
    risk_per_trade_pct: float = 1.0          # INCREASED: 1.0% per trade for faster compounding while staying within limits.
    max_trades_per_day: int = 3              # INCREASED: Allow up to 3 trades to catch multiple setups across sessions.
    max_consecutive_losses: int = 3          # INCREASED: Allow 3 to account for normal market variance before halting.
    max_daily_loss_pct: float = 3.0          # ADJUSTED: 3% daily cap gives more breathing room than 2% while staying safe.
    max_overall_drawdown_pct: float = 8.0    # Prop firm max drawdown (KEEP as absolute limit).
    challenge_profit_target_pct: float = 10.0 # 10% challenge target.
    min_reward_risk_ratio: float = 1.5       # DECREASED: 1:1.5 is more realistic for consistent win rates than strict 1:2.
    trail_activation_rr: float = 1.0         # DECREASED: Secure break-even sooner (at 1R) to protect capital.


@dataclass
class StrategyConfig:
    """Strategy parameters for Daily Breakout + Retest Momentum."""
    # Trend Filter
    ema_slow_period: int = 200               # 200 EMA on 4H (Strong trend filter - KEEP).
    ema_fast_period: int = 50                # 50 EMA (Dynamic support/resistance - KEEP).

    # Breakout + Retest
    lookback_period: int = 15                # DECREASED: 15 bars is often more responsive to recent market structure than 20.
    retest_tolerance_pct: float = 0.8       # INCREASED: 0.8% gives a wider zone to catch imperfect retests (markets are messy).
    breakout_min_body_pct: float = 0.40      # INCREASED: 0.40% demands stronger momentum to filter out fakeouts.
    volume_expansion_factor: float = 1.1     # BALANCED: 1.1x is a sweet spot; 1.0x ignores volume entirely, 1.2x is often too strict.

    # Engulfing Pattern
    engulfing_min_body_ratio: float = 1.2    # INCREASED: Ensure the engulfing candle has significant body size compared to previous.

    # ATR for dynamic stops
    atr_period: int = 14                     # Standard 14 period (KEEP).
    atr_sl_multiplier: float = 0.4           # SCALP: 0.4x ATR gives tight, achievable stops (BTC ~$800-1000 away).
    atr_tp_multiplier: float = 1.5           # SCALP: 1.5x ATR target — R:R = 3.75:1, realistic and reachable.

    # RR filter (mirrored from RiskConfig for strategy use)
    min_reward_risk_ratio: float = 1.5       # Mirrored adjusted RR.


@dataclass
class AssetConfig:
    """Per-asset configuration."""
    symbol: str
    display_name: str
    asset_class: str                         # forex, crypto, commodity
    pip_value: float = 0.0001               # Pip size
    spread_pips: float = 2.0                 # Typical spread
    data_source: str = "yfinance"
    yf_ticker: str = ""                      # Yahoo Finance ticker
    timeframe_bias: str = "1d"               # CHANGED: Daily bias provides stronger directional context than 4H.
    timeframe_entry: str = "5m"             # Entry timeframe (15m is good for balancing execution speed and noise).


# ─── Asset Definitions ────────────────────────────────────────────────

ASSETS: Dict[str, AssetConfig] = {
    "XAUUSD": AssetConfig(
        symbol="XAUUSD",
        display_name="Gold (XAU/USD)",
        asset_class="commodity",
        pip_value=0.01,
        spread_pips=3.0,
        yf_ticker="GC=F",
    ),
    "BTCUSD": AssetConfig(
        symbol="BTCUSD",
        display_name="Bitcoin (BTC/USD)",
        asset_class="crypto",
        pip_value=1.0,
        spread_pips=40.0, # ADJUSTED: 40 is often closer to average decent broker spreads than 50.
        yf_ticker="BTC-USD",
    ),
    "XRPUSD": AssetConfig(
        symbol="XRPUSD",
        display_name="Ripple (XRP/USD)",
        asset_class="crypto",
        pip_value=0.0001,
        spread_pips=5.0,
        yf_ticker="XRP-USD",
    ),
    "EURUSD": AssetConfig(
        symbol="EURUSD",
        display_name="Euro (EUR/USD)",
        asset_class="forex",
        pip_value=0.0001,
        spread_pips=1.0, # DECREASED: EURUSD spread is usually very tight (1.0 or lower).
        yf_ticker="EURUSD=X",
    ),
}

# ─── Default Configs ──────────────────────────────────────────────────

DEFAULT_RISK = RiskConfig()
DEFAULT_STRATEGY = StrategyConfig()

# ─── Logging ──────────────────────────────────────────────────────────

LOG_LEVEL = "INFO"
OUTPUT_DIR = "output"

# ─── Helper Functions ─────────────────────────────────────────────────

def get_asset_config(symbol: str) -> AssetConfig:
    return ASSETS.get(symbol, ASSETS["EURUSD"]) # Default EURUSD