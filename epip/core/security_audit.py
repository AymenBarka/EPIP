"""Read-only deterministic security audit and observability.

This module projects security declarations and caller-supplied observations.
It never validates inputs, evaluates policies, handles failures, or mutates an
observed component.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, cast, runtime_checkable

from epip.core.input_validation import INPUT_VALIDATION_CONTRACTS
from epip.core.runtime_security import RUNTIME_SECURITY_POLICIES, RuntimeSecurityDecision
from epip.core.secure_failure import (
    SECURE_FAILURE_CONTRACTS,
    SecureFailureCategory,
    SecureFailureDecision,
    SecureFailureSeverity,
)
from epip.core.security import SECURITY_CONTRACTS
from epip.core.security_boundaries import SECURITY_BOUNDARY_CONTRACTS


class SecurityObservationKind(str, Enum):
    """Supported caller-supplied security observation categories."""

    DECISION = "decision"
    VIOLATION = "violation"
    INCIDENT = "incident"
    ADOPTION = "adoption"


class SecurityHealth(str, Enum):
    """Descriptive health derived from an immutable audit report."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SecurityAuditEntry:
    """References required to audit one security architecture surface."""

    name: str
    security_contract: str | None = None
    boundary_contract: str | None = None
    validation_contract: str | None = None
    runtime_policy: str | None = None
    secure_failure_contract: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("audit entry name must be non-empty")
        references = (
            self.security_contract,
            self.boundary_contract,
            self.validation_contract,
            self.runtime_policy,
            self.secure_failure_contract,
        )
        if not any(references):
            raise ValueError("audit entry requires at least one contract reference")
        if any(item is not None and not item.strip() for item in references):
            raise ValueError("audit contract references must be non-empty")


@dataclass(frozen=True, slots=True)
class SecurityObservation:
    """One read-only observation at an explicit logical time."""

    logical_time: int
    observation_id: str
    component: str
    kind: SecurityObservationKind
    classification: str
    policy: str | None = None
    adopted: bool = False
    runtime_active: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.logical_time, bool) or self.logical_time < 0:
            raise ValueError("logical time must be a non-negative integer")
        if any(not item.strip() for item in (self.observation_id, self.component)):
            raise ValueError("observation identity and component must be non-empty")
        if not isinstance(self.kind, SecurityObservationKind):
            raise TypeError("observation kind must be declared")
        if not self.classification.strip():
            raise ValueError("observation classification must be non-empty")
        if self.policy is not None and not self.policy.strip():
            raise ValueError("observation policy must be non-empty")
        if not isinstance(self.adopted, bool) or not isinstance(self.runtime_active, bool):
            raise TypeError("adoption and runtime flags must be bool")


@dataclass(frozen=True, slots=True)
class SecurityViolation:
    """One objective audit or caller-supplied security violation."""

    code: str
    component: str
    message: str

    def __post_init__(self) -> None:
        if any(not item.strip() for item in (self.code, self.component, self.message)):
            raise ValueError("violation fields must be non-empty")


@dataclass(frozen=True, slots=True)
class SecurityMetric:
    """One deterministic descriptive security metric."""

    name: str
    value: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("metric name must be non-empty")
        if isinstance(self.value, bool) or self.value < 0:
            raise ValueError("metric value must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class SecurityCoverage:
    """Descriptive coverage percentages represented as basis points."""

    adoption: int
    runtime: int
    policy: int

    def __post_init__(self) -> None:
        if any(
            isinstance(value, bool) or not 0 <= value <= 10_000 for value in asdict(self).values()
        ):
            raise ValueError("coverage values must be basis points in [0, 10000]")


@dataclass(frozen=True, slots=True)
class SecurityStatistics:
    """Immutable aggregate security statistics."""

    contracts: int
    boundaries: int
    policies: int
    violations: int
    incidents: int
    diagnostics: int
    audit_entries: int
    decisions: int

    def __post_init__(self) -> None:
        if any(isinstance(value, bool) or value < 0 for value in asdict(self).values()):
            raise ValueError("security statistics must be non-negative integers")


@dataclass(frozen=True, slots=True)
class SecurityDiagnostic:
    """One deterministic audit diagnostic."""

    code: str
    subject: str
    message: str

    def __post_init__(self) -> None:
        if any(not item.strip() for item in (self.code, self.subject, self.message)):
            raise ValueError("diagnostic fields must be non-empty")


@dataclass(frozen=True, slots=True)
class SecurityDiagnostics:
    """Immutable ordered diagnostic collection."""

    items: tuple[SecurityDiagnostic, ...] = ()

    @property
    def valid(self) -> bool:
        """Return whether no diagnostic was found."""

        return not self.items


@dataclass(frozen=True, slots=True)
class SecuritySnapshot:
    """Immutable deterministic projection of security state."""

    logical_time: int
    entries: tuple[SecurityAuditEntry, ...]
    observations: tuple[SecurityObservation, ...]
    statistics: SecurityStatistics
    coverage: SecurityCoverage


@dataclass(frozen=True, slots=True)
class SecurityAuditHistory:
    """Immutable ordered collection of security snapshots."""

    snapshots: tuple[SecuritySnapshot, ...] = ()

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.snapshots, key=lambda item: item.logical_time))
        if len({item.logical_time for item in ordered}) != len(ordered):
            raise ValueError("security history logical times must be unique")
        object.__setattr__(self, "snapshots", ordered)

    def append(self, snapshot: SecuritySnapshot) -> SecurityAuditHistory:
        """Return a new history containing ``snapshot``."""

        return SecurityAuditHistory((*self.snapshots, snapshot))


