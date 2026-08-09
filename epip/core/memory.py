"""Official memory and resource contracts for public EPIP components.

This module is descriptive only.  It records existing ownership and lifecycle
expectations without allocating resources, adding caches, or changing runtime
behaviour.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable


class MemoryClassification(str, Enum):
    """Official memory and resource classifications."""

    STATELESS = "memory_stateless"
    OWNED = "memory_owned"
    SHARED = "memory_shared"
    CACHED = "memory_cached"
    EPHEMERAL = "memory_ephemeral"
    PERSISTENT = "memory_persistent"
    RESOURCE_MANAGED = "resource_managed"
    RESOURCE_EXTERNAL = "resource_external"


class MemoryOwnership(str, Enum):
    """Party responsible for memory or resource state."""

    CALLER = "caller"
    COMPONENT = "component"
    FRAMEWORK = "framework"
    SHARED = "shared"
    EXTERNAL_SYSTEM = "external_system"


class MemoryLifecycle(str, Enum):
    """Scope that bounds the declared state lifetime."""

    CALL = "call"
    INSTANCE = "instance"
    RUN = "run"
    APPLICATION = "application"
    PERSISTENT = "persistent"
    EXTERNAL = "external"


class AllocationPolicy(str, Enum):
    """How the component obtains state or resources."""

    NONE = "none"
    EAGER = "eager"
    LAZY = "lazy"
    CALLER_PROVIDED = "caller_provided"
    EXTERNAL = "external"


class ReleasePolicy(str, Enum):
    """How owned state or resources are released."""

    NONE = "none"
    GARBAGE_COLLECTED = "garbage_collected"
    EXPLICIT = "explicit"
    CONTEXT_MANAGED = "context_managed"
    PROCESS_LIFETIME = "process_lifetime"
    EXTERNAL = "external"


class CachePolicy(str, Enum):
    """Cache retention policy."""

    NONE = "none"
    BOUNDED = "bounded"
    UNBOUNDED = "unbounded"
    EXTERNAL = "external"


class HistoryPolicy(str, Enum):
    """Historical state retention policy."""

    NONE = "none"
    BOUNDED = "bounded"
    UNBOUNDED = "unbounded"
    PERSISTENT = "persistent"


class ThreadVisibility(str, Enum):
    """Visibility of state across execution threads."""

    IMMUTABLE_SHARED = "immutable_shared"
    SHARED = "shared"
    THREAD_CONFINED = "thread_confined"
    RUN_CONFINED = "run_confined"
    EXTERNAL = "external"


class MemoryMutability(str, Enum):
    """Mutability of the component's retained state."""

    IMMUTABLE = "immutable"
    MUTABLE = "mutable"
    SYNCHRONIZED = "synchronized"
    EXTERNAL = "external"


class CleanupStrategy(str, Enum):
    """Mechanism expected to clean up retained state or resources."""

    NONE = "none"
    GARBAGE_COLLECTION = "garbage_collection"
    EXPLICIT_CLOSE = "explicit_close"
    CONTEXT_EXIT = "context_exit"
    CLEAR_OPERATION = "clear_operation"
    EXTERNAL_OWNER = "external_owner"


class GarbageCollectionExpectation(str, Enum):
    """Garbage-collection expectation for the component."""

    IMMEDIATE_ELIGIBILITY = "immediate_eligibility"
    AFTER_INSTANCE_RELEASE = "after_instance_release"
    AFTER_RUN = "after_run"
    PROCESS_LIFETIME = "process_lifetime"
    EXTERNAL_LIFETIME = "external_lifetime"


class ResourceType(str, Enum):
    """Primary resource governed by the contract."""

    MEMORY = "memory"
    CACHE = "cache"
    HISTORY = "history"
    FILE = "file"
    NETWORK = "network"
    BROKER = "broker"
    CLOCK = "clock"
    IDENTITY = "identity"
    PLUGIN = "plugin"


class MemoryFailureBehaviour(str, Enum):
    """State and resource behaviour when an operation fails."""

    NO_RETAINED_STATE = "no_retained_state"
    STATE_PRESERVED = "state_preserved"
    STATE_ROLLED_BACK = "state_rolled_back"
    RESOURCE_RELEASE_REQUIRED = "resource_release_required"
    EXTERNAL_SYSTEM_DEFINED = "external_system_defined"


