"""Experimental Hardening-005 memory baseline; results are not an SLA."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from time import perf_counter

from epip.core.memory_audit import MemoryAuditManager, MemoryAuditRegistry
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
from epip.core.runtime_retention import (
    RetentionAdoptionMode,
    RuntimeRetentionAdapter,
    RuntimeRetentionAdoption,
)


def _contract() -> MemoryRetentionContract:
    return MemoryRetentionContract(
        component="benchmark.memory",
        policy=RetentionPolicy.FIFO,
        maximum_size=1_024,
        time_window=None,
        cleanup_trigger=CleanupTrigger.ON_INSERT,
        history_retention="bounded benchmark data",
        snapshot_policy=SnapshotPolicy.IMMUTABLE_ORDERED,
        compaction_policy=CompactionPolicy.EVICT,
        manual_cleanup=False,
        automatic_cleanup=True,
        determinism_impact="stable insertion order",
        serialization_impact="none",
    )


def _measure(name: str, cycles: int, operation: Callable[[], None]) -> None:
    started = perf_counter()
    operation()
    duration = perf_counter() - started
    rate = cycles / duration if duration else float("inf")
    print(f"{name}: cycles={cycles} duration={duration:.6f}s rate={rate:.0f}/s")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=100_000)
    cycles = parser.parse_args().cycles
    if cycles <= 0:
        raise ValueError("cycles must be positive")

    def lifecycle() -> None:
        manager = LifecycleManager("benchmark")
        for index in range(cycles):
            manager.acquire(str(index), index, close_callback=lambda _: None)
        manager.close_all()

    def recovery() -> None:
        manager = MemoryRecoveryManager()
        for index in range(cycles):
            scope = manager.scope(str(index))
            scope.register(str(index), index, lambda _: None)
            scope.rollback()

    retention = RetentionManager[int, int](_contract())

    def retain() -> None:
        for index in range(cycles):
            retention.put(index, index)

    adoption = RuntimeRetentionAdoption(
        component="benchmark.memory",
        contract=_contract(),
        mode=RetentionAdoptionMode.TRANSPARENT_ADAPTER,
        migrated=True,
        preserves_default=True,
    )

    def runtime_adoption() -> None:
        for index in range(cycles):
            adapter = RuntimeRetentionAdapter[object, int](object(), adoption)
            adapter.retain(index, index)
            adapter.clear_retained()

    registry = MemoryAuditRegistry()
    registry.register_retention("benchmark", retention)
    audit = MemoryAuditManager(registry)

    def snapshot() -> None:
        for index in range(cycles):
            audit.report(index)

    _measure("lifecycle", cycles, lifecycle)
    _measure("recovery", cycles, recovery)
    _measure("retention", cycles, retain)
    _measure("runtime_adoption", cycles, runtime_adoption)
    _measure("audit", cycles, snapshot)


if __name__ == "__main__":
    main()
