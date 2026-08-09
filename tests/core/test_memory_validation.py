"""Institutional stress and endurance validation for Hardening-005."""

from __future__ import annotations

import gc
import json
import weakref

from epip.core.event_bus import EventBus
from epip.core.memory_audit import MemoryAuditManager, MemoryAuditRegistry
from epip.core.recovery import MemoryRecoveryManager
from epip.core.resource_lifecycle import LifecycleManager, LifecycleState
from epip.core.retention import (
    CleanupTrigger,
    CompactionPolicy,
    MemoryRetentionContract,
    RetentionManager,
    RetentionPolicy,
    SnapshotPolicy,
)
from epip.core.runtime_retention import (
    RetentionAdoptionMode,
    RuntimeRetentionAdapter,
    RuntimeRetentionAdoption,
)

CI_STRESS_CYCLES = 10_000
CI_ENDURANCE_CYCLES = 100_000


class _Payload:
    pass


def _contract(*, maximum: int = 64) -> MemoryRetentionContract:
    return MemoryRetentionContract(
        component="test.validation",
        policy=RetentionPolicy.FIFO,
        maximum_size=maximum,
        time_window=None,
        cleanup_trigger=CleanupTrigger.ON_INSERT,
        history_retention="bounded validation data",
        snapshot_policy=SnapshotPolicy.IMMUTABLE_ORDERED,
        compaction_policy=CompactionPolicy.EVICT,
        manual_cleanup=False,
        automatic_cleanup=True,
        determinism_impact="stable insertion order",
        serialization_impact="none",
    )


def _adapter(component: object) -> RuntimeRetentionAdapter[object, int]:
    contract = _contract()
    adoption = RuntimeRetentionAdoption(
        component=contract.component,
        contract=contract,
        mode=RetentionAdoptionMode.TRANSPARENT_ADAPTER,
        migrated=True,
        preserves_default=True,
    )
    return RuntimeRetentionAdapter(component, adoption)


def test_lifecycle_mass_creation_and_cleanup_has_no_orphans() -> None:
    manager = LifecycleManager("validation")
    closed: list[int] = []
    for index in range(CI_STRESS_CYCLES):
        manager.acquire(str(index), index, close_callback=closed.append)
    manager.close_all()
    audit = manager.audit()
    assert len(closed) == CI_STRESS_CYCLES
    assert audit.never_closed == ()
    assert audit.abandoned == ()
    assert all(manager[str(index)].state is LifecycleState.CLOSED for index in range(100))


def test_recovery_endurance_preserves_cleanup_and_scope_invariants() -> None:
    manager = MemoryRecoveryManager()
    cleaned = 0

    def cleanup(_value: int) -> None:
        nonlocal cleaned
        cleaned += 1

    for index in range(CI_ENDURANCE_CYCLES):
        scope = manager.scope(f"scope-{index}")
        scope.register(f"resource-{index}", index, cleanup)
        scope.rollback() if index % 2 else scope.abandon()
    audit = manager.recovery_audit()
    assert cleaned == CI_ENDURANCE_CYCLES
    assert audit.open_scopes == ()
    assert audit.unrecovered_resources == ()
    assert audit.cleanup_failures == ()


def test_nested_recovery_commit_and_rollback_remain_complete() -> None:
    manager = MemoryRecoveryManager()
    cleaned: list[int] = []
    for index in range(CI_STRESS_CYCLES):
        outer = manager.scope(f"outer-{index}")
        inner = manager.scope(f"inner-{index}")
        inner.register(f"nested-{index}", index, cleaned.append)
        inner.commit()
        outer.rollback()
    assert cleaned == list(range(CI_STRESS_CYCLES))
    assert manager.recovery_audit().open_scopes == ()


def test_retention_endurance_is_bounded_ordered_and_deterministic() -> None:
    first = RetentionManager[int, int](_contract())
    second = RetentionManager[int, int](_contract())
    for index in range(CI_ENDURANCE_CYCLES):
        first.put(index, index)
        second.put(index, index)
    expected = tuple(
        (index, index) for index in range(CI_ENDURANCE_CYCLES - 64, CI_ENDURANCE_CYCLES)
    )
    assert first.snapshot() == second.snapshot() == expected
    assert first.eviction_count == second.eviction_count == CI_ENDURANCE_CYCLES - 64
    assert first.clear() == 64
    assert first.snapshot() == ()


def test_runtime_retention_adapters_release_components_and_retained_values() -> None:
    component = _Payload()
    retained = _Payload()
    component_ref = weakref.ref(component)
    retained_ref = weakref.ref(retained)
    adapter = _adapter(component)
    adapter.retain(1, retained)
    assert adapter.retained_snapshot() == ((1, retained),)
    assert adapter.clear_retained() == 1
    del retained
    del component
    del adapter
    gc.collect()
    assert retained_ref() is None
    assert component_ref() is None


def test_audit_snapshots_diagnostics_and_reports_are_stable() -> None:
    retention = RetentionManager[int, int](_contract())
    for index in range(CI_STRESS_CYCLES):
        retention.put(index, index)
    registry = MemoryAuditRegistry()
    registry.register_retention("validation", retention)
    manager = MemoryAuditManager(registry)
    snapshots = tuple(manager.snapshot(7) for _ in range(1_000))
    diagnostics = tuple(manager.diagnose(snapshot) for snapshot in snapshots)
    reports = tuple(manager.report(7) for _ in range(1_000))
    assert len(set(snapshots)) == 1
    assert len(set(diagnostics)) == 1
    assert len({json.dumps(report.to_dict(), sort_keys=True) for report in reports}) == 1
    assert reports[0].compliant


def test_managers_are_collectable_after_massive_cleanup() -> None:
    payloads = [_Payload() for _ in range(1_000)]
    references = tuple(weakref.ref(item) for item in payloads)
    manager = LifecycleManager("collectable")
    for index, payload in enumerate(payloads):
        manager.acquire(str(index), payload, close_callback=lambda _: None)
    manager.close_all()
    del payload
    del payloads
    del manager
    gc.collect()
    assert all(reference() is None for reference in references)


def test_hardening_compatibility_boundaries_remain_unchanged() -> None:
    bus = EventBus()
    before = bus.event_history()
    MemoryAuditManager().report(1)
    assert bus.event_history() == before
    assert MemoryAuditManager().report(1).compliant
    assert isinstance(MemoryAuditManager().report(1).to_dict(), dict)
