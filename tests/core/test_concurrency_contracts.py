from __future__ import annotations

from importlib import import_module

import pytest

from epip.core.concurrency import (
    CONCURRENCY_CONTRACTS,
    ConcurrencyCapability,
    ThreadExecutionScope,
    ThreadOwnership,
    ThreadSafetyContract,
    ThreadSafetyLevel,
    concurrency_contract_for,
    declared_concurrency_contracts,
)

REQUIRED_COMPONENTS = {
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
    "epip.features.providers.base_provider.BaseFeatureProvider",
    "epip.features.providers.indicator_provider.IndicatorProvider",
    "epip.features.providers.ohlc_provider.OHLCProvider",
    "epip.features.providers.session_provider.SessionProvider",
    "epip.features.providers.structure_provider.StructureProvider",
    "epip.marketdata.datasource_cache.DataSourceCache",
    "epip.marketdata.providers.base_provider.BaseProvider",
    "epip.marketdata.providers.csv_provider.CSVProvider",
    "epip.marketdata.providers.fake_provider.FakeProvider",
    "epip.marketdata.providers.mt5_provider.MT5Provider",
    "epip.marketdata.providers.twelvedata_provider.TwelveDataProvider",
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
    "epip.execution.mt5_adapter.MT5Adapter",
    "epip.marketdata.adapters.mt5_adapter.NullMT5Adapter",
    "epip.marketdata.adapters.twelvedata_adapter.NullTwelveDataAdapter",
    "epip.core.plugin_context.PluginContext",
    "epip.core.plugin_result.PluginResult",
    "epip.core.identity.SystemClock",
    "epip.core.identity.DeterministicClock",
    "epip.core.identity.SystemIdGenerator",
    "epip.core.identity.DeterministicIdGenerator",
}


def _load_type(qualified_name: str) -> type[object]:
    module_name, class_name = qualified_name.rsplit(".", 1)
    value = getattr(import_module(module_name), class_name)
    assert isinstance(value, type)
    return value


def test_every_required_public_component_has_a_contract() -> None:
    assert REQUIRED_COMPONENTS <= CONCURRENCY_CONTRACTS.keys()
    for name in REQUIRED_COMPONENTS:
        component_type = _load_type(name)
        assert concurrency_contract_for(component_type).component == name


def test_every_engine_provider_and_adapter_has_a_contract() -> None:
    classified_names = set(CONCURRENCY_CONTRACTS)
    for name in REQUIRED_COMPONENTS:
        if name.endswith(("Engine", "Provider", "Adapter")):
            assert name in classified_names


def test_statistics_histories_and_graphs_are_fully_classified() -> None:
    names = set(CONCURRENCY_CONTRACTS)
    statistics = {name for name in names if ".statistics." in name}
    statistics.add("epip.replay.replay_statistics.ReplayStatistics")
    assert statistics <= names
    assert len(statistics) == 11
    assert len([name for name in names if ".history." in name]) == 9
    assert len([name for name in names if ".graph." in name]) == 9


def test_contracts_are_complete_and_valid() -> None:
    contracts = declared_concurrency_contracts()
    assert len(contracts) == len(CONCURRENCY_CONTRACTS)
    assert tuple(item.component for item in contracts) == tuple(sorted(CONCURRENCY_CONTRACTS))
    for contract in contracts:
        assert isinstance(contract.level, ThreadSafetyLevel)
        assert isinstance(contract.ownership, ThreadOwnership)
        assert isinstance(contract.execution_scope, ThreadExecutionScope)
        assert contract.restrictions
        assert all(item.strip() for item in contract.restrictions)
        assert all(isinstance(item, ConcurrencyCapability) for item in contract.capabilities)


def test_immutable_components_have_coherent_contracts() -> None:
    for contract in declared_concurrency_contracts():
        if ConcurrencyCapability.IMMUTABLE in contract.capabilities:
            assert contract.level is ThreadSafetyLevel.THREAD_SAFE
            assert contract.ownership is ThreadOwnership.SHARED
            assert contract.execution_scope is ThreadExecutionScope.SHARED_INSTANCE
            assert contract.reentrant is True


def test_unknown_and_incomplete_contracts_are_rejected() -> None:
    with pytest.raises(LookupError, match="no concurrency contract"):
        concurrency_contract_for("epip.unknown.Component")
    with pytest.raises(ValueError, match="component"):
        ThreadSafetyContract(
            component="",
            level=ThreadSafetyLevel.NOT_THREAD_SAFE,
            ownership=ThreadOwnership.CALLER,
            execution_scope=ThreadExecutionScope.PER_RUN,
            capabilities=frozenset(),
            reentrant=False,
            deterministic_under_concurrency=False,
            restrictions=("restricted",),
        )
    with pytest.raises(ValueError, match="restriction"):
        ThreadSafetyContract(
            component="epip.example.Component",
            level=ThreadSafetyLevel.NOT_THREAD_SAFE,
            ownership=ThreadOwnership.CALLER,
            execution_scope=ThreadExecutionScope.PER_RUN,
            capabilities=frozenset(),
            reentrant=False,
            deterministic_under_concurrency=False,
            restrictions=(),
        )
