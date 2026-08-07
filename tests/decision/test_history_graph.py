import pytest

from epip.core.event_bus import EventBus
from epip.decision import DecisionConfig, DecisionEngine
from epip.decision.exceptions import DecisionVersionError
from epip.decision.graph import DecisionGraph
from epip.decision.history import DecisionHistory
from tests.decision.helpers import snapshots


def test_history_and_graph() -> None:
    engine = DecisionEngine(config=DecisionConfig(), event_bus=EventBus())
    first = engine.process(*snapshots())
    second = engine.process(*snapshots())
    history = engine.history("EURUSD", "M15")
    assert history.latest() == second
    assert history.by_version(1) == first
    assert history.by_timestamp(first.timestamp) == first
    assert tuple(history.replay()) == (first, second)
    graph = engine.graph("EURUSD", "M15")
    first_id, second_id = graph.nodes[0].node_id, graph.nodes[1].node_id
    assert graph.next(first_id) == graph.nodes[1]
    assert graph.previous(second_id) == graph.nodes[0]
    assert graph.linked_context(first_id) == "context:v1"
    assert graph.linked_elliott(first_id) == "elliott:v1"
    child_graph = DecisionGraph().append(first).append(second, first_id)
    assert child_graph.parent(second_id) == child_graph.nodes[0]
    assert child_graph.children(first_id) == (child_graph.nodes[1],)
    with pytest.raises(KeyError):
        DecisionGraph().append(first, "missing")
    with pytest.raises(DecisionVersionError):
        DecisionHistory().append(second)
