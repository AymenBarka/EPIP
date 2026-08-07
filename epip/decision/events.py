"""EPIP-012 decision events."""

from dataclasses import dataclass

from epip.core.events import BaseEvent
from epip.decision.models import DecisionAction


@dataclass(frozen=True, slots=True, kw_only=True)
class TradeDecisionEvent(BaseEvent):
    symbol: str
    timeframe: str
    version: int
    decision_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DecisionCreated(TradeDecisionEvent):
    action: DecisionAction


@dataclass(frozen=True, slots=True, kw_only=True)
class DecisionUpdated(TradeDecisionEvent):
    action: DecisionAction


@dataclass(frozen=True, slots=True, kw_only=True)
class DecisionInvalidated(TradeDecisionEvent):
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DecisionExecuted(TradeDecisionEvent):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class DecisionExpired(TradeDecisionEvent):
    pass
