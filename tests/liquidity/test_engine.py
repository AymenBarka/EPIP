import pytest

from epip.core.event_bus import EventBus
from epip.liquidity import LiquidityConfig, LiquidityEngine
from epip.liquidity.events import LiquidityDetected
from epip.liquidity.exceptions import InvalidLiquidityInputError
from tests.liquidity.helpers import sequence, structure


def test_engine_multi_stream_events_and_metrics() -> None:
    bus = EventBus()
    engine = LiquidityEngine(config=LiquidityConfig(), event_bus=bus)
    first = engine.process(structure(), sequence())
    second = engine.process(structure(), sequence())
    assert (first.version, second.version) == (1, 2)
    assert engine.snapshot("EURUSD", "M1") == second
    assert engine.metrics().pools >= 2
    assert any(isinstance(x, LiquidityDetected) for x in bus.event_history())
    gbp = engine.process(structure("GBPUSD", "M5"), sequence(symbol="GBPUSD", timeframe="M5"))
    assert gbp.symbol == "GBPUSD"


def test_invalid_input_and_scope_filters() -> None:
    engine = LiquidityEngine(config=LiquidityConfig(internal_only=True), event_bus=EventBus())
    with pytest.raises(InvalidLiquidityInputError):
        engine.process(structure(), sequence(symbol="GBPUSD"))
    assert all(x.scope.value == "INTERNAL" for x in engine.process(structure(), sequence()).levels)
