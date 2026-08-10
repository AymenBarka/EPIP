"""Tests for deterministic read-only memory observability."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from typing import Any

import pytest

from epip.core.event_bus import EventBus
from epip.core.memory_audit import (
    MemoryAuditEntry,
    MemoryAuditManager,
    MemoryAuditRegistry,
    MemoryViolation,
    audit_contract_coverage,
)
from epip.core.recovery import MemoryRecoveryManager
from epip.core.resource_lifecycle import LifecycleManager
from epip.core.retention import (
    CleanupTrigger,
    CompactionPolicy,
    MemoryRetentionContract,
    RetentionManager,
    RetentionPolicy,
    SnapshotPolicy,
)


def _entry(**changes: Any) -> MemoryAuditEntry:
    base = MemoryAuditEntry(
        component="test.component",
        resource="test.resource",
        owner="test-owner",
        lifecycle="instance",
        policy="manual",
    )
    return replace(base, **changes)


def _registry_with(entry: MemoryAuditEntry) -> MemoryAuditRegistry:
    registry = MemoryAuditRegistry()
    registry.register("test", lambda: entry)
    return registry


def _retention_contract(maximum: int = 2) -> MemoryRetentionContract:
    return MemoryRetentionContract(
        component="test.retention",
        policy=RetentionPolicy.FIFO,
        maximum_size=maximum,
        time_window=None,
        cleanup_trigger=CleanupTrigger.ON_INSERT,
        history_retention="bounded",
        snapshot_policy=SnapshotPolicy.IMMUTABLE_ORDERED,
        compaction_policy=CompactionPolicy.EVICT,
        manual_cleanup=False,
        automatic_cleanup=True,
        determinism_impact="ordered",
        serialization_impact="none",
    )


def test_empty_audit_is_deterministic_and_compliant() -> None:
    manager = MemoryAuditManager()
    report = manager.report(0)
    assert report.compliant
    assert report.snapshot.entries == ()
    assert report.snapshot.statistics.active_resources == 0


def test_normal_audit_produces_immutable_serializable_snapshot() -> None:
    manager = MemoryAuditManager(_registry_with(_entry(closed_resources=1)))
    first = manager.report(7)
    second = manager.report(7)
    assert first == second
    assert json.dumps(first.to_dict(), sort_keys=True)
    with pytest.raises(FrozenInstanceError):
        first.snapshot.sequence = 8  # type: ignore[misc]


@pytest.mark.parametrize(
    ("entry", "violation"),
    [
        (_entry(memory_contract=False), MemoryViolation.MISSING_MEMORY_CONTRACT),
        (
            _entry(retention_contract=False),
            MemoryViolation.MISSING_RETENTION_POLICY,
        ),
        (
            _entry(active_resources=1, cleanup_declared=False, retained_objects=1),
            MemoryViolation.MISSING_CLEANUP,
        ),
        (_entry(lifecycle_valid=False), MemoryViolation.INVALID_LIFECYCLE),
        (
            _entry(rollback_complete=False, retained_objects=1),
            MemoryViolation.INCOMPLETE_ROLLBACK,
        ),
        (_entry(scopes=1), MemoryViolation.OPEN_SCOPE),
        (_entry(orphaned=True, handles=1), MemoryViolation.ORPHAN_HANDLE),
    ],
)
def test_diagnostics_detect_contract_and_lifecycle_violations(
    entry: MemoryAuditEntry, violation: MemoryViolation
) -> None:
    report = MemoryAuditManager(_registry_with(entry)).report(1)
    assert violation in {diagnostic.violation for diagnostic in report.diagnostics.violations}


def test_leak_candidate_is_reported_for_orphaned_resource() -> None:
    report = MemoryAuditManager(_registry_with(_entry(orphaned=True, retained_objects=3))).report(1)
    assert report.diagnostics.leak_candidates[0].retained_objects == 3


def test_double_ownership_is_detected_without_runtime_mutation() -> None:
    registry = MemoryAuditRegistry()
    registry.register("one", lambda: _entry(owner="owner-a"))
    registry.register("two", lambda: replace(_entry(), component="other", owner="owner-b"))
    report = MemoryAuditManager(registry).report(1)
    assert MemoryViolation.DOUBLE_OWNERSHIP in {
        item.violation for item in report.diagnostics.violations
    }


def test_recovery_probe_detects_open_scope_and_incomplete_rollback() -> None:
    recovery = MemoryRecoveryManager()
    scope = recovery.scope("forgotten")
    scope.register("buffer", [], lambda value: value.clear())
    registry = MemoryAuditRegistry()
    registry.register_recovery("recovery", recovery)
    report = MemoryAuditManager(registry).report(1)
    violations = {item.violation for item in report.diagnostics.violations}
    assert MemoryViolation.OPEN_SCOPE in violations
    scope.rollback()
    assert MemoryAuditManager(registry).report(2).compliant


def test_lifecycle_probe_reports_orphan_then_closed_resource() -> None:
    lifecycle = LifecycleManager("owner")
    lifecycle.acquire("resource", object(), close_callback=lambda _: None)
    registry = MemoryAuditRegistry()
    registry.register_lifecycle("lifecycle", lifecycle)
    first = MemoryAuditManager(registry).report(1)
    assert MemoryViolation.ORPHAN_HANDLE in {
        item.violation for item in first.diagnostics.violations
    }
    lifecycle.close_all()
    second = MemoryAuditManager(registry).report(2, previous=first.snapshot)
    assert second.compliant
    assert second.snapshot.statistics.closed_resources == 1


def test_retention_probe_reports_size_eviction_and_policy() -> None:
    retention = RetentionManager[str, int](_retention_contract())
    retention.put("a", 1)
    retention.put("b", 2)
    retention.put("c", 3)
    registry = MemoryAuditRegistry()
    registry.register_retention("retention", retention)
    report = MemoryAuditManager(registry).report(1)
    assert report.compliant
    assert report.snapshot.statistics.retained_objects == 2
    assert report.snapshot.statistics.evictions == 1
    assert report.snapshot.statistics.resources_by_policy == (("fifo", 1),)


def test_growth_report_compares_explicit_logical_snapshots() -> None:
    current = {"retained": 1}
    registry = MemoryAuditRegistry()
    registry.register(
        "growth",
        lambda: _entry(
            active_resources=current["retained"],
            retained_objects=current["retained"],
        ),
    )
    manager = MemoryAuditManager(registry)
    first = manager.snapshot(1)
    current["retained"] = 5
    report = manager.report(2, previous=first, growth_limit=2)
    assert report.snapshot.statistics.logical_growth == 4
    assert MemoryViolation.ABNORMAL_GROWTH in {
        item.violation for item in report.diagnostics.violations
    }


def test_statistics_are_grouped_in_sorted_order() -> None:
    registry = MemoryAuditRegistry()
    registry.register("z", lambda: _entry(owner="z", active_resources=2))
    registry.register(
        "a",
        lambda: replace(_entry(), component="a", resource="a", owner="a", closed_resources=1),
    )
    statistics = MemoryAuditManager(registry).snapshot(1).statistics
    assert statistics.resources_by_owner == (("a", 1), ("z", 1))
    assert statistics.active_resources == 2
    assert statistics.closed_resources == 1


def test_registry_rejects_duplicates_and_invalid_growth_limit() -> None:
    registry = _registry_with(_entry())
    with pytest.raises(ValueError):
        registry.register("test", lambda: _entry())
    manager = MemoryAuditManager(registry)
    with pytest.raises(ValueError):
        manager.diagnose(manager.snapshot(1), growth_limit=-1)


def test_contract_coverage_and_hardening_compatibility() -> None:
    assert audit_contract_coverage() == ()
    bus = EventBus()
    before = bus.event_history()
    MemoryAuditManager().report(1)
    assert bus.event_history() == before
