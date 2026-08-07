"""EPIP-011 Elliott domain events."""

from dataclasses import dataclass

from epip.core.events import BaseEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class ElliottEvent(BaseEvent):
    symbol: str
    timeframe: str
    version: int


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveDetected(ElliottEvent):
    wave_count: int


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveValidated(ElliottEvent):
    count_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveInvalidated(ElliottEvent):
    violation_count: int


@dataclass(frozen=True, slots=True, kw_only=True)
class AlternateCreated(ElliottEvent):
    alternate_count: int


@dataclass(frozen=True, slots=True, kw_only=True)
class CountUpdated(ElliottEvent):
    probability: float


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectionUpdated(ElliottEvent):
    target_count: int
