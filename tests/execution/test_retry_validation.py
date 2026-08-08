from dataclasses import replace

import pytest

from epip.execution.config import ExecutionConfig
from epip.execution.exceptions import InvalidExecutionInputError
from epip.execution.models import BrokerResponse, Order
from epip.execution.order_manager import OrderManager
from epip.execution.retry_manager import RetryManager
from epip.execution.validators import validate_order, validate_plan
from tests.execution.helpers import position_plan


class TemporaryBroker:
    def __init__(self) -> None:
        self.calls = 0

    def submit(self, order: Order) -> BrokerResponse:
        self.calls += 1
        return BrokerResponse(
            self.calls == 3,
            "id" if self.calls == 3 else None,
            "OK" if self.calls == 3 else "TEMPORARY",
        )

    def cancel(self, order: Order) -> BrokerResponse:
        return BrokerResponse(True, "id", "OK")


def test_retry() -> None:
    broker = TemporaryBroker()
    order = OrderManager().create(position_plan(), ExecutionConfig())
    response, retries = RetryManager().submit(broker, order, ExecutionConfig(max_retries=2))
    assert response.accepted and retries == 2 and broker.calls == 3


def test_validation_edges() -> None:
    with pytest.raises(InvalidExecutionInputError):
        validate_plan(position_plan(accepted=False))
    order = OrderManager().create(position_plan(), ExecutionConfig())
    with pytest.raises(ValueError, match="order.quantity"):
        invalid = replace(order, quantity=0)
        validate_order(invalid)
