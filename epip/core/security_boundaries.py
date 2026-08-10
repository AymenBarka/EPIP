"""Declarative security boundaries and trust transitions for EPIP.

The declarations in this module are architecture metadata only. They do not
authenticate callers, authorize operations, validate payloads, or enforce a
runtime policy.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable


class SecurityZone(str, Enum):
    """Architectural zones participating in security boundaries."""

    CORE = "core"
    FRAMEWORK = "framework"
    KERNEL = "kernel"
    ENGINE = "engine"
    EVENTBUS = "eventbus"
    PLUGIN = "plugin"
    PROVIDER = "provider"
    ADAPTER = "adapter"
    EXTERNAL = "external"
    SYSTEM = "system"
    USER = "user"
    NETWORK = "network"
    FILESYSTEM = "filesystem"


class TrustDomain(str, Enum):
    """Trust assumption assigned to the source of a transition."""

    FULLY_TRUSTED = "fully_trusted"
    TRUSTED = "trusted"
    PARTIALLY_TRUSTED = "partially_trusted"
    UNTRUSTED = "untrusted"
    EXTERNAL_TRUST = "external_trust"
    UNKNOWN_TRUST = "unknown_trust"


class BoundaryDirection(str, Enum):
    """Direction in which a declared boundary may be crossed."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class BoundaryCapability(str, Enum):
    """Capability visible at a declared security boundary."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    PUBLISH = "publish"
    SUBSCRIBE = "subscribe"
    IMPORT = "import"
    EXPORT = "export"
    SERIALIZE = "serialize"
    DESERIALIZE = "deserialize"
    FILESYSTEM_ACCESS = "filesystem_access"
    NETWORK_ACCESS = "network_access"
    CLOCK_ACCESS = "clock_access"
    IDENTITY_ACCESS = "identity_access"
    CONFIGURATION_ACCESS = "configuration_access"


class BoundaryPolicy(str, Enum):
    """Declarative treatment expected for a boundary capability."""

    ALLOWED = "allowed"
    RESTRICTED = "restricted"
    FORBIDDEN = "forbidden"
    DELEGATED = "delegated"
    OBSERVED = "observed"
    DOCUMENTED = "documented"


class BoundaryClassification(str, Enum):
    """Architectural category of a security boundary."""

    INTERNAL = "internal"
    TRUST = "trust"
    EXTERNAL = "external"
    SYSTEM = "system"
    USER = "user"


@dataclass(frozen=True, slots=True)
class TrustTransition:
    """Immutable declaration of one transition between security zones."""

    source: SecurityZone
    destination: SecurityZone
    direction: BoundaryDirection
    ownership: str
    responsibility: str
    expected_validation: tuple[str, ...]
    trust_level: TrustDomain

    def __post_init__(self) -> None:
        if self.source is self.destination:
            raise ValueError("trust transition zones must differ")
        if not self.ownership.strip():
            raise ValueError("transition ownership must be non-empty")
        if not self.responsibility.strip():
            raise ValueError("transition responsibility must be non-empty")
        if not self.expected_validation or any(
            not item.strip() for item in self.expected_validation
        ):
            raise ValueError("expected validation declarations must be non-empty")
        object.__setattr__(self, "expected_validation", tuple(self.expected_validation))


@dataclass(frozen=True, slots=True)
class SecurityBoundaryContract:
    """Immutable declarative contract for one named trust boundary."""

    name: str
    classification: BoundaryClassification
    transition: TrustTransition
    capabilities: frozenset[BoundaryCapability]
    policies: tuple[tuple[BoundaryCapability, BoundaryPolicy], ...]
    restrictions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("boundary name must be non-empty")
        if not self.capabilities:
            raise ValueError("at least one boundary capability is required")
        if not self.policies:
            raise ValueError("at least one boundary policy is required")
        if not self.restrictions or any(not item.strip() for item in self.restrictions):
            raise ValueError("boundary restrictions must be non-empty")
        capabilities = frozenset(self.capabilities)
        policies = tuple(
            sorted(
                self.policies,
                key=lambda item: (
                    item[0].value if isinstance(item[0], BoundaryCapability) else str(item[0])
                ),
            )
        )
        policy_capabilities = tuple(item[0] for item in policies)
        if len(set(policy_capabilities)) != len(policy_capabilities):
            raise ValueError("boundary policy capabilities must be unique")
        if set(policy_capabilities) != set(capabilities):
            raise ValueError("every boundary capability requires exactly one policy")
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "policies", policies)
        object.__setattr__(self, "restrictions", tuple(self.restrictions))


@runtime_checkable
class SecurityBoundaryAware(Protocol):
    """Protocol for objects exposing a native boundary declaration."""

    @property
    def security_boundary_contract(self) -> SecurityBoundaryContract:
        """Return the object's immutable declarative boundary contract."""


@dataclass(frozen=True, slots=True)
class BoundaryDiagnostics:
    """Deterministic result of a declarative boundary audit."""

    boundaries_checked: int
    violations: tuple[str, ...]

    @property
    def valid(self) -> bool:
        """Return whether all audited declarations are coherent."""

        return not self.violations


