from dataclasses import dataclass

from epip.core.events import BaseEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class FibonacciEvent(BaseEvent):
    symbol: str
    timeframe: str


@dataclass(frozen=True, slots=True, kw_only=True)
class FibonacciComputed(FibonacciEvent):
    version: int


@dataclass(frozen=True, slots=True, kw_only=True)
class GoldenZoneDetected(FibonacciEvent):
    low: float
    high: float


@dataclass(frozen=True, slots=True, kw_only=True)
class OTEFound(FibonacciEvent):
    low: float
    high: float


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtensionComputed(FibonacciEvent):
    level_count: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfluenceUpdated(FibonacciEvent):
    score: float
