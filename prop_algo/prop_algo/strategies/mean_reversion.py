"""
Strategy 3: Range Mean Reversion
=================================
Best for low-volatility / ranging markets.

Rules:
  1. Identify clear horizontal range (20-bar high/low)
  2. SELL at upper boundary with rejection
  3. BUY at lower boundary with rejection
  4. Stop outside the range
  5. Target mid-range or opposite boundary
  6. Exit if range breaks with volume

Expected: Win rate 55-65%, RR 1:1 to 1:2
"""

import pandas as pd
import numpy as np
from typing import List

from ..strategies.base import BaseStrategy, TradeSignal, SignalType
from ..config.settings import DEFAULT_STRATEGY


class MeanReversionStrategy(BaseStrategy):
    """Range-bound mean reversion strategy."""

    def __init__(self, config=None):
        super().__init__(name="Mean_Reversion")
        self.config = config or DEFAULT_STRATEGY
        self.range_period = 30               # Bars to define range
        self.range_threshold_atr = 4.0       # Max range width in ATR units
        self.boundary_zone_pct = 0.10        # Top/bottom 10% of range
        self.min_range_bars = 15             # Min bars in range to validate

    def _identify_range(self, df: pd.DataFrame, idx: int):
        """
        Identify if market is in a defined range.
        Returns (range_high, range_low, is_ranging) tuple.
        """
        start = max(0, idx - self.range_period)
        subset = df.iloc[start:idx + 1]

        range_high = subset["high"].max()
        range_low = subset["low"].min()
        range_width = range_high - range_low
        atr = df.iloc[idx].get("atr", 0)

        if atr <= 0:
            return range_high, range_low, False

        # Range is valid if width is within threshold
        is_ranging = range_width <= atr * self.range_threshold_atr

        # Additional: most candles should be within the range
        within = ((subset["close"] >= range_low) & (subset["close"] <= range_high)).sum()
        pct_within = within / len(subset)
        is_ranging = is_ranging and pct_within >= 0.80

        return range_high, range_low, is_ranging

    def _is_rejection_candle(self, row, direction: int) -> bool:
        """
        Detect rejection (pin bar / wick rejection) at boundary.
        direction: 1 = rejection at support (bullish), -1 = rejection at resistance (bearish)
        """
        if row["candle_range"] == 0:
            return False

        upper_wick = row["high"] - max(row["open"], row["close"])
        lower_wick = min(row["open"], row["close"]) - row["low"]

        if direction == 1:  # Bullish rejection (long lower wick)
            return lower_wick / row["candle_range"] >= 0.5 and row["is_bullish"]
        elif direction == -1:  # Bearish rejection (long upper wick)
            return upper_wick / row["candle_range"] >= 0.5 and row["is_bearish"]

        return False

    def generate_signals(self, df: pd.DataFrame, symbol: str) -> List[TradeSignal]:
        """
        Generate mean reversion signals at range boundaries.
        """
        signals = []

        if len(df) < self.range_period + 10:
            return signals

        for i in range(self.range_period, len(df)):
            row = df.iloc[i]

            if pd.isna(row.get("atr")) or row["atr"] <= 0:
                continue

            range_high, range_low, is_ranging = self._identify_range(df, i)

            if not is_ranging:
                continue

            range_width = range_high - range_low
            boundary_zone = range_width * self.boundary_zone_pct
            mid_range = (range_high + range_low) / 2
            atr = row["atr"]

            # ─── BUY at lower boundary ────────────────────────
            if row["low"] <= range_low + boundary_zone:
                if self._is_rejection_candle(row, direction=1):
                    entry = row["close"]
                    sl = range_low - atr * 0.5  # Just outside range
                    risk = entry - sl
                    tp = mid_range  # Target mid-range
                    rr = abs(tp - entry) / risk if risk > 0 else 0

                    if rr >= 1.0:  # Mean reversion can accept 1:1
                        confidence = 0.5
                        if row.get("volume_ratio", 1) < 1.0:
                            confidence += 0.10  # Low volume = still ranging
                        if row["body_pct"] >= 0.4:
                            confidence += 0.10
                        confidence = min(confidence, 1.0)

                        signals.append(TradeSignal(
                            timestamp=df.index[i],
                            symbol=symbol,
                            signal=SignalType.BUY,
                            strategy_name=self.name,
                            entry_price=entry,
                            stop_loss=sl,
                            take_profit=tp,
                            risk_reward_ratio=rr,
                            confidence=confidence,
                            reason=f"Mean reversion BUY at range low ({range_low:.2f}). Target mid-range.",
                            atr_value=atr,
                            trend_direction=0,
                            volume_confirmed=row.get("volume_ratio", 1) < 1.2,
                        ))

            # ─── SELL at upper boundary ───────────────────────
            if row["high"] >= range_high - boundary_zone:
                if self._is_rejection_candle(row, direction=-1):
                    entry = row["close"]
                    sl = range_high + atr * 0.5
                    risk = sl - entry
                    tp = mid_range
                    rr = abs(entry - tp) / risk if risk > 0 else 0

                    if rr >= 1.0:
                        confidence = 0.5
                        if row.get("volume_ratio", 1) < 1.0:
                            confidence += 0.10
                        if row["body_pct"] >= 0.4:
                            confidence += 0.10
                        confidence = min(confidence, 1.0)

                        signals.append(TradeSignal(
                            timestamp=df.index[i],
                            symbol=symbol,
                            signal=SignalType.SELL,
                            strategy_name=self.name,
                            entry_price=entry,
                            stop_loss=sl,
                            take_profit=tp,
                            risk_reward_ratio=rr,
                            confidence=confidence,
                            reason=f"Mean reversion SELL at range high ({range_high:.2f}). Target mid-range.",
                            atr_value=atr,
                            trend_direction=0,
                            volume_confirmed=row.get("volume_ratio", 1) < 1.2,
                        ))

        return signals
