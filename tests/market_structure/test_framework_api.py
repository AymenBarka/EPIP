from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from epip.core.event_bus import EventBus
from epip.core.integrity import RelationshipIntegrityError
from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.engine import MarketStructureEngine
from epip.market_structure.exceptions import (
    HistoryError,
    InvalidBOSError,
    InvalidCHOCHError,
    InvalidRangeError,
    InvalidStructureError,
    InvalidTrendError,
    StructureVersionError,
)
from epip.market_structure.graph import StructureGraph
from epip.market_structure.history import StructureHistory
from epip.market_structure.models import (
    BreakOfStructure,
    ChangeOfCharacter,
    MarketStructure,
    MarketStructureSnapshot,
    Range,
    StructureState,
    Trend,
    TrendDirection,
)
from epip.market_structure.observers import ObserverRegistry
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope


def _structure(timestamp: str = "2024-01-01T00:00:01+00:00") -> MarketStructure:
    trend = Trend(TrendDirection.UPTREND, 1, timestamp, timestamp)
    bos = BreakOfStructure("EURUSD", "M1", timestamp, TrendDirection.UPTREND, 1.1, 1.2, 1, True)
    choch = ChangeOfCharacter(
        "EURUSD", "M1", timestamp, TrendDirection.DOWNTREND, TrendDirection.UPTREND, 1.2, 1
    )
    range_regime = Range("EURUSD", "M1", 0, 1, 1.2, 1.1, 2, 2, True)
    return MarketStructure(
        "EURUSD", "M1", trend, StructureState.UPTREND, bos, choch, range_regime, 4, 0.8
    )


def _snapshot(version: int, second: int) -> MarketStructureSnapshot:
    timestamp = f"2024-01-01T00:00:{second:02d}+00:00"
    return MarketStructureSnapshot(timestamp, _structure(timestamp), version=version)


def _swing(idx: int, classification: SwingClassification, pivot: PivotType) -> Swing:
    return Swing(
        SwingPoint(
            "EURUSD",
            "M1",
            idx,
            f"2024-01-01T00:00:{idx:02d}+00:00",
            1.1 + idx / 100,
            pivot,
            2,
            2,
        ),
        classification,
        SwingScope.EXTERNAL,
        2,
        0.01,
        2,
    )


def _sequence() -> SwingSequence:
    return SwingSequence(
        "EURUSD",
        "M1",
        (
            _swing(1, SwingClassification.SWING_LOW, PivotType.LOW),
            _swing(2, SwingClassification.HIGHER_HIGH, PivotType.HIGH),
            _swing(3, SwingClassification.HIGHER_LOW, PivotType.LOW),
            _swing(4, SwingClassification.HIGHER_HIGH, PivotType.HIGH),
        ),
    )


def test_all_public_domain_models_round_trip_deterministically() -> None:
    structure = _structure()
    snapshot = MarketStructureSnapshot(structure.updated_at, structure)
    values = (
        structure.trend,
        structure.last_bos,
        structure.last_choch,
        structure.active_range,
        structure,
        snapshot,
    )
    for value in values:
        assert value is not None
        encoded = value.to_json()
        restored = type(value).from_json(encoded)
        assert restored == value
        assert restored.to_json() == encoded


def test_structure_metadata_is_immutable_and_deterministic() -> None:
    first = _structure()
    second = _structure()
    assert first.uuid == second.uuid
    assert first.created_at == first.trend.since_timestamp
    assert first.updated_at == first.trend.last_updated_timestamp
    assert first.engine_version == "EPIP-007"
    with pytest.raises(FrozenInstanceError):
        cast(Any, first).uuid = "changed"


def test_history_is_immutable_versioned_serializable_and_replayable() -> None:
    empty = StructureHistory()
    first = empty.append(_snapshot(1, 1))
    history = first.append(_snapshot(2, 2))
    assert empty.latest() is None
    assert first.latest() == _snapshot(1, 1)
    assert history.latest() == _snapshot(2, 2)
    assert history.by_version(1) == _snapshot(1, 1)
    assert history.by_timestamp("2024-01-01T00:00:02+00:00") == _snapshot(2, 2)
    assert tuple(history.replay()) == history.snapshots
    assert StructureHistory.from_json(history.to_json()) == history
    with pytest.raises(StructureVersionError) as version_error:
        history.append(_snapshot(4, 4))
    assert version_error.value.metadata["expected"] == 3
    with pytest.raises(HistoryError):
        StructureHistory((_snapshot(1, 2), _snapshot(2, 1)))


def test_graph_supports_hierarchy_and_chronological_traversal() -> None:
    first, second, child = _snapshot(1, 1), _snapshot(2, 2), _snapshot(3, 3)
    graph = StructureGraph().append(first).append(second)
    parent_id = graph.nodes[0].node_id
    graph = graph.append(child, parent_id=parent_id)
    assert graph.next(parent_id) == graph.nodes[1]
    assert graph.previous(graph.nodes[1].node_id) == graph.nodes[0]
    assert graph.parent(graph.nodes[2].node_id) == graph.nodes[0]
    assert graph.children(parent_id) == (graph.nodes[2],)
    assert StructureGraph.from_snapshots((first, second)).nodes == graph.nodes[:2]
    with pytest.raises(RelationshipIntegrityError):
        graph.append(_snapshot(4, 4), parent_id="missing")


def test_engine_versions_history_and_notifies_optional_observers() -> None:
    received: list[MarketStructureSnapshot] = []

    class Recorder:
        def on_structure(self, snapshot: MarketStructureSnapshot) -> None:
            received.append(snapshot)

    observer = Recorder()
    registry = ObserverRegistry()
    registry.register(observer)
    registry.register(observer)
    engine = MarketStructureEngine(
        config=MarketStructureConfig(minimum_swings=4),
        event_bus=EventBus(),
        observer_registry=registry,
    )
    first = engine.process_sequence(_sequence())
    second = engine.process_sequence(_sequence())
    assert (first.version, second.version) == (1, 2)
    assert first.structure_version == 1
    assert second.created_at == second.timestamp
    assert second.engine_version == "EPIP-007"
    assert engine.history("EURUSD", "M1").snapshots == (first, second)
    assert received == [first, second]
    registry.unregister(observer)
    assert registry.observers() == ()
    engine.reset("EURUSD", "M1")
    assert engine.history("EURUSD", "M1").latest() is None


def test_domain_error_hierarchy_exposes_immutable_context() -> None:
    for error_type in (
        InvalidStructureError,
        InvalidTrendError,
        InvalidBOSError,
        InvalidCHOCHError,
        InvalidRangeError,
        StructureVersionError,
        HistoryError,
    ):
        error = error_type("failure", metadata={"symbol": "EURUSD"})
        assert error.metadata["symbol"] == "EURUSD"
        with pytest.raises(TypeError):
            cast(Any, error.metadata)["symbol"] = "GBPUSD"
