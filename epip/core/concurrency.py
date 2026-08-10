"""Official concurrency contracts for public EPIP components.

The registry in this module is descriptive only: it documents the guarantees
implemented today and does not add synchronization or change runtime behavior.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable


class ThreadSafetyLevel(str, Enum):
    """Supported thread-safety classifications."""

    THREAD_SAFE = "thread_safe"
    THREAD_COMPATIBLE = "thread_compatible"
    THREAD_CONFINED = "thread_confined"
    NOT_THREAD_SAFE = "not_thread_safe"


class ThreadOwnership(str, Enum):
    """Owner responsible for coordinating a component instance."""

    SHARED = "shared"
    CALLER = "caller"
    THREAD = "thread"
    RUN = "run"
    EXTERNAL_SYSTEM = "external_system"


class ThreadExecutionScope(str, Enum):
    """Execution scope in which the documented guarantee applies."""

    SHARED_INSTANCE = "shared_instance"
    SERIALIZED_INSTANCE = "serialized_instance"
    PER_THREAD = "per_thread"
    PER_RUN = "per_run"
    EXTERNAL_ADAPTER = "external_adapter"


class ConcurrencyCapability(str, Enum):
    """Capabilities relevant to concurrent framework execution."""

    CONCURRENT_READS = "concurrent_reads"
    SERIALIZED_WRITES = "serialized_writes"
    IMMUTABLE = "immutable"
    REENTRANT = "reentrant"
    DETERMINISTIC_SEQUENTIAL_ORDER = "deterministic_sequential_order"
    EXTERNAL_SYNCHRONIZATION_REQUIRED = "external_synchronization_required"


@dataclass(frozen=True, slots=True)
class ThreadSafetyContract:
    """Immutable declaration of one component's concurrency guarantees."""

    component: str
    level: ThreadSafetyLevel
    ownership: ThreadOwnership
    execution_scope: ThreadExecutionScope
    capabilities: frozenset[ConcurrencyCapability]
    reentrant: bool
    deterministic_under_concurrency: bool
    restrictions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.component.strip():
            raise ValueError("component must be non-empty")
        if not self.restrictions:
            raise ValueError("at least one concurrency restriction is required")
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "restrictions", tuple(self.restrictions))


@runtime_checkable
class ConcurrencyAware(Protocol):
    """Protocol for components that declare a native concurrency contract."""

    @property
    def concurrency_contract(self) -> ThreadSafetyContract:
        """Return the component's immutable concurrency contract."""


def _contract(
    component: str,
    level: ThreadSafetyLevel,
    ownership: ThreadOwnership,
    scope: ThreadExecutionScope,
    *capabilities: ConcurrencyCapability,
    reentrant: bool = False,
    deterministic: bool = False,
    restrictions: tuple[str, ...],
) -> ThreadSafetyContract:
    return ThreadSafetyContract(
        component=component,
        level=level,
        ownership=ownership,
        execution_scope=scope,
        capabilities=frozenset(capabilities),
        reentrant=reentrant,
        deterministic_under_concurrency=deterministic,
        restrictions=restrictions,
    )


_SAFE_STATE = (
    ConcurrencyCapability.CONCURRENT_READS,
    ConcurrencyCapability.SERIALIZED_WRITES,
)
_IMMUTABLE = (ConcurrencyCapability.CONCURRENT_READS, ConcurrencyCapability.IMMUTABLE)
_CONFINED = (ConcurrencyCapability.EXTERNAL_SYNCHRONIZATION_REQUIRED,)


def _safe(component: str, restriction: str, *, deterministic: bool = False) -> ThreadSafetyContract:
    return _contract(
        component,
        ThreadSafetyLevel.THREAD_SAFE,
        ThreadOwnership.SHARED,
        ThreadExecutionScope.SHARED_INSTANCE,
        *_SAFE_STATE,
        reentrant=True,
        deterministic=deterministic,
        restrictions=(restriction,),
    )


def _immutable(component: str) -> ThreadSafetyContract:
    return _contract(
        component,
        ThreadSafetyLevel.THREAD_SAFE,
        ThreadOwnership.SHARED,
        ThreadExecutionScope.SHARED_INSTANCE,
        *_IMMUTABLE,
        reentrant=True,
        deterministic=True,
        restrictions=("Contained values must satisfy their own immutability contracts.",),
    )


def _serialized(component: str, restriction: str) -> ThreadSafetyContract:
    return _contract(
        component,
        ThreadSafetyLevel.THREAD_COMPATIBLE,
        ThreadOwnership.CALLER,
        ThreadExecutionScope.SERIALIZED_INSTANCE,
        ConcurrencyCapability.CONCURRENT_READS,
        ConcurrencyCapability.SERIALIZED_WRITES,
        restrictions=(restriction,),
    )


