from epip.core.event_bus import EventBus
from epip.execution import (
    ExecutionCompleted,
    ExecutionEngine,
    OrderCancelled,
    OrderFilled,
    OrderRejected,
    OrderState,
)
from epip.execution.models import BrokerResponse, Order
from tests.execution.helpers import position_plan


class RejectingBroker:
    def submit(self, order: Order) -> BrokerResponse:
        return BrokerResponse(False, None, "DENIED")

    def cancel(self, order: Order) -> BrokerResponse:
        return BrokerResponse(False, None, "DENIED")


class RestingBroker:
    def submit(self, order: Order) -> BrokerResponse:
        return BrokerResponse(True, "resting-1", "ACKNOWLEDGED")

    def cancel(self, order: Order) -> BrokerResponse:
        return BrokerResponse(True, "resting-1", "CANCELLED")


def test_engine_executes_tracks_and_publishes() -> None:
    bus = EventBus()
    engine = ExecutionEngine(event_bus=bus)
    first = engine.execute(position_plan(), timestamp="t1")
    second = engine.execute(position_plan(), timestamp="t2")
    assert first.report.completed and second.version == 2
    assert engine.snapshot("EURUSD") == second
    assert engine.history("EURUSD").latest() == second
    assert engine.graph("EURUSD").previous("EURUSD:v2") is not None
    assert engine.metrics().orders == 2 and engine.metrics().filled == 2
    assert any(isinstance(event, OrderFilled) for event in bus.event_history())
    assert any(isinstance(event, ExecutionCompleted) for event in bus.event_history())


def test_rejection_and_cancel() -> None:
    bus = EventBus()
    rejected = ExecutionEngine(event_bus=bus, broker=RejectingBroker())
    result = rejected.execute(position_plan(), timestamp="t")
    assert result.report.order.state == OrderState.REJECTED
    assert any(isinstance(event, OrderRejected) for event in bus.event_history())
    engine = ExecutionEngine(event_bus=bus, broker=RestingBroker())
    engine.execute(position_plan(), timestamp="t")
    cancelled = engine.cancel("EURUSD", timestamp="t2")
    assert cancelled.report.order.state == OrderState.CANCELLED
    assert any(isinstance(event, OrderCancelled) for event in bus.event_history())
