"""Deterministic, read-only memory and resource observability."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from threading import RLock
from typing import Protocol, runtime_checkable

from epip.core.memory import MEMORY_CONTRACTS
from epip.core.recovery import MemoryRecoveryManager, RecoveryCheckpoint
from epip.core.resource_lifecycle import LifecycleManager, LifecycleState
from epip.core.retention import MEMORY_RETENTION_CONTRACTS, RetentionManager


class MemoryViolation(str, Enum):
    """Machine-readable H005 memory audit violations."""

    UNRELEASED_RESOURCE = "unreleased_resource"
    ORPHAN_HANDLE = "orphan_handle"
    OPEN_SCOPE = "open_scope"
    RETENTION_INCONSISTENCY = "retention_inconsistency"
    DOUBLE_OWNERSHIP = "double_ownership"
    MISSING_CLEANUP = "missing_cleanup"
    INVALID_LIFECYCLE = "invalid_lifecycle"
    MISSING_RETENTION_POLICY = "missing_retention_policy"
    MISSING_MEMORY_CONTRACT = "missing_memory_contract"
    ABNORMAL_GROWTH = "abnormal_growth"
    CACHE_LIMIT_EXCEEDED = "cache_limit_exceeded"
    INCOMPLETE_ROLLBACK = "incomplete_rollback"


@dataclass(frozen=True, slots=True)
class MemoryAuditEntry:
    """One normalized and immutable resource observation."""

    component: str
    resource: str
    owner: str
    lifecycle: str
    policy: str
    active_resources: int = 0
    closed_resources: int = 0
    handles: int = 0
    scopes: int = 0
    cleanups: int = 0
    rollbacks: int = 0
    evictions: int = 0
    retained_objects: int = 0
    recovered_objects: int = 0
    memory_contract: bool = True
    retention_contract: bool = True
    cleanup_declared: bool = True
    lifecycle_valid: bool = True
    rollback_complete: bool = True
    orphaned: bool = False

    def __post_init__(self) -> None:
        for value in (
            self.component,
            self.resource,
            self.owner,
            self.lifecycle,
            self.policy,
        ):
            if not value.strip():
                raise ValueError("memory audit identity fields must be non-empty")
        counters = (
            self.active_resources,
            self.closed_resources,
            self.handles,
            self.scopes,
            self.cleanups,
            self.rollbacks,
            self.evictions,
            self.retained_objects,
            self.recovered_objects,
        )
        if any(value < 0 for value in counters):
            raise ValueError("memory audit counters cannot be negative")


@dataclass(frozen=True, slots=True)
class MemoryStatistics:
    """Deterministic aggregate resource metrics."""

    active_resources: int
    closed_resources: int
    handles: int
    scopes: int
    resources_by_owner: tuple[tuple[str, int], ...]
    resources_by_lifecycle: tuple[tuple[str, int], ...]
    resources_by_policy: tuple[tuple[str, int], ...]
    cleanups: int
    rollbacks: int
    evictions: int
    logical_growth: int
    retained_objects: int
    recovered_objects: int


@dataclass(frozen=True, slots=True)
class MemorySnapshot:
    """Immutable, ordered, comparable, serialization-safe audit snapshot."""

    sequence: int
    entries: tuple[MemoryAuditEntry, ...]
    statistics: MemoryStatistics

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("snapshot sequence cannot be negative")
        ordered = tuple(sorted(self.entries, key=lambda item: (item.component, item.resource)))
        object.__setattr__(self, "entries", ordered)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic representation using JSON-compatible values."""

        return {
            "sequence": self.sequence,
            "entries": [asdict(entry) for entry in self.entries],
            "statistics": asdict(self.statistics),
        }


@dataclass(frozen=True, slots=True)
class MemoryLeakCandidate:
    """Deterministic evidence of a potentially unreleased resource."""

    component: str
    resource: str
    reason: str
    retained_objects: int


@dataclass(frozen=True, slots=True)
class MemoryDiagnostic:
    """One concrete H005 contract violation."""

    violation: MemoryViolation
    component: str
    resource: str
    detail: str


