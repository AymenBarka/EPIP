"""Immutable EPIP-015 portfolio domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from epip.core.integrity import (
    RelationshipIntegrityError,
    integrity_deserializer,
    require_finite,
    require_non_negative,
    require_positive,
    require_text,
    require_unit_interval,
    require_version,
)


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

    def __post_init__(self) -> None:
        require_text(self.symbol, "portfolio_position.symbol")
        require_positive(self.quantity, "portfolio_position.quantity")
        require_positive(self.average_price, "portfolio_position.average_price")
        require_positive(self.market_price, "portfolio_position.market_price")
        require_finite(self.realized_pnl, "portfolio_position.realized_pnl")
        require_finite(self.unrealized_pnl, "portfolio_position.unrealized_pnl")

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

    def __post_init__(self) -> None:
        require_non_negative(self.long_exposure, "portfolio_exposure.long")
        require_non_negative(self.short_exposure, "portfolio_exposure.short")
        require_non_negative(self.gross_exposure, "portfolio_exposure.gross")
        require_finite(self.net_exposure, "portfolio_exposure.net")
        require_unit_interval(self.concentration, "portfolio_exposure.concentration")


@dataclass(frozen=True, slots=True)
class PortfolioAllocation:
    symbol: str
    market_value: float
    fraction: float
    correlation_group: str | None = None

    def __post_init__(self) -> None:
        require_text(self.symbol, "portfolio_allocation.symbol")
        require_non_negative(self.market_value, "portfolio_allocation.market_value")
        require_unit_interval(self.fraction, "portfolio_allocation.fraction")


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

    def __post_init__(self) -> None:
        require_non_negative(self.initial, "portfolio_equity.initial")
        require_non_negative(self.current, "portfolio_equity.current")
        require_non_negative(self.peak, "portfolio_equity.peak")
        require_unit_interval(self.drawdown, "portfolio_equity.drawdown")
        require_non_negative(self.available_cash, "portfolio_equity.available_cash")
        require_non_negative(self.used_margin, "portfolio_equity.used_margin")
        if self.peak < self.current:
            raise RelationshipIntegrityError("portfolio equity peak is below current equity")


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

    def validate_integrity(self) -> None:
        symbols = tuple(position.symbol for position in self.positions)
        if len(symbols) != len(set(symbols)):
            raise RelationshipIntegrityError("portfolio contains duplicated position symbols")
        allocation_symbols = tuple(item.symbol for item in self.allocations)
        if len(allocation_symbols) != len(set(allocation_symbols)):
            raise RelationshipIntegrityError("portfolio contains duplicated allocations")
        for name, value in self.correlation_exposure:
            require_text(name, "portfolio_state.correlation_group")
            require_non_negative(value, "portfolio_state.correlation_exposure")


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    timestamp: str
    version: int
    execution_version: int
    execution_plan_id: str
    state: PortfolioState
    engine_version: str = "EPIP-015"

    def __post_init__(self) -> None:
        self.validate_integrity()

    def validate_integrity(self) -> None:
        require_text(self.timestamp, "portfolio_snapshot.timestamp")
        require_version(self.version, "portfolio_snapshot.version")
        require_version(self.execution_version, "portfolio_snapshot.execution_version")
        require_text(self.execution_plan_id, "portfolio_snapshot.execution_plan_id")
        require_text(self.engine_version, "portfolio_snapshot.engine_version")
        self.state.validate_integrity()

    def to_dict(self) -> dict[str, Any]:
        from epip.portfolio.serialization import to_dict

        return to_dict(self)

    @classmethod
    @integrity_deserializer
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