@dataclass(frozen=True, slots=True)
class SecuritySummary:
    """Compact immutable report summary."""

    health: SecurityHealth
    entries: int
    observations: int
    violations: int
    diagnostics: int


@dataclass(frozen=True, slots=True)
class SecurityCompliance:
    """Descriptive compliance result without enforcement semantics."""

    compliant: bool
    violation_codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SecurityReport:
    """Comparable, immutable, canonically serializable security report."""

    summary: SecuritySummary
    snapshot: SecuritySnapshot
    metrics: tuple[SecurityMetric, ...]
    violations: tuple[SecurityViolation, ...]
    diagnostics: SecurityDiagnostics
    compliance: SecurityCompliance
    history: SecurityAuditHistory

    def to_dict(self) -> dict[str, object]:
        """Return a primitive deterministic representation."""

        return cast(dict[str, object], _primitive(self))

    def to_json(self) -> str:
        """Return canonical JSON."""

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
class SecurityAuditAware(Protocol):
    """Protocol for explicit read-only security audit declarations."""

    @property
    def security_audit_entry(self) -> SecurityAuditEntry:
        """Return an immutable audit entry."""


class SecurityAuditRegistry(Mapping[str, SecurityAuditEntry]):
    """Immutable deterministic registry of audit entries."""

    __slots__ = ("_entries",)

    def __init__(self, entries: Iterable[SecurityAuditEntry]) -> None:
        items = tuple(entries)
        mapping = {entry.name: entry for entry in items}
        if len(mapping) != len(items):
            raise ValueError("security audit entry names must be unique")
        self._entries: Mapping[str, SecurityAuditEntry] = MappingProxyType(mapping)

    def __getitem__(self, key: str) -> SecurityAuditEntry:
        return self._entries[key]

    def __iter__(self) -> Iterator[str]:
        return iter(sorted(self._entries))

    def __len__(self) -> int:
        return len(self._entries)

    def resolve(self, subject: str | SecurityAuditAware) -> SecurityAuditEntry:
        """Resolve an entry by stable name or aware object."""

        if not isinstance(subject, str) and isinstance(subject, SecurityAuditAware):
            return subject.security_audit_entry
        name = subject if isinstance(subject, str) else type(subject).__qualname__
        try:
            return self._entries[name]
        except KeyError as error:
            raise LookupError(f"no security audit entry declared for {name}") from error

    def declared(self) -> tuple[SecurityAuditEntry, ...]:
        """Return entries in stable name order."""

        return tuple(self._entries[name] for name in sorted(self._entries))


