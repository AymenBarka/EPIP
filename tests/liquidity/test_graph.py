import pytest

from epip.liquidity.graph import LiquidityGraph
from epip.liquidity.models import LiquiditySnapshot


def snap(v: int) -> LiquiditySnapshot:
    return LiquiditySnapshot(f"2024-01-0{v}", "EURUSD", "M1", v)


def test_graph_navigation() -> None:
    graph = LiquidityGraph().append(snap(1))
    parent = graph.nodes[0].node_id
    graph = graph.append(snap(2), parent_id=parent)
    assert graph.next(parent) == graph.nodes[1]
    assert graph.previous(graph.nodes[1].node_id) == graph.nodes[0]
    assert graph.parent(graph.nodes[1].node_id) == graph.nodes[0]
    assert graph.children(parent) == (graph.nodes[1],)
    with pytest.raises(KeyError):
        graph.append(snap(3), parent_id="missing")
