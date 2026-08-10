"""Declarative input-validation contracts for EPIP public boundaries.

This module contains architecture metadata only. It does not validate,
normalize, reject, or otherwise alter values at runtime.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable


class ValidationCategory(str, Enum):
    """Category of an expected input-validation rule."""

    TYPE_VALIDATION = "type_validation"
    NULLABILITY = "nullability"
    RANGE_VALIDATION = "range_validation"
    ENUM_VALIDATION = "enum_validation"
    FORMAT_VALIDATION = "format_validation"
    STRUCTURE_VALIDATION = "structure_validation"
    IDENTITY_VALIDATION = "identity_validation"
    RESOURCE_VALIDATION = "resource_validation"
    SECURITY_VALIDATION = "security_validation"
    CONFIGURATION_VALIDATION = "configuration_validation"


class ValidationPolicy(str, Enum):
    """Declarative policy assigned to an input-validation rule."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    DOCUMENTED_ONLY = "documented_only"
    CALLER_RESPONSIBLE = "caller_responsible"
    FRAMEWORK_RESPONSIBLE = "framework_responsible"
    EXTERNAL_RESPONSIBLE = "external_responsible"
    NOT_APPLICABLE = "not_applicable"


class ValidationSeverity(str, Enum):
    """Architectural significance of a missing or failed validation."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationResponsibility(str, Enum):
    """Party expected to own validation at a declared boundary."""

    CALLER = "caller"
    FRAMEWORK = "framework"
    KERNEL = "kernel"
    PLUGIN = "plugin"
    PROVIDER = "provider"
    ADAPTER = "adapter"
    EXTERNAL_SYSTEM = "external_system"
    OPERATING_SYSTEM = "operating_system"
    USER = "user"


class ValidationBoundary(str, Enum):
    """Public or integration boundary receiving inputs."""

    PUBLIC_API = "public_api"
    KERNEL = "kernel"
    REPLAY = "replay"
    PROVIDERS = "providers"
    ADAPTERS = "adapters"
    PLUGINS = "plugins"
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    SERIALIZATION = "serialization"
    CONFIGURATION = "configuration"
    EVENTBUS = "eventbus"


class ValidationCapability(str, Enum):
    """Validation capability expected at a declared boundary."""

    TYPE_CHECKING = "type_checking"
    RANGE_CHECKING = "range_checking"
    IDENTITY_VERIFICATION = "identity_verification"
    CONFIGURATION_VALIDATION = "configuration_validation"
    INPUT_NORMALIZATION = "input_normalization"
    FORMAT_VERIFICATION = "format_verification"
    RESOURCE_EXISTENCE = "resource_existence"
    SCHEMA_VERIFICATION = "schema_verification"
    PERMISSION_DECLARATION = "permission_declaration"
    CONSTRAINT_DECLARATION = "constraint_declaration"


@dataclass(frozen=True, slots=True)
class InputValidationRule:
    """Immutable declaration of one expected validation rule."""

    name: str
    category: ValidationCategory
    severity: ValidationSeverity
    policy: ValidationPolicy
    responsibility: ValidationResponsibility
    capability: ValidationCapability
    description: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("validation rule name must be non-empty")
        if not self.description.strip():
            raise ValueError("validation rule description must be non-empty")


@dataclass(frozen=True, slots=True)
class InputValidationContract:
    """Immutable declarative validation contract for one boundary."""

    name: str
    boundary: ValidationBoundary
    rules: tuple[InputValidationRule, ...]
    capabilities: frozenset[ValidationCapability]
    responsibility: ValidationResponsibility
    restrictions: tuple[str, ...]
    deterministic: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("input-validation contract name must be non-empty")
        if not self.rules:
            raise ValueError("at least one input-validation rule is required")
        if not self.capabilities:
            raise ValueError("at least one validation capability is required")
        if not self.restrictions or any(not item.strip() for item in self.restrictions):
            raise ValueError("input-validation restrictions must be non-empty")
        rules = tuple(sorted(self.rules, key=lambda item: item.name))
        if len({rule.name for rule in rules}) != len(rules):
            raise ValueError("input-validation rule names must be unique")
        if {rule.capability for rule in rules} - set(self.capabilities):
            raise ValueError("every rule capability must be declared by the contract")
        object.__setattr__(self, "rules", rules)
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "restrictions", tuple(self.restrictions))


@runtime_checkable
class InputValidationAware(Protocol):
    """Protocol for objects exposing declarative validation metadata."""

    @property
    def input_validation_contract(self) -> InputValidationContract:
        """Return the object's immutable input-validation contract."""


@dataclass(frozen=True, slots=True)
class ValidationDiagnostics:
    """Deterministic result of an input-validation contract audit."""

    contracts_checked: int
    violations: tuple[str, ...]

    @property
    def valid(self) -> bool:
        """Return whether all declarations are coherent and complete."""

        return not self.violations


