import pytest

from epip.core.event_bus import EventBus
from epip.portfolio import PortfolioEngine, PortfolioGraph, PortfolioHistory, PortfolioSnapshot
from epip.portfolio.exceptions import PortfolioVersionError
from tests.portfolio.helpers import execution


def snapshots() -> tuple[PortfolioSnapshot, PortfolioSnapshot]:
    engine = PortfolioEngine(event_bus=EventBus())
    return engine.process(execution()), engine.process(execution(version=2))


def test_serialization_round_trip() -> None:
    first, _ = snapshots()
    assert PortfolioSnapshot.from_dict(first.to_dict()) == first
    assert PortfolioSnapshot.from_json(first.to_json()) == first
    assert first.to_json() == first.to_json()


def test_history() -> None:
    first, second = snapshots()
    history = PortfolioHistory().append(first).append(second)
    assert history.latest() == second and history.by_version(1) == first
    assert history.by_timestamp("t1") == first and tuple(history.replay()) == (first, second)
    assert PortfolioHistory().latest() is None and history.by_version(99) is None
    with pytest.raises(PortfolioVersionError):
        PortfolioHistory().append(second)


def test_graph() -> None:
    first, second = snapshots()
    graph = PortfolioGraph().append(first)
    graph = graph.append(second, "portfolio:v1")
    assert graph.previous("portfolio:v2") == graph.node("portfolio:v1")
    assert graph.next("portfolio:v1") == graph.node("portfolio:v2")
    assert graph.parent("portfolio:v2") == graph.node("portfolio:v1")
    assert graph.children("portfolio:v1") == (graph.node("portfolio:v2"),)
    assert graph.linked_execution("portfolio:v1") == "p-1"
    assert graph.node("missing") is None and graph.next("missing") is None
    with pytest.raises(KeyError):
        graph.append(second, "missing")
