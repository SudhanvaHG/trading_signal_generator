"""
Strategy 1: Daily Breakout + Retest Momentum
=============================================
From the handbook - institutional-style breakout system.

Rules:
  1. TREND FILTER: 200 EMA on 4H — above = buy only, below = sell only
  2. MARK LEVELS: Previous day high & low
  3. BREAKOUT: Price breaks PDH/PDL cleanly
  4. RETEST: Pullback to breakout level
  5. ENTRY: Bullish/bearish engulfing on 15m confirmation
  6. SL/TP: SL below pullback low, TP at 2R minimum

Expected: Win rate 45-55%, RR 1:2 to 1:3, PF 1.4-1.8
"""

import pandas as pd
import numpy as np
from typing import List

from ..strategies.base import BaseStrategy, TradeSignal, SignalType
from ..config.settings import DEFAULT_STRATEGY


class BreakoutRetestStrategy(BaseStrategy):
    """
    Daily Breakout + Retest Momentum Strategy.
    The primary strategy designed for prop firm challenges.
    """

    def __init__(self, config=None):
        super().__init__(name="Breakout_Retest")
        self.config = config or DEFAULT_STRATEGY

    def _detect_breakout(self, row, prev_row) -> int:
        """
        Detect if current bar broke above resistance or below support.
        Uses rolling high/low and previous candle levels.
        Returns: 1 (bullish breakout), -1 (bearish breakout), 0 (none)
        """
        if pd.isna(row.get("resistance")) or pd.isna(row.get("support")):
            return 0

        # Bullish breakout: close above recent resistance zone
        prev_res = row.get("prev_candle_high", row.get("prev_high", 0))
        prev_sup = row.get("prev_candle_low", row.get("prev_low", 0))

        if pd.isna(prev_res) or pd.isna(prev_sup):
            return 0

        # Check resistance breakout
        if row["close"] > prev_res and prev_row["close"] <= prev_res:
            return 1

        # Check support breakdown  
        if row["close"] < prev_sup and prev_row["close"] >= prev_sup:
            return -1

        return 0

    def _detect_retest(self, df: pd.DataFrame, idx: int, breakout_level: float,
                       direction: int) -> bool:
        """
        Check if price has pulled back to retest the breakout level.
        """
        if idx < 2:
            return False

        row = df.iloc[idx]
        tolerance = breakout_level * (self.config.retest_tolerance_pct / 100)

        if direction == 1:  # Bullish — price should pull back DOWN to level
            retest_zone_low = breakout_level - tolerance
            retest_zone_high = breakout_level + tolerance
            if retest_zone_low <= row["low"] <= retest_zone_high:
                return True

        elif direction == -1:  # Bearish — price should pull back UP to level
            retest_zone_low = breakout_level - tolerance
            retest_zone_high = breakout_level + tolerance
            if retest_zone_low <= row["high"] <= retest_zone_high:
                return True

        return False

    def _detect_engulfing(self, row, direction: int) -> bool:
        """
        Detect bullish or bearish confirmation candle.
        Relaxed for daily: strong directional candle is enough.
        """
        if pd.isna(row.get("body_pct")):
            return False

        solid_candle = row["body_pct"] >= self.config.breakout_min_body_pct

        if direction == 1:
            return row["is_bullish"] and solid_candle
        elif direction == -1:
            return row["is_bearish"] and solid_candle

        return False

    def _check_volume(self, row) -> bool:
        """Check if volume exceeds expansion threshold."""
        if pd.isna(row.get("volume_ratio")):
            return True  # Pass if no volume data (some forex feeds)
        return row["volume_ratio"] >= self.config.volume_expansion_factor

    def generate_signals(self, df: pd.DataFrame, symbol: str) -> List[TradeSignal]:
        """
        Generate breakout + retest signals.

        Logic flow:
          1. Scan for breakout of previous high/low
          2. Track breakout levels awaiting retest
          3. On retest + engulfing confirmation → signal
          4. Filter by trend (200 EMA) and volume
        """
        signals = []

        if len(df) < self.config.ema_slow_period + 10:
            return signals

        # State tracking: pending breakouts awaiting retest
        pending_breakouts = []  # (index, level, direction, timestamp)

        for i in range(self.config.ema_slow_period + 1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i - 1]

            # Skip if indicators are NaN
            if pd.isna(row.get("ema_slow")) or pd.isna(row.get("atr")):
                continue

            # ─── Step 1: Trend Filter (200 EMA) ──────────────
            trend = row["trend"]  # 1 = bullish, -1 = bearish

            # ─── Step 2: Detect New Breakouts ─────────────────
            breakout = self._detect_breakout(row, prev_row)

            if breakout == 1 and trend >= 0:  # Allow in bullish or neutral trend
                pending_breakouts.append({
                    "idx": i,
                    "level": prev_row["high"],
                    "direction": 1,
                    "timestamp": df.index[i],
                    "age": 0,
                })
            elif breakout == -1 and trend <= 0:  # Allow in bearish or neutral trend
                pending_breakouts.append({
                    "idx": i,
                    "level": prev_row["low"],
                    "direction": -1,
                    "timestamp": df.index[i],
                    "age": 0,
                })

            # ─── Step 3: Check Pending Breakouts for Retest ───
            new_pending = []
            for bp in pending_breakouts:
                bp["age"] += 1

                # Expire after 10 bars (too old)
                if bp["age"] > 10:
                    continue

                # Check for retest
                if self._detect_retest(df, i, bp["level"], bp["direction"]):
                    # ─── Step 4: Engulfing Confirmation ───────
                    if self._detect_engulfing(row, bp["direction"]):
                        volume_ok = self._check_volume(row)
                        atr = row["atr"]

                        # ─── Step 5: Calculate SL & TP ───────
                        if bp["direction"] == 1:  # BUY
                            entry = row["close"]
                            sl = entry - (atr * self.config.atr_sl_multiplier)
                            risk = entry - sl
                            tp = entry + (risk * self.config.min_reward_risk_ratio)
                            sig_type = SignalType.BUY
                        else:  # SELL
                            entry = row["close"]
                            sl = entry + (atr * self.config.atr_sl_multiplier)
                            risk = sl - entry
                            tp = entry - (risk * self.config.min_reward_risk_ratio)
                            sig_type = SignalType.SELL

                        rr = abs(tp - entry) / abs(entry - sl) if abs(entry - sl) > 0 else 0

                        # Only signal if RR meets minimum
                        if rr >= self.config.min_reward_risk_ratio:
                            # Confidence scoring
                            confidence = 0.5
                            if row["ema_alignment"] == bp["direction"]:
                                confidence += 0.15  # EMA alignment bonus
                            if volume_ok:
                                confidence += 0.15  # Volume confirmation bonus
                            if row["body_pct"] >= 0.65:
                                confidence += 0.10  # Strong candle body
                            if bp["age"] <= 5:
                                confidence += 0.10  # Fresh breakout bonus

                            confidence = min(confidence, 1.0)

                            reason = (
                                f"{'Bullish' if bp['direction'] == 1 else 'Bearish'} breakout "
                                f"of {bp['level']:.2f} + retest + engulfing. "
                                f"Trend={'UP' if trend == 1 else 'DOWN'}. "
                                f"Vol={'OK' if volume_ok else 'WEAK'}."
                            )

                            signals.append(TradeSignal(
                                timestamp=df.index[i],
                                symbol=symbol,
                                signal=sig_type,
                                strategy_name=self.name,
                                entry_price=entry,
                                stop_loss=sl,
                                take_profit=tp,
                                risk_reward_ratio=rr,
                                confidence=confidence,
                                reason=reason,
                                atr_value=atr,
                                trend_direction=trend,
                                volume_confirmed=volume_ok,
                            ))
                        # Remove this pending (consumed)
                        continue

                new_pending.append(bp)
            pending_breakouts = new_pending

        return signals
