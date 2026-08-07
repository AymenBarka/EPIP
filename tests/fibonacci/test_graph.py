from epip.fibonacci.graph import FibonacciGraph
from tests.fibonacci.test_history import snap


def test_graph_navigation() -> None:
    g = FibonacciGraph().append(snap(1), (1, 2))
    p = g.nodes[0].node_id
    g = g.append(snap(2), (2, 3), p)
    assert g.next(p) == g.nodes[1]
    assert g.previous(g.nodes[1].node_id) == g.nodes[0]
    assert g.parent(g.nodes[1].node_id) == g.nodes[0]
    assert g.children(p) == (g.nodes[1],)