class ValidationAudit:
    """Stateless consistency audit for declarative validation metadata."""

    @staticmethod
    def inspect(
        contracts: Iterable[InputValidationContract],
        expected_boundaries: Iterable[ValidationBoundary] = (),
    ) -> ValidationDiagnostics:
        """Inspect declarations without activating their validation rules."""

        items = tuple(contracts)
        violations: list[str] = []
        names: set[str] = set()
        boundaries: set[ValidationBoundary] = set()
        for contract in sorted(items, key=lambda item: item.name):
            if contract.name in names:
                violations.append(f"duplicate input-validation contract: {contract.name}")
            names.add(contract.name)
            if not isinstance(contract.boundary, ValidationBoundary):
                violations.append(f"invalid validation boundary: {contract.name}")
            else:
                boundaries.add(contract.boundary)
            if not isinstance(contract.responsibility, ValidationResponsibility):
                violations.append(f"incoherent validation responsibility: {contract.name}")
            for rule in contract.rules:
                if not isinstance(rule.category, ValidationCategory):
                    violations.append(f"invalid validation category: {contract.name}")
                if not isinstance(rule.severity, ValidationSeverity):
                    violations.append(f"invalid validation severity: {contract.name}")
                if not isinstance(rule.policy, ValidationPolicy):
                    violations.append(f"incompatible validation policy: {contract.name}")
                if not isinstance(rule.responsibility, ValidationResponsibility):
                    violations.append(f"incoherent rule responsibility: {contract.name}")
                if not isinstance(rule.capability, ValidationCapability):
                    violations.append(f"invalid validation capability: {contract.name}")
                if (
                    rule.policy is ValidationPolicy.CALLER_RESPONSIBLE
                    and rule.responsibility is not ValidationResponsibility.CALLER
                ):
                    violations.append(f"contradictory caller responsibility: {contract.name}")
                if (
                    rule.policy is ValidationPolicy.FRAMEWORK_RESPONSIBLE
                    and rule.responsibility is not ValidationResponsibility.FRAMEWORK
                ):
                    violations.append(f"contradictory framework responsibility: {contract.name}")
                if (
                    rule.policy is ValidationPolicy.EXTERNAL_RESPONSIBLE
                    and rule.responsibility
                    not in {
                        ValidationResponsibility.EXTERNAL_SYSTEM,
                        ValidationResponsibility.OPERATING_SYSTEM,
                    }
                ):
                    violations.append(f"contradictory external responsibility: {contract.name}")
        for boundary in sorted(set(expected_boundaries) - boundaries, key=lambda item: item.value):
            violations.append(f"missing validation boundary: {boundary.value}")
        if not items:
            violations.append("incomplete input-validation registry")
        return ValidationDiagnostics(len(items), tuple(violations))


@dataclass(frozen=True, slots=True, init=False)
class InputValidationRegistry:
    """Immutable registry of declarative input-validation contracts."""

    _contracts: Mapping[str, InputValidationContract]

    def __init__(self, contracts: Iterable[InputValidationContract]) -> None:
        items = tuple(contracts)
        mapped = {contract.name: contract for contract in items}
        if len(mapped) != len(items):
            raise ValueError("input-validation contract names must be unique")
        diagnostics = ValidationAudit.inspect(items)
        if not diagnostics.valid:
            raise ValueError("; ".join(diagnostics.violations))
        object.__setattr__(self, "_contracts", MappingProxyType(mapped))

    @property
    def contracts(self) -> Mapping[str, InputValidationContract]:
        """Return a read-only view of registered contracts."""

        return self._contracts

    def get(self, name: str) -> InputValidationContract:
        """Resolve a contract by stable name."""

        try:
            return self._contracts[name]
        except KeyError as exc:
            raise LookupError(f"no input-validation contract declared for {name}") from exc

    def declared(self) -> tuple[InputValidationContract, ...]:
        """Return contracts in deterministic name order."""

        return tuple(self._contracts[name] for name in sorted(self._contracts))


def _contract(
    name: str,
    boundary: ValidationBoundary,
    category: ValidationCategory,
    severity: ValidationSeverity,
    responsibility: ValidationResponsibility,
    capability: ValidationCapability,
) -> InputValidationContract:
    policy = {
        ValidationResponsibility.CALLER: ValidationPolicy.CALLER_RESPONSIBLE,
        ValidationResponsibility.FRAMEWORK: ValidationPolicy.FRAMEWORK_RESPONSIBLE,
        ValidationResponsibility.EXTERNAL_SYSTEM: ValidationPolicy.EXTERNAL_RESPONSIBLE,
        ValidationResponsibility.OPERATING_SYSTEM: ValidationPolicy.EXTERNAL_RESPONSIBLE,
    }.get(responsibility, ValidationPolicy.DOCUMENTED_ONLY)
    return InputValidationContract(
        name=name,
        boundary=boundary,
        rules=(
            InputValidationRule(
                name=f"{name}-declaration",
                category=category,
                severity=severity,
                policy=policy,
                responsibility=responsibility,
                capability=capability,
                description="Expected validation is declared but not enforced by this module.",
            ),
        ),
        capabilities=frozenset({capability}),
        responsibility=responsibility,
        restrictions=("Declaration only; no automatic validation is performed.",),
    )


