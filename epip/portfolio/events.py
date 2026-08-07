"""EPIP-015 portfolio events."""

from dataclasses import dataclass

from epip.core.events import BaseEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioEvent(BaseEvent):
    version: int
    execution_plan_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioUpdated(PortfolioEvent):
    positions: int


@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioRebalanced(PortfolioEvent):
    symbols: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ExposureExceeded(PortfolioEvent):
    gross_exposure: float


@dataclass(frozen=True, slots=True, kw_only=True)
class RiskLimitReached(PortfolioEvent):
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class AllocationChanged(PortfolioEvent):
    symbol: str
    allocation: float