def _confined(component: str, restriction: str) -> ThreadSafetyContract:
    return _contract(
        component,
        ThreadSafetyLevel.THREAD_CONFINED,
        ThreadOwnership.THREAD,
        ThreadExecutionScope.PER_THREAD,
        *_CONFINED,
        restrictions=(restriction,),
    )


_CONTRACT_ITEMS = (
    _serialized(
        "epip.core.kernel.Kernel",
        "Only one run may be active per Kernel; concurrent or recursive entry fails fast.",
    ),
    _safe(
        "epip.core.registry.Registry",
        "Registry structure is protected; registered plugin instances keep their own contracts.",
        deterministic=True,
    ),
    _safe(
        "epip.core.event_bus.EventBus",
        "Callbacks are lock-free and FIFO; recursive publication is bounded per dispatch cycle.",
    ),
    _confined(
        "epip.replay.replay_engine.ReplayEngine",
        "Replay runs must not share an engine or its dependencies across threads.",
    ),
    _confined(
        "epip.replay.replay_session.ReplaySession",
        "Replay windows are owned by one replay run and must remain thread-confined.",
    ),
    _safe(
        "epip.replay.replay_scheduler.ReplayScheduler",
        "Operations are serialized, including calls into replay iterators and providers.",
        deterministic=True,
    ),
    _safe(
        "epip.replay.replay_clock.ReplayClock",
        "Individual operations are atomic; compound state transitions require caller coordination.",
    ),
    _serialized(
        "epip.replay.replay_controller.ReplayController",
        "Lifecycle operations span multiple independently locked replay objects.",
    ),
    _safe(
        "epip.replay.replay_iterator.ReplayIterator",
        "Iterator state is serialized, including calls to the owned market-data provider.",
    ),
    _serialized(
        "epip.features.feature_store.FeatureStore",
        "A global instance lock serializes provider execution and cache mutation.",
    ),
    _safe(
        "epip.marketdata.datasource_cache.DataSourceCache",
        "Cache state is protected; identical misses are not coalesced into a single request.",
    ),
    _safe(
        "epip.features.providers.base_provider.BaseFeatureProvider",
        "Concrete implementations must remain stateless or declare a stronger restriction.",
        deterministic=True,
    ),
    _safe(
        "epip.features.providers.ohlc_provider.OHLCProvider",
        "The provider is stateless; input payloads remain caller-owned.",
        deterministic=True,
    ),
    _safe(
        "epip.features.providers.indicator_provider.IndicatorProvider",
        "The placeholder provider is stateless.",
        deterministic=True,
    ),
    _safe(
        "epip.features.providers.session_provider.SessionProvider",
        "The provider is stateless; input payloads remain caller-owned.",
        deterministic=True,
    ),
    _safe(
        "epip.features.providers.structure_provider.StructureProvider",
        "The placeholder provider is stateless.",
        deterministic=True,
    ),
    _confined(
        "epip.marketdata.providers.base_provider.BaseProvider",
        "Connection lifecycle and reads are not one atomic operation.",
    ),
    _confined(
        "epip.marketdata.providers.csv_provider.CSVProvider",
        "Do not connect or disconnect while reads are in progress.",
    ),
    _confined(
        "epip.marketdata.providers.fake_provider.FakeProvider",
        "Concurrent reads require a stable connected lifecycle.",
    ),
    _confined(
        "epip.marketdata.providers.mt5_provider.MT5Provider",
        "The external MT5 adapter has no framework thread-safety guarantee.",
    ),
    _confined(
        "epip.marketdata.providers.twelvedata_provider.TwelveDataProvider",
        "The external client lifecycle has no framework thread-safety guarantee.",
    ),
    _serialized(
        "epip.swing.engine.SwingEngine",
        "State mutation is serialized; event callbacks run after state-lock release.",
    ),
    _serialized(
        "epip.market_structure.engine.MarketStructureEngine",
        "State mutation is serialized; event callbacks run after state-lock release.",
    ),
    _serialized(
        "epip.liquidity.engine.LiquidityEngine",
        "State mutation is serialized; event callbacks run after state-lock release.",
    ),
    _serialized(
        "epip.fibonacci.engine.FibonacciEngine",
        "State mutation is serialized; event callbacks run after state-lock release.",
    ),
    _serialized(
        "epip.context.engine.MarketContextEngine",
        "State mutation is serialized; event callbacks run after state-lock release.",
    ),
    _serialized(
        "epip.elliott.engine.ElliottWaveEngine",
        "State mutation is serialized; event callbacks run after state-lock release.",
    ),
    _serialized(
        "epip.decision.engine.DecisionEngine",
        "State mutation is serialized; event callbacks run after state-lock release.",
    ),
    _serialized(
        "epip.risk.engine.RiskEngine",
        "State mutation is serialized; event callbacks run after state-lock release.",
    ),
    _serialized(
        "epip.execution.engine.ExecutionEngine",
        "Broker calls remain serialized; event callbacks run after state-lock release.",
    ),
    _serialized(
        "epip.portfolio.engine.PortfolioEngine",
        "Use one serialized producer; callbacks run after commit and may start a later update.",
    ),
    _safe(
        "epip.execution.paper_adapter.PaperTradingAdapter",
        "Calls are serialized; cross-thread completion order follows lock acquisition order.",
    ),
    _safe(
        "epip.execution.mt5_adapter.MT5Adapter",
        "The dependency-free stub is stateless; a real adapter requires its own contract.",
        deterministic=True,
    ),
    _safe(
        "epip.marketdata.adapters.mt5_adapter.NullMT5Adapter",
        "The architecture-only null adapter is stateless.",
        deterministic=True,
    ),
    _safe(
        "epip.marketdata.adapters.twelvedata_adapter.NullTwelveDataAdapter",
        "The architecture-only null adapter is stateless.",
        deterministic=True,
    ),
    _immutable("epip.core.plugin_context.PluginContext"),
    _immutable("epip.core.plugin_result.PluginResult"),
    _safe(
        "epip.core.identity.SystemClock",
        "Timestamps follow the system clock and are not reproducible.",
    ),
    _safe(
        "epip.core.identity.DeterministicClock",
        "Concurrent mutation order follows lock acquisition order.",
        deterministic=True,
    ),
    _safe("epip.core.identity.SystemIdGenerator", "Generated identities are intentionally random."),
    _safe(
        "epip.core.identity.DeterministicIdGenerator",
        "Values are unique, but concurrent assignment order follows lock acquisition order.",
    ),
)

