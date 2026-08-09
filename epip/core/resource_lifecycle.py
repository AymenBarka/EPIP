"""Deterministic lifecycle management for EPIP resource handles.

The infrastructure is additive: existing runtime components are not modified.
Callers may wrap resources when explicit lifecycle enforcement is required.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from types import MappingProxyType, TracebackType
from typing import Any, Protocol, Self, runtime_checkable

from epip.core.memory import MEMORY_CONTRACTS, MemoryClassification


class LifecycleState(str, Enum):
    """Official resource lifecycle states."""

    CREATED = "created"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    IDLE = "idle"
    CLOSING = "closing"
    CLOSED = "closed"
    FAILED = "failed"
    ABORTED = "aborted"


class ResourceOwnership(str, Enum):
    """Official resource ownership roles."""

    OWNER = "owner"
    BORROWER = "borrower"
    SHARED_OWNER = "shared_owner"
    TRANSFERRED_OWNER = "transferred_owner"
    EXTERNAL_OWNER = "external_owner"


class ResourceLifecycleError(RuntimeError):
    """Base error for resource lifecycle violations."""


class InvalidLifecycleTransitionError(ResourceLifecycleError):
    """Raised when a requested state transition is forbidden."""


class ResourceClosedError(ResourceLifecycleError):
    """Raised when a closed resource is used."""


class ResourceOwnershipError(ResourceLifecycleError):
    """Raised when an ownership operation is forbidden."""


class ResourceCleanupError(ResourceLifecycleError):
    """Raised when deterministic cleanup fails."""


@dataclass(frozen=True, slots=True)
class ResourceLifecycle:
    """Immutable snapshot of a resource's lifecycle declaration and state."""

    name: str
    state: LifecycleState
    ownership: ResourceOwnership
    owner_id: str
    cleanup_operations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("resource name must be non-empty")
        if not self.owner_id.strip():
            raise ValueError("owner_id must be non-empty")
        if not self.cleanup_operations:
            raise ValueError("at least one cleanup operation must be documented")
        object.__setattr__(self, "cleanup_operations", tuple(self.cleanup_operations))


@dataclass(frozen=True, slots=True)
class ResourceAudit:
    """Immutable audit result for managed handles."""

    never_closed: tuple[str, ...]
    abandoned: tuple[str, ...]
    double_close_attempts: Mapping[str, int]
    use_after_close_attempts: Mapping[str, int]
    invalid_transition_attempts: Mapping[str, int]
    ownership_violations: Mapping[str, int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "never_closed", tuple(self.never_closed))
        object.__setattr__(self, "abandoned", tuple(self.abandoned))
        for field_name in (
            "double_close_attempts",
            "use_after_close_attempts",
            "invalid_transition_attempts",
            "ownership_violations",
        ):
            value = dict(getattr(self, field_name))
            object.__setattr__(self, field_name, MappingProxyType(value))


@runtime_checkable
class AutoCloseableResource(Protocol):
    """Structural protocol for resources exposing deterministic cleanup."""

    def close(self) -> None:
        """Release the resource."""


@runtime_checkable
class MemoryLifecycleAware(Protocol):
    """Protocol for objects exposing lifecycle state and deterministic close."""

    @property
    def lifecycle(self) -> ResourceLifecycle:
        """Return an immutable lifecycle snapshot."""

    def close(self) -> None:
        """Close the resource idempotently."""


@runtime_checkable
class ResourceOwner(Protocol):
    """Protocol for owners that can close managed resources."""

    @property
    def owner_id(self) -> str:
        """Return the stable owner identifier."""

    def close_all(self) -> None:
        """Close every resource owned by this owner."""


_ALLOWED_TRANSITIONS: Mapping[LifecycleState, frozenset[LifecycleState]] = MappingProxyType(
    {
        LifecycleState.CREATED: frozenset(
            {
                LifecycleState.INITIALIZED,
                LifecycleState.CLOSING,
                LifecycleState.FAILED,
                LifecycleState.ABORTED,
            }
        ),
        LifecycleState.INITIALIZED: frozenset(
            {
                LifecycleState.ACTIVE,
                LifecycleState.IDLE,
                LifecycleState.CLOSING,
                LifecycleState.FAILED,
                LifecycleState.ABORTED,
            }
        ),
        LifecycleState.ACTIVE: frozenset(
            {
                LifecycleState.IDLE,
                LifecycleState.CLOSING,
                LifecycleState.FAILED,
                LifecycleState.ABORTED,
            }
        ),
        LifecycleState.IDLE: frozenset(
            {
                LifecycleState.ACTIVE,
                LifecycleState.CLOSING,
                LifecycleState.FAILED,
                LifecycleState.ABORTED,
            }
        ),
        LifecycleState.CLOSING: frozenset({LifecycleState.CLOSED, LifecycleState.FAILED}),
        LifecycleState.CLOSED: frozenset(),
        LifecycleState.FAILED: frozenset({LifecycleState.CLOSING, LifecycleState.ABORTED}),
        LifecycleState.ABORTED: frozenset({LifecycleState.CLOSING}),
    }
)


