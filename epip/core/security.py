"""Declarative security contracts for public EPIP components.

This module describes trust, responsibility, boundary, and capability metadata.
It deliberately performs no authentication, authorization, access control, or
other runtime enforcement.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable


class SecurityClassification(str, Enum):
    """Architectural classification of a component or interface."""

    PUBLIC = "public"
    INTERNAL = "internal"
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    EXTERNAL = "external"
    SYSTEM = "system"
    PLUGIN = "plugin"
    FRAMEWORK = "framework"


class SecurityLevel(str, Enum):
    """Declared sensitivity of a security contract."""

    BASELINE = "baseline"
    GUARDED = "guarded"
    SENSITIVE = "sensitive"
    CRITICAL = "critical"


class TrustLevel(str, Enum):
    """Trust assumption made at the declared boundary."""

    TRUSTED = "trusted"
    CONDITIONAL = "conditional"
    UNTRUSTED = "untrusted"


class SecurityResponsibility(str, Enum):
    """Party responsible for satisfying a declared security restriction."""

    CALLER = "caller"
    FRAMEWORK = "framework"
    PLUGIN = "plugin"
    PROVIDER = "provider"
    ADAPTER = "adapter"
    OPERATING_SYSTEM = "operating_system"
    EXTERNAL_SYSTEM = "external_system"
    USER = "user"


class SecurityBoundary(str, Enum):
    """Architectural boundary crossed or protected by a component."""

    CORE = "core"
    KERNEL = "kernel"
    REPLAY = "replay"
    EVENT_BUS = "event_bus"
    PROVIDER = "provider"
    ADAPTER = "adapter"
    PLUGIN = "plugin"
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    SERIALIZATION = "serialization"
    CONFIGURATION = "configuration"
    EXTERNAL_API = "external_api"


class SecurityCapability(str, Enum):
    """Capability exposed or consumed at a security boundary."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    CREATE = "create"
    DELETE = "delete"
    IMPORT = "import"
    EXPORT = "export"
    SERIALIZE = "serialize"
    DESERIALIZE = "deserialize"
    NETWORK_ACCESS = "network_access"
    FILESYSTEM_ACCESS = "filesystem_access"
    CLOCK_ACCESS = "clock_access"
    IDENTITY_GENERATION = "identity_generation"


@dataclass(frozen=True, slots=True)
class SecurityContract:
    """Immutable declaration of one component's security assumptions."""

    component: str
    classification: SecurityClassification
    level: SecurityLevel
    trust: TrustLevel
    boundaries: frozenset[SecurityBoundary]
    responsibilities: frozenset[SecurityResponsibility]
    capabilities: frozenset[SecurityCapability]
    restrictions: tuple[str, ...]
    deterministic: bool = True

    def __post_init__(self) -> None:
        if not self.component.strip():
            raise ValueError("component must be non-empty")
        if not self.boundaries:
            raise ValueError("at least one security boundary is required")
        if not self.responsibilities:
            raise ValueError("at least one security responsibility is required")
        if not self.capabilities:
            raise ValueError("at least one security capability is required")
        if not self.restrictions or any(not item.strip() for item in self.restrictions):
            raise ValueError("security restrictions must be non-empty")
        if (
            self.classification is SecurityClassification.TRUSTED
            and self.trust is TrustLevel.UNTRUSTED
        ):
            raise ValueError("trusted classification contradicts untrusted trust")
        if (
            self.classification is SecurityClassification.UNTRUSTED
            and self.trust is TrustLevel.TRUSTED
        ):
            raise ValueError("untrusted classification contradicts trusted trust")
        object.__setattr__(self, "boundaries", frozenset(self.boundaries))
        object.__setattr__(self, "responsibilities", frozenset(self.responsibilities))
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "restrictions", tuple(self.restrictions))


@runtime_checkable
class SecurityAware(Protocol):
    """Protocol for objects that natively expose a security contract."""

    @property
    def security_contract(self) -> SecurityContract:
        """Return the object's immutable declarative security contract."""


@dataclass(frozen=True, slots=True)
class SecurityDiagnostics:
    """Deterministic diagnostics produced by a declarative contract audit."""

    components_checked: int
    violations: tuple[str, ...]

    @property
    def valid(self) -> bool:
        """Return whether the audited declarations are internally consistent."""

        return not self.violations


