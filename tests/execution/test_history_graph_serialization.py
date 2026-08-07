import pytest

from epip.core.event_bus import EventBus
from epip.execution import ExecutionEngine, ExecutionGraph, ExecutionHistory, ExecutionSnapshot
from epip.execution.exceptions import ExecutionVersionError
from tests.execution.helpers import position_plan


def snapshots() -> tuple[ExecutionSnapshot, ExecutionSnapshot]:
    engine = ExecutionEngine(event_bus=EventBus())
    return (
        engine.execute(position_plan(), timestamp="t1"),
        engine.execute(position_plan(), timestamp="t2"),
    )


def test_serialization() -> None:
    first, _ = snapshots()
    assert ExecutionSnapshot.from_dict(first.to_dict()) == first
    assert ExecutionSnapshot.from_json(first.to_json()) == first


def test_history() -> None:
    first, second = snapshots()
    history = ExecutionHistory().append(first).append(second)
    assert history.latest() == second and history.by_version(1) == first
    assert history.by_timestamp("t1") == first and tuple(history.replay()) == (first, second)
    assert ExecutionHistory().latest() is None and history.by_version(9) is None
    with pytest.raises(ExecutionVersionError):
        ExecutionHistory().append(second)


def test_graph() -> None:
    first, second = snapshots()
    graph = ExecutionGraph().append(first)
    graph = graph.append(second, "EURUSD:v1")
    assert graph.previous("EURUSD:v2") == graph.node("EURUSD:v1")
    assert graph.next("EURUSD:v1") == graph.node("EURUSD:v2")
    assert graph.parent("EURUSD:v2") == graph.node("EURUSD:v1")
    assert graph.children("EURUSD:v1") == (graph.node("EURUSD:v2"),)
    assert graph.linked_position_plan("EURUSD:v1") == "p-1"
    assert graph.node("none") is None and graph.next("none") is None
    with pytest.raises(KeyError):
        graph.append(second, "none")
