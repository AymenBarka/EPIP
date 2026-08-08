import pytest

from epip.context import MarketContextConfig, MarketContextEngine
from epip.context.graph import MarketContextGraph
from epip.core.event_bus import EventBus
from epip.core.integrity import RelationshipIntegrityError
from tests.context.helpers import official_inputs


def test_graph_traversal_and_links() -> None:
    engine = MarketContextEngine(config=MarketContextConfig(), event_bus=EventBus())
    first = engine.process(*official_inputs())
    second = engine.process(*official_inputs())
    graph = engine.graph("EURUSD", "M15")
    first_id, second_id = graph.nodes[0].node_id, graph.nodes[1].node_id
    assert graph.next(first_id) == graph.nodes[1]
    assert graph.previous(second_id) == graph.nodes[0]
    child_graph = MarketContextGraph().append(first).append(second, first_id)
    assert child_graph.parent(second_id) == child_graph.nodes[0]
    assert child_graph.children(first_id) == (child_graph.nodes[1],)
    assert child_graph.nodes[0].linked_snapshots
    with pytest.raises(RelationshipIntegrityError):
        MarketContextGraph().append(first, "missing")
