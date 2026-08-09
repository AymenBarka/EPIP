"""Official failure and reliability contracts for EPIP components.

The declarations in this module are descriptive only.  They make existing
failure responsibilities machine-readable without changing runtime behaviour.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable


class FailureCategory(str, Enum):
    """Stable taxonomy used to classify failures."""

    PROGRAMMING_ERROR = "programming_error"
    DATA_ERROR = "data_error"
    CONFIGURATION_ERROR = "configuration_error"
    TRANSIENT_ERROR = "transient_error"
    PERMANENT_ERROR = "permanent_error"
    EXTERNAL_FAILURE = "external_failure"
    RESOURCE_FAILURE = "resource_failure"
    TIMEOUT = "timeout"
    INTERRUPTION = "interruption"
    CANCELLATION = "cancellation"


class FailureSeverity(str, Enum):
    """Operational impact assigned to a failure category."""

    INFORMATIONAL = "informational"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FailurePolicy(str, Enum):
    """Permitted framework response to a failure."""

    FAIL_FAST = "fail_fast"
    PROPAGATE = "propagate"
    RETRY_FORBIDDEN = "retry_forbidden"
    RETRY_ALLOWED = "retry_allowed"
    IGNORE = "ignore"
    ISOLATE = "isolate"
    COMPENSATE = "compensate"
    ABORT = "abort"


class FailureBoundary(str, Enum):
    """Boundary at which a failure must be contained or propagated."""

    CALL = "call"
    COMPONENT = "component"
    PIPELINE = "pipeline"
    REPLAY_RUN = "replay_run"
    PLUGIN = "plugin"
    PROVIDER = "provider"
    ADAPTER = "adapter"
    EXTERNAL_SYSTEM = "external_system"


class RecoveryExpectation(str, Enum):
    """Recovery action expected after a failure."""

    NONE = "none"
    CALLER_CORRECTION = "caller_correction"
    RETRY = "retry"
    ROLLBACK = "rollback"
    RECREATE_COMPONENT = "recreate_component"
    COMPENSATION = "compensation"
    EXTERNAL_RECOVERY = "external_recovery"


class FailureResponsibility(str, Enum):
    """Party responsible for handling or correcting a failure."""

    FRAMEWORK = "framework"
    CALLER = "caller"
    PLUGIN = "plugin"
    PROVIDER = "provider"
    ADAPTER = "adapter"
    EXTERNAL_SYSTEM = "external_system"
    OPERATING_SYSTEM = "operating_system"
    USER = "user"


@dataclass(frozen=True, slots=True)
class FailureContract:
    """Immutable policy for one failure category at one component boundary."""

    category: FailureCategory
    severity: FailureSeverity
    policy: FailurePolicy
    boundary: FailureBoundary
    recovery: RecoveryExpectation
    responsibility: FailureResponsibility
    description: str

    def __post_init__(self) -> None:
        enum_fields = (
            ("category", self.category, FailureCategory),
            ("severity", self.severity, FailureSeverity),
            ("policy", self.policy, FailurePolicy),
            ("boundary", self.boundary, FailureBoundary),
            ("recovery", self.recovery, RecoveryExpectation),
            ("responsibility", self.responsibility, FailureResponsibility),
        )
        for name, value, expected_type in enum_fields:
            if not isinstance(value, expected_type):
                raise TypeError(f"invalid failure {name}: {value!r}")
        if not self.description.strip():
            raise ValueError("failure description must be non-empty")
        if (
            self.policy is FailurePolicy.RETRY_ALLOWED
            and self.recovery is not RecoveryExpectation.RETRY
        ):
            raise ValueError("retry-allowed failures must declare retry recovery")
        if (
            self.policy is FailurePolicy.RETRY_FORBIDDEN
            and self.recovery is RecoveryExpectation.RETRY
        ):
            raise ValueError("retry-forbidden failures cannot declare retry recovery")
        if self.policy is FailurePolicy.IGNORE and self.severity is FailureSeverity.CRITICAL:
            raise ValueError("critical failures cannot be ignored")


@dataclass(frozen=True, slots=True)
class ReliabilityContract:
    """Complete, immutable reliability declaration for one component."""

    component: str
    failures: tuple[FailureContract, ...]
    availability_guarantee: str
    restrictions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.component.strip():
            raise ValueError("component must be non-empty")
        if not self.failures:
            raise ValueError("at least one failure contract is required")
        if not all(isinstance(failure, FailureContract) for failure in self.failures):
            raise ValueError("failures must contain only FailureContract values")
        if not self.availability_guarantee.strip():
            raise ValueError("availability guarantee must be non-empty")
        if not self.restrictions or not all(item.strip() for item in self.restrictions):
            raise ValueError("at least one non-empty reliability restriction is required")
        failures = tuple(self.failures)
        categories = {failure.category for failure in failures}
        if len(categories) != len(failures):
            raise ValueError("failure categories must be unique per component")
        object.__setattr__(self, "failures", failures)
        object.__setattr__(self, "restrictions", tuple(self.restrictions))


@runtime_checkable
class ReliabilityAware(Protocol):
    """Protocol for components exposing a native reliability contract."""

    @property
    def reliability_contract(self) -> ReliabilityContract:
        """Return the component's immutable reliability contract."""


