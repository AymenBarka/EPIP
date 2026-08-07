"""PositionPlan to Order mapping."""

from epip.execution.config import ExecutionConfig
from epip.execution.models import Order, OrderSide
from epip.risk.models import PositionPlan


class OrderManager:
    def create(self, plan: PositionPlan, config: ExecutionConfig) -> Order:
        side = OrderSide.LONG if plan.action in ("LONG", "BUY") else OrderSide.SHORT
        return Order(
            f"order-{plan.plan_id}",
            plan.plan_id,
            plan.symbol,
            side,
            config.default_order_type,
            plan.position_size.quantity,
            plan.entry_price,
            (
                plan.entry_price
                if config.default_order_type.value in ("LIMIT", "STOP_LIMIT")
                else None
            ),
            (
                plan.stop_loss.price
                if config.default_order_type.value in ("STOP", "STOP_LIMIT")
                else None
            ),
        )
