"""EPIP-014 execution events."""

from dataclasses import dataclass

from epip.core.events import BaseEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionEvent(BaseEvent):
    symbol: str
    order_id: str
    plan_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderCreated(ExecutionEvent):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderSubmitted(ExecutionEvent):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderFilled(ExecutionEvent):
    quantity: float


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderRejected(ExecutionEvent):
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderCancelled(ExecutionEvent):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionCompleted(ExecutionEvent):
    commission: float
