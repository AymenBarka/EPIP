"""Canonical exception taxonomy and declarative error boundaries for EPIP.

This module is descriptive infrastructure.  It does not catch, translate, wrap,
retry, log, or otherwise alter exceptions raised by the existing runtime.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from epip.core.reliability import (
    FailureCategory,
    FailureResponsibility,
    RecoveryExpectation,
)


class EPIPError(Exception):
    """Root of the canonical EPIP exception hierarchy."""


class FrameworkError(EPIPError):
    """Failure owned by framework code."""


class InfrastructureError(EPIPError):
    """Failure in technical infrastructure supporting the framework."""


class ConfigurationError(FrameworkError):
    """Invalid or inconsistent framework configuration."""


class ValidationError(FrameworkError):
    """Input or invariant validation failure."""


class RuntimeError(FrameworkError):
    """Framework runtime failure not owned by a narrower subsystem."""


class ConcurrencyError(InfrastructureError):
    """Concurrency contract or coordination failure."""


class MemoryError(InfrastructureError):
    """Memory or managed-resource failure."""


class ReliabilityError(InfrastructureError):
    """Reliability contract failure."""


class ExternalSystemError(EPIPError):
    """Failure originating beyond the EPIP process boundary."""


class ProviderError(ExternalSystemError):
    """Failure reported by a market-data or service provider."""


class AdapterError(ExternalSystemError):
    """Failure reported by an external-system adapter."""


class PluginError(EPIPError):
    """Failure owned by plugin code or its declared boundary."""


class ReplayError(FrameworkError):
    """Replay subsystem failure."""


class KernelError(FrameworkError):
    """Kernel orchestration failure."""


class EventBusError(InfrastructureError):
    """EventBus dispatch or publication failure."""


class ExecutionError(FrameworkError):
    """Execution domain failure."""


class PortfolioError(FrameworkError):
    """Portfolio domain failure."""


class RiskError(FrameworkError):
    """Risk domain failure."""


class SerializationError(InfrastructureError):
    """Serialization or deserialization failure."""


class TimeoutError(InfrastructureError):
    """Operation exceeded its declared time budget."""


class CancellationError(InfrastructureError):
    """Operation was explicitly cancelled."""


class InterruptedError(InfrastructureError):
    """Operation was interrupted before completion."""


class RetryableError(EPIPError):
    """Failure classified as eligible for a future retry policy."""


class NonRetryableError(EPIPError):
    """Failure that must not be retried."""


class FatalError(EPIPError):
    """Unrecoverable failure requiring boundary abortion."""


class RecoverableError(EPIPError):
    """Failure for which recovery may be possible at the owning boundary."""


class BoundaryViolationError(ReliabilityError):
    """Invalid exception propagation across a declared boundary."""


class ExceptionVisibility(str, Enum):
    """Audience to which an exception is allowed to remain visible."""

    INTERNAL = "internal"
    PUBLIC = "public"
    OPERATOR = "operator"
    EXTERNAL = "external"


@dataclass(frozen=True, slots=True)
class ExceptionContract:
    """Immutable classification of one canonical exception type."""

    exception_type: type[EPIPError]
    category: FailureCategory
    responsibility: FailureResponsibility
    public: bool
    retryable: bool
    fatal: bool
    description: str

    def __post_init__(self) -> None:
        exception_type = self.exception_type
        if not isinstance(exception_type, type) or not issubclass(exception_type, EPIPError):
            raise TypeError("exception_type must be an EPIPError subclass")
        if len(exception_type.__bases__) != 1:
            raise ValueError("canonical exceptions must have exactly one direct parent")
        if not isinstance(self.category, FailureCategory):
            raise TypeError("exception category must be a FailureCategory")
        if not isinstance(self.responsibility, FailureResponsibility):
            raise TypeError("exception responsibility must be a FailureResponsibility")
        if self.retryable and self.fatal:
            raise ValueError("fatal exceptions cannot be retryable")
        if not self.description.strip():
            raise ValueError("exception description must be non-empty")

    @property
    def qualified_name(self) -> str:
        """Return the deterministic qualified exception name."""

        return f"{self.exception_type.__module__}.{self.exception_type.__qualname__}"


@dataclass(frozen=True, slots=True)
class ExceptionBoundary:
    """Declarative propagation policy at one architectural boundary."""

    name: str
    capture: tuple[type[EPIPError], ...]
    translation: type[EPIPError] | None
    propagation: bool
    wrapping: bool
    logging_responsibility: FailureResponsibility
    visibility: ExceptionVisibility
    recovery_expectation: RecoveryExpectation
    description: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("boundary name must be non-empty")
        captures = tuple(self.capture)
        if not captures:
            raise ValueError("boundary capture set must be non-empty")
        if not all(isinstance(item, type) and issubclass(item, EPIPError) for item in captures):
            raise TypeError("boundary capture values must be EPIPError subclasses")
        if len(set(captures)) != len(captures):
            raise ValueError("boundary capture values must be unique")
        if self.translation is not None and not (
            isinstance(self.translation, type) and issubclass(self.translation, EPIPError)
        ):
            raise TypeError("boundary translation must be an EPIPError subclass")
        if self.wrapping and self.translation is None:
            raise ValueError("wrapping boundaries must declare a translation target")
        if not self.propagation and self.visibility is ExceptionVisibility.PUBLIC:
            raise ValueError("non-propagating boundaries cannot expose public exceptions")
        if not isinstance(self.logging_responsibility, FailureResponsibility):
            raise TypeError("logging responsibility must be a FailureResponsibility")
        if not isinstance(self.visibility, ExceptionVisibility):
            raise TypeError("boundary visibility must be an ExceptionVisibility")
        if not isinstance(self.recovery_expectation, RecoveryExpectation):
            raise TypeError("recovery expectation must be a RecoveryExpectation")
        if not self.description.strip():
            raise ValueError("boundary description must be non-empty")
        object.__setattr__(self, "capture", captures)


@runtime_checkable
class ExceptionAware(Protocol):
    """Protocol for components exposing a native exception boundary."""

    @property
    def exception_boundary(self) -> ExceptionBoundary:
        """Return the component's immutable exception boundary."""


