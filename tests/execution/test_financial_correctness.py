"""Institutional execution-accounting regression tests."""

import pytest

from epip.core.integrity import RelationshipIntegrityError
from epip.execution.commission import calculate_commission
from epip.execution.fill_manager import FillManager
from epip.execution.models import (
    CommissionMode,
    Order,
    OrderFill,
    OrderSide,
    OrderState,
    OrderType,
)


def order() -> Order:
    return Order(
        "order-1",
        "plan-1",
        "EURUSD",
        OrderSide.BUY,
        OrderType.MARKET,
        10.0,
        100.0,
        None,
        None,
    )


@pytest.mark.parametrize(
    ("mode", "value", "quantity", "price", "expected"),
    [
        (CommissionMode.FIXED, 2.5, 4.0, 100.0, 2.5),
        (CommissionMode.PERCENTAGE, 0.001, 4.0, 100.0, 0.4),
        (CommissionMode.PER_LOT, 3.0, 4.0, 100.0, 12.0),
    ],
)
def test_commission_models_have_exact_declared_units(
    mode: CommissionMode,
    value: float,
    quantity: float,
    price: float,
    expected: float,
) -> None:
    assert calculate_commission(mode, value, quantity, price) == pytest.approx(expected)


def test_partial_fills_use_quantity_weighted_execution_price() -> None:
    manager = FillManager()
    first = OrderFill("fill-1", 4.0, 100.0, 1.0, "t1")
    second = OrderFill("fill-2", 6.0, 110.0, 1.5, "t2")
    partial = manager.apply(order(), (first,))
    assert partial.state == OrderState.PARTIALLY_FILLED
    assert partial.filled_quantity == 4.0

    completed = manager.apply(partial, (second,))
    assert completed.state == OrderState.FILLED
    assert completed.filled_quantity == 10.0
    assert manager.average_price(completed) == 106.0
    assert sum(fill.commission for fill in completed.fills) == 2.5


def test_duplicate_and_overfill_are_rejected() -> None:
    manager = FillManager()
    first = OrderFill("fill-1", 6.0, 100.0, 0.0, "t1")
    partial = manager.apply(order(), (first,))
    with pytest.raises(RelationshipIntegrityError):
        manager.apply(partial, (first,))
    with pytest.raises(RelationshipIntegrityError):
        manager.apply(
            partial,
            (OrderFill("fill-2", 5.0, 100.0, 0.0, "t2"),),
        )
