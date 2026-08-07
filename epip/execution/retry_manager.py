"""Bounded broker retry orchestration."""

from epip.execution.config import ExecutionConfig
from epip.execution.models import BrokerResponse, Order
from epip.execution.protocols import BrokerAdapterProtocol


class RetryManager:
    def submit(
        self, adapter: BrokerAdapterProtocol, order: Order, config: ExecutionConfig
    ) -> tuple[BrokerResponse, int]:
        retries = 0
        response = adapter.submit(order)
        while (
            not response.accepted
            and response.message in config.retryable_messages
            and retries < config.max_retries
        ):
            retries += 1
            response = adapter.submit(order)
        return response, retries
