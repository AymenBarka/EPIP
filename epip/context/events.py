"""EPIP-010 Market Context domain events."""

from dataclasses import dataclass

from epip.context.snapshot import InstitutionalBias, MarketPhase
from epip.core.events import BaseEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class MarketContextEvent(BaseEvent):
    symbol: str
    timeframe: str
    version: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextCreated(MarketContextEvent):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextUpdated(MarketContextEvent):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class BiasChanged(MarketContextEvent):
    previous: InstitutionalBias
    current: InstitutionalBias


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseChanged(MarketContextEvent):
    previous: MarketPhase
    current: MarketPhase


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfluenceUpdated(MarketContextEvent):
    score: float
