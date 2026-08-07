"""Execution validation."""

from epip.execution.exceptions import InvalidExecutionInputError
from epip.execution.models import Order
from epip.risk.models import PositionPlan


def validate_plan(plan: PositionPlan) -> None:
    if not plan.accepted:
        raise InvalidExecutionInputError("only accepted PositionPlan instances may execute")
    if plan.position_size.quantity <= 0 or plan.entry_price <= 0:
        raise InvalidExecutionInputError("position quantity and entry price must be positive")


def validate_order(order: Order) -> None:
    if order.quantity <= 0 or order.requested_price <= 0:
        raise InvalidExecutionInputError("order quantity and price must be positive")