_STATISTICS = (
    "epip.swing.statistics.SwingStatisticsCollector",
    "epip.market_structure.statistics.MarketStructureStatistics",
    "epip.liquidity.statistics.LiquidityStatistics",
    "epip.fibonacci.statistics.FibonacciStatistics",
    "epip.context.statistics.MarketContextStatistics",
    "epip.elliott.statistics.ElliottStatistics",
    "epip.decision.statistics.DecisionStatistics",
    "epip.risk.statistics.RiskStatistics",
    "epip.execution.statistics.StatisticsCollector",
    "epip.portfolio.statistics.PortfolioStatistics",
    "epip.replay.replay_statistics.ReplayStatistics",
)

_HISTORIES = (
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

_GRAPHS = (
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

_ALL_CONTRACTS = (
    *_CONTRACT_ITEMS,
    *(
        _safe(name, "Collector mutations are serialized; snapshots are immutable.")
        for name in _STATISTICS
    ),
    *(_immutable(name) for name in _HISTORIES),
    *(_immutable(name) for name in _GRAPHS),
)

CONCURRENCY_CONTRACTS: Mapping[str, ThreadSafetyContract] = MappingProxyType(
    {contract.component: contract for contract in _ALL_CONTRACTS}
)


def concurrency_contract_for(component: object | type[object] | str) -> ThreadSafetyContract:
    """Resolve the official contract for an instance, type, or qualified name."""

    if not isinstance(component, (str, type)) and isinstance(component, ConcurrencyAware):
        return component.concurrency_contract
    if isinstance(component, str):
        name = component
    else:
        component_type = component if isinstance(component, type) else type(component)
        name = f"{component_type.__module__}.{component_type.__qualname__}"
    try:
        return CONCURRENCY_CONTRACTS[name]
    except KeyError as exc:
        raise LookupError(f"no concurrency contract declared for {name}") from exc


def declared_concurrency_contracts() -> tuple[ThreadSafetyContract, ...]:
    """Return all official contracts in stable component-name order."""

    return tuple(CONCURRENCY_CONTRACTS[name] for name in sorted(CONCURRENCY_CONTRACTS))


__all__ = [
    "CONCURRENCY_CONTRACTS",
    "ConcurrencyAware",
    "ConcurrencyCapability",
    "ThreadExecutionScope",
    "ThreadOwnership",
    "ThreadSafetyContract",
    "ThreadSafetyLevel",
    "concurrency_contract_for",
    "declared_concurrency_contracts",
]