class ReliabilityRegistry(Mapping[str, ReliabilityContract]):
    """Immutable, deterministic registry of reliability contracts."""

    __slots__ = ("_contracts",)

    def __init__(self, contracts: Iterable[ReliabilityContract]) -> None:
        items = tuple(contracts)
        mapping = {contract.component: contract for contract in items}
        if len(mapping) != len(items):
            raise ValueError("reliability contract component names must be unique")
        self._contracts: Mapping[str, ReliabilityContract] = MappingProxyType(mapping)

    def __getitem__(self, key: str) -> ReliabilityContract:
        return self._contracts[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._contracts)

    def __len__(self) -> int:
        return len(self._contracts)

    def resolve(self, component: str | type[object] | object) -> ReliabilityContract:
        """Resolve a contract using a qualified name, type, or instance."""

        if not isinstance(component, (str, type)) and isinstance(component, ReliabilityAware):
            return component.reliability_contract
        if isinstance(component, str):
            name = component
        else:
            component_type = component if isinstance(component, type) else type(component)
            name = f"{component_type.__module__}.{component_type.__qualname__}"
        try:
            return self._contracts[name]
        except KeyError as error:
            raise LookupError(f"no reliability contract declared for {name}") from error

    def declared(self) -> tuple[ReliabilityContract, ...]:
        """Return contracts in deterministic qualified-name order."""

        return tuple(self._contracts[name] for name in sorted(self._contracts))

    def audit(self, required: Iterable[str] = ()) -> tuple[str, ...]:
        """Return stable diagnostics for missing or structurally invalid declarations."""

        diagnostics = [
            f"missing reliability contract: {name}"
            for name in sorted(set(required) - self._contracts.keys())
        ]
        for contract in self.declared():
            if not contract.failures:
                diagnostics.append(f"incomplete reliability contract: {contract.component}")
        return tuple(diagnostics)


def _failure(
    category: FailureCategory,
    severity: FailureSeverity,
    policy: FailurePolicy,
    boundary: FailureBoundary,
    recovery: RecoveryExpectation,
    responsibility: FailureResponsibility,
    description: str,
) -> FailureContract:
    return FailureContract(
        category, severity, policy, boundary, recovery, responsibility, description
    )


