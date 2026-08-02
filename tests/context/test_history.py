import pytest

from epip.context import MarketContextConfig, MarketContextEngine
from epip.context.exceptions import MarketContextVersionError
from epip.context.history import MarketContextHistory
from epip.core.event_bus import EventBus
from tests.context.helpers import official_inputs


def test_history_queries_and_replay() -> None:
    engine = MarketContextEngine(config=MarketContextConfig(), event_bus=EventBus())
    first = engine.process(*official_inputs())
    second = engine.process(*official_inputs())
    history = engine.history("EURUSD", "M15")
    assert history.latest() == second
    assert history.by_version(1) == first
    assert history.by_timestamp("2") == first
    assert tuple(history.replay()) == (first, second)
    with pytest.raises(MarketContextVersionError):
        MarketContextHistory().append(second)
