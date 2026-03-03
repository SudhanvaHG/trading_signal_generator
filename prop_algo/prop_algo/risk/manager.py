"""
Risk Manager Module
=====================
Enforces ALL prop firm rules from the handbook:
  - 0.5% risk per trade
  - Max 2 trades per day
  - Stop after 2 consecutive losses
  - 2% daily loss cap
  - 8-10% overall drawdown limit
  - Minimum 1:2 RR filter
  - Position sizing calculator
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional
import logging

from ..config.settings import RiskConfig, DEFAULT_RISK
from ..strategies.base import TradeSignal, SignalType

logger = logging.getLogger(__name__)


@dataclass
class DailyStats:
    """Track daily trading statistics."""
    date: date = None
    trades_taken: int = 0
    consecutive_losses: int = 0
    daily_pnl_pct: float = 0.0
    is_locked: bool = False
    lock_reason: str = ""


@dataclass
class AccountState:
    """Track overall account state."""
    initial_balance: float = 10000.0
    current_balance: float = 10000.0
    peak_balance: float = 10000.0
    total_trades: int = 0
    total_wins: int = 0
    total_losses: int = 0
    current_drawdown_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    is_blown: bool = False


class RiskManager:
    """
    Central risk management engine.
    Filters signals and calculates position sizes.
    """

    def __init__(self, config: RiskConfig = None, initial_balance: float = 10000.0):
        self.config = config or DEFAULT_RISK
        self.account = AccountState(
            initial_balance=initial_balance,
            current_balance=initial_balance,
            peak_balance=initial_balance,
        )
        self.daily_stats: dict[date, DailyStats] = {}
        self.trade_log: List[dict] = []

    def _get_daily_stats(self, trade_date: date) -> DailyStats:
        """Get or create daily stats for a date."""
        if trade_date not in self.daily_stats:
            self.daily_stats[trade_date] = DailyStats(date=trade_date)
        return self.daily_stats[trade_date]

    def check_signal_allowed(self, signal: TradeSignal) -> tuple[bool, str]:
        """
        Check if a signal passes ALL risk rules.

        Returns:
            (allowed: bool, reason: str)
        """
        # ─── Rule 0: Account blown? ──────────────────────────
        if self.account.is_blown:
            return False, "BLOCKED: Account breached maximum drawdown limit"

        trade_date = signal.timestamp.date() if hasattr(signal.timestamp, 'date') else signal.timestamp

        daily = self._get_daily_stats(trade_date)

        # ─── Rule 1: Daily lock check ────────────────────────
        if daily.is_locked:
            return False, f"BLOCKED: Day locked — {daily.lock_reason}"

        # ─── Rule 2: Max trades per day ──────────────────────
        if daily.trades_taken >= self.config.max_trades_per_day:
            return False, f"BLOCKED: Max {self.config.max_trades_per_day} trades/day reached"

        # ─── Rule 3: Consecutive losses check ────────────────
        if daily.consecutive_losses >= self.config.max_consecutive_losses:
            daily.is_locked = True
            daily.lock_reason = f"{self.config.max_consecutive_losses} consecutive losses"
            return False, f"BLOCKED: {self.config.max_consecutive_losses} consecutive losses — day stopped"

        # ─── Rule 4: Daily loss cap ──────────────────────────
        if abs(daily.daily_pnl_pct) >= self.config.max_daily_loss_pct and daily.daily_pnl_pct < 0:
            daily.is_locked = True
            daily.lock_reason = f"Daily loss cap ({self.config.max_daily_loss_pct}%) hit"
            return False, f"BLOCKED: Daily loss limit of {self.config.max_daily_loss_pct}% reached"

        # ─── Rule 5: Overall drawdown ────────────────────────
        if self.account.current_drawdown_pct >= self.config.max_overall_drawdown_pct:
            self.account.is_blown = True
            return False, f"BLOCKED: Overall drawdown {self.account.current_drawdown_pct:.1f}% exceeds max"

        # ─── Rule 6: Minimum RR check ────────────────────────
        if signal.risk_reward_ratio < self.config.min_reward_risk_ratio:
            return False, f"BLOCKED: RR {signal.risk_reward_ratio:.1f} below minimum {self.config.min_reward_risk_ratio}"

        return True, "APPROVED"

    def calculate_position_size(
        self, signal: TradeSignal, pip_value: float = 0.0001
    ) -> dict:
        """
        Calculate position size based on 0.5% risk rule.

        Args:
            signal: TradeSignal with entry and SL
            pip_value: Value per pip for the asset

        Returns:
            Dict with lots, units, risk_amount, etc.
        """
        balance = self.account.current_balance
        risk_amount = balance * (self.config.risk_per_trade_pct / 100)
        sl_distance = abs(signal.entry_price - signal.stop_loss)

        if sl_distance <= 0:
            return {"lots": 0, "units": 0, "risk_amount": 0, "error": "Invalid SL distance"}

        # Units = risk_amount / sl_distance
        units = risk_amount / sl_distance

        # Standard lot = 100,000 units for forex
        lots = units / 100000 if pip_value <= 0.01 else units

        return {
            "lots": round(lots, 4),
            "units": round(units, 2),
            "risk_amount": round(risk_amount, 2),
            "risk_pct": self.config.risk_per_trade_pct,
            "sl_distance": round(sl_distance, 6),
            "balance": round(balance, 2),
        }

    def record_trade_result(
        self, signal: TradeSignal, result: str, pnl_pct: float
    ):
        """
        Record a trade result and update all state.

        Args:
            signal: The original signal
            result: 'WIN' or 'LOSS'
            pnl_pct: P&L as percentage of account
        """
        trade_date = signal.timestamp.date() if hasattr(signal.timestamp, 'date') else signal.timestamp
        daily = self._get_daily_stats(trade_date)

        # Update daily
        daily.trades_taken += 1
        daily.daily_pnl_pct += pnl_pct

        if result == "LOSS":
            daily.consecutive_losses += 1
            self.account.total_losses += 1
        else:
            daily.consecutive_losses = 0  # Reset on win
            self.account.total_wins += 1

        # Update account
        self.account.total_trades += 1
        pnl_amount = self.account.current_balance * (pnl_pct / 100)
        self.account.current_balance += pnl_amount

        # Update peak and drawdown
        if self.account.current_balance > self.account.peak_balance:
            self.account.peak_balance = self.account.current_balance

        self.account.current_drawdown_pct = (
            (self.account.peak_balance - self.account.current_balance)
            / self.account.peak_balance * 100
        )
        self.account.max_drawdown_pct = max(
            self.account.max_drawdown_pct,
            self.account.current_drawdown_pct
        )

        # Log
        self.trade_log.append({
            "timestamp": signal.timestamp,
            "symbol": signal.symbol,
            "strategy": signal.strategy_name,
            "signal": signal.signal.value,
            "entry": signal.entry_price,
            "sl": signal.stop_loss,
            "tp": signal.take_profit,
            "rr": signal.risk_reward_ratio,
            "result": result,
            "pnl_pct": round(pnl_pct, 3),
            "balance": round(self.account.current_balance, 2),
            "drawdown_pct": round(self.account.current_drawdown_pct, 2),
        })

    def get_summary(self) -> dict:
        """Get comprehensive account summary."""
        win_rate = (
            self.account.total_wins / self.account.total_trades * 100
            if self.account.total_trades > 0 else 0
        )
        total_return = (
            (self.account.current_balance - self.account.initial_balance)
            / self.account.initial_balance * 100
        )

        return {
            "initial_balance": self.account.initial_balance,
            "current_balance": round(self.account.current_balance, 2),
            "total_return_pct": round(total_return, 2),
            "total_trades": self.account.total_trades,
            "wins": self.account.total_wins,
            "losses": self.account.total_losses,
            "win_rate_pct": round(win_rate, 1),
            "max_drawdown_pct": round(self.account.max_drawdown_pct, 2),
            "current_drawdown_pct": round(self.account.current_drawdown_pct, 2),
            "account_blown": self.account.is_blown,
            "challenge_target_pct": self.config.challenge_profit_target_pct,
            "challenge_passed": total_return >= self.config.challenge_profit_target_pct,
        }

    def get_trade_log_df(self) -> pd.DataFrame:
        """Return trade log as DataFrame."""
        if not self.trade_log:
            return pd.DataFrame()
        return pd.DataFrame(self.trade_log)
