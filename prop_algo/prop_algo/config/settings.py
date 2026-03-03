"""
Configuration Module
All trading parameters derived from the Prop Firm Handbook rules.
Centralized config — change here, applies everywhere.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class RiskConfig:
    """Risk management parameters — Golden Rules from handbook."""
    risk_per_trade_pct: float = 0.5          # 0.5% per trade (handbook rule #1)
    max_trades_per_day: int = 2              # Max 2 trades/day
    max_consecutive_losses: int = 2          # Stop after 2 losses (rule #3)
    max_daily_loss_pct: float = 2.0          # Self-imposed 2% daily cap (rule #2)
    max_overall_drawdown_pct: float = 8.0    # Prop firm max drawdown
    challenge_profit_target_pct: float = 10.0 # 10% challenge target
    min_reward_risk_ratio: float = 2.0       # Minimum 1:2 RR
    trail_activation_rr: float = 1.5         # Trail stop after 1.5R


@dataclass
class StrategyConfig:
    """Strategy parameters for Daily Breakout + Retest Momentum."""
    # Trend Filter
    ema_slow_period: int = 200               # 200 EMA on 4H (trend filter)
    ema_fast_period: int = 50                # 50 EMA (pullback zone)

    # Breakout + Retest
    lookback_period: int = 20                # Bars to find prev day high/low
    retest_tolerance_pct: float = 0.5       # % tolerance for retest zone
    breakout_min_body_pct: float = 0.25      # Min candle body % for confirmation (lowered from 0.35 — more candles qualify)
    volume_expansion_factor: float = 1.0     # Volume must be 1.0x avg (lowered from 1.2 — yfinance daily volume is noisy)

    # Engulfing Pattern
    engulfing_min_body_ratio: float = 1.0    # Engulfing body >= prev body

    # ATR for dynamic stops
    atr_period: int = 14
    atr_sl_multiplier: float = 1.5           # SL = 1.5 x ATR
    atr_tp_multiplier: float = 3.0           # TP = 2x SL minimum (1:2 RR)

    # RR filter (mirrored from RiskConfig for strategy use)
    min_reward_risk_ratio: float = 2.0       # Minimum 1:2 RR


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
    timeframe_bias: str = "4h"               # Bias timeframe
    timeframe_entry: str = "15m"             # Entry timeframe


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
        spread_pips=50.0,
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
        spread_pips=1.5,
        yf_ticker="EURUSD=X",
    ),
}

# ─── Default Configs ──────────────────────────────────────────────────

DEFAULT_RISK = RiskConfig()
DEFAULT_STRATEGY = StrategyConfig()

# ─── Logging ──────────────────────────────────────────────────────────

LOG_LEVEL = "INFO"
OUTPUT_DIR = "output"