_PROGRAMMING = _failure(
    FailureCategory.PROGRAMMING_ERROR,
    FailureSeverity.CRITICAL,
    FailurePolicy.FAIL_FAST,
    FailureBoundary.COMPONENT,
    RecoveryExpectation.NONE,
    FailureResponsibility.FRAMEWORK,
    "Invariant violations fail immediately and are never retried.",
)
_DATA = _failure(
    FailureCategory.DATA_ERROR,
    FailureSeverity.ERROR,
    FailurePolicy.PROPAGATE,
    FailureBoundary.CALL,
    RecoveryExpectation.CALLER_CORRECTION,
    FailureResponsibility.CALLER,
    "Invalid input is rejected and must be corrected by the caller.",
)
_CONFIGURATION = _failure(
    FailureCategory.CONFIGURATION_ERROR,
    FailureSeverity.ERROR,
    FailurePolicy.FAIL_FAST,
    FailureBoundary.COMPONENT,
    RecoveryExpectation.CALLER_CORRECTION,
    FailureResponsibility.USER,
    "Invalid configuration prevents the affected operation from starting.",
)
_INTERRUPTION = _failure(
    FailureCategory.INTERRUPTION,
    FailureSeverity.ERROR,
    FailurePolicy.ABORT,
    FailureBoundary.CALL,
    RecoveryExpectation.NONE,
    FailureResponsibility.CALLER,
    "Process interruption aborts the active operation and is propagated.",
)
_CANCELLATION = _failure(
    FailureCategory.CANCELLATION,
    FailureSeverity.WARNING,
    FailurePolicy.PROPAGATE,
    FailureBoundary.CALL,
    RecoveryExpectation.NONE,
    FailureResponsibility.CALLER,
    "Cancellation remains an explicit caller-controlled outcome.",
)
_TRANSIENT_EXTERNAL = _failure(
    FailureCategory.TRANSIENT_ERROR,
    FailureSeverity.WARNING,
    FailurePolicy.RETRY_ALLOWED,
    FailureBoundary.EXTERNAL_SYSTEM,
    RecoveryExpectation.RETRY,
    FailureResponsibility.EXTERNAL_SYSTEM,
    "A caller may retry only when the external operation is documented as safe.",
)
_EXTERNAL = _failure(
    FailureCategory.EXTERNAL_FAILURE,
    FailureSeverity.ERROR,
    FailurePolicy.PROPAGATE,
    FailureBoundary.EXTERNAL_SYSTEM,
    RecoveryExpectation.EXTERNAL_RECOVERY,
    FailureResponsibility.EXTERNAL_SYSTEM,
    "External failures are surfaced without being reclassified as framework success.",
)
_TIMEOUT = _failure(
    FailureCategory.TIMEOUT,
    FailureSeverity.ERROR,
    FailurePolicy.PROPAGATE,
    FailureBoundary.EXTERNAL_SYSTEM,
    RecoveryExpectation.EXTERNAL_RECOVERY,
    FailureResponsibility.EXTERNAL_SYSTEM,
    "Timeout handling follows the external boundary contract.",
)
_RESOURCE = _failure(
    FailureCategory.RESOURCE_FAILURE,
    FailureSeverity.ERROR,
    FailurePolicy.ABORT,
    FailureBoundary.COMPONENT,
    RecoveryExpectation.RECREATE_COMPONENT,
    FailureResponsibility.OPERATING_SYSTEM,
    "Resource exhaustion aborts the operation; silent degradation is forbidden.",
)
_PERMANENT = _failure(
    FailureCategory.PERMANENT_ERROR,
    FailureSeverity.ERROR,
    FailurePolicy.RETRY_FORBIDDEN,
    FailureBoundary.COMPONENT,
    RecoveryExpectation.CALLER_CORRECTION,
    FailureResponsibility.CALLER,
    "Permanent failures require correction before another attempt.",
)


def _internal(component: str, restriction: str) -> ReliabilityContract:
    return ReliabilityContract(
        component,
        (
            _PROGRAMMING,
            _DATA,
            _CONFIGURATION,
            _PERMANENT,
            _RESOURCE,
            _INTERRUPTION,
            _CANCELLATION,
        ),
        "The component remains available after rejected input; invariant failures are explicit.",
        (restriction,),
    )


def _external(
    component: str, boundary: FailureBoundary, owner: FailureResponsibility
) -> ReliabilityContract:
    transient = FailureContract(
        _TRANSIENT_EXTERNAL.category,
        _TRANSIENT_EXTERNAL.severity,
        _TRANSIENT_EXTERNAL.policy,
        boundary,
        _TRANSIENT_EXTERNAL.recovery,
        owner,
        _TRANSIENT_EXTERNAL.description,
    )
    external = FailureContract(
        _EXTERNAL.category,
        _EXTERNAL.severity,
        _EXTERNAL.policy,
        boundary,
        _EXTERNAL.recovery,
        owner,
        _EXTERNAL.description,
    )
    timeout = FailureContract(
        _TIMEOUT.category,
        _TIMEOUT.severity,
        _TIMEOUT.policy,
        boundary,
        _TIMEOUT.recovery,
        owner,
        _TIMEOUT.description,
    )
    return ReliabilityContract(
        component,
        (_PROGRAMMING, _DATA, transient, external, timeout, _RESOURCE, _INTERRUPTION),
        "Framework availability excludes the availability of the external dependency.",
        ("Retries require an idempotent operation and an explicit caller policy.",),
    )