class SecurityAudit:
    """Stateless audit of declarative security metadata."""

    @staticmethod
    def inspect(contracts: Iterable[SecurityContract]) -> SecurityDiagnostics:
        """Inspect declarations without enforcing any runtime policy."""

        items = tuple(contracts)
        seen: set[str] = set()
        violations: list[str] = []
        for contract in sorted(items, key=lambda item: item.component):
            if contract.component in seen:
                violations.append(f"duplicate security contract: {contract.component}")
            seen.add(contract.component)
            if (
                SecurityCapability.NETWORK_ACCESS in contract.capabilities
                and SecurityBoundary.NETWORK not in contract.boundaries
            ):
                violations.append(f"network capability without boundary: {contract.component}")
            if (
                SecurityCapability.FILESYSTEM_ACCESS in contract.capabilities
                and SecurityBoundary.FILESYSTEM not in contract.boundaries
            ):
                violations.append(f"filesystem capability without boundary: {contract.component}")
        return SecurityDiagnostics(len(items), tuple(violations))


@dataclass(frozen=True, slots=True, init=False)
class SecurityRegistry:
    """Immutable registry of security contract declarations."""

    _contracts: Mapping[str, SecurityContract]

    def __init__(self, contracts: Iterable[SecurityContract]) -> None:
        items = tuple(contracts)
        mapped = {contract.component: contract for contract in items}
        if len(mapped) != len(items):
            raise ValueError("security contract components must be unique")
        diagnostics = SecurityAudit.inspect(items)
        if not diagnostics.valid:
            raise ValueError("; ".join(diagnostics.violations))
        object.__setattr__(self, "_contracts", MappingProxyType(mapped))

    @property
    def contracts(self) -> Mapping[str, SecurityContract]:
        """Return a read-only view of registered declarations."""

        return self._contracts

    def get(self, component: str) -> SecurityContract:
        """Resolve a contract by qualified component name."""

        try:
            return self._contracts[component]
        except KeyError as exc:
            raise LookupError(f"no security contract declared for {component}") from exc

    def declared(self) -> tuple[SecurityContract, ...]:
        """Return declarations in stable component-name order."""

        return tuple(self._contracts[name] for name in sorted(self._contracts))


def _contract(
    component: str,
    classification: SecurityClassification,
    level: SecurityLevel,
    trust: TrustLevel,
    boundaries: tuple[SecurityBoundary, ...],
    responsibilities: tuple[SecurityResponsibility, ...],
    capabilities: tuple[SecurityCapability, ...],
    restriction: str,
) -> SecurityContract:
    return SecurityContract(
        component=component,
        classification=classification,
        level=level,
        trust=trust,
        boundaries=frozenset(boundaries),
        responsibilities=frozenset(responsibilities),
        capabilities=frozenset(capabilities),
        restrictions=(restriction,),
    )


