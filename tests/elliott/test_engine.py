import pytest

from epip.core.event_bus import EventBus
from epip.elliott import ElliottConfig, ElliottWaveEngine
from epip.elliott.exceptions import InvalidElliottInputError
from tests.elliott.helpers import market_context


def test_engine_processes_market_context_and_isolates_streams() -> None:
    engine = ElliottWaveEngine(config=ElliottConfig(), event_bus=EventBus())
    first = engine.process(market_context())
    second = engine.process(market_context())
    other = engine.process(market_context(symbol="GBPUSD", timeframe="H1"))
    assert (first.version, second.version, other.version) == (1, 2, 1)
    assert engine.snapshot("EURUSD", "M15") == second
    assert engine.metrics().analyses == 3


def test_engine_rejects_invalid_context_version() -> None:
    context = market_context()
    invalid = context.__class__(
        context.timestamp, context.version.__class__(0, 1, 1, 1), context.context
    )
    with pytest.raises(InvalidElliottInputError):
        ElliottWaveEngine(config=ElliottConfig(), event_bus=EventBus()).process(invalid)
