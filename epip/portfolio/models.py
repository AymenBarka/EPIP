"""Immutable EPIP-015 portfolio domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class PositionDirection(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True, slots=True)
class PortfolioPosition:
    symbol: str
    quantity: float
    direction: PositionDirection
    average_price: float
    market_price: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    @property
    def signed_quantity(self) -> float:
        return self.quantity if self.direction == PositionDirection.LONG else -self.quantity

    @property
    def market_value(self) -> float:
        return self.quantity * self.market_price


@dataclass(frozen=True, slots=True)
class PortfolioExposure:
    long_exposure: float
    short_exposure: float
    gross_exposure: float
    net_exposure: float
    concentration: float


@dataclass(frozen=True, slots=True)
class PortfolioAllocation:
    symbol: str
    market_value: float
    fraction: float
    correlation_group: str | None = None


@dataclass(frozen=True, slots=True)
class PortfolioPnL:
    daily: float
    weekly: float
    monthly: float
    floating: float
    realized: float
    unrealized: float


@dataclass(frozen=True, slots=True)
class PortfolioEquity:
    initial: float
    current: float
    peak: float
    drawdown: float
    available_cash: float
    used_margin: float


@dataclass(frozen=True, slots=True)
class PortfolioMetrics:
    snapshots: int = 0
    positions: int = 0
    realized_pnl: float = 0.0
    gross_exposure: float = 0.0
    average_latency_seconds: float = 0.0
    limit_breaches: int = 0


@dataclass(frozen=True, slots=True)
class PortfolioState:
    positions: tuple[PortfolioPosition, ...]
    exposure: PortfolioExposure
    allocations: tuple[PortfolioAllocation, ...]
    pnl: PortfolioPnL
    equity: PortfolioEquity
    correlation_exposure: tuple[tuple[str, float], ...]
    limit_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    timestamp: str
    version: int
    execution_version: int
    execution_plan_id: str
    state: PortfolioState
    engine_version: str = "EPIP-015"

    def to_dict(self) -> dict[str, Any]:
        from epip.portfolio.serialization import to_dict

        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PortfolioSnapshot:
        from epip.portfolio.serialization import from_dict

        return from_dict(data)

    def to_json(self) -> str:
        from epip.portfolio.serialization import to_json

        return to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> PortfolioSnapshot:
        from epip.portfolio.serialization import from_json

        return from_json(payload)
