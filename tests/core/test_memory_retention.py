"""Tests for deterministic H005 memory retention."""

from __future__ import annotations

import pytest

from epip.core.retention import (
    MEMORY_RETENTION_CONTRACTS,
    CleanupTrigger,
    CompactionPolicy,
    MemoryRetentionContract,
    MemoryRetentionRegistry,
    RetentionManager,
    RetentionPolicy,
    SnapshotPolicy,
)


def _contract(
    policy: RetentionPolicy,
    *,
    maximum_size: int | None = None,
    time_window: float | None = None,
    automatic: bool = True,
) -> MemoryRetentionContract:
    return MemoryRetentionContract(
        component=f"test.{policy.value}",
        policy=policy,
        maximum_size=maximum_size,
        time_window=time_window,
        cleanup_trigger=CleanupTrigger.ON_INSERT if automatic else CleanupTrigger.MANUAL,
        history_retention="test",
        snapshot_policy=SnapshotPolicy.IMMUTABLE_ORDERED,
        compaction_policy=CompactionPolicy.EVICT if automatic else CompactionPolicy.MANUAL,
        manual_cleanup=not automatic,
        automatic_cleanup=automatic,
        determinism_impact="deterministic",
        serialization_impact="none",
        unbounded_justification="compatibility" if policy is RetentionPolicy.UNBOUNDED else None,
    )


@pytest.mark.parametrize(
    "policy",
    [RetentionPolicy.FIFO, RetentionPolicy.FIXED_SIZE, RetentionPolicy.RING_BUFFER],
)
def test_insertion_order_retention_is_bounded(policy: RetentionPolicy) -> None:
    manager = RetentionManager[str, int](_contract(policy, maximum_size=2))
    manager.put("a", 1)
    manager.put("b", 2)
    manager.put("c", 3)
    assert manager.snapshot() == (("b", 2), ("c", 3))
    assert manager.eviction_count == 1


def test_lru_access_changes_deterministic_eviction_order() -> None:
    manager = RetentionManager[str, int](_contract(RetentionPolicy.LRU, maximum_size=2))
    manager.put("a", 1)
    manager.put("b", 2)
    assert manager.get("a") == 1
    manager.put("c", 3)
    assert manager.snapshot() == (("a", 1), ("c", 3))


def test_time_window_requires_explicit_time_and_evicts_deterministically() -> None:
    manager = RetentionManager[str, int](_contract(RetentionPolicy.TIME_WINDOW, time_window=10.0))
    manager.put("old", 1, timestamp=1.0)
    manager.put("new", 2, timestamp=12.0)
    assert manager.snapshot() == (("new", 2),)
    with pytest.raises(ValueError):
        manager.put("implicit", 3)


def test_documented_unbounded_retention_preserves_all_values() -> None:
    manager = RetentionManager[int, int](_contract(RetentionPolicy.UNBOUNDED, automatic=False))
    for value in range(100):
        manager.put(value, value)
    assert len(manager) == 100


def test_manual_cleanup_and_disabled_policy() -> None:
    manual = RetentionManager[str, int](_contract(RetentionPolicy.MANUAL, automatic=False))
    manual.put("a", 1)
    assert manual.clear() == 1
    disabled = RetentionManager[str, int](_contract(RetentionPolicy.DISABLED, automatic=False))
    disabled.put("a", 1)
    assert disabled.snapshot() == ()


def test_snapshots_after_eviction_are_stable_and_serializable() -> None:
    first = RetentionManager[str, int](_contract(RetentionPolicy.FIFO, maximum_size=2))
    second = RetentionManager[str, int](_contract(RetentionPolicy.FIFO, maximum_size=2))
    for manager in (first, second):
        manager.put("a", 1)
        manager.put("b", 2)
        manager.put("c", 3)
    assert first.snapshot() == second.snapshot() == (("b", 2), ("c", 3))
    assert repr(first.snapshot()) == repr(second.snapshot())


def test_invalid_contracts_are_rejected() -> None:
    with pytest.raises(ValueError):
        _contract(RetentionPolicy.FIFO, maximum_size=0)
    with pytest.raises(ValueError):
        _contract(RetentionPolicy.FIFO)
    with pytest.raises(ValueError):
        _contract(RetentionPolicy.TIME_WINDOW, time_window=-1.0)
    with pytest.raises(ValueError):
        _contract(RetentionPolicy.UNBOUNDED)


def test_official_registry_covers_every_declared_growth_structure() -> None:
    assert MEMORY_RETENTION_CONTRACTS.audit() == ()
    assert MEMORY_RETENTION_CONTRACTS.declared()
    assert all(contract.determinism_impact for contract in MEMORY_RETENTION_CONTRACTS.values())
    assert "epip.features.feature_store.FeatureStore" in MEMORY_RETENTION_CONTRACTS
    assert "epip.replay.replay_scheduler.ReplayScheduler" in MEMORY_RETENTION_CONTRACTS
    assert "epip.portfolio.graph.PortfolioGraph" in MEMORY_RETENTION_CONTRACTS
    assert "epip.execution.statistics.StatisticsCollector" in MEMORY_RETENTION_CONTRACTS


def test_registry_detects_implicit_growth() -> None:
    assert MemoryRetentionRegistry(()).audit()
