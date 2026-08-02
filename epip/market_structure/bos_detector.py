"""Break Of Structure detector."""

from __future__ import annotations

from dataclasses import dataclass

from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.models import BreakOfStructure, TrendDirection
from epip.swing.models import Swing, SwingSequence
from epip.swing.types import SwingClassification


@dataclass(frozen=True, slots=True)
class _BOSKey:
    symbol: str
    timeframe: str
    direction: TrendDirection
    swing_index: int


class BOSDetector:
    """Detects bullish/bearish BOS and suppresses duplicates."""

    def __init__(self) -> None:
        self._last_key: _BOSKey | None = None
        self.last_duplicate = False

    def detect(
        self,
        data: SwingSequence,
        *,
        trend: TrendDirection,
        config: MarketStructureConfig,
        **kwargs: object,
    ) -> BreakOfStructure | None:
        del kwargs
        sequence = data
        self.last_duplicate = False
        if not config.enable_bos or not sequence.swings:
            return None

        latest = sequence.swings[-1]
        if (
            latest.classification == SwingClassification.HIGHER_HIGH
            and trend == TrendDirection.UPTREND
        ):
            return self._build_bos(sequence, latest, TrendDirection.UPTREND, config)

        if (
            latest.classification == SwingClassification.LOWER_LOW
            and trend == TrendDirection.DOWNTREND
        ):
            return self._build_bos(sequence, latest, TrendDirection.DOWNTREND, config)

        return None

    def _build_bos(
        self,
        sequence: SwingSequence,
        latest: Swing,
        direction: TrendDirection,
        config: MarketStructureConfig,
    ) -> BreakOfStructure | None:
        reference = self._reference_price(sequence, direction)
        if reference is None:
            return None

        if config.confirmation_required:
            if direction == TrendDirection.UPTREND and latest.point.price <= reference:
                return None
            if direction == TrendDirection.DOWNTREND and latest.point.price >= reference:
                return None

        key = _BOSKey(
            symbol=sequence.symbol,
            timeframe=sequence.timeframe,
            direction=direction,
            swing_index=latest.point.index,
        )
        if self._last_key == key:
            self.last_duplicate = True
            return None
        self._last_key = key

        origin_swing = sequence.swings[-2] if len(sequence.swings) >= 2 else None
        destination_swing = latest

        return BreakOfStructure(
            symbol=sequence.symbol,
            timeframe=sequence.timeframe,
            timestamp=latest.point.timestamp,
            direction=direction,
            reference_price=reference,
            break_price=latest.point.price,
            swing_index=latest.point.index,
            confirmed=True,
            origin_swing=origin_swing,
            destination_swing=destination_swing,
        )

    def _reference_price(self, sequence: SwingSequence, direction: TrendDirection) -> float | None:
        if len(sequence.swings) < 2:
            return None
        previous = sequence.swings[-2]
        if direction == TrendDirection.UPTREND:
            return previous.point.price
        return previous.point.price
