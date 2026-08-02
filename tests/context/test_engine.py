import pytest

from epip.context import MarketContextConfig, MarketContextEngine
from epip.context.exceptions import InvalidMarketContextInputError
from epip.core.event_bus import EventBus
from tests.context.helpers import official_inputs


def test_engine_versions_multi_symbol_and_timeframe() -> None:
    engine = MarketContextEngine(config=MarketContextConfig(), event_bus=EventBus())
    first = engine.process(*official_inputs())
    second = engine.process(*official_inputs())
    other = engine.process(*official_inputs("GBPUSD", "H1"))
    assert (first.version.context, second.version.context, other.version.context) == (1, 2, 1)
    assert engine.snapshot("EURUSD", "M15") == second
    assert engine.metrics().contexts == 3


def test_engine_rejects_mixed_streams() -> None:
    engine = MarketContextEngine(config=MarketContextConfig(), event_bus=EventBus())
    _, structure, liquidity, fibonacci = official_inputs()
    other_swings, _, _, _ = official_inputs("GBPUSD")
    with pytest.raises(InvalidMarketContextInputError):
        engine.process(other_swings, structure, liquidity, fibonacci)