_CONTRACTS = (
    _contract(
        "public-api",
        ValidationBoundary.PUBLIC_API,
        ValidationCategory.TYPE_VALIDATION,
        ValidationSeverity.HIGH,
        ValidationResponsibility.CALLER,
        ValidationCapability.TYPE_CHECKING,
    ),
    _contract(
        "kernel",
        ValidationBoundary.KERNEL,
        ValidationCategory.IDENTITY_VALIDATION,
        ValidationSeverity.CRITICAL,
        ValidationResponsibility.KERNEL,
        ValidationCapability.IDENTITY_VERIFICATION,
    ),
    _contract(
        "replay",
        ValidationBoundary.REPLAY,
        ValidationCategory.STRUCTURE_VALIDATION,
        ValidationSeverity.HIGH,
        ValidationResponsibility.FRAMEWORK,
        ValidationCapability.SCHEMA_VERIFICATION,
    ),
    _contract(
        "providers",
        ValidationBoundary.PROVIDERS,
        ValidationCategory.RANGE_VALIDATION,
        ValidationSeverity.HIGH,
        ValidationResponsibility.PROVIDER,
        ValidationCapability.RANGE_CHECKING,
    ),
    _contract(
        "adapters",
        ValidationBoundary.ADAPTERS,
        ValidationCategory.SECURITY_VALIDATION,
        ValidationSeverity.CRITICAL,
        ValidationResponsibility.ADAPTER,
        ValidationCapability.PERMISSION_DECLARATION,
    ),
    _contract(
        "plugins",
        ValidationBoundary.PLUGINS,
        ValidationCategory.IDENTITY_VALIDATION,
        ValidationSeverity.CRITICAL,
        ValidationResponsibility.PLUGIN,
        ValidationCapability.IDENTITY_VERIFICATION,
    ),
    _contract(
        "filesystem",
        ValidationBoundary.FILESYSTEM,
        ValidationCategory.RESOURCE_VALIDATION,
        ValidationSeverity.HIGH,
        ValidationResponsibility.OPERATING_SYSTEM,
        ValidationCapability.RESOURCE_EXISTENCE,
    ),
    _contract(
        "network",
        ValidationBoundary.NETWORK,
        ValidationCategory.FORMAT_VALIDATION,
        ValidationSeverity.CRITICAL,
        ValidationResponsibility.EXTERNAL_SYSTEM,
        ValidationCapability.FORMAT_VERIFICATION,
    ),
    _contract(
        "serialization",
        ValidationBoundary.SERIALIZATION,
        ValidationCategory.STRUCTURE_VALIDATION,
        ValidationSeverity.HIGH,
        ValidationResponsibility.FRAMEWORK,
        ValidationCapability.SCHEMA_VERIFICATION,
    ),
    _contract(
        "configuration",
        ValidationBoundary.CONFIGURATION,
        ValidationCategory.CONFIGURATION_VALIDATION,
        ValidationSeverity.HIGH,
        ValidationResponsibility.USER,
        ValidationCapability.CONFIGURATION_VALIDATION,
    ),
    _contract(
        "eventbus",
        ValidationBoundary.EVENTBUS,
        ValidationCategory.ENUM_VALIDATION,
        ValidationSeverity.MEDIUM,
        ValidationResponsibility.FRAMEWORK,
        ValidationCapability.CONSTRAINT_DECLARATION,
    ),
)

_INPUT_VALIDATION_REGISTRY = InputValidationRegistry(_CONTRACTS)
INPUT_VALIDATION_CONTRACTS: Mapping[str, InputValidationContract] = (
    _INPUT_VALIDATION_REGISTRY.contracts
)


def get_input_validation_contract(
    subject: InputValidationAware | str,
) -> InputValidationContract:
    """Resolve a native or registered declarative validation contract."""

    if not isinstance(subject, str):
        return subject.input_validation_contract
    return _INPUT_VALIDATION_REGISTRY.get(subject)


def declared_input_validation_contracts() -> tuple[InputValidationContract, ...]:
    """Return all official declarations in deterministic order."""

    return _INPUT_VALIDATION_REGISTRY.declared()


__all__ = [
    "INPUT_VALIDATION_CONTRACTS",
    "InputValidationAware",
    "InputValidationContract",
    "InputValidationRegistry",
    "InputValidationRule",
    "ValidationAudit",
    "ValidationBoundary",
    "ValidationCapability",
    "ValidationCategory",
    "ValidationDiagnostics",
    "ValidationPolicy",
    "ValidationResponsibility",
    "ValidationSeverity",
    "declared_input_validation_contracts",
    "get_input_validation_contract",
]
