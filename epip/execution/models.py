"""Immutable EPIP-014 execution domain objects."""

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
    require_version,
)


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"
    BUY = "BUY"
    SELL = "SELL"


class OrderState(StrEnum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class SlippageMode(StrEnum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"
    DYNAMIC = "DYNAMIC"


class CommissionMode(StrEnum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"
    PER_LOT = "PER_LOT"


@dataclass(frozen=True, slots=True)
class ExecutionReason:
    code: str
    message: str
    accepted: bool


@dataclass(frozen=True, slots=True)
class OrderFill:
    fill_id: str
    quantity: float
    price: float
    commission: float
    timestamp: str

    def __post_init__(self) -> None:
        require_text(self.fill_id, "fill.id")
        require_positive(self.quantity, "fill.quantity")
        require_positive(self.price, "fill.price")
        require_non_negative(self.commission, "fill.commission")
        require_text(self.timestamp, "fill.timestamp")


@dataclass(frozen=True, slots=True)
class Order:
    order_id: str
    plan_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    requested_price: float
    limit_price: float | None
    stop_price: float | None
    state: OrderState = OrderState.CREATED
    fills: tuple[OrderFill, ...] = ()

    def __post_init__(self) -> None:
        self.validate_integrity()

    def validate_integrity(self) -> None:
        require_text(self.order_id, "order.id")
        require_text(self.plan_id, "order.plan_id")
        require_text(self.symbol, "order.symbol")
        require_positive(self.quantity, "order.quantity")
        require_positive(self.requested_price, "order.requested_price")
        if self.limit_price is not None:
            require_positive(self.limit_price, "order.limit_price")
        if self.stop_price is not None:
            require_positive(self.stop_price, "order.stop_price")
        if self.filled_quantity > self.quantity:
            raise RelationshipIntegrityError("filled quantity exceeds requested quantity")
        fill_ids = tuple(fill.fill_id for fill in self.fills)
        if len(fill_ids) != len(set(fill_ids)):
            raise RelationshipIntegrityError("order contains duplicated fill identifiers")

    @property
    def filled_quantity(self) -> float:
        return sum(fill.quantity for fill in self.fills)


@dataclass(frozen=True, slots=True)
class BrokerResponse:
    accepted: bool
    broker_order_id: str | None
    message: str
    fills: tuple[OrderFill, ...] = ()


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    order: Order
    requested_quantity: float
    filled_quantity: float
    average_fill_price: float | None
    slippage: float
    commission: float
    completed: bool
    reasons: tuple[ExecutionReason, ...]

    def __post_init__(self) -> None:
        require_positive(self.requested_quantity, "report.requested_quantity")
        require_non_negative(self.filled_quantity, "report.filled_quantity")
        if self.average_fill_price is not None:
            require_positive(self.average_fill_price, "report.average_fill_price")
        require_finite(self.slippage, "report.slippage")
        require_non_negative(self.commission, "report.commission")
        if self.filled_quantity > self.requested_quantity:
            raise RelationshipIntegrityError("report fill exceeds requested quantity")
        if self.filled_quantity != self.order.filled_quantity:
            raise RelationshipIntegrityError("report and order filled quantities differ")


@dataclass(frozen=True, slots=True)
class ExecutionStatistics:
    orders: int = 0
    filled: int = 0
    rejected: int = 0
    retries: int = 0
    average_latency_seconds: float = 0.0
    average_slippage: float = 0.0
    total_commission: float = 0.0


@dataclass(frozen=True, slots=True)
class ExecutionSnapshot:
    timestamp: str
    symbol: str
    version: int
    position_plan_id: str
    report: ExecutionReport
    engine_version: str = "EPIP-014"

    def __post_init__(self) -> None:
        self.validate_integrity()

    def validate_integrity(self) -> None:
        require_text(self.timestamp, "execution_snapshot.timestamp")
        require_text(self.symbol, "execution_snapshot.symbol")
        require_version(self.version, "execution_snapshot.version")
        require_text(self.position_plan_id, "execution_snapshot.position_plan_id")
        require_text(self.engine_version, "execution_snapshot.engine_version")
        self.report.order.validate_integrity()
        if self.symbol != self.report.order.symbol:
            raise RelationshipIntegrityError("execution snapshot and order symbols differ")
        if self.position_plan_id != self.report.order.plan_id:
            raise RelationshipIntegrityError("execution snapshot and order plan identifiers differ")

    def to_dict(self) -> dict[str, Any]:
        from epip.execution.serialization import to_dict

        return to_dict(self)

    @classmethod
    @integrity_deserializer
    def from_dict(cls, data: dict[str, Any]) -> ExecutionSnapshot:
        from epip.execution.serialization import from_dict

        return from_dict(data)

    def to_json(self) -> str:
        from epip.execution.serialization import to_json

        return to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> ExecutionSnapshot:
        from epip.execution.serialization import from_json

        return from_json(payload)
