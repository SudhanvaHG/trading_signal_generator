"""
Strategy 2: EMA Trend Pullback
================================
Simple but powerful trend-following strategy.

Rules:
  1. 50 EMA above 200 EMA → only BUY
  2. 50 EMA below 200 EMA → only SELL
  3. Wait for pullback to 50 EMA zone
  4. Enter on bullish/bearish confirmation candle
  5. Stop below recent swing
  6. Target 1:2 minimum RR

Expected: Win rate 45-55%, very prop-firm-friendly.
"""

import pandas as pd
import numpy as np
from typing import List

from ..strategies.base import BaseStrategy, TradeSignal, SignalType
from ..config.settings import DEFAULT_STRATEGY


class EMATrendPullbackStrategy(BaseStrategy):
    """
    Trend Pullback strategy using 50/200 EMA crossover
    with pullback entries to the 50 EMA zone.
    """

    def __init__(self, config=None):
        super().__init__(name="EMA_Trend_Pullback")
        self.config = config or DEFAULT_STRATEGY
        self.pullback_zone_atr_factor = 1.0  # How close to 50 EMA counts as pullback

    def _is_pullback_to_ema(self, row, direction: int) -> bool:
        """Check if price has pulled back near the 50 EMA zone."""
        if pd.isna(row.get("ema_fast")) or pd.isna(row.get("atr")):
            return False

        zone_width = row["atr"] * self.pullback_zone_atr_factor

        if direction == 1:  # Bullish — low should touch/near 50 EMA
            return row["low"] <= row["ema_fast"] + zone_width
        elif direction == -1:  # Bearish — high should touch/near 50 EMA
            return row["high"] >= row["ema_fast"] - zone_width

        return False

    def _is_confirmation_candle(self, row, direction: int) -> bool:
        """Check if current candle confirms the direction."""
        if direction == 1:
            return (
                row["is_bullish"]
                and row["body_pct"] >= self.config.breakout_min_body_pct
            )
        elif direction == -1:
            return (
                row["is_bearish"]
                and row["body_pct"] >= self.config.breakout_min_body_pct
            )
        return False

    def _find_recent_swing(self, df: pd.DataFrame, idx: int,
                           direction: int, lookback: int = 10) -> float:
        """Find recent swing low (for buys) or swing high (for sells)."""
        start = max(0, idx - lookback)
        subset = df.iloc[start:idx + 1]

        if direction == 1:
            return subset["low"].min()
        else:
            return subset["high"].max()

    def generate_signals(self, df: pd.DataFrame, symbol: str) -> List[TradeSignal]:
        """
        Generate EMA trend pullback signals.

        Logic:
          1. Determine trend from EMA alignment
          2. Detect pullback to 50 EMA zone
          3. Confirm with strong directional candle
          4. Set SL at recent swing, TP at 2R
        """
        signals = []

        if len(df) < self.config.ema_slow_period + 10:
            return signals

        for i in range(self.config.ema_slow_period + 1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i - 1]

            if pd.isna(row.get("ema_slow")) or pd.isna(row.get("ema_fast")) or pd.isna(row.get("atr")):
                continue

            # ─── Step 1: EMA Alignment (Trend Filter) ─────────
            ema_dir = row["ema_alignment"]  # 1=bullish, -1=bearish

            if ema_dir == 0:
                continue

            # ─── Step 2: Detect Pullback + Confirmation ─────────
            if self._is_pullback_to_ema(row, ema_dir):
                # Check for confirmation candle while in pullback zone
                if self._is_confirmation_candle(row, ema_dir):
                    atr = row["atr"]

                    # ─── Step 3: SL & TP ──────────────────
                    swing = self._find_recent_swing(df, i, ema_dir)

                    if ema_dir == 1:  # BUY
                        entry = row["close"]
                        sl = min(swing, entry - atr * self.config.atr_sl_multiplier)
                        if sl >= entry:
                            sl = entry - atr * self.config.atr_sl_multiplier
                        risk = entry - sl
                        tp = entry + risk * self.config.min_reward_risk_ratio
                        sig_type = SignalType.BUY
                    else:  # SELL
                        entry = row["close"]
                        sl = max(swing, entry + atr * self.config.atr_sl_multiplier)
                        if sl <= entry:
                            sl = entry + atr * self.config.atr_sl_multiplier
                        risk = sl - entry
                        tp = entry - risk * self.config.min_reward_risk_ratio
                        sig_type = SignalType.SELL

                    rr = abs(tp - entry) / abs(entry - sl) if abs(entry - sl) > 0 else 0

                    if rr >= self.config.min_reward_risk_ratio:
                        confidence = 0.5
                        if row["trend"] == ema_dir:
                            confidence += 0.15
                        vol_ok = row.get("volume_ratio", 1.0) >= 1.0
                        if vol_ok:
                            confidence += 0.10
                        if row["body_pct"] >= 0.6:
                            confidence += 0.10
                        ema_spread = abs(row["ema_fast"] - row["ema_slow"]) / row["close"] * 100
                        if ema_spread > 1.0:
                            confidence += 0.15
                        confidence = min(confidence, 1.0)

                        reason = (
                            f"EMA Trend {'UP' if ema_dir == 1 else 'DOWN'}: "
                            f"Pullback to 50 EMA zone + confirmation candle. "
                            f"EMA spread={ema_spread:.2f}%."
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
                            trend_direction=ema_dir,
                            volume_confirmed=vol_ok,
                        ))

        return signals
