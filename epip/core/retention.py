"""Deterministic memory-retention contracts and runtime manager."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Hashable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from epip.core.memory import (
    MEMORY_CONTRACTS,
    HistoryPolicy,
    MemoryClassification,
    MemoryContract,
)
from epip.core.memory import (
    CachePolicy as MemoryCachePolicy,
)


class RetentionPolicy(str, Enum):
    """Official deterministic retention policies."""

    UNBOUNDED = "unbounded"
    FIXED_SIZE = "fixed_size"
    RING_BUFFER = "ring_buffer"
    LRU = "lru"
    FIFO = "fifo"
    TIME_WINDOW = "time_window"
    MANUAL = "manual"
    DISABLED = "disabled"


class CleanupTrigger(str, Enum):
    """Events that initiate retention cleanup."""

    ON_INSERT = "on_insert"
    MANUAL = "manual"
    NEVER = "never"


class SnapshotPolicy(str, Enum):
    """Snapshot behaviour for retained data."""

    IMMUTABLE_ORDERED = "immutable_ordered"
    DISABLED = "disabled"


class CompactionPolicy(str, Enum):
    """Compaction behaviour for retained data."""

    EVICT = "evict"
    MANUAL = "manual"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class MemoryRetentionContract:
    """Immutable declaration of one component's retention policy."""

    component: str
    policy: RetentionPolicy
    maximum_size: int | None
    time_window: float | None
    cleanup_trigger: CleanupTrigger
    history_retention: str
    snapshot_policy: SnapshotPolicy
    compaction_policy: CompactionPolicy
    manual_cleanup: bool
    automatic_cleanup: bool
    determinism_impact: str
    serialization_impact: str
    unbounded_justification: str | None = None

    def __post_init__(self) -> None:
        if not self.component.strip():
            raise ValueError("component must be non-empty")
        if self.maximum_size is not None and self.maximum_size <= 0:
            raise ValueError("maximum_size must be positive")
        if (
            self.policy
            in {
                RetentionPolicy.FIXED_SIZE,
                RetentionPolicy.RING_BUFFER,
                RetentionPolicy.LRU,
                RetentionPolicy.FIFO,
            }
            and self.maximum_size is None
        ):
            raise ValueError("bounded policies require maximum_size")
        if self.policy is RetentionPolicy.TIME_WINDOW:
            if self.time_window is None or self.time_window <= 0:
                raise ValueError("time-window policy requires a positive window")
        elif self.time_window is not None:
            raise ValueError("time_window is valid only for TIME_WINDOW")
        if self.manual_cleanup == self.automatic_cleanup:
            raise ValueError("exactly one cleanup mode must be enabled")
        if self.policy is RetentionPolicy.UNBOUNDED and not (
            self.unbounded_justification and self.unbounded_justification.strip()
        ):
            raise ValueError("unbounded retention requires a justification")
        if self.policy is RetentionPolicy.UNBOUNDED and self.automatic_cleanup:
            raise ValueError("unbounded retention must use explicit manual cleanup")
        if self.automatic_cleanup and self.cleanup_trigger is not CleanupTrigger.ON_INSERT:
            raise ValueError("automatic cleanup requires ON_INSERT")
        if self.manual_cleanup and self.cleanup_trigger is CleanupTrigger.ON_INSERT:
            raise ValueError("manual cleanup cannot use ON_INSERT")


@runtime_checkable
class RetentionAware(Protocol):
    """Protocol for components exposing a native retention contract."""

    @property
    def retention_contract(self) -> MemoryRetentionContract:
        """Return the immutable retention declaration."""


_RETENTION_COMPONENT_MARKERS = (
    "Cache",
    "EventBus",
    "FeatureStore",
    "Graph",
    "History",
    "ReplayIterator",
    "ReplayScheduler",
    "ReplayStatistics",
    "Statistics",
)


def _requires_retention_contract(name: str, memory: MemoryContract) -> bool:
    return (
        MemoryClassification.CACHED in memory.classifications
        or MemoryClassification.PERSISTENT in memory.classifications
        or memory.cache_policy is not MemoryCachePolicy.NONE
        or memory.history_policy is not HistoryPolicy.NONE
        or any(marker in name for marker in _RETENTION_COMPONENT_MARKERS)
    )


class MemoryRetentionRegistry(Mapping[str, MemoryRetentionContract]):
    """Immutable deterministic registry of retention contracts."""

    def __init__(self, contracts: Iterable[MemoryRetentionContract]) -> None:
        items = tuple(contracts)
        values = {item.component: item for item in items}
        if len(values) != len(items):
            raise ValueError("retention contract component names must be unique")
        self._contracts: Mapping[str, MemoryRetentionContract] = MappingProxyType(values)

    def __getitem__(self, key: str) -> MemoryRetentionContract:
        return self._contracts[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._contracts)

    def __len__(self) -> int:
        return len(self._contracts)

    def declared(self) -> tuple[MemoryRetentionContract, ...]:
        return tuple(self._contracts[name] for name in sorted(self._contracts))

    def audit(self) -> tuple[str, ...]:
        """Return deterministic contract errors; valid registries return empty."""

        errors: list[str] = []
        required = {
            name
            for name, memory in MEMORY_CONTRACTS.items()
            if _requires_retention_contract(name, memory)
        }
        for name in sorted(required - set(self._contracts)):
            errors.append(f"missing retention policy: {name}")
        return tuple(errors)


