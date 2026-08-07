from epip.core.event_bus import EventBus
from epip.decision import DecisionConfig, DecisionEngine
from epip.decision.events import DecisionCreated, DecisionExecuted, DecisionExpired, DecisionUpdated
from tests.decision.helpers import snapshots


def test_decision_lifecycle_events() -> None:
    bus = EventBus()
    engine = DecisionEngine(config=DecisionConfig(), event_bus=bus)
    first = engine.process(*snapshots())
    engine.process(*snapshots())
    engine.mark_executed(first)
    engine.mark_expired(first)
    history = bus.event_history()
    assert any(isinstance(event, DecisionCreated) for event in history)
    assert any(isinstance(event, DecisionUpdated) for event in history)
    assert any(isinstance(event, DecisionExecuted) for event in history)
    assert any(isinstance(event, DecisionExpired) for event in history)