class MemoryGrowthExpectation(str, Enum):
    """Expected upper-bound shape for retained memory."""

    CONSTANT = "constant"
    INPUT_BOUNDED = "input_bounded"
    CONFIGURATION_BOUNDED = "configuration_bounded"
    HISTORY_DEPENDENT = "history_dependent"
    CACHE_DEPENDENT = "cache_dependent"
    EXTERNAL = "external"


@dataclass(frozen=True, slots=True)
class MemoryContract:
    """Immutable, machine-readable declaration of memory responsibilities."""

    component: str
    classifications: frozenset[MemoryClassification]
    ownership: MemoryOwnership
    lifecycle: MemoryLifecycle
    allocation_policy: AllocationPolicy
    release_policy: ReleasePolicy
    cache_policy: CachePolicy
    history_policy: HistoryPolicy
    thread_visibility: ThreadVisibility
    mutability: MemoryMutability
    cleanup_strategy: CleanupStrategy
    garbage_collection: GarbageCollectionExpectation
    resource_type: ResourceType
    external_dependencies: tuple[str, ...]
    failure_behaviour: MemoryFailureBehaviour
    growth_expectation: MemoryGrowthExpectation
    restrictions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.component.strip():
            raise ValueError("component must be non-empty")
        if not self.classifications:
            raise ValueError("at least one memory classification is required")
        if not self.restrictions or not all(item.strip() for item in self.restrictions):
            raise ValueError("at least one non-empty memory restriction is required")
        object.__setattr__(self, "classifications", frozenset(self.classifications))
        object.__setattr__(self, "external_dependencies", tuple(self.external_dependencies))
        object.__setattr__(self, "restrictions", tuple(self.restrictions))


@runtime_checkable
class MemoryAware(Protocol):
    """Protocol for components that expose a native memory contract."""

    @property
    def memory_contract(self) -> MemoryContract:
        """Return the component's immutable memory contract."""


class MemoryRegistry(Mapping[str, MemoryContract]):
    """Immutable registry resolving contracts by name, type, or instance."""

    __slots__ = ("_contracts",)

    def __init__(self, contracts: Iterable[MemoryContract]) -> None:
        items = tuple(contracts)
        mapping = {contract.component: contract for contract in items}
        if len(mapping) != len(items):
            raise ValueError("memory contract component names must be unique")
        self._contracts: Mapping[str, MemoryContract] = MappingProxyType(mapping)

    def __getitem__(self, key: str) -> MemoryContract:
        return self._contracts[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._contracts)

    def __len__(self) -> int:
        return len(self._contracts)

    def resolve(self, component: str | type[object] | object) -> MemoryContract:
        """Resolve a contract using a qualified name, type, or instance."""

        if not isinstance(component, (str, type)) and isinstance(component, MemoryAware):
            return component.memory_contract
        if isinstance(component, str):
            name = component
        else:
            component_type = component if isinstance(component, type) else type(component)
            name = f"{component_type.__module__}.{component_type.__qualname__}"
        try:
            return self._contracts[name]
        except KeyError as error:
            raise LookupError(f"no memory contract declared for {name}") from error

    def declared(self) -> tuple[MemoryContract, ...]:
        """Return contracts in deterministic qualified-name order."""

        return tuple(self._contracts[name] for name in sorted(self._contracts))


def _contract(
    component: str,
    *classifications: MemoryClassification,
    ownership: MemoryOwnership,
    lifecycle: MemoryLifecycle,
    allocation: AllocationPolicy,
    release: ReleasePolicy,
    cache: CachePolicy = CachePolicy.NONE,
    history: HistoryPolicy = HistoryPolicy.NONE,
    visibility: ThreadVisibility,
    mutability: MemoryMutability,
    cleanup: CleanupStrategy,
    gc: GarbageCollectionExpectation,
    resource: ResourceType = ResourceType.MEMORY,
    external: tuple[str, ...] = (),
    failure: MemoryFailureBehaviour = MemoryFailureBehaviour.STATE_PRESERVED,
    growth: MemoryGrowthExpectation,
    restrictions: tuple[str, ...],
) -> MemoryContract:
    return MemoryContract(
        component=component,
        classifications=frozenset(classifications),
        ownership=ownership,
        lifecycle=lifecycle,
        allocation_policy=allocation,
        release_policy=release,
        cache_policy=cache,
        history_policy=history,
        thread_visibility=visibility,
        mutability=mutability,
        cleanup_strategy=cleanup,
        garbage_collection=gc,
        resource_type=resource,
        external_dependencies=external,
        failure_behaviour=failure,
        growth_expectation=growth,
        restrictions=restrictions,
    )


