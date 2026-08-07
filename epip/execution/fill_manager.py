"""Immutable fill aggregation."""

from dataclasses import replace

from epip.execution.models import Order, OrderFill, OrderState


class FillManager:
    def apply(self, order: Order, fills: tuple[OrderFill, ...]) -> Order:
        updated = (*order.fills, *fills)
        quantity = sum(fill.quantity for fill in updated)
        state = OrderState.FILLED if quantity >= order.quantity else OrderState.PARTIALLY_FILLED
        return replace(order, fills=updated, state=state)

    def average_price(self, order: Order) -> float | None:
        quantity = order.filled_quantity
        return (
            None
            if quantity == 0
            else sum(fill.price * fill.quantity for fill in order.fills) / quantity
        )
