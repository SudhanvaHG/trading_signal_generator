"""
Trading Engine Service
Wraps the prop_algo engine for async/background use inside FastAPI.
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import json

# Add prop_algo to path — works both locally and inside Docker
# Docker: PYTHONPATH=/app:/prop_algo_src is set via environment
# Local:  walk up to find the prop_algo package
import os
_docker_path = Path("/prop_algo_src")
try:
    # services(0) -> app(1) -> backend(2) -> dashboard(3) -> repo_root(4)
    _local_path = Path(__file__).parents[4]
except IndexError:
    _local_path = None

for _candidate in [_docker_path, _local_path]:
    if _candidate and (_candidate / "prop_algo").exists():
        sys.path.insert(0, str(_candidate))
        break

from prop_algo.signals.engine import SignalEngine
from prop_algo.config.settings import DEFAULT_RISK, DEFAULT_STRATEGY, ASSETS, RiskConfig, StrategyConfig

logger = logging.getLogger(__name__)


class TradingEngineService:
    """
    Async wrapper around SignalEngine.
    Manages live scanning state and backtest execution.
    """

    def __init__(self):
        self.is_scanning = False
        self.scan_count = 0
        self.last_scan_time: Optional[datetime] = None
        self.last_signals: List[dict] = []
        self.last_scan_summary: dict = {}
        self._engine: Optional[SignalEngine] = None
        self._scan_task: Optional[asyncio.Task] = None

    def _build_engine(self, initial_balance: float = 10000.0) -> SignalEngine:
        return SignalEngine(
            assets=["XAUUSD", "BTCUSD", "XRPUSD", "EURUSD"],
            risk_config=DEFAULT_RISK,
            strategy_config=DEFAULT_STRATEGY,
            initial_balance=initial_balance,
        )

    async def run_single_scan(
        self,
        period: str = "3mo",
        interval: str = "1d",
    ) -> dict:
        """
        Run one signal scan (no backtest). Returns results dict.
        Runs in a thread pool to avoid blocking the event loop.
        """
        loop = asyncio.get_event_loop()

        def _sync_scan():
            engine = self._build_engine()
            results = engine.run_signals_only(period=period, interval=interval)
            signals = [s.to_dict() for s in engine.approved_signals]
            rejected = engine.rejected_signals
            return results, signals, rejected, engine

        results, signals, rejected, engine = await loop.run_in_executor(
            None, _sync_scan
        )

        self._engine = engine
        self.last_scan_time = datetime.utcnow()
        self.last_signals = signals
        self.scan_count += 1

        self.last_scan_summary = {
            "scan_number": self.scan_count,
            "scan_time": self.last_scan_time.isoformat(),
            "raw_signals": results["raw_signals_count"],
            "approved_signals": results["approved_signals_count"],
            "rejected_signals": results["rejected_signals_count"],
            "data_status": results["data_status"],
            "signals": signals,
            "rejected": rejected,
        }

        return self.last_scan_summary

    async def run_backtest(
        self,
        period: str = "1y",
        interval: str = "1d",
        initial_balance: float = 10000.0,
        progress_callback=None,
    ) -> dict:
        """
        Run full backtest pipeline. Returns comprehensive results.
        """
        loop = asyncio.get_event_loop()

        def _sync_backtest():
            if progress_callback:
                asyncio.run_coroutine_threadsafe(
                    progress_callback(10, "Initializing engine..."), loop
                )

            engine = self._build_engine(initial_balance)

            if progress_callback:
                asyncio.run_coroutine_threadsafe(
                    progress_callback(20, "Fetching market data..."), loop
                )

            results = engine.run_full_pipeline(period=period, interval=interval)

            if progress_callback:
                asyncio.run_coroutine_threadsafe(
                    progress_callback(90, "Compiling results..."), loop
                )

            signals = [s.to_dict() for s in engine.approved_signals]
            trade_log = engine.risk_manager.get_trade_log_df()
            trade_log_records = trade_log.to_dict("records") if not trade_log.empty else []

            return results, signals, trade_log_records, engine

        results, signals, trade_log, engine = await loop.run_in_executor(
            None, _sync_backtest
        )

        summary = results["backtest_summary"]

        return {
            "run_at": datetime.utcnow().isoformat(),
            "period": period,
            "timeframe": interval,
            "initial_balance": initial_balance,
            "final_balance": summary["current_balance"],
            "total_return_pct": summary["total_return_pct"],
            "total_trades": summary["total_trades"],
            "wins": summary["wins"],
            "losses": summary["losses"],
            "win_rate_pct": summary["win_rate_pct"],
            "max_drawdown_pct": summary["max_drawdown_pct"],
            "current_drawdown_pct": summary["current_drawdown_pct"],
            "challenge_passed": summary["challenge_passed"],
            "challenge_target_pct": summary["challenge_target_pct"],
            "account_blown": summary["account_blown"],
            "approved_signals": signals,
            "raw_signals_count": results["raw_signals_count"],
            "approved_signals_count": results["approved_signals_count"],
            "rejected_signals_count": results["rejected_signals_count"],
            "data_status": results["data_status"],
            "trade_log": trade_log,
            "equity_curve": _build_equity_curve(trade_log, initial_balance),
            "strategy_breakdown": _build_strategy_breakdown(signals),
            "asset_breakdown": _build_asset_breakdown(signals),
        }

    def get_risk_config(self) -> dict:
        return {
            "risk_per_trade_pct": DEFAULT_RISK.risk_per_trade_pct,
            "max_trades_per_day": DEFAULT_RISK.max_trades_per_day,
            "max_consecutive_losses": DEFAULT_RISK.max_consecutive_losses,
            "max_daily_loss_pct": DEFAULT_RISK.max_daily_loss_pct,
            "max_overall_drawdown_pct": DEFAULT_RISK.max_overall_drawdown_pct,
            "challenge_profit_target_pct": DEFAULT_RISK.challenge_profit_target_pct,
            "min_reward_risk_ratio": DEFAULT_RISK.min_reward_risk_ratio,
            "trail_activation_rr": DEFAULT_RISK.trail_activation_rr,
        }

    def get_assets_config(self) -> list:
        return [
            {
                "symbol": key,
                "display_name": a.display_name,
                "asset_class": a.asset_class,
                "pip_value": a.pip_value,
                "spread_pips": a.spread_pips,
                "yf_ticker": a.yf_ticker,
            }
            for key, a in ASSETS.items()
        ]

    def get_strategy_config(self) -> dict:
        return {
            "ema_fast_period": DEFAULT_STRATEGY.ema_fast_period,
            "ema_slow_period": DEFAULT_STRATEGY.ema_slow_period,
            "lookback_period": DEFAULT_STRATEGY.lookback_period,
            "atr_period": DEFAULT_STRATEGY.atr_period,
            "atr_sl_multiplier": DEFAULT_STRATEGY.atr_sl_multiplier,
            "atr_tp_multiplier": DEFAULT_STRATEGY.atr_tp_multiplier,
            "min_reward_risk_ratio": DEFAULT_STRATEGY.min_reward_risk_ratio,
            "breakout_min_body_pct": DEFAULT_STRATEGY.breakout_min_body_pct,
            "volume_expansion_factor": DEFAULT_STRATEGY.volume_expansion_factor,
            "retest_tolerance_pct": DEFAULT_STRATEGY.retest_tolerance_pct,
        }


def _build_equity_curve(trade_log: list, initial_balance: float) -> list:
    """Build equity curve data points from trade log."""
    curve = [{"trade": 0, "balance": initial_balance, "drawdown": 0.0}]
    balance = initial_balance
    peak = initial_balance

    for i, trade in enumerate(trade_log, 1):
        balance = trade.get("balance", balance)
        peak = max(peak, balance)
        dd = (peak - balance) / peak * 100 if peak > 0 else 0
        curve.append({
            "trade": i,
            "balance": round(balance, 2),
            "drawdown": round(dd, 2),
            "symbol": trade.get("symbol", ""),
            "result": trade.get("result", ""),
            "pnl_pct": trade.get("pnl_pct", 0),
            "timestamp": str(trade.get("timestamp", "")),
        })

    return curve


def _build_strategy_breakdown(signals: list) -> dict:
    """Build strategy performance breakdown."""
    breakdown = {}
    for s in signals:
        strat = s.get("strategy", "Unknown")
        sig_type = s.get("signal", "")
        if strat not in breakdown:
            breakdown[strat] = {"total": 0, "buy": 0, "sell": 0, "avg_confidence": 0, "confidences": []}
        breakdown[strat]["total"] += 1
        breakdown[strat][sig_type.lower()] = breakdown[strat].get(sig_type.lower(), 0) + 1
        breakdown[strat]["confidences"].append(s.get("confidence", 0))

    for strat in breakdown:
        confs = breakdown[strat].pop("confidences")
        breakdown[strat]["avg_confidence"] = round(sum(confs) / len(confs), 2) if confs else 0

    return breakdown


def _build_asset_breakdown(signals: list) -> dict:
    """Build per-asset signal breakdown."""
    breakdown = {}
    for s in signals:
        symbol = s.get("symbol", "Unknown")
        sig_type = s.get("signal", "")
        if symbol not in breakdown:
            breakdown[symbol] = {"total": 0, "buy": 0, "sell": 0}
        breakdown[symbol]["total"] += 1
        breakdown[symbol][sig_type.lower()] = breakdown[symbol].get(sig_type.lower(), 0) + 1
    return breakdown


# Singleton
trading_engine = TradingEngineService()
