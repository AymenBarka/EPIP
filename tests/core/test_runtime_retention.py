"""Tests for transparent runtime retention adoption."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from epip.core.event_bus import EventBus
from epip.core.retention import (
    CleanupTrigger,
    CompactionPolicy,
    MemoryRetentionContract,
    RetentionPolicy,
    SnapshotPolicy,
)
from epip.core.runtime_retention import (
    RUNTIME_RETENTION_ADOPTIONS,
    RetentionAdoptionMode,
    RuntimeRetentionAdapter,
    RuntimeRetentionRegistry,
    adopt_runtime_retention,
)
from epip.features.feature_store import FeatureStore
from epip.marketdata.datasource_cache import DataSourceCache
from epip.replay.replay_statistics import ReplayStatistics


def _bounded_contract(component: str, size: int = 2) -> MemoryRetentionContract:
    return MemoryRetentionContract(
        component=component,
        policy=RetentionPolicy.FIFO,
        maximum_size=size,
        time_window=None,
        cleanup_trigger=CleanupTrigger.ON_INSERT,
        history_retention="explicit bounded adoption",
        snapshot_policy=SnapshotPolicy.IMMUTABLE_ORDERED,
        compaction_policy=CompactionPolicy.EVICT,
        manual_cleanup=False,
        automatic_cleanup=True,
        determinism_impact="logical insertion order only",
        serialization_impact="no component format change",
    )


@pytest.mark.parametrize(
    ("component", "qualified_name"),
    [
        (EventBus(), "epip.core.event_bus.EventBus"),
        (FeatureStore(), "epip.features.feature_store.FeatureStore"),
        (ReplayStatistics(), "epip.replay.replay_statistics.ReplayStatistics"),
        (DataSourceCache(), "epip.marketdata.datasource_cache.DataSourceCache"),
    ],
)
def test_runtime_components_adopt_transparently(component: object, qualified_name: str) -> None:
    adapter: RuntimeRetentionAdapter[object, str] = adopt_runtime_retention(component)
    assert adapter.component is component
    assert adapter.runtime_retention.component == qualified_name
    assert adapter.runtime_retention.preserves_default


def test_explicit_bounded_adoption_is_deterministic_and_reversible() -> None:
    bus = EventBus()
    name = "epip.core.event_bus.EventBus"
    contract = _bounded_contract(name)
    first: RuntimeRetentionAdapter[EventBus, str] = adopt_runtime_retention(bus, contract=contract)
    second: RuntimeRetentionAdapter[EventBus, str] = adopt_runtime_retention(
        EventBus(), contract=contract
    )
    for adapter in (first, second):
        adapter.retain("a", 1)
        adapter.retain("b", 2)
        adapter.retain("c", 3)
    assert first.retained_snapshot() == second.retained_snapshot() == (("b", 2), ("c", 3))
    assert first.component is bus


def test_disabled_adoption_retains_nothing() -> None:
    name = "epip.core.event_bus.EventBus"
    disabled = MemoryRetentionContract(
        component=name,
        policy=RetentionPolicy.DISABLED,
        maximum_size=None,
        time_window=None,
        cleanup_trigger=CleanupTrigger.MANUAL,
        history_retention="disabled",
        snapshot_policy=SnapshotPolicy.DISABLED,
        compaction_policy=CompactionPolicy.MANUAL,
        manual_cleanup=True,
        automatic_cleanup=False,
        determinism_impact="no retained data",
        serialization_impact="none",
    )
    adapter: RuntimeRetentionAdapter[EventBus, str] = adopt_runtime_retention(
        EventBus(), contract=disabled
    )
    adapter.retain("event", object())
    assert adapter.retained_snapshot() == ()


def test_existing_methods_are_delegated_without_api_change() -> None:
    bus = EventBus()
    adapter: RuntimeRetentionAdapter[EventBus, str] = adopt_runtime_retention(bus)
    adapter.clear()
    assert adapter.component is bus


def test_runtime_registry_covers_histories_graphs_statistics_and_replay() -> None:
    assert RUNTIME_RETENTION_ADOPTIONS.audit() == ()
    names = set(RUNTIME_RETENTION_ADOPTIONS)
    assert "epip.market_structure.history.StructureHistory" in names
    assert "epip.portfolio.graph.PortfolioGraph" in names
    assert "epip.execution.statistics.StatisticsCollector" in names
    assert "epip.replay.replay_scheduler.ReplayScheduler" in names


def test_adoption_declarations_are_immutable_and_transparent() -> None:
    adoption = RUNTIME_RETENTION_ADOPTIONS["epip.core.event_bus.EventBus"]
    assert adoption.mode is RetentionAdoptionMode.TRANSPARENT_ADAPTER
    with pytest.raises(FrozenInstanceError):
        adoption.migrated = False  # type: ignore[misc]


def test_empty_registry_audit_detects_every_unmigrated_runtime() -> None:
    errors = RuntimeRetentionRegistry(()).audit()
    assert errors
    assert all(error.startswith("runtime structure not migrated:") for error in errors)


def test_mismatched_contract_is_rejected() -> None:
    with pytest.raises(ValueError):
        adopt_runtime_retention(
            EventBus(),
            contract=_bounded_contract("epip.features.feature_store.FeatureStore"),
        )
