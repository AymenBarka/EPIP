import pytest

from epip.risk import RiskConfig
from epip.risk.analyzer import RiskAnalyzer
from epip.risk.exceptions import RiskVersionError
from epip.risk.graph import RiskGraph
from epip.risk.history import RiskHistory
from epip.risk.models import RiskSnapshot
from tests.risk.helpers import decision


def snapshot(version: int = 1) -> RiskSnapshot:
    source = decision(version=version)
    return RiskSnapshot(
        source.timestamp,
        source.symbol,
        source.timeframe,
        version,
        source.version,
        RiskAnalyzer(RiskConfig()).analyze(source),
    )


def test_serialization_round_trip() -> None:
    item = snapshot()
    assert RiskSnapshot.from_dict(item.to_dict()) == item
    assert RiskSnapshot.from_json(item.to_json()) == item
    assert item.to_json() == item.to_json()


def test_history_queries_and_version_validation() -> None:
    first, second = snapshot(), snapshot(2)
    history = RiskHistory().append(first).append(second)
    assert history.latest() == second and history.by_version(1) == first
    assert history.by_timestamp(first.timestamp) == first
    assert tuple(history.replay()) == (first, second)
    assert RiskHistory().latest() is None and history.by_version(99) is None
    with pytest.raises(RiskVersionError):
        RiskHistory().append(second)


def test_graph_traversal() -> None:
    first, second = snapshot(), snapshot(2)
    graph = RiskGraph().append(first)
    graph = graph.append(second, "EURUSD:H1:v1")
    assert graph.previous("EURUSD:H1:v2") == graph.node("EURUSD:H1:v1")
    assert graph.next("EURUSD:H1:v1") == graph.node("EURUSD:H1:v2")
    assert graph.parent("EURUSD:H1:v2") == graph.node("EURUSD:H1:v1")
    assert graph.children("EURUSD:H1:v1") == (graph.node("EURUSD:H1:v2"),)
    assert graph.linked_trade_decision("EURUSD:H1:v1") == "d-1"
    assert graph.node("missing") is None and graph.next("missing") is None
    with pytest.raises(KeyError):
        graph.append(snapshot(3), "missing")