class SecurityAuditManager:
    """Read-only security snapshot, diagnostics, and reporting manager."""

    __slots__ = ("_registry",)

    def __init__(self, registry: SecurityAuditRegistry) -> None:
        if not isinstance(registry, SecurityAuditRegistry):
            raise TypeError("registry must be a SecurityAuditRegistry")
        self._registry = registry

    def snapshot(
        self,
        logical_time: int,
        observations: Iterable[SecurityObservation] = (),
    ) -> SecuritySnapshot:
        """Create an immutable view without invoking observed components."""

        if isinstance(logical_time, bool) or logical_time < 0:
            raise ValueError("logical time must be a non-negative integer")
        observed = tuple(sorted(observations, key=_observation_key))
        entries = self._registry.declared()
        coverage = _coverage(observed)
        statistics = _statistics(entries, observed, 0)
        return SecuritySnapshot(logical_time, entries, observed, statistics, coverage)

    def audit(self, snapshot: SecuritySnapshot) -> SecurityDiagnostics:
        """Diagnose declarations and observations without enforcement."""

        if not isinstance(snapshot, SecuritySnapshot):
            raise TypeError("snapshot must be a SecuritySnapshot")
        findings = [*self._entry_diagnostics(), *_observation_diagnostics(snapshot.observations)]
        if not self._registry:
            findings.append(
                SecurityDiagnostic("INCOMPLETE_REGISTRY", "registry", "registry is empty")
            )
        return SecurityDiagnostics(
            tuple(sorted(findings, key=lambda item: (item.code, item.subject, item.message)))
        )

    def report(
        self,
        snapshot: SecuritySnapshot,
        history: SecurityAuditHistory | None = None,
    ) -> SecurityReport:
        """Build a deterministic descriptive report."""

        diagnostics = self.audit(snapshot)
        violations = tuple(
            SecurityViolation(item.code, item.subject, item.message)
            for item in diagnostics.items
            if item.code.endswith("VIOLATION") or item.code.startswith("MISSING_")
        )
        stats = _statistics(snapshot.entries, snapshot.observations, len(diagnostics.items))
        normalized = SecuritySnapshot(
            snapshot.logical_time,
            snapshot.entries,
            snapshot.observations,
            stats,
            snapshot.coverage,
        )
        health = (
            SecurityHealth.DEGRADED
            if diagnostics.items
            else SecurityHealth.HEALTHY if snapshot.entries else SecurityHealth.UNKNOWN
        )
        summary = SecuritySummary(
            health,
            len(snapshot.entries),
            len(snapshot.observations),
            len(violations),
            len(diagnostics.items),
        )
        compliance = SecurityCompliance(
            not violations, tuple(sorted({item.code for item in violations}))
        )
        report_history = history or SecurityAuditHistory((normalized,))
        return SecurityReport(
            summary,
            normalized,
            _metrics(stats, snapshot.coverage),
            violations,
            diagnostics,
            compliance,
            report_history,
        )

    def _entry_diagnostics(self) -> tuple[SecurityDiagnostic, ...]:
        findings: list[SecurityDiagnostic] = []
        registries: tuple[tuple[str, Mapping[str, object]], ...] = (
            ("security_contract", SECURITY_CONTRACTS),
            ("boundary_contract", SECURITY_BOUNDARY_CONTRACTS),
            ("validation_contract", INPUT_VALIDATION_CONTRACTS),
            ("runtime_policy", RUNTIME_SECURITY_POLICIES.policies),
            ("secure_failure_contract", SECURE_FAILURE_CONTRACTS.contracts),
        )
        for entry in self._registry.declared():
            for attribute, registry in registries:
                reference = getattr(entry, attribute)
                if reference is not None and reference not in registry:
                    findings.append(
                        SecurityDiagnostic(
                            f"MISSING_{attribute.upper()}",
                            entry.name,
                            f"missing declaration: {reference}",
                        )
                    )
        return tuple(findings)


def _observation_key(item: SecurityObservation) -> tuple[int, str, str]:
    return item.logical_time, item.observation_id, item.component


def _observation_diagnostics(
    observations: tuple[SecurityObservation, ...],
) -> tuple[SecurityDiagnostic, ...]:
    findings: list[SecurityDiagnostic] = []
    seen: set[str] = set()
    valid_decisions = {item.value for item in RuntimeSecurityDecision} | {
        item.value for item in SecureFailureDecision
    }
    valid_violations = {item.value for item in SecureFailureCategory}
    valid_incidents = {item.value for item in SecureFailureSeverity}
    valid_policies = set(RUNTIME_SECURITY_POLICIES.policies) | set(
        SECURE_FAILURE_CONTRACTS.contracts
    )
    for item in observations:
        if item.observation_id in seen:
            findings.append(
                SecurityDiagnostic(
                    "CONTRADICTORY_REPORT",
                    item.observation_id,
                    "duplicate observation identity",
                )
            )
        seen.add(item.observation_id)
        if (
            item.kind is SecurityObservationKind.DECISION
            and item.classification not in valid_decisions
        ):
            findings.append(
                SecurityDiagnostic("UNKNOWN_DECISION", item.component, item.classification)
            )
        if (
            item.kind is SecurityObservationKind.VIOLATION
            and item.classification not in valid_violations
        ):
            findings.append(
                SecurityDiagnostic("UNCLASSIFIED_VIOLATION", item.component, item.classification)
            )
        if (
            item.kind is SecurityObservationKind.INCIDENT
            and item.classification not in valid_incidents
        ):
            findings.append(
                SecurityDiagnostic("UNCLASSIFIED_INCIDENT", item.component, item.classification)
            )
        if item.policy is not None and item.policy not in valid_policies:
            findings.append(SecurityDiagnostic("INCOMPATIBLE_POLICY", item.component, item.policy))
        if item.runtime_active and not item.adopted:
            findings.append(
                SecurityDiagnostic(
                    "INCOHERENT_ADOPTION",
                    item.component,
                    "runtime active without explicit adoption",
                )
            )
    return tuple(findings)


