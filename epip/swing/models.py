"""Immutable swing-domain value objects."""

from __future__ import annotations

from dataclasses import dataclass

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

    def last(self) -> Swing | None:
        return self.swings[-1] if self.swings else None

    def last_by_pivot_type(self, pivot_type: PivotType) -> Swing | None:
        for swing in reversed(self.swings):
            if swing.point.pivot_type == pivot_type:
                return swing
        return None
