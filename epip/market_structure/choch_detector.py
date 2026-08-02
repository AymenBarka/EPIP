"""Change of Character detector."""

from __future__ import annotations

from dataclasses import dataclass

from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.models import ChangeOfCharacter, TrendDirection
from epip.swing.models import SwingSequence
from epip.swing.types import SwingClassification


@dataclass(frozen=True, slots=True)
class _CHOCHKey:
    symbol: str
    timeframe: str
    previous: TrendDirection
    new: TrendDirection
    swing_index: int


class CHOCHDetector:
    """Detects first reversal signal from previous trend."""

    def __init__(self) -> None:
        self._last_key: _CHOCHKey | None = None
        self.last_duplicate = False

    def detect(
        self,
        data: SwingSequence,
        *,
        previous_trend: TrendDirection,
        config: MarketStructureConfig,
        **kwargs: object,
    ) -> ChangeOfCharacter | None:
        del kwargs
        sequence = data
        self.last_duplicate = False
        if not config.enable_choch or not sequence.swings:
            return None
        if previous_trend not in (TrendDirection.UPTREND, TrendDirection.DOWNTREND):
            return None

        latest = sequence.swings[-1]
        new_trend = self._reversal_trend(previous_trend, latest.classification)
        if new_trend is None:
            return None

        key = _CHOCHKey(
            symbol=sequence.symbol,
            timeframe=sequence.timeframe,
            previous=previous_trend,
            new=new_trend,
            swing_index=latest.point.index,
        )
        if self._last_key == key:
            self.last_duplicate = True
            return None
        self._last_key = key

        origin_swing = sequence.swings[-2] if len(sequence.swings) >= 2 else None
        destination_swing = latest

        return ChangeOfCharacter(
            symbol=sequence.symbol,
            timeframe=sequence.timeframe,
            timestamp=latest.point.timestamp,
            previous_trend=previous_trend,
            new_trend=new_trend,
            trigger_price=latest.point.price,
            swing_index=latest.point.index,
            origin_swing=origin_swing,
            destination_swing=destination_swing,
        )

    def _reversal_trend(
        self,
        previous_trend: TrendDirection,
        latest: SwingClassification,
    ) -> TrendDirection | None:
        if previous_trend == TrendDirection.UPTREND and latest in (
            SwingClassification.LOWER_LOW,
            SwingClassification.LOWER_HIGH,
        ):
            return TrendDirection.DOWNTREND
        if previous_trend == TrendDirection.DOWNTREND and latest in (
            SwingClassification.HIGHER_HIGH,
            SwingClassification.HIGHER_LOW,
        ):
            return TrendDirection.UPTREND
        return None
