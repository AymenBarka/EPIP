from __future__ import annotations

from dataclasses import FrozenInstanceError
from importlib import import_module

import pytest

from epip.core.reliability import (
    RELIABILITY_CONTRACTS,
    FailureBoundary,
    FailureCategory,
    FailureContract,
    FailurePolicy,
    FailureResponsibility,
    FailureSeverity,
    RecoveryExpectation,
    ReliabilityContract,
    ReliabilityRegistry,
    declared_reliability_contracts,
    get_reliability_contract,
)

REQUIRED_COMPONENTS = {
    "epip.core.kernel.Kernel",
    "epip.core.registry.Registry",
    "epip.core.event_bus.EventBus",
    "epip.replay.replay_engine.ReplayEngine",
    "epip.replay.replay_session.ReplaySession",
    "epip.replay.replay_scheduler.ReplayScheduler",
    "epip.replay.replay_clock.ReplayClock",
    "epip.features.feature_store.FeatureStore",
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
    "epip.core.plugin_context.PluginContext",
    "epip.core.plugin_result.PluginResult",
    "epip.core.plugin_protocol.PluginProtocol",
    "epip.core.external_effects.ExternalEffectContract",
}


def _load_type(qualified_name: str) -> type[object]:
    module_name, class_name = qualified_name.rsplit(".", 1)
    value = getattr(import_module(module_name), class_name)
    assert isinstance(value, type)
    return value


def _sample_failure(**overrides: object) -> FailureContract:
    values: dict[str, object] = {
        "category": FailureCategory.DATA_ERROR,
        "severity": FailureSeverity.ERROR,
        "policy": FailurePolicy.PROPAGATE,
        "boundary": FailureBoundary.CALL,
        "recovery": RecoveryExpectation.CALLER_CORRECTION,
        "responsibility": FailureResponsibility.CALLER,
        "description": "Caller corrects invalid data.",
    }
    values.update(overrides)
    return FailureContract(**values)  # type: ignore[arg-type]


def test_required_components_have_resolvable_contracts() -> None:
    assert REQUIRED_COMPONENTS <= RELIABILITY_CONTRACTS.keys()
    for name in REQUIRED_COMPONENTS:
        assert get_reliability_contract(name).component == name
        assert get_reliability_contract(_load_type(name)).component == name


def test_registry_is_immutable_and_deterministic() -> None:
    declared = declared_reliability_contracts()
    assert tuple(item.component for item in declared) == tuple(sorted(RELIABILITY_CONTRACTS))
    assert len(declared) == len(RELIABILITY_CONTRACTS)
    with pytest.raises(TypeError):
        RELIABILITY_CONTRACTS["invalid"] = declared[0]  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        declared[0].component = "changed"  # type: ignore[misc]


def test_contracts_are_complete_and_machine_readable() -> None:
    observed_categories: set[FailureCategory] = set()
    observed_policies: set[FailurePolicy] = set()
    observed_responsibilities: set[FailureResponsibility] = set()
    for contract in declared_reliability_contracts():
        assert contract.availability_guarantee.strip()
        assert contract.restrictions
        categories = [failure.category for failure in contract.failures]
        assert len(categories) == len(set(categories))
        for failure in contract.failures:
            observed_categories.add(failure.category)
            observed_policies.add(failure.policy)
            observed_responsibilities.add(failure.responsibility)
            assert failure.description.strip()
    assert set(FailureCategory) <= observed_categories
    assert FailurePolicy.FAIL_FAST in observed_policies
    assert FailurePolicy.RETRY_ALLOWED in observed_policies
    assert FailureResponsibility.FRAMEWORK in observed_responsibilities
    assert FailureResponsibility.EXTERNAL_SYSTEM in observed_responsibilities


def test_unknown_duplicate_and_incomplete_contracts_are_rejected() -> None:
    with pytest.raises(LookupError, match="no reliability contract"):
        get_reliability_contract("epip.unknown.Component")
    with pytest.raises(ValueError, match="component"):
        ReliabilityContract("", (_sample_failure(),), "available", ("restricted",))
    with pytest.raises(ValueError, match="failure contract"):
        ReliabilityContract("epip.Empty", (), "available", ("restricted",))
    with pytest.raises(ValueError, match="unique"):
        ReliabilityContract(
            "epip.Duplicate",
            (_sample_failure(), _sample_failure()),
            "available",
            ("restricted",),
        )
    with pytest.raises(ValueError, match="availability"):
        ReliabilityContract("epip.Empty", (_sample_failure(),), "", ("restricted",))
    with pytest.raises(ValueError, match="restriction"):
        ReliabilityContract("epip.Empty", (_sample_failure(),), "available", ())


def test_contradictory_failure_contracts_are_rejected() -> None:
    with pytest.raises(ValueError, match="retry-allowed"):
        _sample_failure(policy=FailurePolicy.RETRY_ALLOWED)
    with pytest.raises(ValueError, match="retry-forbidden"):
        _sample_failure(
            policy=FailurePolicy.RETRY_FORBIDDEN,
            recovery=RecoveryExpectation.RETRY,
        )
    with pytest.raises(ValueError, match="critical"):
        _sample_failure(policy=FailurePolicy.IGNORE, severity=FailureSeverity.CRITICAL)
    with pytest.raises(ValueError, match="description"):
        _sample_failure(description="")
    with pytest.raises(TypeError, match="category"):
        _sample_failure(category="invalid")
    with pytest.raises(TypeError, match="policy"):
        _sample_failure(policy="invalid")
    with pytest.raises(TypeError, match="responsibility"):
        _sample_failure(responsibility="ambiguous")


def test_registry_rejects_duplicates_and_reports_missing_components() -> None:
    contract = ReliabilityContract(
        "epip.Sample",
        (_sample_failure(),),
        "Available after caller correction.",
        ("No implicit retries.",),
    )
    with pytest.raises(ValueError, match="unique"):
        ReliabilityRegistry((contract, contract))
    registry = ReliabilityRegistry((contract,))
    assert registry.audit(("epip.Sample",)) == ()
    assert registry.audit(("epip.Sample", "epip.Missing")) == (
        "missing reliability contract: epip.Missing",
    )


def test_protocol_resolution_uses_native_contract() -> None:
    contract = ReliabilityContract(
        "custom.Component",
        (_sample_failure(),),
        "Available after caller correction.",
        ("No implicit retries.",),
    )

    class Aware:
        @property
        def reliability_contract(self) -> ReliabilityContract:
            return contract

    assert get_reliability_contract(Aware()) is contract
