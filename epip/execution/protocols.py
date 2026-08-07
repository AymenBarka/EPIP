"""Execution protocols."""

from typing import Protocol, runtime_checkable

from epip.execution.models import BrokerResponse, ExecutionSnapshot, Order
from epip.risk.models import PositionPlan


@runtime_checkable
class BrokerAdapterProtocol(Protocol):
    def submit(self, order: Order) -> BrokerResponse: ...
    def cancel(self, order: Order) -> BrokerResponse: ...


class ExecutionEngineProtocol(Protocol):
    def execute(
        self, plan: PositionPlan, *, timestamp: str, **observations: float
    ) -> ExecutionSnapshot: ...