@dataclass(frozen=True, slots=True)
class MemoryDiagnostics:
    """Immutable deterministic diagnostics for one snapshot."""

    violations: tuple[MemoryDiagnostic, ...]
    leak_candidates: tuple[MemoryLeakCandidate, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "violations",
            tuple(
                sorted(
                    self.violations,
                    key=lambda item: (item.component, item.resource, item.violation.value),
                )
            ),
        )
        object.__setattr__(
            self,
            "leak_candidates",
            tuple(
                sorted(
                    self.leak_candidates,
                    key=lambda item: (item.component, item.resource, item.reason),
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class MemoryReport:
    """Complete immutable memory audit result."""

    snapshot: MemorySnapshot
    diagnostics: MemoryDiagnostics

    @property
    def compliant(self) -> bool:
        return not self.diagnostics.violations

    def to_dict(self) -> dict[str, object]:
        return {
            "snapshot": self.snapshot.to_dict(),
            "diagnostics": {
                "violations": [
                    {
                        **asdict(item),
                        "violation": item.violation.value,
                    }
                    for item in self.diagnostics.violations
                ],
                "leak_candidates": [asdict(item) for item in self.diagnostics.leak_candidates],
            },
        }


@runtime_checkable
class MemoryAuditAware(Protocol):
    """Protocol for components exposing a read-only memory audit entry."""

    def memory_audit_entry(self) -> MemoryAuditEntry:
        """Return the component's current immutable observation."""


class MemoryAuditRegistry(Mapping[str, Callable[[], MemoryAuditEntry]]):
    """Thread-safe deterministic registry of read-only observation probes."""

    def __init__(self) -> None:
        self._probes: dict[str, Callable[[], MemoryAuditEntry]] = {}
        self._lock = RLock()

    def __getitem__(self, key: str) -> Callable[[], MemoryAuditEntry]:
        with self._lock:
            return self._probes[key]

    def __iter__(self) -> Iterator[str]:
        with self._lock:
            return iter(tuple(sorted(self._probes)))

    def __len__(self) -> int:
        with self._lock:
            return len(self._probes)

    def register(self, name: str, probe: Callable[[], MemoryAuditEntry]) -> None:
        if not name.strip():
            raise ValueError("audit probe name must be non-empty")
        with self._lock:
            if name in self._probes:
                raise ValueError(f"audit probe already registered: {name}")
            self._probes[name] = probe

    def entries(self) -> tuple[MemoryAuditEntry, ...]:
        with self._lock:
            probes = tuple(self._probes[name] for name in sorted(self._probes))
        return tuple(probe() for probe in probes)

    def register_recovery(
        self, name: str, manager: MemoryRecoveryManager, *, owner: str = "framework"
    ) -> None:
        def probe() -> MemoryAuditEntry:
            audit = manager.recovery_audit()
            trace = manager.trace()
            registered = sum(item.checkpoint is RecoveryCheckpoint.REGISTER for item in trace)
            recovered = sum(item.checkpoint is RecoveryCheckpoint.RECOVER for item in trace)
            commits = sum(item.checkpoint is RecoveryCheckpoint.COMMIT for item in trace)
            return MemoryAuditEntry(
                component=name,
                resource=f"{name}.recovery",
                owner=owner,
                lifecycle="transaction",
                policy="explicit_recovery",
                active_resources=len(audit.unrecovered_resources),
                closed_resources=recovered + commits,
                handles=registered,
                scopes=len(audit.open_scopes),
                cleanups=recovered,
                rollbacks=sum(item.checkpoint is RecoveryCheckpoint.ROLLBACK for item in trace),
                retained_objects=len(audit.unrecovered_resources),
                recovered_objects=recovered,
                cleanup_declared=True,
                lifecycle_valid=not audit.invalid_release_order,
                rollback_complete=not (audit.unrecovered_resources or audit.cleanup_failures),
                orphaned=bool(audit.lost_handles or audit.orphan_checkpoints),
            )

        self.register(name, probe)

    def register_lifecycle(self, name: str, manager: LifecycleManager) -> None:
        def probe() -> MemoryAuditEntry:
            handles = tuple(manager[key] for key in manager)
            audit = manager.audit()
            closed = sum(handle.state is LifecycleState.CLOSED for handle in handles)
            active = len(handles) - closed
            invalid = bool(
                audit.invalid_transition_attempts
                or audit.ownership_violations
                or audit.use_after_close_attempts
            )
            return MemoryAuditEntry(
                component=name,
                resource=f"{name}.lifecycle",
                owner=manager.owner_id,
                lifecycle="managed",
                policy="explicit_close",
                active_resources=active,
                closed_resources=closed,
                handles=len(handles),
                cleanups=closed,
                retained_objects=active,
                recovered_objects=closed,
                cleanup_declared=True,
                lifecycle_valid=not invalid,
                orphaned=bool(audit.never_closed or audit.abandoned),
            )

        self.register(name, probe)

    def register_retention[K, V](
        self, name: str, manager: RetentionManager[K, V], *, owner: str = "component"
    ) -> None:
        def probe() -> MemoryAuditEntry:
            contract = manager.retention_contract
            retained = len(manager)
            maximum = contract.maximum_size
            within_limit = maximum is None or retained <= maximum
            return MemoryAuditEntry(
                component=name,
                resource=f"{name}.retention",
                owner=owner,
                lifecycle="retained",
                policy=contract.policy.value,
                active_resources=retained,
                retained_objects=retained,
                evictions=manager.eviction_count,
                retention_contract=True,
                lifecycle_valid=within_limit,
            )

        self.register(name, probe)


class MemoryAuditManager:
    """Read-only deterministic audit, diagnostic, and reporting service."""

    def __init__(self, registry: MemoryAuditRegistry | None = None) -> None:
        self._registry = registry or MemoryAuditRegistry()
        self._lock = RLock()

    @property
    def registry(self) -> MemoryAuditRegistry:
        return self._registry

    def snapshot(
        self,
        sequence: int,
        *,
        previous: MemorySnapshot | None = None,
    ) -> MemorySnapshot:
        entries = self._registry.entries()
        retained = sum(item.retained_objects for item in entries)
        previous_retained = 0 if previous is None else previous.statistics.retained_objects
        statistics = MemoryStatistics(
            active_resources=sum(item.active_resources for item in entries),
            closed_resources=sum(item.closed_resources for item in entries),
            handles=sum(item.handles for item in entries),
            scopes=sum(item.scopes for item in entries),
            resources_by_owner=_counts(item.owner for item in entries),
            resources_by_lifecycle=_counts(item.lifecycle for item in entries),
            resources_by_policy=_counts(item.policy for item in entries),
            cleanups=sum(item.cleanups for item in entries),
            rollbacks=sum(item.rollbacks for item in entries),
            evictions=sum(item.evictions for item in entries),
            logical_growth=retained - previous_retained,
            retained_objects=retained,
            recovered_objects=sum(item.recovered_objects for item in entries),
        )
        return MemorySnapshot(sequence, entries, statistics)

    def diagnose(
        self,
        snapshot: MemorySnapshot,
        *,
        growth_limit: int | None = None,
    ) -> MemoryDiagnostics:
        violations: list[MemoryDiagnostic] = []
        leaks: list[MemoryLeakCandidate] = []
        owners: dict[str, set[str]] = {}
        for entry in snapshot.entries:
            owners.setdefault(entry.resource, set()).add(entry.owner)
            self._diagnose_entry(entry, violations, leaks)
        for resource in sorted(owners):
            resource_owners = owners[resource]
            if len(resource_owners) > 1:
                violations.append(
                    MemoryDiagnostic(
                        MemoryViolation.DOUBLE_OWNERSHIP,
                        "memory-audit",
                        resource,
                        "multiple owners: " + ", ".join(sorted(resource_owners)),
                    )
                )
        if growth_limit is not None:
            if growth_limit < 0:
                raise ValueError("growth_limit cannot be negative")
            if snapshot.statistics.logical_growth > growth_limit:
                violations.append(
                    MemoryDiagnostic(
                        MemoryViolation.ABNORMAL_GROWTH,
                        "memory-audit",
                        "aggregate",
                        f"logical growth {snapshot.statistics.logical_growth} exceeds {growth_limit}",
                    )
                )
        return MemoryDiagnostics(tuple(violations), tuple(leaks))

    def report(
        self,
        sequence: int,
        *,
        previous: MemorySnapshot | None = None,
        growth_limit: int | None = None,
    ) -> MemoryReport:
        with self._lock:
            snapshot = self.snapshot(sequence, previous=previous)
            return MemoryReport(
                snapshot,
                self.diagnose(snapshot, growth_limit=growth_limit),
            )

    @staticmethod
    def _diagnose_entry(
        entry: MemoryAuditEntry,
        violations: list[MemoryDiagnostic],
        leaks: list[MemoryLeakCandidate],
    ) -> None:
        checks = (
            (
                not entry.memory_contract,
                MemoryViolation.MISSING_MEMORY_CONTRACT,
                "memory contract is absent",
            ),
            (
                not entry.retention_contract,
                MemoryViolation.MISSING_RETENTION_POLICY,
                "retention policy is absent",
            ),
            (
                entry.active_resources > 0 and not entry.cleanup_declared,
                MemoryViolation.MISSING_CLEANUP,
                "active resource has no cleanup declaration",
            ),
            (
                not entry.lifecycle_valid,
                (
                    MemoryViolation.CACHE_LIMIT_EXCEEDED
                    if entry.policy in {"fixed_size", "ring_buffer", "lru", "fifo", "time_window"}
                    else MemoryViolation.INVALID_LIFECYCLE
                ),
                "lifecycle or retention invariant is violated",
            ),
            (
                not entry.rollback_complete,
                MemoryViolation.INCOMPLETE_ROLLBACK,
                "rollback did not recover every registered resource",
            ),
            (
                entry.scopes > 0,
                MemoryViolation.OPEN_SCOPE,
                "recovery scope remains open",
            ),
            (
                entry.orphaned,
                MemoryViolation.ORPHAN_HANDLE,
                "resource handle has no completed ownership lifecycle",
            ),
        )
        for failed, violation, detail in checks:
            if failed:
                violations.append(
                    MemoryDiagnostic(violation, entry.component, entry.resource, detail)
                )
        if (
            entry.orphaned
            or not entry.rollback_complete
            or (entry.active_resources > 0 and not entry.cleanup_declared)
        ):
            leaks.append(
                MemoryLeakCandidate(
                    entry.component,
                    entry.resource,
                    "resource remains retained after an incomplete lifecycle",
                    entry.retained_objects,
                )
            )


def _counts(values: Iterable[str]) -> tuple[tuple[str, int], ...]:
    counts = Counter(values)
    return tuple((name, counts[name]) for name in sorted(counts))


def audit_contract_coverage() -> tuple[MemoryDiagnostic, ...]:
    """Audit H005 contract registries without observing or mutating runtime."""

    diagnostics: list[MemoryDiagnostic] = []
    for detail in MEMORY_RETENTION_CONTRACTS.audit():
        diagnostics.append(
            MemoryDiagnostic(
                MemoryViolation.MISSING_RETENTION_POLICY,
                "memory-contracts",
                "registry",
                detail,
            )
        )
    if not MEMORY_CONTRACTS:
        diagnostics.append(
            MemoryDiagnostic(
                MemoryViolation.MISSING_MEMORY_CONTRACT,
                "memory-contracts",
                "registry",
                "memory contract registry is empty",
            )
        )
    return tuple(diagnostics)


__all__ = [
    "MemoryAuditAware",
    "MemoryAuditEntry",
    "MemoryAuditManager",
    "MemoryAuditRegistry",
    "MemoryDiagnostic",
    "MemoryDiagnostics",
    "MemoryLeakCandidate",
    "MemoryReport",
    "MemorySnapshot",
    "MemoryStatistics",
    "MemoryViolation",
    "audit_contract_coverage",
]
