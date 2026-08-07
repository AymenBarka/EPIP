"""Explicit order lifecycle state machine."""

from dataclasses import replace

from epip.execution.exceptions import IllegalOrderTransitionError
from epip.execution.models import Order, OrderState

_TRANSITIONS: dict[OrderState, frozenset[OrderState]] = {
    OrderState.CREATED: frozenset((OrderState.VALIDATED, OrderState.REJECTED)),
    OrderState.VALIDATED: frozenset(
        (OrderState.SUBMITTED, OrderState.REJECTED, OrderState.CANCELLED)
    ),
    OrderState.SUBMITTED: frozenset(
        (OrderState.ACKNOWLEDGED, OrderState.REJECTED, OrderState.CANCELLED, OrderState.EXPIRED)
    ),
    OrderState.ACKNOWLEDGED: frozenset(
        (OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCELLED, OrderState.EXPIRED)
    ),
    OrderState.PARTIALLY_FILLED: frozenset(
        (OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCELLED, OrderState.EXPIRED)
    ),
    OrderState.FILLED: frozenset(),
    OrderState.CANCELLED: frozenset(),
    OrderState.REJECTED: frozenset(),
    OrderState.EXPIRED: frozenset(),
}


class OrderStateMachine:
    def can_transition(self, source: OrderState, target: OrderState) -> bool:
        return target in _TRANSITIONS[source]

    def transition(self, order: Order, target: OrderState) -> Order:
        if not self.can_transition(order.state, target):
            raise IllegalOrderTransitionError(f"illegal transition: {order.state} -> {target}")
        return replace(order, state=target)