def _stateless(component: str) -> MemoryContract:
    return _contract(
        component,
        MemoryClassification.STATELESS,
        MemoryClassification.EPHEMERAL,
        ownership=MemoryOwnership.CALLER,
        lifecycle=MemoryLifecycle.CALL,
        allocation=AllocationPolicy.CALLER_PROVIDED,
        release=ReleasePolicy.NONE,
        visibility=ThreadVisibility.IMMUTABLE_SHARED,
        mutability=MemoryMutability.IMMUTABLE,
        cleanup=CleanupStrategy.NONE,
        gc=GarbageCollectionExpectation.IMMEDIATE_ELIGIBILITY,
        failure=MemoryFailureBehaviour.NO_RETAINED_STATE,
        growth=MemoryGrowthExpectation.CONSTANT,
        restrictions=("Inputs and returned values remain caller-owned.",),
    )


def _owned(
    component: str, *, lifecycle: MemoryLifecycle = MemoryLifecycle.INSTANCE
) -> MemoryContract:
    return _contract(
        component,
        MemoryClassification.OWNED,
        ownership=MemoryOwnership.COMPONENT,
        lifecycle=lifecycle,
        allocation=AllocationPolicy.LAZY,
        release=ReleasePolicy.GARBAGE_COLLECTED,
        visibility=(
            ThreadVisibility.RUN_CONFINED
            if lifecycle is MemoryLifecycle.RUN
            else ThreadVisibility.SHARED
        ),
        mutability=MemoryMutability.MUTABLE,
        cleanup=CleanupStrategy.GARBAGE_COLLECTION,
        gc=(
            GarbageCollectionExpectation.AFTER_RUN
            if lifecycle is MemoryLifecycle.RUN
            else GarbageCollectionExpectation.AFTER_INSTANCE_RELEASE
        ),
        growth=MemoryGrowthExpectation.INPUT_BOUNDED,
        restrictions=("Release all references to make owned state collectible.",),
    )


def _immutable(component: str) -> MemoryContract:
    return _contract(
        component,
        MemoryClassification.OWNED,
        MemoryClassification.EPHEMERAL,
        ownership=MemoryOwnership.CALLER,
        lifecycle=MemoryLifecycle.INSTANCE,
        allocation=AllocationPolicy.CALLER_PROVIDED,
        release=ReleasePolicy.GARBAGE_COLLECTED,
        visibility=ThreadVisibility.IMMUTABLE_SHARED,
        mutability=MemoryMutability.IMMUTABLE,
        cleanup=CleanupStrategy.GARBAGE_COLLECTION,
        gc=GarbageCollectionExpectation.AFTER_INSTANCE_RELEASE,
        growth=MemoryGrowthExpectation.INPUT_BOUNDED,
        restrictions=("Contained values must satisfy their own ownership contracts.",),
    )


def _history(component: str) -> MemoryContract:
    return _contract(
        component,
        MemoryClassification.OWNED,
        MemoryClassification.PERSISTENT,
        ownership=MemoryOwnership.COMPONENT,
        lifecycle=MemoryLifecycle.INSTANCE,
        allocation=AllocationPolicy.LAZY,
        release=ReleasePolicy.GARBAGE_COLLECTED,
        history=HistoryPolicy.UNBOUNDED,
        visibility=ThreadVisibility.SHARED,
        mutability=MemoryMutability.MUTABLE,
        cleanup=CleanupStrategy.GARBAGE_COLLECTION,
        gc=GarbageCollectionExpectation.AFTER_INSTANCE_RELEASE,
        resource=ResourceType.HISTORY,
        growth=MemoryGrowthExpectation.HISTORY_DEPENDENT,
        restrictions=("Retention follows the public history API and has no implicit pruning.",),
    )


