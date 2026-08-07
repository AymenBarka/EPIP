"""Deterministic default paper-trading adapter."""

from threading import RLock

from epip.execution.commission import calculate_commission
from epip.execution.config import ExecutionConfig
from epip.execution.models import BrokerResponse, Order, OrderFill
from epip.execution.slippage import apply_slippage


class PaperTradingAdapter:
    def __init__(self, config: ExecutionConfig | None = None) -> None:
        self._config = config or ExecutionConfig()
        self._sequence = 0
        self._lock = RLock()

    def submit(self, order: Order) -> BrokerResponse:
        with self._lock:
            self._sequence += 1
            price = apply_slippage(
                order.requested_price,
                order.side,
                self._config.slippage_mode,
                self._config.slippage_value,
            )
            commission = calculate_commission(
                self._config.commission_mode, self._config.commission_value, order.quantity, price
            )
            fill = OrderFill(
                f"paper-fill-{self._sequence}",
                order.quantity,
                price,
                commission,
                f"paper-{self._sequence}",
            )
            return BrokerResponse(True, f"paper-{self._sequence}", "FILLED", (fill,))

    def cancel(self, order: Order) -> BrokerResponse:
        return BrokerResponse(True, order.order_id, "CANCELLED")
