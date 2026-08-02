from epip.context import MarketContextConfig, MarketContextEngine
from epip.context.events import ConfluenceUpdated, ContextCreated, ContextUpdated
from epip.core.event_bus import EventBus
from tests.context.helpers import official_inputs


def test_engine_publishes_context_events() -> None:
    bus = EventBus()
    engine = MarketContextEngine(config=MarketContextConfig(), event_bus=bus)
    engine.process(*official_inputs())
    engine.process(*official_inputs())
    history = bus.event_history()
    assert any(isinstance(event, ContextCreated) for event in history)
    assert any(isinstance(event, ContextUpdated) for event in history)
    assert sum(isinstance(event, ConfluenceUpdated) for event in history) == 2
