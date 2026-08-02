from epip.core.event_bus import EventBus
from epip.elliott import ElliottConfig, ElliottWaveEngine
from epip.elliott.events import (
    AlternateCreated,
    CountUpdated,
    ProjectionUpdated,
    WaveDetected,
    WaveValidated,
)
from tests.elliott.helpers import market_context


def test_engine_publishes_analysis_events() -> None:
    bus = EventBus()
    ElliottWaveEngine(config=ElliottConfig(), event_bus=bus).process(market_context())
    history = bus.event_history()
    assert any(isinstance(event, WaveDetected) for event in history)
    assert any(isinstance(event, WaveValidated) for event in history)
    assert any(isinstance(event, AlternateCreated) for event in history)
    assert any(isinstance(event, CountUpdated) for event in history)
    assert any(isinstance(event, ProjectionUpdated) for event in history)
