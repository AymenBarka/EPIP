"""Optional runtime execution model for EPIP security declarations.

The runtime is deliberately inert until an application explicitly registers an
adoption.  Importing this module never changes an existing EPIP component.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable


class RuntimeSecurityPolicy(str, Enum):
    """Runtime enforcement mode selected by an application."""

    NO_SECURITY = "no_security"
    MONITOR_ONLY = "monitor_only"
    VALIDATE_ONLY = "validate_only"
    VALIDATE_AND_REPORT = "validate_and_report"
    STRICT = "strict"
    CUSTOM = "custom"
    DISABLED = "disabled"


class RuntimeSecurityDecision(str, Enum):
    """Deterministic outcome of a runtime security evaluation."""

    ALLOW = "allow"
    DENY = "deny"
    REPORT_ONLY = "report_only"
    IGNORE = "ignore"
    DELEGATE = "delegate"
    UNKNOWN = "unknown"


class SecurityPolicyScope(str, Enum):
    """Lifetime and visibility of an explicit policy binding."""

    GLOBAL = "global"
    COMPONENT = "component"
    INSTANCE = "instance"
    CALL = "call"
    SESSION = "session"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class SecurityPolicyConfiguration:
    """Immutable policy configuration; disabled unless explicitly enabled."""

    policy: RuntimeSecurityPolicy
    enabled: bool = False
    report_violations: bool = False
    deny_on_violation: bool = False
    custom_policy_name: str | None = None


@dataclass(frozen=True, slots=True)
class SecurityPolicyBinding:
    """Bind a configured policy to one declared runtime target."""

    binding_id: str
    policy_name: str
    scope: SecurityPolicyScope
    target: str
    security_contracts: tuple[str, ...] = ()
    boundary_contracts: tuple[str, ...] = ()
    validation_contracts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for label, value in (
            ("binding id", self.binding_id),
            ("policy name", self.policy_name),
            ("target", self.target),
        ):
            if not value.strip():
                raise ValueError(f"{label} must be non-empty")
        object.__setattr__(self, "security_contracts", tuple(sorted(self.security_contracts)))
        object.__setattr__(self, "boundary_contracts", tuple(sorted(self.boundary_contracts)))
        object.__setattr__(self, "validation_contracts", tuple(sorted(self.validation_contracts)))


@dataclass(frozen=True, slots=True)
class RuntimeSecurityAdoption:
    """Explicit opt-in connecting a binding to its configuration."""

    binding: SecurityPolicyBinding
    configuration: SecurityPolicyConfiguration
    explicitly_adopted: bool = False

    @property
    def active(self) -> bool:
        """Return whether runtime evaluation is explicitly enabled."""

        return self.explicitly_adopted and self.configuration.enabled


@dataclass(frozen=True, slots=True)
class RuntimeSecurityContext:
    """Immutable context supplied to one policy evaluation."""

    component: str
    operation: str
    scope: SecurityPolicyScope
    session_id: str | None = None
    attributes: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.component.strip() or not self.operation.strip():
            raise ValueError("component and operation must be non-empty")
        ordered = dict(sorted(self.attributes.items()))
        object.__setattr__(self, "attributes", MappingProxyType(ordered))


@dataclass(frozen=True, slots=True)
class RuntimeSecurityViolation:
    """Typed runtime violation emitted by an explicitly adopted policy."""

    code: str
    message: str
    contract_name: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise ValueError("violation code and message must be non-empty")


@dataclass(frozen=True, slots=True)
class RuntimeSecurityResult:
    """Immutable deterministic result of a policy evaluation."""

    binding_id: str
    decision: RuntimeSecurityDecision
    violations: tuple[RuntimeSecurityViolation, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "violations",
            tuple(sorted(self.violations, key=lambda item: (item.code, item.message))),
        )


@dataclass(frozen=True, slots=True)
class RuntimeSecurityStatistics:
    """Immutable counters derived from runtime results."""

    evaluations: int = 0
    allowed: int = 0
    denied: int = 0
    reported: int = 0
    ignored: int = 0
    delegated: int = 0
    unknown: int = 0
    violations: int = 0

    @classmethod
    def from_results(cls, results: Iterable[RuntimeSecurityResult]) -> RuntimeSecurityStatistics:
        """Build deterministic statistics from immutable results."""

        items = tuple(results)
        counts = {decision: 0 for decision in RuntimeSecurityDecision}
        for item in items:
            counts[item.decision] += 1
        return cls(
            evaluations=len(items),
            allowed=counts[RuntimeSecurityDecision.ALLOW],
            denied=counts[RuntimeSecurityDecision.DENY],
            reported=counts[RuntimeSecurityDecision.REPORT_ONLY],
            ignored=counts[RuntimeSecurityDecision.IGNORE],
            delegated=counts[RuntimeSecurityDecision.DELEGATE],
            unknown=counts[RuntimeSecurityDecision.UNKNOWN],
            violations=sum(len(item.violations) for item in items),
        )


@dataclass(frozen=True, slots=True)
class RuntimeSecuritySnapshot:
    """Immutable point-in-time view without implicit timestamps."""

    sequence: int
    adoptions: tuple[RuntimeSecurityAdoption, ...]
    results: tuple[RuntimeSecurityResult, ...]
    statistics: RuntimeSecurityStatistics


@dataclass(frozen=True, slots=True)
class RuntimeSecurityDiagnostics:
    """Deterministic diagnostic categories for runtime configuration."""

    missing_policies: tuple[str, ...] = ()
    incompatible_policies: tuple[str, ...] = ()
    invalid_bindings: tuple[str, ...] = ()
    incoherent_scopes: tuple[str, ...] = ()
    incompatible_contracts: tuple[str, ...] = ()
    invalid_configurations: tuple[str, ...] = ()
    typed_violations: tuple[RuntimeSecurityViolation, ...] = ()
    incomplete_registry: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        """Return whether no configuration defect was detected."""

        return not any(
            (
                self.missing_policies,
                self.incompatible_policies,
                self.invalid_bindings,
                self.incoherent_scopes,
                self.incompatible_contracts,
                self.invalid_configurations,
                self.typed_violations,
                self.incomplete_registry,
            )
        )


@dataclass(frozen=True, slots=True, init=False)
class RuntimeSecurityRegistry:
    """Immutable registry of named policy configurations."""

    _policies: Mapping[str, SecurityPolicyConfiguration]

    def __init__(self, policies: Mapping[str, SecurityPolicyConfiguration]) -> None:
        if any(not name.strip() for name in policies):
            raise ValueError("runtime security policy names must be non-empty")
        object.__setattr__(self, "_policies", MappingProxyType(dict(sorted(policies.items()))))

    @property
    def policies(self) -> Mapping[str, SecurityPolicyConfiguration]:
        """Return the read-only policy mapping."""

        return self._policies

    def get(self, name: str) -> SecurityPolicyConfiguration:
        """Resolve a policy configuration by stable name."""

        try:
            return self._policies[name]
        except KeyError as exc:
            raise LookupError(f"no runtime security policy declared for {name}") from exc

    def declared(self) -> tuple[tuple[str, SecurityPolicyConfiguration], ...]:
        """Return entries in deterministic name order."""

        return tuple(self._policies.items())


class RuntimeSecurityAudit:
    """Stateless validation of explicit runtime security adoption."""

    @staticmethod
    def inspect(
        registry: RuntimeSecurityRegistry,
        adoptions: Iterable[RuntimeSecurityAdoption],
        *,
        security_contracts: Iterable[str] = (),
        boundary_contracts: Iterable[str] = (),
        validation_contracts: Iterable[str] = (),
        violations: Iterable[RuntimeSecurityViolation] = (),
    ) -> RuntimeSecurityDiagnostics:
        """Inspect bindings and compatibility without executing a policy."""

        items = tuple(adoptions)
        known_security = set(security_contracts)
        known_boundaries = set(boundary_contracts)
        known_validation = set(validation_contracts)
        missing: list[str] = []
        incompatible: list[str] = []
        invalid_bindings: list[str] = []
        scopes: list[str] = []
        contracts: list[str] = []
        configurations: list[str] = []
        ids: set[str] = set()
        for adoption in sorted(items, key=lambda item: item.binding.binding_id):
            binding = adoption.binding
            if binding.binding_id in ids:
                invalid_bindings.append(f"duplicate binding: {binding.binding_id}")
            ids.add(binding.binding_id)
            try:
                declared = registry.get(binding.policy_name)
            except LookupError:
                missing.append(binding.policy_name)
                continue
            if declared.policy is not adoption.configuration.policy:
                incompatible.append(binding.binding_id)
            if binding.scope is SecurityPolicyScope.GLOBAL and binding.target != "*":
                scopes.append(binding.binding_id)
            if adoption.configuration.policy is RuntimeSecurityPolicy.CUSTOM:
                if not adoption.configuration.custom_policy_name:
                    configurations.append(binding.binding_id)
            elif adoption.configuration.custom_policy_name is not None:
                configurations.append(binding.binding_id)
            for name in binding.security_contracts:
                if name not in known_security:
                    contracts.append(f"security:{name}")
            for name in binding.boundary_contracts:
                if name not in known_boundaries:
                    contracts.append(f"boundary:{name}")
            for name in binding.validation_contracts:
                if name not in known_validation:
                    contracts.append(f"validation:{name}")
        return RuntimeSecurityDiagnostics(
            missing_policies=tuple(sorted(set(missing))),
            incompatible_policies=tuple(sorted(set(incompatible))),
            invalid_bindings=tuple(sorted(set(invalid_bindings))),
            incoherent_scopes=tuple(sorted(set(scopes))),
            incompatible_contracts=tuple(sorted(set(contracts))),
            invalid_configurations=tuple(sorted(set(configurations))),
            typed_violations=tuple(sorted(violations, key=lambda item: (item.code, item.message))),
            incomplete_registry=() if registry.policies else ("registry is empty",),
        )


class RuntimeSecurityAdapter:
    """Pure adapter mapping violations to a configured policy decision."""

    @staticmethod
    def evaluate(
        adoption: RuntimeSecurityAdoption,
        context: RuntimeSecurityContext,
        violations: Iterable[RuntimeSecurityViolation] = (),
    ) -> RuntimeSecurityResult:
        """Evaluate only the supplied violations; no contract runs implicitly."""

        del context
        items = tuple(violations)
        if not adoption.active:
            decision = RuntimeSecurityDecision.IGNORE
        elif adoption.configuration.policy is RuntimeSecurityPolicy.CUSTOM:
            decision = RuntimeSecurityDecision.DELEGATE
        elif adoption.configuration.policy in {
            RuntimeSecurityPolicy.NO_SECURITY,
            RuntimeSecurityPolicy.DISABLED,
        }:
            decision = RuntimeSecurityDecision.IGNORE
        elif not items:
            decision = RuntimeSecurityDecision.ALLOW
        elif adoption.configuration.policy is RuntimeSecurityPolicy.MONITOR_ONLY:
            decision = RuntimeSecurityDecision.REPORT_ONLY
        else:
            decision = RuntimeSecurityDecision.DENY
        return RuntimeSecurityResult(adoption.binding.binding_id, decision, items)


class RuntimeSecurityManager:
    """Explicit adoption manager; empty and inert when constructed."""

    def __init__(self, registry: RuntimeSecurityRegistry | None = None) -> None:
        self._registry = registry or RUNTIME_SECURITY_POLICIES
        self._adoptions: dict[str, RuntimeSecurityAdoption] = {}
        self._results: list[RuntimeSecurityResult] = []
        self._sequence = 0

    def adopt(self, adoption: RuntimeSecurityAdoption) -> None:
        """Register an application-provided explicit adoption."""

        if not adoption.explicitly_adopted:
            raise ValueError("runtime security adoption must be explicit")
        self._registry.get(adoption.binding.policy_name)
        if adoption.binding.binding_id in self._adoptions:
            raise ValueError(f"duplicate runtime security binding: {adoption.binding.binding_id}")
        self._adoptions[adoption.binding.binding_id] = adoption
        self._sequence += 1

    def revoke(self, binding_id: str) -> None:
        """Remove an explicit adoption by stable binding identity."""

        if binding_id not in self._adoptions:
            raise LookupError(f"runtime security binding not adopted: {binding_id}")
        del self._adoptions[binding_id]
        self._sequence += 1

    def evaluate(
        self,
        binding_id: str,
        context: RuntimeSecurityContext,
        violations: Iterable[RuntimeSecurityViolation] = (),
    ) -> RuntimeSecurityResult:
        """Evaluate one explicitly adopted binding."""

        try:
            adoption = self._adoptions[binding_id]
        except KeyError as exc:
            raise LookupError(f"runtime security binding not adopted: {binding_id}") from exc
        result = RuntimeSecurityAdapter.evaluate(adoption, context, violations)
        self._results.append(result)
        self._sequence += 1
        return result

    def snapshot(self) -> RuntimeSecuritySnapshot:
        """Return a deterministic immutable manager snapshot."""

        adoptions = tuple(self._adoptions[name] for name in sorted(self._adoptions))
        results = tuple(self._results)
        return RuntimeSecuritySnapshot(
            self._sequence,
            adoptions,
            results,
            RuntimeSecurityStatistics.from_results(results),
        )


@runtime_checkable
class RuntimeSecurityAware(Protocol):
    """Protocol for components opting into a runtime security adoption."""

    @property
    def runtime_security_adoption(self) -> RuntimeSecurityAdoption:
        """Return the component's explicit runtime security adoption."""


_POLICY_CONFIGURATIONS = {
    policy.value: SecurityPolicyConfiguration(policy=policy) for policy in RuntimeSecurityPolicy
}

RUNTIME_SECURITY_POLICIES = RuntimeSecurityRegistry(_POLICY_CONFIGURATIONS)


def get_runtime_security_policy(name: str) -> SecurityPolicyConfiguration:
    """Resolve an official inert runtime security policy by name."""

    return RUNTIME_SECURITY_POLICIES.get(name)


def declared_runtime_security_policies() -> tuple[tuple[str, SecurityPolicyConfiguration], ...]:
    """Return official policies in deterministic order."""

    return RUNTIME_SECURITY_POLICIES.declared()