def _external(component: str, resource: ResourceType, dependency: str) -> MemoryContract:
    return _contract(
        component,
        MemoryClassification.RESOURCE_MANAGED,
        MemoryClassification.RESOURCE_EXTERNAL,
        ownership=MemoryOwnership.EXTERNAL_SYSTEM,
        lifecycle=MemoryLifecycle.EXTERNAL,
        allocation=AllocationPolicy.EXTERNAL,
        release=ReleasePolicy.EXTERNAL,
        cache=CachePolicy.EXTERNAL,
        visibility=ThreadVisibility.EXTERNAL,
        mutability=MemoryMutability.EXTERNAL,
        cleanup=CleanupStrategy.EXTERNAL_OWNER,
        gc=GarbageCollectionExpectation.EXTERNAL_LIFETIME,
        resource=resource,
        external=(dependency,),
        failure=MemoryFailureBehaviour.EXTERNAL_SYSTEM_DEFINED,
        growth=MemoryGrowthExpectation.EXTERNAL,
        restrictions=("The external dependency owns resource lifetime and cleanup semantics.",),
    )


_ENGINE_NAMES = (
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
)

_GRAPH_NAMES = (
    "epip.market_structure.graph.StructureGraph",
    "epip.liquidity.graph.LiquidityGraph",
    "epip.fibonacci.graph.FibonacciGraph",
    "epip.context.graph.MarketContextGraph",
    "epip.elliott.graph.WaveGraph",
    "epip.decision.graph.DecisionGraph",
    "epip.risk.graph.RiskGraph",
    "epip.execution.graph.ExecutionGraph",
    "epip.portfolio.graph.PortfolioGraph",
)

_HISTORY_NAMES = (
    "epip.market_structure.history.StructureHistory",
    "epip.liquidity.history.LiquidityHistory",
    "epip.fibonacci.history.FibonacciHistory",
    "epip.context.history.MarketContextHistory",
    "epip.elliott.history.WaveHistory",
    "epip.decision.history.DecisionHistory",
    "epip.risk.history.RiskHistory",
    "epip.execution.history.ExecutionHistory",
    "epip.portfolio.history.PortfolioHistory",
)

_STATISTICS_NAMES = (
    "epip.swing.statistics.SwingStatistics",
    "epip.swing.statistics.SwingStatisticsCollector",
    "epip.market_structure.models.StructureStatistics",
    "epip.market_structure.statistics.MarketStructureStatistics",
    "epip.liquidity.statistics.LiquidityStatistics",
    "epip.fibonacci.statistics.FibonacciStatistics",
    "epip.context.statistics.MarketContextStatistics",
    "epip.elliott.statistics.ElliottStatistics",
    "epip.decision.statistics.DecisionStatistics",
    "epip.risk.statistics.RiskStatistics",
    "epip.execution.models.ExecutionStatistics",
    "epip.execution.statistics.StatisticsCollector",
    "epip.portfolio.statistics.PortfolioStatistics",
    "epip.replay.replay_statistics.ReplayStatisticsCheckpoint",
    "epip.replay.replay_statistics.ReplayStatistics",
)

_CONTEXT_NAMES = (
    "epip.core.context.MarketContext",
    "epip.core.plugin_context.PluginContext",
    "epip.core.plugin_result.PluginResult",
    "epip.context.snapshot.TrendContext",
    "epip.context.snapshot.BiasContext",
    "epip.context.snapshot.ConfluenceContext",
    "epip.context.snapshot.MarketContext",
    "epip.context.snapshot.MarketContextSnapshot",
)

