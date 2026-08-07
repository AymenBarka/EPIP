"""Trend detection from swing classifications."""

from __future__ import annotations

from epip.market_structure.models import TrendDirection
from epip.swing.models import SwingSequence
from epip.swing.types import SwingClassification


class TrendDetector:
    """Determines trend from the latest structural swing semantics."""

    def detect(self, data: SwingSequence, **kwargs: object) -> TrendDirection:
        del kwargs
        sequence = data
        if not sequence.swings:
            return TrendDirection.UNKNOWN

        latest = sequence.swings[-1].classification
        if latest in (SwingClassification.HIGHER_HIGH, SwingClassification.HIGHER_LOW):
            return TrendDirection.UPTREND
        if latest in (SwingClassification.LOWER_HIGH, SwingClassification.LOWER_LOW):
            return TrendDirection.DOWNTREND
        if latest in (SwingClassification.EQUAL_HIGH, SwingClassification.EQUAL_LOW):
            return TrendDirection.RANGE
        return TrendDirection.UNKNOWN
