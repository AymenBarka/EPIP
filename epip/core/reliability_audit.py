"""Read-only deterministic reliability audit and failure observability.

The audit layer consumes immutable declarations and observations.  It never
invokes retry, circuit-breaker, fallback, recovery, or business operations.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, TypeAlias, cast, runtime_checkable

from epip.core.circuit_breaker import (
    CIRCUIT_BREAKER_CONTRACTS,
    CircuitBreakerSnapshot,
    CircuitBreakerState,
)
from epip.core.exceptions import EXCEPTION_REGISTRY
from epip.core.fallback import (
    DEGRADATION_CONTRACTS,
    AvailabilityLevel,
    FallbackAction,
    FallbackPolicy,
    FallbackSnapshot,
    ServiceCapability,
)
from epip.core.reliability import (
    RELIABILITY_CONTRACTS,
    FailureBoundary,
    FailureCategory,
)
from epip.core.retry import (
    RETRY_CONTRACTS,
    RetryClassification,
)


@dataclass(frozen=True, slots=True)
class FailureObservation:
    """One typed failure observed at a caller-supplied logical time."""

    logical_time: int
    component: str
    category: FailureCategory
    exception_contract: str
    boundary: FailureBoundary
    contract_present: bool = True

    def __post_init__(self) -> None:
        _validate_observation(self.logical_time, self.component, self.contract_present)
        if not isinstance(self.category, FailureCategory):
            raise TypeError("failure category must be declared")
        if not self.exception_contract.strip():
            raise ValueError("exception contract must be non-empty")
        if not isinstance(self.boundary, FailureBoundary):
            raise TypeError("failure boundary must be declared")


@dataclass(frozen=True, slots=True)
class RetryObservation:
    """One read-only observation of a retry decision."""

    logical_time: int
    contract_name: str
    allowed: bool
    classification: RetryClassification
    contract_present: bool = True

    def __post_init__(self) -> None:
        _validate_observation(self.logical_time, self.contract_name, self.contract_present)
        if not isinstance(self.allowed, bool):
            raise TypeError("retry allowed flag must be bool")
        if not isinstance(self.classification, RetryClassification):
            raise TypeError("retry classification must be declared")


@dataclass(frozen=True, slots=True)
class CircuitBreakerObservation:
    """One read-only circuit-breaker state observation."""

    logical_time: int
    contract_name: str
    state: CircuitBreakerState
    contract_present: bool = True

    def __post_init__(self) -> None:
        _validate_observation(self.logical_time, self.contract_name, self.contract_present)
        if not isinstance(self.state, CircuitBreakerState):
            raise TypeError("circuit-breaker state must be declared")


@dataclass(frozen=True, slots=True)
class FallbackObservation:
    """One read-only fallback decision observation."""

    logical_time: int
    contract_name: str
    action: FallbackAction
    applied: bool
    availability: AvailabilityLevel
    contract_present: bool = True

    def __post_init__(self) -> None:
        _validate_observation(self.logical_time, self.contract_name, self.contract_present)
        if not isinstance(self.action, FallbackAction):
            raise TypeError("fallback action must be declared")
        if not isinstance(self.applied, bool):
            raise TypeError("fallback applied flag must be bool")
        if not isinstance(self.availability, AvailabilityLevel):
            raise TypeError("fallback availability must be declared")


@dataclass(frozen=True, slots=True)
class AvailabilityObservation:
    """One service availability and remaining-capability observation."""

    logical_time: int
    service: str
    level: AvailabilityLevel
    remaining_capabilities: tuple[ServiceCapability, ...] = ()

    def __post_init__(self) -> None:
        _validate_observation(self.logical_time, self.service, True)
        if not isinstance(self.level, AvailabilityLevel):
            raise TypeError("availability level must be declared")
        capabilities = tuple(self.remaining_capabilities)
        if not all(isinstance(item, ServiceCapability) for item in capabilities):
            raise TypeError("remaining capabilities must be declared")
        if len(set(capabilities)) != len(capabilities):
            raise ValueError("remaining capabilities must be unique")
        object.__setattr__(self, "remaining_capabilities", capabilities)


def _validate_observation(logical_time: int, name: str, flag: bool) -> None:
    if isinstance(logical_time, bool) or logical_time < 0:
        raise ValueError("logical time must be a non-negative integer")
    if not name.strip():
        raise ValueError("observation name must be non-empty")
    if not isinstance(flag, bool):
        raise TypeError("contract presence flag must be bool")


ReliabilityObservation: TypeAlias = (
    FailureObservation
    | RetryObservation
    | CircuitBreakerObservation
    | FallbackObservation
    | AvailabilityObservation
)


@dataclass(frozen=True, slots=True)
class FailureMetric:
    """One deterministic descriptive metric."""

    name: str
    value: int
    dimensions: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("metric name must be non-empty")
        if isinstance(self.value, bool) or self.value < 0:
            raise ValueError("metric value must be a non-negative integer")
        dimensions = tuple(sorted(tuple(item) for item in self.dimensions))
        if any(len(item) != 2 or not all(part.strip() for part in item) for item in dimensions):
            raise ValueError("metric dimensions must contain non-empty key/value pairs")
        object.__setattr__(self, "dimensions", dimensions)


@dataclass(frozen=True, slots=True)
class ReliabilityStatistics:
    """Immutable aggregate reliability statistics."""

    failure_count: int
    retry_count: int
    retry_denied: int
    fallback_count: int
    degraded_mode_count: int
    availability_distribution: tuple[tuple[str, int], ...]
    circuit_breaker_distribution: tuple[tuple[str, int], ...]
    failure_category_distribution: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class ReliabilityViolation:
    """One objective contract or observation violation."""

    code: str
    component: str
    message: str


@dataclass(frozen=True, slots=True)
class ReliabilityDiagnostic:
    """One deterministic audit diagnostic."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ReliabilityDiagnostics:
    """Immutable ordered diagnostic collection."""

    items: tuple[ReliabilityDiagnostic, ...] = ()

    @property
    def valid(self) -> bool:
        """Return whether the diagnostic collection is empty."""

        return not self.items