class BoundaryAudit:
    """Stateless consistency audit for declarative boundary metadata."""

    @staticmethod
    def inspect(
        contracts: Iterable[SecurityBoundaryContract],
        expected_boundaries: Iterable[str] = (),
    ) -> BoundaryDiagnostics:
        """Inspect declarations without applying or enforcing their policies."""

        items = tuple(contracts)
        violations: list[str] = []
        names: set[str] = set()
        transition_owners: dict[tuple[object, object], str] = {}
        for contract in sorted(items, key=lambda item: item.name):
            if contract.name in names:
                violations.append(f"duplicate boundary: {contract.name}")
            names.add(contract.name)
            transition = contract.transition
            if not isinstance(transition.source, SecurityZone) or not isinstance(
                transition.destination, SecurityZone
            ):
                violations.append(f"unknown security zone: {contract.name}")
            if not isinstance(transition.direction, BoundaryDirection):
                violations.append(f"invalid transition direction: {contract.name}")
            if not isinstance(transition.trust_level, TrustDomain):
                violations.append(f"incompatible trust declaration: {contract.name}")
            key = (transition.source, transition.destination)
            previous_owner = transition_owners.get(key)
            if previous_owner is not None and previous_owner != transition.ownership:
                violations.append(f"contradictory boundary ownership: {contract.name}")
            transition_owners[key] = transition.ownership
            for capability, policy in contract.policies:
                if not isinstance(capability, BoundaryCapability):
                    violations.append(f"incoherent boundary capability: {contract.name}")
                if not isinstance(policy, BoundaryPolicy):
                    violations.append(f"invalid boundary policy: {contract.name}")
            if transition.source in {
                SecurityZone.NETWORK,
                SecurityZone.EXTERNAL,
            } and transition.trust_level not in {TrustDomain.UNTRUSTED, TrustDomain.EXTERNAL_TRUST}:
                violations.append(f"incompatible external trust: {contract.name}")
        for name in sorted(set(expected_boundaries) - names):
            violations.append(f"missing boundary: {name}")
        if not items:
            violations.append("incomplete security boundary registry")
        return BoundaryDiagnostics(len(items), tuple(violations))


@dataclass(frozen=True, slots=True, init=False)
class SecurityBoundaryRegistry:
    """Immutable registry of declarative security boundary contracts."""

    _contracts: Mapping[str, SecurityBoundaryContract]

    def __init__(self, contracts: Iterable[SecurityBoundaryContract]) -> None:
        items = tuple(contracts)
        mapped = {contract.name: contract for contract in items}
        if len(mapped) != len(items):
            raise ValueError("security boundary names must be unique")
        diagnostics = BoundaryAudit.inspect(items)
        if not diagnostics.valid:
            raise ValueError("; ".join(diagnostics.violations))
        object.__setattr__(self, "_contracts", MappingProxyType(mapped))

    @property
    def contracts(self) -> Mapping[str, SecurityBoundaryContract]:
        """Return a read-only view of registered boundary contracts."""

        return self._contracts

    def get(self, name: str) -> SecurityBoundaryContract:
        """Resolve a boundary contract by its stable name."""

        try:
            return self._contracts[name]
        except KeyError as exc:
            raise LookupError(f"no security boundary declared for {name}") from exc

    def declared(self) -> tuple[SecurityBoundaryContract, ...]:
        """Return registered boundaries in deterministic name order."""

        return tuple(self._contracts[name] for name in sorted(self._contracts))


def _boundary(
    name: str,
    classification: BoundaryClassification,
    source: SecurityZone,
    destination: SecurityZone,
    direction: BoundaryDirection,
    trust: TrustDomain,
    ownership: str,
    responsibility: str,
    validation: str,
    capabilities: tuple[BoundaryCapability, ...],
    policy: BoundaryPolicy,
) -> SecurityBoundaryContract:
    return SecurityBoundaryContract(
        name=name,
        classification=classification,
        transition=TrustTransition(
            source=source,
            destination=destination,
            direction=direction,
            ownership=ownership,
            responsibility=responsibility,
            expected_validation=(validation,),
            trust_level=trust,
        ),
        capabilities=frozenset(capabilities),
        policies=tuple((capability, policy) for capability in capabilities),
        restrictions=("Declaration only; no runtime security enforcement is performed.",),
    )


