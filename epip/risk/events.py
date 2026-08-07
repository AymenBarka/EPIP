"""EPIP-013 risk events."""

from dataclasses import dataclass

from epip.core.events import BaseEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class RiskEvent(BaseEvent):
    symbol: str
    decision_id: str
    plan_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PositionPlanned(RiskEvent):
    accepted: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class RiskAccepted(RiskEvent):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class RiskRejected(RiskEvent):
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ExposureExceeded(RiskEvent):
    exposure: float


@dataclass(frozen=True, slots=True, kw_only=True)
class DrawdownExceeded(RiskEvent):
    drawdown: float