class ExceptionRegistry(Mapping[str, ExceptionContract]):
    """Immutable registry of exception contracts and propagation boundaries."""

    __slots__ = ("_boundaries", "_contracts")

    def __init__(
        self,
        contracts: Iterable[ExceptionContract],
        boundaries: Iterable[ExceptionBoundary] = (),
    ) -> None:
        contract_items = tuple(contracts)
        contract_map = {contract.qualified_name: contract for contract in contract_items}
        if len(contract_map) != len(contract_items):
            raise ValueError("exception contracts must be unique")
        boundary_items = tuple(boundaries)
        boundary_map = {boundary.name: boundary for boundary in boundary_items}
        if len(boundary_map) != len(boundary_items):
            raise ValueError("exception boundary names must be unique")
        registered_types = {contract.exception_type for contract in contract_items}
        for boundary in boundary_items:
            referenced = set(boundary.capture)
            if boundary.translation is not None:
                referenced.add(boundary.translation)
            missing = referenced - registered_types
            if missing:
                names = ", ".join(sorted(item.__name__ for item in missing))
                raise ValueError(f"boundary references unregistered exceptions: {names}")
        self._contracts: Mapping[str, ExceptionContract] = MappingProxyType(contract_map)
        self._boundaries: Mapping[str, ExceptionBoundary] = MappingProxyType(boundary_map)

    def __getitem__(self, key: str) -> ExceptionContract:
        return self._contracts[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._contracts)

    def __len__(self) -> int:
        return len(self._contracts)

    def resolve(self, exception: str | type[EPIPError] | EPIPError) -> ExceptionContract:
        """Resolve an exception contract by qualified name, type, or instance."""

        if isinstance(exception, str):
            name = exception
        else:
            exception_type = exception if isinstance(exception, type) else type(exception)
            name = f"{exception_type.__module__}.{exception_type.__qualname__}"
        try:
            return self._contracts[name]
        except KeyError as error:
            raise LookupError(f"unregistered exception: {name}") from error

    def resolve_boundary(self, name: str) -> ExceptionBoundary:
        """Resolve an exception boundary by stable name."""

        try:
            return self._boundaries[name]
        except KeyError as error:
            raise LookupError(f"unknown exception boundary: {name}") from error

    def declared(self) -> tuple[ExceptionContract, ...]:
        """Return contracts in deterministic qualified-name order."""

        return tuple(self._contracts[name] for name in sorted(self._contracts))

    def declared_boundaries(self) -> tuple[ExceptionBoundary, ...]:
        """Return boundaries in deterministic name order."""

        return tuple(self._boundaries[name] for name in sorted(self._boundaries))

    def audit(
        self,
        required_exceptions: Iterable[type[EPIPError]] = (),
        required_boundaries: Iterable[str] = (),
    ) -> tuple[str, ...]:
        """Return deterministic diagnostics for missing declarations."""

        required_names = {
            f"{exception.__module__}.{exception.__qualname__}" for exception in required_exceptions
        }
        diagnostics = [
            f"unregistered exception: {name}"
            for name in sorted(required_names - self._contracts.keys())
        ]
        diagnostics.extend(
            f"missing exception boundary: {name}"
            for name in sorted(set(required_boundaries) - self._boundaries.keys())
        )
        return tuple(diagnostics)