class RetentionManager[K: Hashable, V]:
    """Thread-safe deterministic retention container."""

    def __init__(self, contract: MemoryRetentionContract) -> None:
        self._contract = contract
        self._items: OrderedDict[K, tuple[V, float | None]] = OrderedDict()
        self._lock = RLock()
        self._evictions = 0

    @property
    def retention_contract(self) -> MemoryRetentionContract:
        return self._contract

    @property
    def eviction_count(self) -> int:
        with self._lock:
            return self._evictions

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)

    def put(self, key: K, value: V, *, timestamp: float | None = None) -> None:
        """Insert a value and apply deterministic automatic cleanup."""

        with self._lock:
            if self._contract.policy is RetentionPolicy.DISABLED:
                return
            if self._contract.policy is RetentionPolicy.TIME_WINDOW and timestamp is None:
                raise ValueError("TIME_WINDOW insert requires an explicit timestamp")
            if key in self._items:
                del self._items[key]
            self._items[key] = (value, timestamp)
            if self._contract.automatic_cleanup:
                self._cleanup_locked(timestamp)

    def get(self, key: K) -> V:
        """Get a value; LRU access deterministically updates recency."""

        with self._lock:
            value, _timestamp = self._items[key]
            if self._contract.policy is RetentionPolicy.LRU:
                self._items.move_to_end(key)
            return value

    def cleanup(self, *, timestamp: float | None = None) -> int:
        """Run deterministic cleanup and return the number evicted."""

        with self._lock:
            return self._cleanup_locked(timestamp)

    def clear(self) -> int:
        """Perform explicit manual cleanup."""

        with self._lock:
            removed = len(self._items)
            self._items.clear()
            self._evictions += removed
            return removed

    def snapshot(self) -> tuple[tuple[K, V], ...]:
        """Return an immutable ordered snapshot."""

        with self._lock:
            return tuple((key, value) for key, (value, _) in self._items.items())

    def _cleanup_locked(self, timestamp: float | None) -> int:
        before = len(self._items)
        policy = self._contract.policy
        maximum = self._contract.maximum_size
        if policy in {
            RetentionPolicy.FIXED_SIZE,
            RetentionPolicy.RING_BUFFER,
            RetentionPolicy.LRU,
            RetentionPolicy.FIFO,
        }:
            assert maximum is not None
            while len(self._items) > maximum:
                self._items.popitem(last=False)
        elif policy is RetentionPolicy.TIME_WINDOW:
            if timestamp is None:
                raise ValueError("TIME_WINDOW cleanup requires an explicit timestamp")
            assert self._contract.time_window is not None
            cutoff = timestamp - self._contract.time_window
            expired = [
                key
                for key, (_, item_timestamp) in self._items.items()
                if item_timestamp is not None and item_timestamp < cutoff
            ]
            for key in expired:
                del self._items[key]
        removed = before - len(self._items)
        self._evictions += removed
        return removed


def _retention_contracts() -> tuple[MemoryRetentionContract, ...]:
    contracts: list[MemoryRetentionContract] = []
    for name, memory in MEMORY_CONTRACTS.items():
        if not _requires_retention_contract(name, memory):
            continue
        bounded = memory.cache_policy is MemoryCachePolicy.BOUNDED
        unlimited = (
            MemoryClassification.PERSISTENT in memory.classifications
            or memory.cache_policy is MemoryCachePolicy.UNBOUNDED
            or memory.history_policy in {HistoryPolicy.UNBOUNDED, HistoryPolicy.PERSISTENT}
        )
        policy = (
            RetentionPolicy.LRU
            if bounded
            else RetentionPolicy.UNBOUNDED if unlimited else RetentionPolicy.MANUAL
        )
        contracts.append(
            MemoryRetentionContract(
                component=name,
                policy=policy,
                maximum_size=1024 if bounded else None,
                time_window=None,
                cleanup_trigger=CleanupTrigger.ON_INSERT if bounded else CleanupTrigger.MANUAL,
                history_retention="bounded cache" if bounded else "existing full history",
                snapshot_policy=SnapshotPolicy.IMMUTABLE_ORDERED,
                compaction_policy=CompactionPolicy.EVICT if bounded else CompactionPolicy.MANUAL,
                manual_cleanup=not bounded,
                automatic_cleanup=bounded,
                determinism_impact="stable insertion/access ordering",
                serialization_impact="no format change",
                unbounded_justification=(
                    None
                    if not unlimited
                    else "Existing API retains complete history; manual cleanup preserves compatibility."
                ),
            )
        )
    return tuple(contracts)


MEMORY_RETENTION_CONTRACTS = MemoryRetentionRegistry(_retention_contracts())


__all__ = [
    "MEMORY_RETENTION_CONTRACTS",
    "CleanupTrigger",
    "CompactionPolicy",
    "MemoryRetentionContract",
    "MemoryRetentionRegistry",
    "RetentionAware",
    "RetentionManager",
    "RetentionPolicy",
    "SnapshotPolicy",
]