def _coverage(observations: tuple[SecurityObservation, ...]) -> SecurityCoverage:
    total = len(observations)
    if not total:
        return SecurityCoverage(0, 0, 0)
    adopted = sum(item.adopted for item in observations)
    active = sum(item.runtime_active for item in observations)
    policy = sum(item.policy is not None for item in observations)
    return SecurityCoverage(
        adopted * 10_000 // total,
        active * 10_000 // total,
        policy * 10_000 // total,
    )


def _statistics(
    entries: tuple[SecurityAuditEntry, ...],
    observations: tuple[SecurityObservation, ...],
    diagnostics: int,
) -> SecurityStatistics:
    kinds = Counter(item.kind for item in observations)
    return SecurityStatistics(
        len(SECURITY_CONTRACTS),
        len(SECURITY_BOUNDARY_CONTRACTS),
        len(RUNTIME_SECURITY_POLICIES.policies),
        kinds[SecurityObservationKind.VIOLATION],
        kinds[SecurityObservationKind.INCIDENT],
        diagnostics,
        len(entries),
        kinds[SecurityObservationKind.DECISION],
    )


def _metrics(
    statistics: SecurityStatistics, coverage: SecurityCoverage
) -> tuple[SecurityMetric, ...]:
    return tuple(
        SecurityMetric(name, value)
        for name, value in (
            ("contracts", statistics.contracts),
            ("boundaries", statistics.boundaries),
            ("policies", statistics.policies),
            ("violations", statistics.violations),
            ("incidents", statistics.incidents),
            ("diagnostics", statistics.diagnostics),
            ("audit_entries", statistics.audit_entries),
            ("adoption_coverage", coverage.adoption),
            ("runtime_coverage", coverage.runtime),
            ("policy_coverage", coverage.policy),
        )
    )


_ENTRIES = (
    SecurityAuditEntry("security-contracts", security_contract="epip.core.kernel.Kernel"),
    SecurityAuditEntry("security-boundaries", boundary_contract="core-provider"),
    SecurityAuditEntry("trust-model", boundary_contract="user-framework"),
    SecurityAuditEntry("input-validation", validation_contract="public-api"),
    SecurityAuditEntry("runtime-security", runtime_policy="disabled"),
    SecurityAuditEntry("secure-failure", secure_failure_contract="component"),
)

SECURITY_AUDIT_REGISTRY = SecurityAuditRegistry(_ENTRIES)


def get_security_audit(subject: str | SecurityAuditAware) -> SecurityAuditEntry:
    """Resolve an official read-only security audit entry."""

    return SECURITY_AUDIT_REGISTRY.resolve(subject)


def declared_security_audits() -> tuple[SecurityAuditEntry, ...]:
    """Return official entries in deterministic order."""

    return SECURITY_AUDIT_REGISTRY.declared()


__all__ = [
    "SECURITY_AUDIT_REGISTRY",
    "SecurityAuditAware",
    "SecurityAuditEntry",
    "SecurityAuditHistory",
    "SecurityAuditManager",
    "SecurityAuditRegistry",
    "SecurityCompliance",
    "SecurityCoverage",
    "SecurityDiagnostic",
    "SecurityDiagnostics",
    "SecurityHealth",
    "SecurityMetric",
    "SecurityObservation",
    "SecurityObservationKind",
    "SecurityReport",
    "SecuritySnapshot",
    "SecurityStatistics",
    "SecuritySummary",
    "SecurityViolation",
    "declared_security_audits",
    "get_security_audit",
]
