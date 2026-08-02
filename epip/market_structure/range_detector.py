"""Range detector based on repeated equal/near-equal swings."""

from __future__ import annotations

from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.models import Range
from epip.swing.models import SwingSequence
from epip.swing.types import SwingClassification


class RangeDetector:
    """Detects sideways ranges and touch counts."""

    def detect(
        self,
        data: SwingSequence,
        config: MarketStructureConfig,
        **kwargs: object,
    ) -> Range | None:
        del kwargs
        sequence = data
        if not config.enable_range:
            return None
        if len(sequence.swings) < max(3, config.range_touch_count * 2):
            return None

        recent = sequence.swings[-(config.range_touch_count * 2 + 1) :]
        highs = [
            s
            for s in recent
            if s.classification in (SwingClassification.EQUAL_HIGH, SwingClassification.SWING_HIGH)
        ]
        lows = [
            s
            for s in recent
            if s.classification in (SwingClassification.EQUAL_LOW, SwingClassification.SWING_LOW)
        ]

        if len(highs) < config.range_touch_count or len(lows) < config.range_touch_count:
            return None

        range_high = max(item.point.price for item in highs)
        range_low = min(item.point.price for item in lows)
        if range_high - range_low <= config.equal_threshold:
            return None

        return Range(
            symbol=sequence.symbol,
            timeframe=sequence.timeframe,
            start_index=recent[0].point.index,
            end_index=recent[-1].point.index,
            range_high=range_high,
            range_low=range_low,
            touches_high=len(highs),
            touches_low=len(lows),
            active=True,
        )