_BOUNDARIES = (
    _boundary(
        "core-provider",
        BoundaryClassification.TRUST,
        SecurityZone.CORE,
        SecurityZone.PROVIDER,
        BoundaryDirection.OUTBOUND,
        TrustDomain.PARTIALLY_TRUSTED,
        "core",
        "provider",
        "Provider input validation is expected.",
        (BoundaryCapability.IMPORT, BoundaryCapability.READ),
        BoundaryPolicy.RESTRICTED,
    ),
    _boundary(
        "core-plugin",
        BoundaryClassification.TRUST,
        SecurityZone.CORE,
        SecurityZone.PLUGIN,
        BoundaryDirection.BIDIRECTIONAL,
        TrustDomain.UNTRUSTED,
        "kernel",
        "plugin",
        "Plugin compatibility and provenance validation are expected.",
        (BoundaryCapability.EXECUTE, BoundaryCapability.IMPORT),
        BoundaryPolicy.RESTRICTED,
    ),
    _boundary(
        "plugin-eventbus",
        BoundaryClassification.TRUST,
        SecurityZone.PLUGIN,
        SecurityZone.EVENTBUS,
        BoundaryDirection.OUTBOUND,
        TrustDomain.UNTRUSTED,
        "eventbus",
        "plugin",
        "Event shape and listener declarations are expected to be validated.",
        (BoundaryCapability.PUBLISH, BoundaryCapability.SUBSCRIBE),
        BoundaryPolicy.RESTRICTED,
    ),
    _boundary(
        "provider-engine",
        BoundaryClassification.TRUST,
        SecurityZone.PROVIDER,
        SecurityZone.ENGINE,
        BoundaryDirection.INBOUND,
        TrustDomain.PARTIALLY_TRUSTED,
        "engine",
        "provider",
        "Provider data integrity validation is expected.",
        (BoundaryCapability.IMPORT, BoundaryCapability.READ),
        BoundaryPolicy.RESTRICTED,
    ),
    _boundary(
        "engine-adapter",
        BoundaryClassification.INTERNAL,
        SecurityZone.ENGINE,
        SecurityZone.ADAPTER,
        BoundaryDirection.OUTBOUND,
        TrustDomain.TRUSTED,
        "engine",
        "adapter",
        "Adapter request validation is expected.",
        (BoundaryCapability.EXECUTE, BoundaryCapability.EXPORT),
        BoundaryPolicy.DELEGATED,
    ),
    _boundary(
        "adapter-external",
        BoundaryClassification.EXTERNAL,
        SecurityZone.ADAPTER,
        SecurityZone.EXTERNAL,
        BoundaryDirection.BIDIRECTIONAL,
        TrustDomain.EXTERNAL_TRUST,
        "adapter",
        "external_system",
        "External response and protocol validation are expected.",
        (BoundaryCapability.NETWORK_ACCESS, BoundaryCapability.READ, BoundaryCapability.WRITE),
        BoundaryPolicy.RESTRICTED,
    ),
    _boundary(
        "user-framework",
        BoundaryClassification.USER,
        SecurityZone.USER,
        SecurityZone.FRAMEWORK,
        BoundaryDirection.INBOUND,
        TrustDomain.UNTRUSTED,
        "framework",
        "user",
        "Public input validation is expected.",
        (BoundaryCapability.CONFIGURATION_ACCESS, BoundaryCapability.EXECUTE),
        BoundaryPolicy.RESTRICTED,
    ),
    _boundary(
        "filesystem-framework",
        BoundaryClassification.SYSTEM,
        SecurityZone.FILESYSTEM,
        SecurityZone.FRAMEWORK,
        BoundaryDirection.INBOUND,
        TrustDomain.EXTERNAL_TRUST,
        "framework",
        "operating_system",
        "Path, format, and content validation are expected.",
        (BoundaryCapability.FILESYSTEM_ACCESS, BoundaryCapability.DESERIALIZE),
        BoundaryPolicy.RESTRICTED,
    ),
    _boundary(
        "network-provider",
        BoundaryClassification.EXTERNAL,
        SecurityZone.NETWORK,
        SecurityZone.PROVIDER,
        BoundaryDirection.INBOUND,
        TrustDomain.EXTERNAL_TRUST,
        "provider",
        "external_system",
        "Transport and payload validation are expected.",
        (BoundaryCapability.NETWORK_ACCESS, BoundaryCapability.DESERIALIZE),
        BoundaryPolicy.RESTRICTED,
    ),
)

_SECURITY_BOUNDARY_REGISTRY = SecurityBoundaryRegistry(_BOUNDARIES)
SECURITY_BOUNDARY_CONTRACTS: Mapping[str, SecurityBoundaryContract] = (
    _SECURITY_BOUNDARY_REGISTRY.contracts
)


def get_security_boundary_contract(
    boundary: SecurityBoundaryAware | str,
) -> SecurityBoundaryContract:
    """Resolve a native or registered declarative boundary contract."""

    if not isinstance(boundary, str):
        return boundary.security_boundary_contract
    return _SECURITY_BOUNDARY_REGISTRY.get(boundary)


def declared_security_boundaries() -> tuple[SecurityBoundaryContract, ...]:
    """Return all official boundary declarations in deterministic order."""

    return _SECURITY_BOUNDARY_REGISTRY.declared()


__all__ = [
    "SECURITY_BOUNDARY_CONTRACTS",
    "BoundaryAudit",
    "BoundaryCapability",
    "BoundaryClassification",
    "BoundaryDiagnostics",
    "BoundaryDirection",
    "BoundaryPolicy",
    "SecurityBoundaryAware",
    "SecurityBoundaryContract",
    "SecurityBoundaryRegistry",
    "SecurityZone",
    "TrustDomain",
    "TrustTransition",
    "declared_security_boundaries",
    "get_security_boundary_contract",
]