_CONTRACT_ITEMS = (
    _owned("epip.core.kernel.Kernel"),
    _owned("epip.core.registry.Registry"),
    _history("epip.core.event_bus.EventBus"),
    _owned("epip.features.feature_store.FeatureStore"),
    _contract(
        "epip.marketdata.datasource_cache.DataSourceCache",
        MemoryClassification.OWNED,
        MemoryClassification.SHARED,
        MemoryClassification.CACHED,
        ownership=MemoryOwnership.COMPONENT,
        lifecycle=MemoryLifecycle.INSTANCE,
        allocation=AllocationPolicy.LAZY,
        release=ReleasePolicy.GARBAGE_COLLECTED,
        cache=CachePolicy.UNBOUNDED,
        visibility=ThreadVisibility.SHARED,
        mutability=MemoryMutability.SYNCHRONIZED,
        cleanup=CleanupStrategy.GARBAGE_COLLECTION,
        gc=GarbageCollectionExpectation.AFTER_INSTANCE_RELEASE,
        resource=ResourceType.CACHE,
        growth=MemoryGrowthExpectation.CACHE_DEPENDENT,
        restrictions=("Cached entries are retained for the lifetime of the cache instance.",),
    ),
    _owned("epip.replay.replay_engine.ReplayEngine", lifecycle=MemoryLifecycle.RUN),
    _owned("epip.replay.replay_session.ReplaySession", lifecycle=MemoryLifecycle.RUN),
    _owned("epip.replay.replay_clock.ReplayClock", lifecycle=MemoryLifecycle.RUN),
    _owned("epip.replay.replay_scheduler.ReplayScheduler", lifecycle=MemoryLifecycle.RUN),
    _owned("epip.replay.replay_iterator.ReplayIterator", lifecycle=MemoryLifecycle.RUN),
    _owned("epip.replay.replay_controller.ReplayController", lifecycle=MemoryLifecycle.RUN),
    _stateless("epip.features.providers.base_provider.BaseFeatureProvider"),
    _stateless("epip.features.providers.indicator_provider.IndicatorProvider"),
    _stateless("epip.features.providers.ohlc_provider.OHLCProvider"),
    _stateless("epip.features.providers.session_provider.SessionProvider"),
    _stateless("epip.features.providers.structure_provider.StructureProvider"),
    _external(
        "epip.marketdata.providers.base_provider.BaseProvider",
        ResourceType.NETWORK,
        "provider implementation",
    ),
    _external(
        "epip.marketdata.providers.csv_provider.CSVProvider", ResourceType.FILE, "filesystem"
    ),
    _stateless("epip.marketdata.providers.fake_provider.FakeProvider"),
    _external(
        "epip.marketdata.providers.mt5_provider.MT5Provider", ResourceType.BROKER, "MetaTrader 5"
    ),
    _external(
        "epip.marketdata.providers.twelvedata_provider.TwelveDataProvider",
        ResourceType.NETWORK,
        "Twelve Data",
    ),
    _external("epip.execution.mt5_adapter.MT5Adapter", ResourceType.BROKER, "MetaTrader 5"),
    _owned("epip.execution.paper_adapter.PaperTradingAdapter"),
    _stateless("epip.marketdata.adapters.mt5_adapter.NullMT5Adapter"),
    _stateless("epip.marketdata.adapters.twelvedata_adapter.NullTwelveDataAdapter"),
    _stateless("epip.core.identity.SystemClock"),
    _owned("epip.core.identity.DeterministicClock"),
    _stateless("epip.core.identity.SystemIdGenerator"),
    _owned("epip.core.identity.DeterministicIdGenerator"),
    *(_owned(name) for name in _ENGINE_NAMES),
    *(_immutable(name) for name in _GRAPH_NAMES),
    *(_history(name) for name in _HISTORY_NAMES),
    *(_owned(name) for name in _STATISTICS_NAMES),
    *(_immutable(name) for name in _CONTEXT_NAMES),
)


MEMORY_CONTRACTS = MemoryRegistry(_CONTRACT_ITEMS)


def get_memory_contract(component: str | type[object] | object) -> MemoryContract:
    """Resolve the official contract for a qualified name, type, or instance."""

    return MEMORY_CONTRACTS.resolve(component)


def declared_memory_contracts() -> tuple[MemoryContract, ...]:
    """Return all contracts in deterministic qualified-name order."""

    return MEMORY_CONTRACTS.declared()


__all__ = [
    "MEMORY_CONTRACTS",
    "AllocationPolicy",
    "CachePolicy",
    "CleanupStrategy",
    "GarbageCollectionExpectation",
    "HistoryPolicy",
    "MemoryAware",
    "MemoryClassification",
    "MemoryContract",
    "MemoryFailureBehaviour",
    "MemoryGrowthExpectation",
    "MemoryLifecycle",
    "MemoryMutability",
    "MemoryOwnership",
    "MemoryRegistry",
    "ReleasePolicy",
    "ResourceType",
    "ThreadVisibility",
    "declared_memory_contracts",
    "get_memory_contract",
]