_CONTRACTS = (
    _contract(
        "epip.core.kernel.Kernel",
        SecurityClassification.FRAMEWORK,
        SecurityLevel.SENSITIVE,
        TrustLevel.CONDITIONAL,
        (SecurityBoundary.CORE, SecurityBoundary.KERNEL, SecurityBoundary.PLUGIN),
        (SecurityResponsibility.FRAMEWORK, SecurityResponsibility.PLUGIN),
        (SecurityCapability.READ, SecurityCapability.EXECUTE),
        "Callers remain responsible for selecting trusted plugin implementations.",
    ),
    _contract(
        "epip.core.event_bus.EventBus",
        SecurityClassification.INTERNAL,
        SecurityLevel.GUARDED,
        TrustLevel.CONDITIONAL,
        (SecurityBoundary.CORE, SecurityBoundary.EVENT_BUS),
        (SecurityResponsibility.CALLER, SecurityResponsibility.FRAMEWORK),
        (SecurityCapability.READ, SecurityCapability.WRITE, SecurityCapability.EXECUTE),
        "Published payloads and listeners remain caller-owned and are not authorized here.",
    ),
    _contract(
        "epip.replay.replay_engine.ReplayEngine",
        SecurityClassification.FRAMEWORK,
        SecurityLevel.GUARDED,
        TrustLevel.CONDITIONAL,
        (SecurityBoundary.REPLAY, SecurityBoundary.PROVIDER),
        (SecurityResponsibility.CALLER, SecurityResponsibility.PROVIDER),
        (SecurityCapability.READ, SecurityCapability.EXECUTE),
        "Input provenance and provider trust must be established by the caller.",
    ),
    _contract(
        "epip.marketdata.providers.base_provider.BaseProvider",
        SecurityClassification.EXTERNAL,
        SecurityLevel.SENSITIVE,
        TrustLevel.UNTRUSTED,
        (SecurityBoundary.PROVIDER, SecurityBoundary.EXTERNAL_API),
        (SecurityResponsibility.PROVIDER, SecurityResponsibility.EXTERNAL_SYSTEM),
        (SecurityCapability.READ, SecurityCapability.IMPORT),
        "Concrete providers must document and secure their own external credentials.",
    ),
    _contract(
        "epip.execution.paper_adapter.PaperTradingAdapter",
        SecurityClassification.INTERNAL,
        SecurityLevel.GUARDED,
        TrustLevel.CONDITIONAL,
        (SecurityBoundary.ADAPTER,),
        (SecurityResponsibility.ADAPTER, SecurityResponsibility.CALLER),
        (SecurityCapability.READ, SecurityCapability.WRITE, SecurityCapability.EXECUTE),
        "Paper execution is non-production and performs no caller authorization.",
    ),
    _contract(
        "epip.core.plugin_context.PluginContext",
        SecurityClassification.PLUGIN,
        SecurityLevel.SENSITIVE,
        TrustLevel.UNTRUSTED,
        (SecurityBoundary.PLUGIN, SecurityBoundary.KERNEL),
        (SecurityResponsibility.PLUGIN, SecurityResponsibility.FRAMEWORK),
        (SecurityCapability.READ, SecurityCapability.EXECUTE),
        "Plugin data and behavior must be treated as untrusted at integration boundaries.",
    ),
    _contract(
        "epip.core.identity.SystemClock",
        SecurityClassification.SYSTEM,
        SecurityLevel.BASELINE,
        TrustLevel.CONDITIONAL,
        (SecurityBoundary.CORE,),
        (SecurityResponsibility.OPERATING_SYSTEM, SecurityResponsibility.FRAMEWORK),
        (SecurityCapability.CLOCK_ACCESS,),
        "System time integrity is provided by the operating environment.",
    ),
    _contract(
        "epip.core.identity.SystemIdGenerator",
        SecurityClassification.SYSTEM,
        SecurityLevel.BASELINE,
        TrustLevel.CONDITIONAL,
        (SecurityBoundary.CORE,),
        (SecurityResponsibility.OPERATING_SYSTEM, SecurityResponsibility.FRAMEWORK),
        (SecurityCapability.IDENTITY_GENERATION,),
        "Generated identifiers are identities, not authentication credentials.",
    ),
)

_SECURITY_REGISTRY = SecurityRegistry(_CONTRACTS)
SECURITY_CONTRACTS: Mapping[str, SecurityContract] = _SECURITY_REGISTRY.contracts


def get_security_contract(component: object | type[object] | str) -> SecurityContract:
    """Resolve a native or registered contract without activating policy."""

    if not isinstance(component, (str, type)) and isinstance(component, SecurityAware):
        return component.security_contract
    if isinstance(component, str):
        name = component
    else:
        component_type = component if isinstance(component, type) else type(component)
        name = f"{component_type.__module__}.{component_type.__qualname__}"
    return _SECURITY_REGISTRY.get(name)


def declared_security_contracts() -> tuple[SecurityContract, ...]:
    """Return all official declarations in deterministic order."""

    return _SECURITY_REGISTRY.declared()


__all__ = [
    "SECURITY_CONTRACTS",
    "SecurityAudit",
    "SecurityAware",
    "SecurityBoundary",
    "SecurityCapability",
    "SecurityClassification",
    "SecurityContract",
    "SecurityDiagnostics",
    "SecurityLevel",
    "SecurityRegistry",
    "SecurityResponsibility",
    "TrustLevel",
    "declared_security_contracts",
    "get_security_contract",
]
