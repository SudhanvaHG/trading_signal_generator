"""
Signal Engine Module
====================
Orchestrates multiple strategies, applies risk filtering,
and produces final actionable signals.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime
import logging

from ..config.settings import (
    ASSETS, AssetConfig, DEFAULT_RISK, DEFAULT_STRATEGY, RiskConfig, StrategyConfig
)
from ..data.fetcher import fetch_ohlcv, add_technical_indicators, validate_data
from ..data.synthetic import generate_synthetic_ohlcv
from ..strategies.base import TradeSignal, SignalType
from ..strategies.breakout_retest import BreakoutRetestStrategy
from ..strategies.ema_trend_pullback import EMATrendPullbackStrategy
from ..strategies.mean_reversion import MeanReversionStrategy
from ..risk.manager import RiskManager

logger = logging.getLogger(__name__)


class SignalEngine:
    """
    Main engine that:
    1. Fetches data for all assets
    2. Runs all strategies
    3. Filters through risk manager
    4. Outputs final approved signals
    """

    def __init__(
        self,
        assets: List[str] = None,
        risk_config: RiskConfig = None,
        strategy_config: StrategyConfig = None,
        initial_balance: float = 10000.0,
    ):
        self.asset_keys = assets or list(ASSETS.keys())
        self.risk_config = risk_config or DEFAULT_RISK
        self.strategy_config = strategy_config or DEFAULT_STRATEGY
        self.risk_manager = RiskManager(self.risk_config, initial_balance)

        # Initialize strategies
        self.strategies = [
            BreakoutRetestStrategy(self.strategy_config),
            EMATrendPullbackStrategy(self.strategy_config),
            MeanReversionStrategy(self.strategy_config),
        ]

        # Data storage
        self.data: Dict[str, pd.DataFrame] = {}
        self.all_signals: List[TradeSignal] = []
        self.approved_signals: List[TradeSignal] = []
        self.rejected_signals: List[dict] = []

    def fetch_all_data(self, period: str = "1y", interval: str = "1d") -> dict:
        """Fetch data for all configured assets. Falls back to synthetic data."""
        results = {}
        for key in self.asset_keys:
            if key not in ASSETS:
                logger.warning(f"Asset {key} not in config. Skipping.")
                continue

            asset = ASSETS[key]
            df = fetch_ohlcv(
                ticker=asset.yf_ticker,
                period=period,
                interval=interval,
            )

            # Fallback to synthetic data if live fetch fails
            if not validate_data(df, min_bars=50):
                logger.info(f"Using synthetic data for {key}")
                n_bars = {"1mo": 22, "3mo": 66, "6mo": 130, "1y": 252, "2y": 504}.get(period, 252)
                df = generate_synthetic_ohlcv(key, n_bars=n_bars, interval=interval)

            if validate_data(df, min_bars=50):
                df = add_technical_indicators(df, self.strategy_config)
                self.data[key] = df
                results[key] = {
                    "status": "OK",
                    "bars": len(df),
                    "start": str(df.index[0].date()),
                    "end": str(df.index[-1].date()),
                }
            else:
                results[key] = {"status": "FAILED", "bars": len(df) if not df.empty else 0}

        return results

    def generate_all_signals(self) -> List[TradeSignal]:
        """Run all strategies on all assets."""
        self.all_signals = []

        for symbol, df in self.data.items():
            for strategy in self.strategies:
                try:
                    signals = strategy.generate_signals(df, symbol)
                    self.all_signals.extend(signals)
                    logger.info(
                        f"  {strategy.name} on {symbol}: {len(signals)} raw signals"
                    )
                except Exception as e:
                    logger.error(f"Error in {strategy.name} on {symbol}: {e}")

        # Sort by timestamp
        self.all_signals.sort(key=lambda s: s.timestamp)
        return self.all_signals

    def filter_signals(self) -> List[TradeSignal]:
        """Apply risk manager filter to all signals."""
        self.approved_signals = []
        self.rejected_signals = []

        for signal in self.all_signals:
            allowed, reason = self.risk_manager.check_signal_allowed(signal)

            if allowed:
                self.approved_signals.append(signal)
            else:
                self.rejected_signals.append({
                    "timestamp": signal.timestamp,
                    "symbol": signal.symbol,
                    "signal": signal.signal.value,
                    "strategy": signal.strategy_name,
                    "reason": reason,
                })

        return self.approved_signals

    def run_backtest(self) -> dict:
        """
        Simple backtest: simulate trade outcomes based on RR ratio.
        Uses a probabilistic model based on expected win rates.
        """
        np.random.seed(42)

        for signal in self.approved_signals:
            # Simulate outcome based on strategy-specific win rates
            if signal.strategy_name == "Breakout_Retest":
                win_prob = 0.48
            elif signal.strategy_name == "EMA_Trend_Pullback":
                win_prob = 0.50
            elif signal.strategy_name == "Mean_Reversion":
                win_prob = 0.58
            else:
                win_prob = 0.45

            # Adjust by confidence
            win_prob = win_prob * (0.8 + 0.4 * signal.confidence)
            win_prob = min(win_prob, 0.75)

            is_win = np.random.random() < win_prob

            if is_win:
                pnl_pct = self.risk_config.risk_per_trade_pct * signal.risk_reward_ratio
                result = "WIN"
            else:
                pnl_pct = -self.risk_config.risk_per_trade_pct
                result = "LOSS"

            # Check if still allowed (running risk checks)
            allowed, _ = self.risk_manager.check_signal_allowed(signal)
            if allowed:
                self.risk_manager.record_trade_result(signal, result, pnl_pct)

        return self.risk_manager.get_summary()

    def run_signals_only(
        self, period: str = "1y", interval: str = "1d"
    ) -> dict:
        """
        Fetch data + generate + filter signals. No backtest.
        Used for real-time / live signal monitoring.
        Note: needs at least 1y of data so the 200-EMA warms up properly
        (strategies skip bars until ema_slow_period + 10 = 210 bars loaded).
        """
        logger.info("=" * 60)
        logger.info("PROP ALGO — LIVE SIGNAL SCAN")
        logger.info("=" * 60)

        logger.info("[1/3] Fetching market data...")
        data_results = self.fetch_all_data(period, interval)

        logger.info("[2/3] Generating signals from all strategies...")
        raw_signals = self.generate_all_signals()

        logger.info("[3/3] Filtering through risk manager...")
        approved = self.filter_signals()

        return {
            "data_status": data_results,
            "raw_signals_count": len(raw_signals),
            "approved_signals_count": len(approved),
            "rejected_signals_count": len(self.rejected_signals),
        }

    def run_full_pipeline(
        self, period: str = "1y", interval: str = "1d"
    ) -> dict:
        """
        Execute the complete pipeline:
        1. Fetch data
        2. Generate signals
        3. Filter through risk manager
        4. Run backtest simulation
        5. Return comprehensive results
        """
        logger.info("=" * 60)
        logger.info("PROP ALGO TRADING SYSTEM — FULL PIPELINE")
        logger.info("=" * 60)

        # Step 1
        logger.info("\n[1/4] Fetching market data...")
        data_results = self.fetch_all_data(period, interval)

        # Step 2
        logger.info("\n[2/4] Generating signals from all strategies...")
        raw_signals = self.generate_all_signals()

        # Step 3
        logger.info("\n[3/4] Filtering through risk manager...")
        approved = self.filter_signals()

        # Step 4
        logger.info("\n[4/4] Running backtest simulation...")
        summary = self.run_backtest()

        results = {
            "data_status": data_results,
            "raw_signals_count": len(raw_signals),
            "approved_signals_count": len(approved),
            "rejected_signals_count": len(self.rejected_signals),
            "backtest_summary": summary,
            "trade_log": self.risk_manager.get_trade_log_df(),
        }

        return results

    def get_latest_signals(self, n: int = 20) -> pd.DataFrame:
        """Get the most recent approved signals as DataFrame."""
        if not self.approved_signals:
            return pd.DataFrame()

        recent = self.approved_signals[-n:]
        rows = [s.to_dict() for s in recent]
        return pd.DataFrame(rows)

    def get_signals_by_asset(self, symbol: str) -> pd.DataFrame:
        """Get all approved signals for a specific asset."""
        filtered = [s for s in self.approved_signals if s.symbol == symbol]
        if not filtered:
            return pd.DataFrame()
        return pd.DataFrame([s.to_dict() for s in filtered])

    def get_signals_summary(self) -> pd.DataFrame:
        """Get signal count summary by asset and strategy."""
        if not self.approved_signals:
            return pd.DataFrame()

        rows = []
        for s in self.approved_signals:
            rows.append({
                "symbol": s.symbol,
                "strategy": s.strategy_name,
                "signal": s.signal.value,
            })

        df = pd.DataFrame(rows)
        summary = df.groupby(["symbol", "strategy", "signal"]).size().reset_index(name="count")
        return summary