_INTERNAL_COMPONENTS = (
    "epip.core.kernel.Kernel",
    "epip.core.registry.Registry",
    "epip.core.event_bus.EventBus",
    "epip.replay.replay_engine.ReplayEngine",
    "epip.replay.replay_session.ReplaySession",
    "epip.replay.replay_scheduler.ReplayScheduler",
    "epip.replay.replay_clock.ReplayClock",
    "epip.replay.replay_controller.ReplayController",
    "epip.replay.replay_iterator.ReplayIterator",
    "epip.features.feature_store.FeatureStore",
    "epip.marketdata.datasource_cache.DataSourceCache",
    "epip.features.providers.base_provider.BaseFeatureProvider",
    "epip.features.providers.indicator_provider.IndicatorProvider",
    "epip.features.providers.ohlc_provider.OHLCProvider",
    "epip.features.providers.session_provider.SessionProvider",
    "epip.features.providers.structure_provider.StructureProvider",
    "epip.swing.engine.SwingEngine",
    "epip.market_structure.engine.MarketStructureEngine",
    "epip.liquidity.engine.LiquidityEngine",
    "epip.fibonacci.engine.FibonacciEngine",
    "epip.context.engine.MarketContextEngine",
    "epip.elliott.engine.ElliottWaveEngine",
    "epip.decision.engine.DecisionEngine",
    "epip.risk.engine.RiskEngine",
    "epip.execution.engine.ExecutionEngine",
    "epip.portfolio.engine.PortfolioEngine",
    "epip.execution.paper_adapter.PaperTradingAdapter",
    "epip.core.plugin_context.PluginContext",
    "epip.core.plugin_result.PluginResult",
    "epip.core.plugin_protocol.PluginProtocol",
)

_EXTERNAL_COMPONENTS = (
    (
        "epip.marketdata.providers.base_provider.BaseProvider",
        FailureBoundary.PROVIDER,
        FailureResponsibility.PROVIDER,
    ),
    (
        "epip.marketdata.providers.csv_provider.CSVProvider",
        FailureBoundary.PROVIDER,
        FailureResponsibility.PROVIDER,
    ),
    (
        "epip.marketdata.providers.fake_provider.FakeProvider",
        FailureBoundary.PROVIDER,
        FailureResponsibility.PROVIDER,
    ),
    (
        "epip.marketdata.providers.mt5_provider.MT5Provider",
        FailureBoundary.PROVIDER,
        FailureResponsibility.PROVIDER,
    ),
    (
        "epip.marketdata.providers.twelvedata_provider.TwelveDataProvider",
        FailureBoundary.PROVIDER,
        FailureResponsibility.PROVIDER,
    ),
    (
        "epip.execution.mt5_adapter.MT5Adapter",
        FailureBoundary.ADAPTER,
        FailureResponsibility.ADAPTER,
    ),
    (
        "epip.marketdata.adapters.mt5_adapter.NullMT5Adapter",
        FailureBoundary.ADAPTER,
        FailureResponsibility.ADAPTER,
    ),
    (
        "epip.marketdata.adapters.twelvedata_adapter.NullTwelveDataAdapter",
        FailureBoundary.ADAPTER,
        FailureResponsibility.ADAPTER,
    ),
    (
        "epip.core.external_effects.ExternalEffectContract",
        FailureBoundary.EXTERNAL_SYSTEM,
        FailureResponsibility.EXTERNAL_SYSTEM,
    ),
)

_CONTRACTS = (
    *(
        _internal(name, "Failures are propagated through the existing public exception surface.")
        for name in _INTERNAL_COMPONENTS
    ),
    *(_external(name, boundary, owner) for name, boundary, owner in _EXTERNAL_COMPONENTS),
)

RELIABILITY_CONTRACTS = ReliabilityRegistry(_CONTRACTS)


def get_reliability_contract(component: str | type[object] | object) -> ReliabilityContract:
    """Resolve the official reliability contract for a component."""

    return RELIABILITY_CONTRACTS.resolve(component)


def declared_reliability_contracts() -> tuple[ReliabilityContract, ...]:
    """Return all reliability contracts in deterministic order."""

    return RELIABILITY_CONTRACTS.declared()


__all__ = [
    "RELIABILITY_CONTRACTS",
    "FailureBoundary",
    "FailureCategory",
    "FailureContract",
    "FailurePolicy",
    "FailureResponsibility",
    "FailureSeverity",
    "RecoveryExpectation",
    "ReliabilityAware",
    "ReliabilityContract",
    "ReliabilityRegistry",
    "declared_reliability_contracts",
    "get_reliability_contract",
]
