"""Validation utilities for swing detection pipeline."""

from __future__ import annotations

from epip.core.candle import Candle
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType


class PriceValidator:
    """Basic sanity checks on input candle prices."""

    def validate(self, candle: Candle) -> bool:
        high = float(candle.high)
        low = float(candle.low)
        return high >= low


class PivotValidator:
    """Structural checks on pivot candidates."""

    def validate(self, point: SwingPoint) -> bool:
        if point.index < 0:
            return False
        if point.left_bars <= 0 or point.right_bars <= 0:
            return False
        return point.pivot_type in (PivotType.HIGH, PivotType.LOW)


class SequenceValidator:
    """Checks continuity and alternating pivot rhythm."""

    def validate(self, sequence: SwingSequence, candidate: Swing) -> bool:
        last = sequence.last()
        if last is None:
            return True
        if candidate.point.index <= last.point.index:
            return False
        # Keep alternating polarity unless candidate is equal-structure update.
        return candidate.point.pivot_type != last.point.pivot_type
