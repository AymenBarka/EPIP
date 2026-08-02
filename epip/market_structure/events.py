"""Market structure domain events."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.events import BaseEvent
from epip.market_structure.models import StructureState, TrendDirection


@dataclass(frozen=True, slots=True, kw_only=True)
class MarketStructureEvent(BaseEvent):
    """Common immutable metadata for all market structure events."""

    event_id: str = ""
    engine_version: str = "EPIP-007"
    source: str = "market-structure-engine"

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "event_id", self.event_id or self.id)


@dataclass(frozen=True, slots=True, kw_only=True)
class StructureDetected(MarketStructureEvent):
    symbol: str
    timeframe: str
    trend: TrendDirection
    state: StructureState


@dataclass(frozen=True, slots=True, kw_only=True)
class BOSDetected(MarketStructureEvent):
    symbol: str
    timeframe: str
    direction: TrendDirection
    break_price: float
    reference_price: float


@dataclass(frozen=True, slots=True, kw_only=True)
class CHOCHDetected(MarketStructureEvent):
    symbol: str
    timeframe: str
    previous_trend: TrendDirection
    new_trend: TrendDirection


@dataclass(frozen=True, slots=True, kw_only=True)
class TrendChanged(MarketStructureEvent):
    symbol: str
    timeframe: str
    previous_trend: TrendDirection
    new_trend: TrendDirection


@dataclass(frozen=True, slots=True, kw_only=True)
class RangeDetected(MarketStructureEvent):
    symbol: str
    timeframe: str
    range_high: float
    range_low: float
    touches_high: int
    touches_low: int


@dataclass(frozen=True, slots=True, kw_only=True)
class StructureReset(MarketStructureEvent):
    symbol: str
    timeframe: str
