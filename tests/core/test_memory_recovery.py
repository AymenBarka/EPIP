"""Tests for deterministic transactional memory recovery."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from epip.core.event_bus import EventBus
from epip.core.recovery import (
    MemoryRecoveryManager,
    RecoveryCheckpoint,
    RecoveryCleanupError,
    RecoveryHandle,
    RecoveryStateError,
    RecoveryStatus,
)
from epip.core.retention import (
    CleanupTrigger,
    CompactionPolicy,
    MemoryRetentionContract,
    RetentionManager,
    RetentionPolicy,
    SnapshotPolicy,
)


class _Interrupt(BaseException):
    pass


def test_simple_rollback_cleans_in_lifo_order() -> None:
    released: list[str] = []
    manager = MemoryRecoveryManager()
    scope = manager.scope("transaction")
    scope.register("first", "first", released.append)
    scope.register("second", "second", released.append)
    scope.rollback()
    assert released == ["second", "first"]
    assert manager.recovery_audit().unrecovered_resources == ()


def test_nested_commit_transfers_resources_to_parent_rollback() -> None:
    released: list[str] = []
    manager = MemoryRecoveryManager()
    outer = manager.scope("outer")
    outer.register("outer-resource", "outer", released.append)
    inner = manager.scope("inner")
    inner.register("inner-resource", "inner", released.append)
    inner.commit()
    outer.rollback()
    assert released == ["inner", "outer"]


@pytest.mark.parametrize("error", [RuntimeError("failure"), _Interrupt()])
def test_context_cleanup_after_exception_or_base_exception(error: BaseException) -> None:
    released: list[str] = []
    manager = MemoryRecoveryManager()
    with pytest.raises(type(error)), manager.scope("operation") as scope:
        scope.register("temporary", "value", released.append)
        raise error
    assert released == ["value"]
    assert manager.recovery_audit().open_scopes == ()


def test_abandon_and_repeated_rollback_are_idempotent() -> None:
    released: list[str] = []
    manager = MemoryRecoveryManager()
    scope = manager.scope("abandoned")
    scope.register("temporary", "value", released.append)
    scope.abandon()
    scope.rollback()
    assert released == ["value"]


def test_commit_failure_rolls_back() -> None:
    released: list[str] = []
    manager = MemoryRecoveryManager()
    scope = manager.scope("commit")
    scope.register("temporary", "value", released.append)
    with pytest.raises(RuntimeError):
        scope.commit(lambda: (_ for _ in ()).throw(RuntimeError("commit failed")))
    assert released == ["value"]
    assert scope.status is RecoveryStatus.RECOVERED


def test_initialization_failure_recovers_allocated_resource() -> None:
    released: list[str] = []
    manager = MemoryRecoveryManager()
    scope = manager.scope("initialize")
    with pytest.raises(ValueError):
        scope.allocate(
            "buffer",
            lambda: "buffer",
            released.append,
            lambda _: (_ for _ in ()).throw(ValueError("initialization failed")),
        )
    scope.rollback()
    assert released == ["buffer"]


def test_cleanup_failure_does_not_skip_remaining_resources() -> None:
    released: list[str] = []
    manager = MemoryRecoveryManager()
    scope = manager.scope("cleanup")
    scope.register("good", "good", released.append)
    scope.register("bad", "bad", lambda _: (_ for _ in ()).throw(RuntimeError()))
    with pytest.raises(RecoveryCleanupError):
        scope.rollback()
    assert released == ["good"]
    assert manager.recovery_audit().cleanup_failures == ("cleanup:bad",)


def test_recovery_handle_is_idempotent_and_rejects_recovery_after_commit() -> None:
    released: list[str] = []
    handle = RecoveryHandle("value", "value", released.append)
    assert handle.recover()
    assert not handle.recover()
    assert released == ["value"]
    committed = RecoveryHandle("committed", "value", released.append)
    committed.commit()
    with pytest.raises(RecoveryStateError):
        committed.recover()


def test_trace_contains_required_checkpoints_in_deterministic_sequence() -> None:
    manager = MemoryRecoveryManager()
    scope = manager.scope("trace")
    scope.allocate("buffer", list, lambda value: value.clear())
    scope.rollback()
    trace = manager.trace()
    assert tuple(record.sequence for record in trace) == tuple(range(1, len(trace) + 1))
    assert tuple(record.checkpoint for record in trace) == (
        RecoveryCheckpoint.BEGIN,
        RecoveryCheckpoint.ALLOCATE,
        RecoveryCheckpoint.REGISTER,
        RecoveryCheckpoint.ROLLBACK,
        RecoveryCheckpoint.RECOVER,
        RecoveryCheckpoint.RELEASE,
    )
    with pytest.raises(FrozenInstanceError):
        trace[0].sequence = 2  # type: ignore[misc]


def test_scopes_must_close_in_lifo_order() -> None:
    manager = MemoryRecoveryManager()
    outer = manager.scope("outer")
    manager.scope("inner")
    with pytest.raises(RecoveryStateError):
        outer.rollback()
    assert manager.recovery_audit().invalid_release_order == ("outer",)


def test_recovery_can_cleanup_retention_and_preserves_eventbus() -> None:
    def clear_retention(value: RetentionManager[str, object]) -> None:
        value.clear()

    contract = MemoryRetentionContract(
        component="test.buffer",
        policy=RetentionPolicy.MANUAL,
        maximum_size=None,
        time_window=None,
        cleanup_trigger=CleanupTrigger.MANUAL,
        history_retention="temporary",
        snapshot_policy=SnapshotPolicy.IMMUTABLE_ORDERED,
        compaction_policy=CompactionPolicy.MANUAL,
        manual_cleanup=True,
        automatic_cleanup=False,
        determinism_impact="logical order",
        serialization_impact="none",
    )
    retained = RetentionManager[str, object](contract)
    retained.put("temporary", object())
    bus = EventBus()
    recovery = MemoryRecoveryManager()
    scope = recovery.scope("event")
    scope.register("retention", retained, clear_retention)
    scope.rollback()
    assert retained.snapshot() == ()
    bus.clear()


def test_successful_scope_commits_without_cleanup() -> None:
    released: list[str] = []
    manager = MemoryRecoveryManager()
    with manager.scope("commit") as scope:
        scope.register("integrated", "value", released.append)
    assert released == []
    assert manager.recovery_audit().open_scopes == ()