class ResourceHandle[T]:
    """Thread-safe lifecycle guard around an existing resource instance."""

    __slots__ = (
        "_cleanup_operations",
        "_close_callback",
        "_double_close_attempts",
        "_invalid_transition_attempts",
        "_lock",
        "_name",
        "_owner_id",
        "_ownership",
        "_ownership_violations",
        "_resource",
        "_state",
        "_use_after_close_attempts",
    )

    def __init__(
        self,
        resource: T,
        *,
        name: str,
        owner_id: str,
        ownership: ResourceOwnership = ResourceOwnership.OWNER,
        close_callback: Callable[[T], None] | None = None,
        cleanup_operations: tuple[str, ...] = ("close",),
    ) -> None:
        if not name.strip():
            raise ValueError("resource name must be non-empty")
        if not owner_id.strip():
            raise ValueError("owner_id must be non-empty")
        if not cleanup_operations:
            raise ValueError("cleanup_operations must be non-empty")
        self._resource = resource
        self._name = name
        self._owner_id = owner_id
        self._ownership = ownership
        self._close_callback = close_callback
        self._cleanup_operations = tuple(cleanup_operations)
        self._state = LifecycleState.CREATED
        self._lock = RLock()
        self._double_close_attempts = 0
        self._use_after_close_attempts = 0
        self._invalid_transition_attempts = 0
        self._ownership_violations = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def owner_id(self) -> str:
        with self._lock:
            return self._owner_id

    @property
    def state(self) -> LifecycleState:
        with self._lock:
            return self._state

    @property
    def lifecycle(self) -> ResourceLifecycle:
        with self._lock:
            return ResourceLifecycle(
                self._name,
                self._state,
                self._ownership,
                self._owner_id,
                self._cleanup_operations,
            )

    def _transition(self, target: LifecycleState) -> None:
        if target not in _ALLOWED_TRANSITIONS[self._state]:
            self._invalid_transition_attempts += 1
            raise InvalidLifecycleTransitionError(
                f"invalid lifecycle transition {self._state.value} -> {target.value}"
            )
        self._state = target

    def initialize(self) -> None:
        with self._lock:
            self._transition(LifecycleState.INITIALIZED)

    def activate(self) -> None:
        with self._lock:
            self._transition(LifecycleState.ACTIVE)

    def idle(self) -> None:
        with self._lock:
            self._transition(LifecycleState.IDLE)

    def fail(self) -> None:
        with self._lock:
            self._transition(LifecycleState.FAILED)

    def abort(self) -> None:
        with self._lock:
            if self._state is LifecycleState.ABORTED:
                return
            self._transition(LifecycleState.ABORTED)

    def use(self) -> T:
        with self._lock:
            if self._state in {
                LifecycleState.CLOSING,
                LifecycleState.CLOSED,
                LifecycleState.FAILED,
                LifecycleState.ABORTED,
            }:
                self._use_after_close_attempts += 1
                raise ResourceClosedError(f"resource {self._name} is not usable")
            if self._state is LifecycleState.CREATED:
                self._invalid_transition_attempts += 1
                raise InvalidLifecycleTransitionError(
                    f"resource {self._name} must be initialized before use"
                )
            return self._resource

    def transfer_ownership(self, new_owner_id: str) -> None:
        with self._lock:
            if not new_owner_id.strip():
                self._ownership_violations += 1
                raise ResourceOwnershipError("new owner_id must be non-empty")
            if self._ownership in {ResourceOwnership.BORROWER, ResourceOwnership.EXTERNAL_OWNER}:
                self._ownership_violations += 1
                raise ResourceOwnershipError("this ownership role cannot transfer the resource")
            if self._state in {LifecycleState.CLOSING, LifecycleState.CLOSED}:
                self._ownership_violations += 1
                raise ResourceOwnershipError("a closing or closed resource cannot be transferred")
            self._owner_id = new_owner_id
            self._ownership = ResourceOwnership.TRANSFERRED_OWNER

    def close(self) -> None:
        with self._lock:
            if self._state is LifecycleState.CLOSED:
                self._double_close_attempts += 1
                return
            if self._ownership is ResourceOwnership.BORROWER:
                self._ownership_violations += 1
                raise ResourceOwnershipError("a borrower cannot close the resource")
            self._transition(LifecycleState.CLOSING)
            try:
                if self._close_callback is not None:
                    self._close_callback(self._resource)
                elif isinstance(self._resource, AutoCloseableResource):
                    self._resource.close()
            except BaseException as error:
                self._state = LifecycleState.FAILED
                raise ResourceCleanupError(f"failed to close resource {self._name}") from error
            self._state = LifecycleState.CLOSED

    def audit_counters(self) -> tuple[int, int, int, int]:
        with self._lock:
            return (
                self._double_close_attempts,
                self._use_after_close_attempts,
                self._invalid_transition_attempts,
                self._ownership_violations,
            )

    def __enter__(self) -> T:
        with self._lock:
            if self._state is LifecycleState.CREATED:
                self._transition(LifecycleState.INITIALIZED)
            if self._state in {LifecycleState.INITIALIZED, LifecycleState.IDLE}:
                self._transition(LifecycleState.ACTIVE)
        return self.use()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc is not None and self.state not in {
            LifecycleState.CLOSING,
            LifecycleState.CLOSED,
            LifecycleState.FAILED,
            LifecycleState.ABORTED,
        }:
            self.abort()
        self.close()


