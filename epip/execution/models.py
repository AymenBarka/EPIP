"""Immutable EPIP-014 execution domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


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

    def to_dict(self) -> dict[str, Any]:
        from epip.execution.serialization import to_dict

        return to_dict(self)

    @classmethod
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
