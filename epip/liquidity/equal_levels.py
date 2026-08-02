"""Equal-high and equal-low detection."""

from epip.liquidity.config import LiquidityConfig
from epip.liquidity.models import EqualHigh, EqualLow
from epip.swing.models import SwingSequence
from epip.swing.types import PivotType


class EqualLevelDetector:
    def detect(
        self, sequence: SwingSequence, config: LiquidityConfig
    ) -> tuple[tuple[EqualHigh, ...], tuple[EqualLow, ...]]:
        highs: list[EqualHigh] = []
        lows: list[EqualLow] = []
        for pivot in (PivotType.HIGH, PivotType.LOW):
            items = [x for x in sequence.swings if x.point.pivot_type == pivot]
            for index, first in enumerate(items):
                matches = [
                    x
                    for x in items[index:]
                    if abs(x.point.price - first.point.price) <= config.equal_threshold
                ]
                target = highs if pivot == PivotType.HIGH else lows
                if len(matches) >= config.minimum_touches and not any(
                    first.point.index in x.indices for x in target
                ):
                    args = (
                        sequence.symbol,
                        sequence.timeframe,
                        sum(x.point.price for x in matches) / len(matches),
                        tuple(x.point.index for x in matches),
                        tuple(x.point.timestamp for x in matches),
                    )
                    if pivot == PivotType.HIGH:
                        highs.append(EqualHigh(*args))
                    else:
                        lows.append(EqualLow(*args))
        return tuple(highs), tuple(lows)