class LifecycleManager(Mapping[str, ResourceHandle[Any]]):
    """Owner and deterministic audit boundary for resource handles."""

    __slots__ = ("_handles", "_lock", "_owner_id")

    def __init__(self, owner_id: str) -> None:
        if not owner_id.strip():
            raise ValueError("owner_id must be non-empty")
        self._owner_id = owner_id
        self._handles: dict[str, ResourceHandle[Any]] = {}
        self._lock = RLock()

    @property
    def owner_id(self) -> str:
        return self._owner_id

    def __getitem__(self, key: str) -> ResourceHandle[Any]:
        with self._lock:
            return self._handles[key]

    def __iter__(self) -> Iterator[str]:
        with self._lock:
            return iter(tuple(self._handles))

    def __len__(self) -> int:
        with self._lock:
            return len(self._handles)

    def acquire[T](
        self,
        name: str,
        resource: T,
        *,
        ownership: ResourceOwnership = ResourceOwnership.OWNER,
        close_callback: Callable[[T], None] | None = None,
        cleanup_operations: tuple[str, ...] = ("close",),
    ) -> ResourceHandle[T]:
        """Register, initialize, and activate one resource handle."""

        with self._lock:
            if name in self._handles:
                raise ResourceLifecycleError(f"resource {name} is already registered")
            handle = ResourceHandle(
                resource,
                name=name,
                owner_id=self._owner_id,
                ownership=ownership,
                close_callback=close_callback,
                cleanup_operations=cleanup_operations,
            )
            handle.initialize()
            handle.activate()
            self._handles[name] = handle
            return handle

    def close(self, name: str) -> None:
        self[name].close()

    def close_all(self) -> None:
        failures: list[ResourceCleanupError] = []
        with self._lock:
            handles = tuple(self._handles[name] for name in sorted(self._handles))
        for handle in handles:
            try:
                handle.close()
            except ResourceCleanupError as error:
                failures.append(error)
        if failures:
            raise ResourceCleanupError(
                f"failed to close {len(failures)} managed resource(s)"
            ) from failures[0]

    def audit(self) -> ResourceAudit:
        """Return deterministic lifecycle misuse and leak indicators."""

        with self._lock:
            handles = tuple(self._handles[name] for name in sorted(self._handles))
        never_closed: list[str] = []
        abandoned: list[str] = []
        double_close: dict[str, int] = {}
        use_after_close: dict[str, int] = {}
        invalid_transition: dict[str, int] = {}
        ownership_violations: dict[str, int] = {}
        for handle in handles:
            if handle.state is not LifecycleState.CLOSED:
                never_closed.append(handle.name)
            if handle.state is LifecycleState.ABORTED:
                abandoned.append(handle.name)
            double, after_close, invalid, ownership = handle.audit_counters()
            if double:
                double_close[handle.name] = double
            if after_close:
                use_after_close[handle.name] = after_close
            if invalid:
                invalid_transition[handle.name] = invalid
            if ownership:
                ownership_violations[handle.name] = ownership
        return ResourceAudit(
            tuple(never_closed),
            tuple(abandoned),
            double_close,
            use_after_close,
            invalid_transition,
            ownership_violations,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close_all()


def resource_managed_components() -> tuple[str, ...]:
    """Return all H005 contracts requiring explicit resource management."""

    return tuple(
        sorted(
            name
            for name, contract in MEMORY_CONTRACTS.items()
            if MemoryClassification.RESOURCE_MANAGED in contract.classifications
        )
    )


__all__ = [
    "AutoCloseableResource",
    "InvalidLifecycleTransitionError",
    "LifecycleManager",
    "LifecycleState",
    "MemoryLifecycleAware",
    "ResourceAudit",
    "ResourceCleanupError",
    "ResourceClosedError",
    "ResourceHandle",
    "ResourceLifecycle",
    "ResourceLifecycleError",
    "ResourceOwner",
    "ResourceOwnership",
    "ResourceOwnershipError",
    "resource_managed_components",
]
