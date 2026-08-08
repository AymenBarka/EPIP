"""Immutable swing-domain value objects."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.integrity import (
    RelationshipIntegrityError,
    require_non_negative,
    require_positive,
    require_text,
)
from epip.swing.types import PivotType, SwingClassification, SwingScope


@dataclass(frozen=True, slots=True)
class SwingPoint:
    """A confirmed pivot point on the price series."""

    symbol: str
    timeframe: str
    index: int
    timestamp: str
    price: float
    pivot_type: PivotType
    left_bars: int
    right_bars: int
    confirmed: bool = True

    def __post_init__(self) -> None:
        require_text(self.symbol, "swing_point.symbol")
        require_text(self.timeframe, "swing_point.timeframe")
        require_text(self.timestamp, "swing_point.timestamp")
        require_non_negative(self.index, "swing_point.index")
        require_positive(self.price, "swing_point.price")
        require_non_negative(self.left_bars, "swing_point.left_bars")
        require_non_negative(self.right_bars, "swing_point.right_bars")


@dataclass(frozen=True, slots=True)
class Swing:
    """A classified swing ready for downstream consumption."""

    point: SwingPoint
    classification: SwingClassification
    scope: SwingScope
    distance_from_previous: int
    price_move_from_previous: float
    detection_latency_bars: int


@dataclass(frozen=True, slots=True)
class SwingSequence:
    """Ordered immutable view of detected swings per stream."""

    symbol: str
    timeframe: str
    swings: tuple[Swing, ...]

    def validate_integrity(self) -> None:
        require_text(self.symbol, "swing_sequence.symbol")
        require_text(self.timeframe, "swing_sequence.timeframe")
        indices = tuple(swing.point.index for swing in self.swings)
        if indices != tuple(sorted(indices)) or len(indices) != len(set(indices)):
            raise RelationshipIntegrityError("swing sequence indices must be unique and ordered")
        if any(swing.point.symbol != self.symbol for swing in self.swings):
            raise RelationshipIntegrityError("swing sequence contains a different symbol")
        if any(swing.point.timeframe != self.timeframe for swing in self.swings):
            raise RelationshipIntegrityError("swing sequence contains a different timeframe")

    def last(self) -> Swing | None:
        return self.swings[-1] if self.swings else None

    def last_by_pivot_type(self, pivot_type: PivotType) -> Swing | None:
        for swing in reversed(self.swings):
            if swing.point.pivot_type == pivot_type:
                return swing
        return None
