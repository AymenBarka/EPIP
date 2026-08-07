import pytest

from epip.execution.exceptions import IllegalOrderTransitionError
from epip.execution.models import Order, OrderSide, OrderState, OrderType
from epip.execution.state_machine import OrderStateMachine


def order() -> Order:
    return Order("o", "p", "X", OrderSide.BUY, OrderType.MARKET, 1, 10, None, None)


def test_lifecycle_and_illegal_transitions() -> None:
    machine = OrderStateMachine()
    current = order()
    for state in (
        OrderState.VALIDATED,
        OrderState.SUBMITTED,
        OrderState.ACKNOWLEDGED,
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
    ):
        assert machine.can_transition(current.state, state)
        current = machine.transition(current, state)
    with pytest.raises(IllegalOrderTransitionError):
        machine.transition(current, OrderState.CREATED)


@pytest.mark.parametrize("target", [OrderState.REJECTED, OrderState.CANCELLED, OrderState.EXPIRED])
def test_terminal_paths(target: OrderState) -> None:
    machine = OrderStateMachine()
    current = machine.transition(order(), OrderState.VALIDATED)
    if target == OrderState.EXPIRED:
        current = machine.transition(current, OrderState.SUBMITTED)
    assert machine.transition(current, target).state == target
