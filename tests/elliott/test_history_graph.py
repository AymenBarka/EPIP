import pytest

from epip.core.event_bus import EventBus
from epip.elliott import ElliottConfig, ElliottWaveEngine
from epip.elliott.exceptions import WaveVersionError
from epip.elliott.graph import WaveGraph
from epip.elliott.history import WaveHistory
from tests.elliott.helpers import market_context


def test_history_and_graph_navigation() -> None:
    engine = ElliottWaveEngine(config=ElliottConfig(), event_bus=EventBus())
    first = engine.process(market_context())
    second = engine.process(market_context())
    history = engine.history("EURUSD", "M15")
    assert history.latest() == second
    assert history.by_version(1) == first
    assert history.by_timestamp(first.timestamp) == first
    assert tuple(history.replay()) == (first, second)
    graph = engine.graph("EURUSD", "M15")
    first_id, second_id = graph.nodes[0].node_id, graph.nodes[1].node_id
    assert graph.next(first_id) == graph.nodes[1]
    assert graph.previous(second_id) == graph.nodes[0]
    assert graph.alternates(first_id) and graph.projections(first_id)
    child_graph = WaveGraph().append(first).append(second, first_id)
    assert child_graph.parent(second_id) == child_graph.nodes[0]
    assert child_graph.children(first_id) == (child_graph.nodes[1],)
    with pytest.raises(KeyError):
        WaveGraph().append(first, "missing")
    with pytest.raises(WaveVersionError):
        WaveHistory().append(second)
