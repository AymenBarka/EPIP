"""Declarative secure-failure contracts for explicit application adoption.

This module classifies failures and containment intent.  It never intercepts,
raises, suppresses, retries, or transforms an exception.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable


class SecureFailureSeverity(str, Enum):
    """Security impact assigned to a classified incident."""

    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class SecureFailureCategory(str, Enum):
    """Stable categories used to classify a failure."""

    VALIDATION_FAILURE = "validation_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    AUTHENTICATION_FAILURE = "authentication_failure"
    CONFIGURATION_FAILURE = "configuration_failure"
    PROVIDER_FAILURE = "provider_failure"
    PLUGIN_FAILURE = "plugin_failure"
    ADAPTER_FAILURE = "adapter_failure"
    SERIALIZATION_FAILURE = "serialization_failure"
    NETWORK_FAILURE = "network_failure"
    FILESYSTEM_FAILURE = "filesystem_failure"
    RESOURCE_FAILURE = "resource_failure"
    UNKNOWN_FAILURE = "unknown_failure"


class SecureFailureBoundary(str, Enum):
    """Declarative containment boundary for an incident."""

    COMPONENT = "component"
    PLUGIN = "plugin"
    PROVIDER = "provider"
    ADAPTER = "adapter"
    SESSION = "session"
    CALL = "call"
    BOUNDARY = "boundary"
    EXTERNAL = "external"


class SecureFailurePolicy(str, Enum):
    """Policy selected explicitly by an application."""

    FAIL_FAST = "fail_fast"
    FAIL_SAFE = "fail_safe"
    CONTAIN = "contain"
    ISOLATE = "isolate"
    REPORT = "report"
    ESCALATE = "escalate"
    IGNORE = "ignore"
    DELEGATE = "delegate"
    CUSTOM = "custom"


class SecureFailureDecision(str, Enum):
    """Deterministic declarative outcome of policy resolution."""

    ALLOW_FAILURE = "allow_failure"
    BLOCK = "block"
    CONTAIN = "contain"
    ISOLATE = "isolate"
    REPORT = "report"
    ESCALATE = "escalate"
    DELEGATE = "delegate"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SecureFailureContract:
    """Immutable declaration of accepted failures and containment intent."""

    name: str
    component: str
    categories: tuple[SecureFailureCategory, ...]
    severities: tuple[SecureFailureSeverity, ...]
    boundary: SecureFailureBoundary
    default_policy: SecureFailurePolicy
    enabled: bool = False
    restrictions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.component.strip():
            raise ValueError("contract name and component must be non-empty")
        if not self.categories or not self.severities:
            raise ValueError("contract categories and severities must be non-empty")
        object.__setattr__(self, "categories", tuple(sorted(set(self.categories), key=str)))
        object.__setattr__(self, "severities", tuple(sorted(set(self.severities), key=str)))
        object.__setattr__(self, "restrictions", tuple(sorted(set(self.restrictions))))


@dataclass(frozen=True, slots=True)
class SecureFailureContext:
    """Immutable caller-provided context; never populated implicitly."""

    component: str
    operation: str
    boundary: SecureFailureBoundary
    attributes: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.component.strip() or not self.operation.strip():
            raise ValueError("context component and operation must be non-empty")
        object.__setattr__(
            self, "attributes", MappingProxyType(dict(sorted(self.attributes.items())))
        )


@dataclass(frozen=True, slots=True)
class SecureFailureIncident:
    """Typed immutable description of a security-relevant failure."""

    incident_id: str
    category: SecureFailureCategory
    severity: SecureFailureSeverity
    boundary: SecureFailureBoundary
    component: str
    summary: str

    def __post_init__(self) -> None:
        values = (self.incident_id, self.component, self.summary)
        if any(not value.strip() for value in values):
            raise ValueError("incident identity, component and summary must be non-empty")


@dataclass(frozen=True, slots=True)
class SecureFailureResult:
    """Deterministic result without exception or runtime side effects."""

    contract_name: str
    incident_id: str
    decision: SecureFailureDecision


@dataclass(frozen=True, slots=True)
class SecureFailureStatistics:
    """Counters derived exclusively from explicit results."""

    total: int = 0
    blocked: int = 0
    contained: int = 0
    isolated: int = 0
    reported: int = 0
    escalated: int = 0
    delegated: int = 0
    allowed: int = 0
    unknown: int = 0

    @classmethod
    def from_results(cls, results: Iterable[SecureFailureResult]) -> SecureFailureStatistics:
        items = tuple(results)
        counts = {decision: 0 for decision in SecureFailureDecision}
        for item in items:
            counts[item.decision] += 1
        return cls(
            total=len(items),
            blocked=counts[SecureFailureDecision.BLOCK],
            contained=counts[SecureFailureDecision.CONTAIN],
            isolated=counts[SecureFailureDecision.ISOLATE],
            reported=counts[SecureFailureDecision.REPORT],
            escalated=counts[SecureFailureDecision.ESCALATE],
            delegated=counts[SecureFailureDecision.DELEGATE],
            allowed=counts[SecureFailureDecision.ALLOW_FAILURE],
            unknown=counts[SecureFailureDecision.UNKNOWN],
        )


@dataclass(frozen=True, slots=True)
class SecureFailureDiagnostics:
    """Deterministically ordered audit findings."""

    missing_contracts: tuple[str, ...] = ()
    incompatible_policies: tuple[str, ...] = ()
    invalid_categories: tuple[str, ...] = ()
    invalid_severities: tuple[str, ...] = ()
    incoherent_boundaries: tuple[str, ...] = ()
    incomplete_incidents: tuple[str, ...] = ()
    invalid_configurations: tuple[str, ...] = ()
    incomplete_registry: tuple[str, ...] = ()
    typed_violations: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        return not any(
            (
                self.missing_contracts,
                self.incompatible_policies,
                self.invalid_categories,
                self.invalid_severities,
                self.incoherent_boundaries,
                self.incomplete_incidents,
                self.invalid_configurations,
                self.incomplete_registry,
                self.typed_violations,
            )
        )


@dataclass(frozen=True, slots=True, init=False)
class SecureFailureRegistry:
    """Immutable contract registry."""

    _contracts: Mapping[str, SecureFailureContract]

    def __init__(self, contracts: Mapping[str, SecureFailureContract]) -> None:
        if any(not name.strip() or name != contract.name for name, contract in contracts.items()):
            raise ValueError("registry names must be non-empty and match contract names")
        object.__setattr__(self, "_contracts", MappingProxyType(dict(sorted(contracts.items()))))

    @property
    def contracts(self) -> Mapping[str, SecureFailureContract]:
        return self._contracts

    def get(self, name: str) -> SecureFailureContract:
        try:
            return self._contracts[name]
        except KeyError as exc:
            raise LookupError(f"no secure failure contract declared for {name}") from exc

    def declared(self) -> tuple[tuple[str, SecureFailureContract], ...]:
        return tuple(self._contracts.items())


class SecureFailureAudit:
    """Pure validation of declarations and caller-supplied incidents."""

    @staticmethod
    def inspect(
        registry: SecureFailureRegistry,
        incidents: Iterable[SecureFailureIncident] = (),
        *,
        required_contracts: Iterable[str] = (),
    ) -> SecureFailureDiagnostics:
        missing = tuple(sorted(set(required_contracts) - set(registry.contracts)))
        incompatible: list[str] = []
        invalid_categories: list[str] = []
        invalid_severities: list[str] = []
        boundaries: list[str] = []
        configurations: list[str] = []
        incomplete: list[str] = []
        typed: list[str] = []
        for contract in registry.contracts.values():
            invalid_categories.extend(
                f"{contract.name}:{category}"
                for category in contract.categories
                if not isinstance(category, SecureFailureCategory)
            )
            invalid_severities.extend(
                f"{contract.name}:{severity}"
                for severity in contract.severities
                if not isinstance(severity, SecureFailureSeverity)
            )
            if contract.default_policy is SecureFailurePolicy.CUSTOM:
                configurations.append(contract.name)
            if (
                contract.boundary is SecureFailureBoundary.PROVIDER
                and "provider" not in contract.component.lower()
            ):
                boundaries.append(contract.name)
            if (
                contract.default_policy is SecureFailurePolicy.ISOLATE
                and contract.boundary is SecureFailureBoundary.CALL
            ):
                incompatible.append(contract.name)
        for incident in incidents:
            if incident.category is SecureFailureCategory.UNKNOWN_FAILURE:
                typed.append(f"unknown-category:{incident.incident_id}")
            if incident.severity is SecureFailureSeverity.UNKNOWN:
                typed.append(f"unknown-severity:{incident.incident_id}")
            if not incident.summary.strip():
                incomplete.append(incident.incident_id)
        return SecureFailureDiagnostics(
            missing_contracts=missing,
            incompatible_policies=tuple(sorted(incompatible)),
            invalid_categories=tuple(sorted(invalid_categories)),
            invalid_severities=tuple(sorted(invalid_severities)),
            incoherent_boundaries=tuple(sorted(boundaries)),
            incomplete_incidents=tuple(sorted(incomplete)),
            invalid_configurations=tuple(sorted(configurations)),
            incomplete_registry=() if registry.contracts else ("registry is empty",),
            typed_violations=tuple(sorted(typed)),
        )


class SecureFailureAdapter:
    """Pure opt-in mapping from policy to decision."""

    _DECISIONS = MappingProxyType(
        {
            SecureFailurePolicy.FAIL_FAST: SecureFailureDecision.BLOCK,
            SecureFailurePolicy.FAIL_SAFE: SecureFailureDecision.BLOCK,
            SecureFailurePolicy.CONTAIN: SecureFailureDecision.CONTAIN,
            SecureFailurePolicy.ISOLATE: SecureFailureDecision.ISOLATE,
            SecureFailurePolicy.REPORT: SecureFailureDecision.REPORT,
            SecureFailurePolicy.ESCALATE: SecureFailureDecision.ESCALATE,
            SecureFailurePolicy.IGNORE: SecureFailureDecision.ALLOW_FAILURE,
            SecureFailurePolicy.DELEGATE: SecureFailureDecision.DELEGATE,
            SecureFailurePolicy.CUSTOM: SecureFailureDecision.UNKNOWN,
        }
    )

    @classmethod
    def decide(
        cls,
        contract: SecureFailureContract,
        context: SecureFailureContext,
        incident: SecureFailureIncident,
    ) -> SecureFailureResult:
        del context
        decision = (
            cls._DECISIONS[contract.default_policy]
            if contract.enabled
            else SecureFailureDecision.UNKNOWN
        )
        return SecureFailureResult(contract.name, incident.incident_id, decision)


@runtime_checkable
class SecureFailureAware(Protocol):
    """Protocol for components that explicitly expose a declaration."""

    @property
    def secure_failure_contract(self) -> SecureFailureContract:
        """Return the explicitly adopted contract."""


_ALL_CATEGORIES = tuple(SecureFailureCategory)
_ALL_SEVERITIES = tuple(SecureFailureSeverity)
_CONTRACTS = {
    boundary.value: SecureFailureContract(
        name=boundary.value,
        component=f"{boundary.value.title()}Boundary",
        categories=_ALL_CATEGORIES,
        severities=_ALL_SEVERITIES,
        boundary=boundary,
        default_policy=SecureFailurePolicy.CONTAIN,
        restrictions=("declarative-only", "explicit-adoption-required"),
    )
    for boundary in SecureFailureBoundary
}

SECURE_FAILURE_CONTRACTS = SecureFailureRegistry(_CONTRACTS)


def get_secure_failure_contract(name: str) -> SecureFailureContract:
    """Resolve an official inert contract by stable name."""

    return SECURE_FAILURE_CONTRACTS.get(name)


def declared_secure_failure_contracts() -> tuple[tuple[str, SecureFailureContract], ...]:
    """Return all official contracts in deterministic order."""

    return SECURE_FAILURE_CONTRACTS.declared()
