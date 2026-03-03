"""
Base Strategy Module
Abstract interface that all strategies must implement.
Ensures consistent signal format across the system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum
import pandas as pd


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradeSignal:
    """Standardized trade signal output from any strategy."""
    timestamp: pd.Timestamp
    symbol: str
    signal: SignalType
    strategy_name: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    confidence: float              # 0.0 to 1.0
    reason: str                    # Human-readable signal reason
    atr_value: float = 0.0
    trend_direction: int = 0       # 1 = bullish, -1 = bearish
    volume_confirmed: bool = False

    @property
    def risk_pips(self) -> float:
        return abs(self.entry_price - self.stop_loss)

    @property
    def reward_pips(self) -> float:
        return abs(self.take_profit - self.entry_price)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "signal": self.signal.value,
            "strategy": self.strategy_name,
            "entry": round(self.entry_price, 5),
            "stop_loss": round(self.stop_loss, 5),
            "take_profit": round(self.take_profit, 5),
            "rr_ratio": round(self.risk_reward_ratio, 2),
            "confidence": round(self.confidence, 2),
            "trend": self.trend_direction,
            "volume_ok": self.volume_confirmed,
            "reason": self.reason,
        }


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    Every strategy MUST implement generate_signals().
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signals(
        self, df: pd.DataFrame, symbol: str
    ) -> list[TradeSignal]:
        """
        Analyze data and return list of trade signals.

        Args:
            df: OHLCV DataFrame with technical indicators
            symbol: Asset symbol

        Returns:
            List of TradeSignal objects
        """
        pass

    def __repr__(self):
        return f"<Strategy: {self.name}>"
