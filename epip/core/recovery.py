"""Deterministic transactional recovery for temporary resources."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from types import MappingProxyType, TracebackType
from typing import Any, Protocol, Self, runtime_checkable


class RecoveryCheckpoint(str, Enum):
    """Official trace checkpoints for memory recovery."""

    BEGIN = "begin"
    ALLOCATE = "allocate"
    REGISTER = "register"
    COMMIT = "commit"
    ROLLBACK = "rollback"
    RECOVER = "recover"
    RELEASE = "release"


class RecoveryStatus(str, Enum):
    """State of a recovery handle or scope."""

    ACTIVE = "active"
    COMMITTED = "committed"
    RECOVERED = "recovered"
    FAILED = "failed"


class MemoryRecoveryError(RuntimeError):
    """Base error for deterministic recovery failures."""


class RecoveryStateError(MemoryRecoveryError):
    """Raised for a forbidden recovery operation."""


class RecoveryCleanupError(MemoryRecoveryError):
    """Raised after one or more cleanup callbacks fail."""


@dataclass(frozen=True, slots=True)
class RecoveryRecord:
    """One deterministic recovery trace entry."""

    sequence: int
    scope: str
    checkpoint: RecoveryCheckpoint
    resource: str | None = None


@dataclass(frozen=True, slots=True)
class RecoveryAudit:
    """Immutable audit of incomplete or invalid recovery activity."""

    open_scopes: tuple[str, ...]
    unrecovered_resources: tuple[str, ...]
    double_cleanup: Mapping[str, int]
    cleanup_failures: tuple[str, ...]
    orphan_checkpoints: tuple[str, ...]
    invalid_release_order: tuple[str, ...]
    lost_handles: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "open_scopes", tuple(self.open_scopes))
        object.__setattr__(self, "unrecovered_resources", tuple(self.unrecovered_resources))
        object.__setattr__(self, "double_cleanup", MappingProxyType(dict(self.double_cleanup)))
        object.__setattr__(self, "cleanup_failures", tuple(self.cleanup_failures))
        object.__setattr__(self, "orphan_checkpoints", tuple(self.orphan_checkpoints))
        object.__setattr__(self, "invalid_release_order", tuple(self.invalid_release_order))
        object.__setattr__(self, "lost_handles", tuple(self.lost_handles))


@runtime_checkable
class MemoryRecoveryAware(Protocol):
    """Protocol for objects exposing a recovery audit."""

    def recovery_audit(self) -> RecoveryAudit:
        """Return the current immutable recovery audit."""


class RecoveryHandle[T]:
    """Idempotent cleanup handle for one temporary resource."""

    def __init__(self, name: str, resource: T, cleanup: Callable[[T], None]) -> None:
        if not name.strip():
            raise ValueError("recovery resource name must be non-empty")
        self._name = name
        self._resource = resource
        self._cleanup = cleanup
        self._status = RecoveryStatus.ACTIVE
        self._cleanup_attempts = 0
        self._lock = RLock()

    @property
    def name(self) -> str:
        return self._name

    @property
    def resource(self) -> T:
        return self._resource

    @property
    def status(self) -> RecoveryStatus:
        with self._lock:
            return self._status

    @property
    def cleanup_attempts(self) -> int:
        with self._lock:
            return self._cleanup_attempts

    def recover(self) -> bool:
        """Clean once; return false for an idempotent repeated request."""

        with self._lock:
            if self._status is RecoveryStatus.RECOVERED:
                self._cleanup_attempts += 1
                return False
            if self._status is RecoveryStatus.COMMITTED:
                raise RecoveryStateError("committed resource cannot be recovered")
            self._cleanup_attempts += 1
            try:
                self._cleanup(self._resource)
            except BaseException:
                self._status = RecoveryStatus.FAILED
                raise
            self._status = RecoveryStatus.RECOVERED
            return True

    def commit(self) -> None:
        with self._lock:
            if self._status is not RecoveryStatus.ACTIVE:
                raise RecoveryStateError("only active resources can be committed")
            self._status = RecoveryStatus.COMMITTED


class RecoveryScope:
    """Transactional LIFO recovery scope."""

    def __init__(
        self,
        manager: MemoryRecoveryManager,
        name: str,
        parent: RecoveryScope | None,
    ) -> None:
        self._manager = manager
        self._name = name
        self._parent = parent
        self._handles: list[RecoveryHandle[Any]] = []
        self._status = RecoveryStatus.ACTIVE
        self._lock = RLock()
        self._manager._record(self._name, RecoveryCheckpoint.BEGIN)

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> RecoveryStatus:
        with self._lock:
            return self._status

    def register[T](
        self, name: str, resource: T, cleanup: Callable[[T], None]
    ) -> RecoveryHandle[T]:
        with self._lock:
            self._require_active()
            handle = RecoveryHandle(name, resource, cleanup)
            self._handles.append(handle)
            self._manager._record(self._name, RecoveryCheckpoint.REGISTER, name)
            return handle

    def allocate[T](
        self,
        name: str,
        factory: Callable[[], T],
        cleanup: Callable[[T], None],
        initializer: Callable[[T], None] | None = None,
    ) -> T:
        with self._lock:
            self._require_active()
            resource = factory()
            self._manager._record(self._name, RecoveryCheckpoint.ALLOCATE, name)
            handle = self.register(name, resource, cleanup)
            try:
                if initializer is not None:
                    initializer(resource)
            except BaseException:
                self._recover_handles((handle,))
                self._handles.remove(handle)
                raise
            return resource

    def commit(self, action: Callable[[], None] | None = None) -> None:
        with self._lock:
            self._require_active()
            self._manager._ensure_current(self)
            try:
                if action is not None:
                    action()
            except BaseException:
                self.rollback()
                raise
            if self._parent is not None:
                self._parent._accept(tuple(self._handles))
                self._handles.clear()
            else:
                for handle in self._handles:
                    handle.commit()
            self._status = RecoveryStatus.COMMITTED
            self._manager._record(self._name, RecoveryCheckpoint.COMMIT)
            self._manager._close_scope(self)

    def rollback(self) -> None:
        with self._lock:
            if self._status is RecoveryStatus.RECOVERED:
                return
            self._require_active()
            self._manager._ensure_current(self)
            self._manager._record(self._name, RecoveryCheckpoint.ROLLBACK)
            try:
                self._recover_handles(tuple(reversed(self._handles)))
            finally:
                self._status = RecoveryStatus.RECOVERED
                self._manager._close_scope(self)

    def abandon(self) -> None:
        self.rollback()

    def _accept(self, handles: tuple[RecoveryHandle[Any], ...]) -> None:
        with self._lock:
            self._require_active()
            self._handles.extend(handles)

    def _recover_handles(self, handles: tuple[RecoveryHandle[Any], ...]) -> None:
        failures: list[BaseException] = []
        for handle in handles:
            try:
                recovered = handle.recover()
                if recovered:
                    self._manager._record(self._name, RecoveryCheckpoint.RECOVER, handle.name)
                    self._manager._record(self._name, RecoveryCheckpoint.RELEASE, handle.name)
            except BaseException as error:  # noqa: BLE001 - cleanup covers interruption
                failures.append(error)
                self._manager._cleanup_failure(self._name, handle.name)
        if failures:
            raise RecoveryCleanupError(
                f"failed to recover {len(failures)} temporary resource(s)"
            ) from failures[0]

    def _require_active(self) -> None:
        if self._status is not RecoveryStatus.ACTIVE:
            raise RecoveryStateError("recovery scope is no longer active")

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc is None:
            self.commit()
        else:
            self.rollback()


class MemoryRecoveryManager:
    """Owner, trace, and audit boundary for recovery scopes."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._sequence = 0
        self._records: list[RecoveryRecord] = []
        self._open: list[RecoveryScope] = []
        self._all_scopes: list[RecoveryScope] = []
        self._cleanup_failures: list[str] = []
        self._invalid_release_order: list[str] = []

    def scope(self, name: str) -> RecoveryScope:
        if not name.strip():
            raise ValueError("recovery scope name must be non-empty")
        with self._lock:
            parent = self._open[-1] if self._open else None
            scope = RecoveryScope(self, name, parent)
            self._open.append(scope)
            self._all_scopes.append(scope)
            return scope

    def trace(self) -> tuple[RecoveryRecord, ...]:
        with self._lock:
            return tuple(self._records)

    def recovery_audit(self) -> RecoveryAudit:
        with self._lock:
            open_names = tuple(scope.name for scope in self._open)
            unrecovered: list[str] = []
            double: dict[str, int] = {}
            for scope in self._all_scopes:
                for handle in scope._handles:
                    if scope.status is RecoveryStatus.RECOVERED and handle.status not in {
                        RecoveryStatus.RECOVERED,
                        RecoveryStatus.COMMITTED,
                    }:
                        unrecovered.append(f"{scope.name}:{handle.name}")
                    if handle.cleanup_attempts > 1:
                        double[f"{scope.name}:{handle.name}"] = handle.cleanup_attempts - 1
            return RecoveryAudit(
                open_names,
                tuple(sorted(set(unrecovered))),
                double,
                tuple(self._cleanup_failures),
                (),
                tuple(self._invalid_release_order),
                (),
            )

    def _record(
        self, scope: str, checkpoint: RecoveryCheckpoint, resource: str | None = None
    ) -> None:
        with self._lock:
            self._sequence += 1
            self._records.append(RecoveryRecord(self._sequence, scope, checkpoint, resource))

    def _close_scope(self, scope: RecoveryScope) -> None:
        with self._lock:
            self._ensure_current(scope)
            self._open.pop()

    def _ensure_current(self, scope: RecoveryScope) -> None:
        with self._lock:
            if not self._open or self._open[-1] is not scope:
                self._invalid_release_order.append(scope.name)
                raise RecoveryStateError("recovery scopes must close in LIFO order")

    def _cleanup_failure(self, scope: str, resource: str) -> None:
        with self._lock:
            self._cleanup_failures.append(f"{scope}:{resource}")


__all__ = [
    "MemoryRecoveryAware",
    "MemoryRecoveryError",
    "MemoryRecoveryManager",
    "RecoveryAudit",
    "RecoveryCheckpoint",
    "RecoveryCleanupError",
    "RecoveryHandle",
    "RecoveryRecord",
    "RecoveryScope",
    "RecoveryStateError",
    "RecoveryStatus",
]