def audit_exception_hierarchy(
    parent_by_exception: Mapping[str, str | None],
) -> tuple[str, ...]:
    """Audit an abstract single-parent hierarchy for cycles and missing parents."""

    diagnostics: list[str] = []
    nodes = set(parent_by_exception)
    for name in sorted(nodes):
        parent = parent_by_exception[name]
        if parent is not None and parent not in nodes:
            diagnostics.append(f"unknown exception parent: {name} -> {parent}")
            continue
        path: set[str] = set()
        current: str | None = name
        while current is not None and current in nodes:
            if current in path:
                diagnostics.append(f"exception hierarchy cycle: {name}")
                break
            path.add(current)
            current = parent_by_exception[current]
    return tuple(dict.fromkeys(diagnostics))


def _contract(
    exception_type: type[EPIPError],
    category: FailureCategory,
    responsibility: FailureResponsibility,
    *,
    public: bool = True,
    retryable: bool = False,
    fatal: bool = False,
) -> ExceptionContract:
    return ExceptionContract(
        exception_type=exception_type,
        category=category,
        responsibility=responsibility,
        public=public,
        retryable=retryable,
        fatal=fatal,
        description=exception_type.__doc__ or exception_type.__name__,
    )


_CONTRACTS = (
    _contract(EPIPError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(FrameworkError, FailureCategory.PROGRAMMING_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(
        InfrastructureError, FailureCategory.RESOURCE_FAILURE, FailureResponsibility.FRAMEWORK
    ),
    _contract(ConfigurationError, FailureCategory.CONFIGURATION_ERROR, FailureResponsibility.USER),
    _contract(ValidationError, FailureCategory.DATA_ERROR, FailureResponsibility.CALLER),
    _contract(RuntimeError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(ConcurrencyError, FailureCategory.RESOURCE_FAILURE, FailureResponsibility.FRAMEWORK),
    _contract(
        MemoryError, FailureCategory.RESOURCE_FAILURE, FailureResponsibility.OPERATING_SYSTEM
    ),
    _contract(ReliabilityError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(
        ExternalSystemError, FailureCategory.EXTERNAL_FAILURE, FailureResponsibility.EXTERNAL_SYSTEM
    ),
    _contract(ProviderError, FailureCategory.EXTERNAL_FAILURE, FailureResponsibility.PROVIDER),
    _contract(AdapterError, FailureCategory.EXTERNAL_FAILURE, FailureResponsibility.ADAPTER),
    _contract(PluginError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.PLUGIN),
    _contract(ReplayError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(KernelError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(EventBusError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(ExecutionError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(PortfolioError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(RiskError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(SerializationError, FailureCategory.DATA_ERROR, FailureResponsibility.CALLER),
    _contract(
        TimeoutError, FailureCategory.TIMEOUT, FailureResponsibility.EXTERNAL_SYSTEM, retryable=True
    ),
    _contract(CancellationError, FailureCategory.CANCELLATION, FailureResponsibility.CALLER),
    _contract(
        InterruptedError, FailureCategory.INTERRUPTION, FailureResponsibility.OPERATING_SYSTEM
    ),
    _contract(
        RetryableError,
        FailureCategory.TRANSIENT_ERROR,
        FailureResponsibility.FRAMEWORK,
        retryable=True,
    ),
    _contract(NonRetryableError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(
        FatalError, FailureCategory.PERMANENT_ERROR, FailureResponsibility.FRAMEWORK, fatal=True
    ),
    _contract(RecoverableError, FailureCategory.TRANSIENT_ERROR, FailureResponsibility.FRAMEWORK),
    _contract(
        BoundaryViolationError, FailureCategory.PROGRAMMING_ERROR, FailureResponsibility.FRAMEWORK
    ),
)


def _boundary(
    name: str,
    capture: tuple[type[EPIPError], ...],
    translation: type[EPIPError] | None,
    visibility: ExceptionVisibility,
    responsibility: FailureResponsibility,
    recovery: RecoveryExpectation,
    description: str,
    *,
    propagation: bool = True,
    wrapping: bool = False,
) -> ExceptionBoundary:
    return ExceptionBoundary(
        name=name,
        capture=capture,
        translation=translation,
        propagation=propagation,
        wrapping=wrapping,
        logging_responsibility=responsibility,
        visibility=visibility,
        recovery_expectation=recovery,
        description=description,
    )


_BOUNDARIES = (
    _boundary(
        "Internal Boundary",
        (FrameworkError, InfrastructureError),
        None,
        ExceptionVisibility.INTERNAL,
        FailureResponsibility.FRAMEWORK,
        RecoveryExpectation.NONE,
        "Internal details remain framework-owned.",
    ),
    _boundary(
        "Public API Boundary",
        (FrameworkError, InfrastructureError),
        EPIPError,
        ExceptionVisibility.PUBLIC,
        FailureResponsibility.FRAMEWORK,
        RecoveryExpectation.CALLER_CORRECTION,
        "Technical failures may be translated to stable public errors.",
        wrapping=True,
    ),
    _boundary(
        "Plugin Boundary",
        (PluginError,),
        PluginError,
        ExceptionVisibility.OPERATOR,
        FailureResponsibility.PLUGIN,
        RecoveryExpectation.RECREATE_COMPONENT,
        "Plugin failures remain attributable to the plugin.",
    ),
    _boundary(
        "Provider Boundary",
        (ProviderError, TimeoutError),
        ProviderError,
        ExceptionVisibility.OPERATOR,
        FailureResponsibility.PROVIDER,
        RecoveryExpectation.EXTERNAL_RECOVERY,
        "Provider details are contained behind provider errors.",
    ),
    _boundary(
        "Adapter Boundary",
        (AdapterError, TimeoutError),
        AdapterError,
        ExceptionVisibility.OPERATOR,
        FailureResponsibility.ADAPTER,
        RecoveryExpectation.EXTERNAL_RECOVERY,
        "Adapter failures are attributed without leaking implementation details.",
    ),
    _boundary(
        "External Boundary",
        (ExternalSystemError, TimeoutError),
        ExternalSystemError,
        ExceptionVisibility.EXTERNAL,
        FailureResponsibility.EXTERNAL_SYSTEM,
        RecoveryExpectation.EXTERNAL_RECOVERY,
        "External failures retain external ownership.",
    ),
    _boundary(
        "Serialization Boundary",
        (SerializationError,),
        SerializationError,
        ExceptionVisibility.PUBLIC,
        FailureResponsibility.CALLER,
        RecoveryExpectation.CALLER_CORRECTION,
        "Serialization failures expose a stable public category.",
    ),
    _boundary(
        "Thread Boundary",
        (ConcurrencyError, InterruptedError, CancellationError),
        ConcurrencyError,
        ExceptionVisibility.OPERATOR,
        FailureResponsibility.FRAMEWORK,
        RecoveryExpectation.RECREATE_COMPONENT,
        "Thread failures do not leak platform-specific details.",
    ),
    _boundary(
        "Replay Boundary",
        (ReplayError,),
        ReplayError,
        ExceptionVisibility.PUBLIC,
        FailureResponsibility.FRAMEWORK,
        RecoveryExpectation.ROLLBACK,
        "Replay failures remain scoped to the replay run.",
    ),
    _boundary(
        "Kernel Boundary",
        (KernelError,),
        KernelError,
        ExceptionVisibility.PUBLIC,
        FailureResponsibility.FRAMEWORK,
        RecoveryExpectation.ROLLBACK,
        "Kernel orchestration exposes a stable kernel failure.",
    ),
    _boundary(
        "EventBus Boundary",
        (EventBusError,),
        EventBusError,
        ExceptionVisibility.PUBLIC,
        FailureResponsibility.FRAMEWORK,
        RecoveryExpectation.RECREATE_COMPONENT,
        "EventBus failures expose a stable event boundary.",
    ),
)


EXCEPTION_REGISTRY = ExceptionRegistry(_CONTRACTS, _BOUNDARIES)


def get_exception_contract(
    exception: str | type[EPIPError] | EPIPError,
) -> ExceptionContract:
    """Resolve a canonical exception contract."""

    return EXCEPTION_REGISTRY.resolve(exception)


def declared_exception_contracts() -> tuple[ExceptionContract, ...]:
    """Return all canonical exception contracts deterministically."""

    return EXCEPTION_REGISTRY.declared()


def declared_exception_boundaries() -> tuple[ExceptionBoundary, ...]:
    """Return all canonical exception boundaries deterministically."""

    return EXCEPTION_REGISTRY.declared_boundaries()