@dataclass(frozen=True, slots=True)
class ReliabilitySnapshot:
    """Immutable read-only projection of observed reliability state."""

    logical_time: int
    statistics: ReliabilityStatistics
    observations: tuple[ReliabilityObservation, ...]
    circuit_breakers: tuple[CircuitBreakerSnapshot, ...] = ()
    fallbacks: tuple[FallbackSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class ReliabilityHistory:
    """Immutable logical audit history."""

    snapshots: tuple[ReliabilitySnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class ReliabilityAuditEntry:
    """Contract references required for one auditable component."""

    component: str
    reliability_contract: str
    exception_contract: str
    retry_contract: str
    circuit_breaker_contract: str
    fallback_contract: str
    expected_boundary: FailureBoundary

    def __post_init__(self) -> None:
        names = (
            self.component,
            self.reliability_contract,
            self.exception_contract,
            self.retry_contract,
            self.circuit_breaker_contract,
            self.fallback_contract,
        )
        if any(not item.strip() for item in names):
            raise ValueError("audit contract references must be non-empty")
        if not isinstance(self.expected_boundary, FailureBoundary):
            raise TypeError("expected boundary must be declared")


@dataclass(frozen=True, slots=True)
class ReliabilityAuditSnapshot:
    """Immutable result of registry and observation validation."""

    logical_time: int
    entries_checked: int
    violations: tuple[ReliabilityViolation, ...]
    diagnostics: ReliabilityDiagnostics


@dataclass(frozen=True, slots=True)
class ReliabilityReport:
    """Comparable and deterministically serializable reliability report."""

    summary: str
    statistics: ReliabilityStatistics
    metrics: tuple[FailureMetric, ...]
    violations: tuple[ReliabilityViolation, ...]
    diagnostics: ReliabilityDiagnostics
    observations: tuple[ReliabilityObservation, ...]
    snapshots: tuple[ReliabilitySnapshot, ...]
    history: ReliabilityHistory
    classification: tuple[tuple[str, int], ...]

    def to_dict(self) -> dict[str, object]:
        """Return a primitive deterministic representation."""

        result = _primitive(self)
        return cast(dict[str, object], result)

    def to_json(self) -> str:
        """Return canonical deterministic JSON."""

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


def _primitive(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _primitive(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _primitive(item) for key, item in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [_primitive(item) for item in value]
    return value


@runtime_checkable
class ReliabilityAuditAware(Protocol):
    """Protocol for explicit read-only audit declaration."""

    @property
    def reliability_audit_entry(self) -> ReliabilityAuditEntry:
        """Return the component's immutable audit entry."""


class ReliabilityAuditRegistry(Mapping[str, ReliabilityAuditEntry]):
    """Immutable deterministic registry of audit declarations."""

    __slots__ = ("_entries",)

    def __init__(self, entries: Iterable[ReliabilityAuditEntry]) -> None:
        items = tuple(entries)
        mapping = {entry.component: entry for entry in items}
        if len(mapping) != len(items):
            raise ValueError("reliability audit components must be unique")
        self._entries: Mapping[str, ReliabilityAuditEntry] = MappingProxyType(mapping)

    def __getitem__(self, key: str) -> ReliabilityAuditEntry:
        return self._entries[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def resolve(self, entry: str | ReliabilityAuditAware) -> ReliabilityAuditEntry:
        """Resolve by stable component name or aware object."""

        if not isinstance(entry, str) and isinstance(entry, ReliabilityAuditAware):
            return entry.reliability_audit_entry
        name = entry if isinstance(entry, str) else type(entry).__qualname__
        try:
            return self._entries[name]
        except KeyError as error:
            raise LookupError(f"no reliability audit entry declared for {name}") from error

    def declared(self) -> tuple[ReliabilityAuditEntry, ...]:
        """Return entries in deterministic component order."""

        return tuple(self._entries[name] for name in sorted(self._entries))


class ReliabilityAuditManager:
    """Read-only audit, reporting, and descriptive-metric manager."""

    __slots__ = ("_registry",)

    def __init__(self, registry: ReliabilityAuditRegistry) -> None:
        if not isinstance(registry, ReliabilityAuditRegistry):
            raise TypeError("registry must be a ReliabilityAuditRegistry")
        self._registry = registry

    def snapshot(
        self,
        logical_time: int,
        observations: Iterable[ReliabilityObservation] = (),
        circuit_breakers: Iterable[CircuitBreakerSnapshot] = (),
        fallbacks: Iterable[FallbackSnapshot] = (),
    ) -> ReliabilitySnapshot:
        """Create a read-only snapshot without invoking observed runtimes."""

        if isinstance(logical_time, bool) or logical_time < 0:
            raise ValueError("logical time must be a non-negative integer")
        observed = tuple(sorted(observations, key=_observation_key))
        circuits = tuple(sorted(circuit_breakers, key=lambda item: item.name))
        fallback_items = tuple(sorted(fallbacks, key=lambda item: item.contract_name))
        return ReliabilitySnapshot(
            logical_time,
            _statistics(observed, circuits, fallback_items),
            observed,
            circuits,
            fallback_items,
        )

    def audit(self, snapshot: ReliabilitySnapshot) -> ReliabilityAuditSnapshot:
        """Validate contracts and observations without changing their sources."""

        if not isinstance(snapshot, ReliabilitySnapshot):
            raise TypeError("snapshot must be a ReliabilitySnapshot")
        violations = [
            *self._contract_violations(),
            *_observation_violations(snapshot.observations),
            *_snapshot_violations(snapshot),
        ]
        ordered = tuple(
            sorted(violations, key=lambda item: (item.code, item.component, item.message))
        )
        diagnostics = ReliabilityDiagnostics(
            tuple(ReliabilityDiagnostic(item.code, item.message) for item in ordered)
        )
        return ReliabilityAuditSnapshot(
            snapshot.logical_time, len(self._registry), ordered, diagnostics
        )

    def report(
        self, snapshot: ReliabilitySnapshot, history: ReliabilityHistory | None = None
    ) -> ReliabilityReport:
        """Build an immutable deterministic report from one snapshot."""

        audit = self.audit(snapshot)
        report_history = history or ReliabilityHistory((snapshot,))
        classification = snapshot.statistics.failure_category_distribution
        summary = (
            f"{snapshot.statistics.failure_count} failures; "
            f"{snapshot.statistics.retry_count} retries; "
            f"{snapshot.statistics.fallback_count} fallbacks; "
            f"{len(audit.violations)} violations"
        )
        return ReliabilityReport(
            summary,
            snapshot.statistics,
            _metrics(snapshot.statistics),
            audit.violations,
            audit.diagnostics,
            snapshot.observations,
            (snapshot,),
            report_history,
            classification,
        )

    def _contract_violations(self) -> tuple[ReliabilityViolation, ...]:
        violations: list[ReliabilityViolation] = []
        for entry in self._registry.declared():
            references = (
                ("MISSING_RELIABILITY_CONTRACT", entry.reliability_contract, RELIABILITY_CONTRACTS),
                ("MISSING_EXCEPTION_CONTRACT", entry.exception_contract, EXCEPTION_REGISTRY),
                ("MISSING_RETRY_CONTRACT", entry.retry_contract, RETRY_CONTRACTS),
                (
                    "MISSING_CIRCUIT_BREAKER_CONTRACT",
                    entry.circuit_breaker_contract,
                    CIRCUIT_BREAKER_CONTRACTS,
                ),
                ("MISSING_FALLBACK_CONTRACT", entry.fallback_contract, DEGRADATION_CONTRACTS),
            )
            for code, name, registry in references:
                if name not in registry:
                    violations.append(
                        ReliabilityViolation(code, entry.component, f"missing contract: {name}")
                    )
            if entry.reliability_contract in RELIABILITY_CONTRACTS:
                contract = RELIABILITY_CONTRACTS[entry.reliability_contract]
                if not any(item.boundary is entry.expected_boundary for item in contract.failures):
                    violations.append(
                        ReliabilityViolation(
                            "INVALID_BOUNDARY",
                            entry.component,
                            f"expected boundary absent: {entry.expected_boundary.value}",
                        )
                    )
            if (
                entry.retry_contract in RETRY_CONTRACTS
                and entry.circuit_breaker_contract in CIRCUIT_BREAKER_CONTRACTS
                and CIRCUIT_BREAKER_CONTRACTS[entry.circuit_breaker_contract].retry_contract.name
                != entry.retry_contract
            ):
                violations.append(
                    ReliabilityViolation(
                        "CONTRACT_CONTRADICTION",
                        entry.component,
                        "retry and circuit-breaker contracts disagree",
                    )
                )
            if (
                entry.fallback_contract in DEGRADATION_CONTRACTS
                and DEGRADATION_CONTRACTS[entry.fallback_contract].retry_contract.name
                != entry.retry_contract
            ):
                violations.append(
                    ReliabilityViolation(
                        "CONTRACT_CONTRADICTION",
                        entry.component,
                        "retry and fallback contracts disagree",
                    )
                )
        return tuple(violations)


def _observation_key(item: ReliabilityObservation) -> tuple[int, str, str]:
    name = getattr(item, "component", getattr(item, "contract_name", getattr(item, "service", "")))
    return item.logical_time, type(item).__name__, str(name)


def _statistics(
    observations: tuple[ReliabilityObservation, ...],
    circuits: tuple[CircuitBreakerSnapshot, ...],
    fallbacks: tuple[FallbackSnapshot, ...],
) -> ReliabilityStatistics:
    failures = tuple(item for item in observations if isinstance(item, FailureObservation))
    retries = tuple(item for item in observations if isinstance(item, RetryObservation))
    fallback_observations = tuple(
        item for item in observations if isinstance(item, FallbackObservation) and item.applied
    )
    availability = Counter(
        item.level.value for item in observations if isinstance(item, AvailabilityObservation)
    )
    availability.update(item.availability.value for item in fallback_observations)
    circuit_distribution = Counter(item.state.value for item in circuits)
    circuit_distribution.update(
        item.state.value for item in observations if isinstance(item, CircuitBreakerObservation)
    )
    categories = Counter(item.category.value for item in failures)
    fallback_count = len(fallback_observations) + sum(item.statistics.applied for item in fallbacks)
    degraded = sum(
        count
        for level, count in availability.items()
        if level in {AvailabilityLevel.DEGRADED.value, AvailabilityLevel.LIMITED.value}
    )
    return ReliabilityStatistics(
        len(failures),
        sum(item.allowed for item in retries),
        sum(not item.allowed for item in retries),
        fallback_count,
        degraded,
        tuple(sorted(availability.items())),
        tuple(sorted(circuit_distribution.items())),
        tuple(sorted(categories.items())),
    )


def _metrics(statistics: ReliabilityStatistics) -> tuple[FailureMetric, ...]:
    metrics = [
        FailureMetric("failure_count", statistics.failure_count),
        FailureMetric("retry_count", statistics.retry_count),
        FailureMetric("retry_denied", statistics.retry_denied),
        FailureMetric("fallback_count", statistics.fallback_count),
        FailureMetric("degraded_mode_count", statistics.degraded_mode_count),
    ]
    metrics.extend(
        FailureMetric("availability", count, (("level", level),))
        for level, count in statistics.availability_distribution
    )
    metrics.extend(
        FailureMetric("circuit_breaker", count, (("state", state),))
        for state, count in statistics.circuit_breaker_distribution
    )
    metrics.extend(
        FailureMetric("failure_category", count, (("category", category),))
        for category, count in statistics.failure_category_distribution
    )
    return tuple(metrics)


def _observation_violations(
    observations: tuple[ReliabilityObservation, ...],
) -> tuple[ReliabilityViolation, ...]:
    violations: list[ReliabilityViolation] = []
    for item in observations:
        name = str(
            getattr(item, "component", getattr(item, "contract_name", getattr(item, "service", "")))
        )
        if hasattr(item, "contract_present") and not item.contract_present:
            violations.append(
                ReliabilityViolation(
                    "MISSING_OBSERVED_CONTRACT", name, "observation has no contract"
                )
            )
        if (
            isinstance(item, RetryObservation)
            and item.allowed
            and item.classification
            in {RetryClassification.NEVER_RETRY, RetryClassification.NON_RETRYABLE}
        ):
            violations.append(
                ReliabilityViolation(
                    "INCOMPATIBLE_RETRY", name, "retry allowed by denied classification"
                )
            )
        if isinstance(item, FallbackObservation) and item.applied:
            if item.contract_name not in DEGRADATION_CONTRACTS:
                violations.append(
                    ReliabilityViolation(
                        "INCOMPATIBLE_FALLBACK", name, "applied fallback is undeclared"
                    )
                )
            elif DEGRADATION_CONTRACTS[item.contract_name].policy is FallbackPolicy.FAIL:
                violations.append(
                    ReliabilityViolation("INCOMPATIBLE_FALLBACK", name, "FAIL policy was applied")
                )
        if (
            isinstance(item, CircuitBreakerObservation)
            and item.contract_name not in CIRCUIT_BREAKER_CONTRACTS
        ):
            violations.append(
                ReliabilityViolation(
                    "INCOHERENT_CIRCUIT_BREAKER", name, "circuit-breaker contract is undeclared"
                )
            )
    return tuple(violations)


def _snapshot_violations(snapshot: ReliabilitySnapshot) -> tuple[ReliabilityViolation, ...]:
    violations: list[ReliabilityViolation] = []
    for circuit_snapshot in snapshot.circuit_breakers:
        if circuit_snapshot.name not in CIRCUIT_BREAKER_CONTRACTS:
            violations.append(
                ReliabilityViolation(
                    "INCOHERENT_CIRCUIT_BREAKER",
                    circuit_snapshot.name,
                    "snapshot contract is undeclared",
                )
            )
    for fallback_snapshot in snapshot.fallbacks:
        if fallback_snapshot.contract_name not in DEGRADATION_CONTRACTS:
            violations.append(
                ReliabilityViolation(
                    "INCOMPATIBLE_FALLBACK",
                    fallback_snapshot.contract_name,
                    "snapshot contract is undeclared",
                )
            )
    return tuple(violations)


def _entry(
    component: str,
    reliability: str,
    exception: str,
    retry: str,
    circuit: str,
    fallback: str,
    boundary: FailureBoundary,
) -> ReliabilityAuditEntry:
    return ReliabilityAuditEntry(
        component, reliability, exception, retry, circuit, fallback, boundary
    )


_ENTRIES = (
    _entry(
        "external_boundary",
        "epip.core.external_effects.ExternalEffectContract",
        "epip.core.exceptions.ExternalSystemError",
        "temporary_external_failure",
        "external_boundary",
        "secondary_provider",
        FailureBoundary.EXTERNAL_SYSTEM,
    ),
    _entry(
        "provider",
        "epip.marketdata.providers.base_provider.BaseProvider",
        "epip.core.exceptions.ProviderError",
        "temporary_external_failure",
        "provider",
        "cached_value",
        FailureBoundary.PROVIDER,
    ),
)

RELIABILITY_AUDIT_REGISTRY = ReliabilityAuditRegistry(_ENTRIES)


__all__ = [
    "RELIABILITY_AUDIT_REGISTRY",
    "AvailabilityObservation",
    "CircuitBreakerObservation",
    "FailureMetric",
    "FailureObservation",
    "FallbackObservation",
    "ReliabilityAuditAware",
    "ReliabilityAuditEntry",
    "ReliabilityAuditManager",
    "ReliabilityAuditRegistry",
    "ReliabilityAuditSnapshot",
    "ReliabilityDiagnostic",
    "ReliabilityDiagnostics",
    "ReliabilityHistory",
    "ReliabilityReport",
    "ReliabilitySnapshot",
    "ReliabilityStatistics",
    "ReliabilityViolation",
    "RetryObservation",
]
