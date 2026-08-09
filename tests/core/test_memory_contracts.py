from __future__ import annotations

from dataclasses import FrozenInstanceError
from importlib import import_module

import pytest

from epip.core.memory import (
    MEMORY_CONTRACTS,
    AllocationPolicy,
    CachePolicy,
    CleanupStrategy,
    GarbageCollectionExpectation,
    HistoryPolicy,
    MemoryClassification,
    MemoryContract,
    MemoryFailureBehaviour,
    MemoryGrowthExpectation,
    MemoryLifecycle,
    MemoryMutability,
    MemoryOwnership,
    MemoryRegistry,
    ReleasePolicy,
    ResourceType,
    ThreadVisibility,
    declared_memory_contracts,
    get_memory_contract,
)


def _load_type(qualified_name: str) -> type[object]:
    module_name, class_name = qualified_name.rsplit(".", 1)
    value = getattr(import_module(module_name), class_name)
    assert isinstance(value, type)
    return value


def test_every_registered_component_is_importable_and_resolvable_by_type() -> None:
    for name in MEMORY_CONTRACTS:
        component_type = _load_type(name)
        assert get_memory_contract(component_type) is MEMORY_CONTRACTS[name]


def test_required_component_families_are_fully_classified() -> None:
    names = set(MEMORY_CONTRACTS)
    assert {
        "epip.core.kernel.Kernel",
        "epip.core.registry.Registry",
        "epip.core.event_bus.EventBus",
        "epip.features.feature_store.FeatureStore",
        "epip.marketdata.datasource_cache.DataSourceCache",
        "epip.replay.replay_engine.ReplayEngine",
        "epip.replay.replay_session.ReplaySession",
        "epip.replay.replay_clock.ReplayClock",
        "epip.replay.replay_scheduler.ReplayScheduler",
        "epip.replay.replay_iterator.ReplayIterator",
        "epip.replay.replay_statistics.ReplayStatistics",
        "epip.core.identity.SystemClock",
        "epip.core.identity.DeterministicClock",
        "epip.core.identity.SystemIdGenerator",
        "epip.core.identity.DeterministicIdGenerator",
    } <= names
    assert len([name for name in names if name.endswith("Engine")]) == 11
    assert len([name for name in names if name.endswith("Provider")]) == 10
    assert len([name for name in names if name.endswith("Adapter")]) == 4
    assert len([name for name in names if ".history." in name]) == 9
    assert len([name for name in names if ".graph." in name]) == 9
    assert len([name for name in names if "Statistics" in name]) == 15
    assert len([name for name in names if "Context" in name]) >= 9


def test_contracts_are_complete_machine_readable_and_deterministic() -> None:
    contracts = declared_memory_contracts()
    assert len(contracts) == len(MEMORY_CONTRACTS)
    assert tuple(contract.component for contract in contracts) == tuple(sorted(MEMORY_CONTRACTS))
    for contract in contracts:
        assert contract.classifications
        assert all(isinstance(item, MemoryClassification) for item in contract.classifications)
        assert isinstance(contract.ownership, MemoryOwnership)
        assert isinstance(contract.lifecycle, MemoryLifecycle)
        assert isinstance(contract.allocation_policy, AllocationPolicy)
        assert isinstance(contract.release_policy, ReleasePolicy)
        assert isinstance(contract.cache_policy, CachePolicy)
        assert isinstance(contract.history_policy, HistoryPolicy)
        assert isinstance(contract.thread_visibility, ThreadVisibility)
        assert isinstance(contract.mutability, MemoryMutability)
        assert isinstance(contract.cleanup_strategy, CleanupStrategy)
        assert isinstance(contract.garbage_collection, GarbageCollectionExpectation)
        assert isinstance(contract.resource_type, ResourceType)
        assert isinstance(contract.failure_behaviour, MemoryFailureBehaviour)
        assert isinstance(contract.growth_expectation, MemoryGrowthExpectation)
        assert contract.restrictions


def test_registry_and_contracts_are_immutable() -> None:
    contract = declared_memory_contracts()[0]
    with pytest.raises(FrozenInstanceError):
        contract.component = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        MEMORY_CONTRACTS[contract.component] = contract  # type: ignore[index]


def test_resolution_by_name_type_instance_and_memory_aware_protocol() -> None:
    name = "epip.core.kernel.Kernel"
    kernel_type = _load_type(name)
    kernel = kernel_type()
    assert get_memory_contract(name) is MEMORY_CONTRACTS[name]
    assert get_memory_contract(kernel_type) is MEMORY_CONTRACTS[name]
    assert get_memory_contract(kernel) is MEMORY_CONTRACTS[name]

    class NativeMemoryAware:
        @property
        def memory_contract(self) -> MemoryContract:
            return MEMORY_CONTRACTS[name]

    assert get_memory_contract(NativeMemoryAware()) is MEMORY_CONTRACTS[name]


def test_unknown_incomplete_and_duplicate_contracts_are_rejected() -> None:
    with pytest.raises(LookupError, match="no memory contract"):
        get_memory_contract("epip.unknown.Component")
    contract = declared_memory_contracts()[0]
    with pytest.raises(ValueError, match="unique"):
        MemoryRegistry((contract, contract))
    with pytest.raises(ValueError, match="component"):
        MemoryContract(
            component="",
            classifications=frozenset({MemoryClassification.STATELESS}),
            ownership=MemoryOwnership.CALLER,
            lifecycle=MemoryLifecycle.CALL,
            allocation_policy=AllocationPolicy.NONE,
            release_policy=ReleasePolicy.NONE,
            cache_policy=CachePolicy.NONE,
            history_policy=HistoryPolicy.NONE,
            thread_visibility=ThreadVisibility.THREAD_CONFINED,
            mutability=MemoryMutability.IMMUTABLE,
            cleanup_strategy=CleanupStrategy.NONE,
            garbage_collection=GarbageCollectionExpectation.IMMEDIATE_ELIGIBILITY,
            resource_type=ResourceType.MEMORY,
            external_dependencies=(),
            failure_behaviour=MemoryFailureBehaviour.NO_RETAINED_STATE,
            growth_expectation=MemoryGrowthExpectation.CONSTANT,
            restrictions=("restricted",),
        )


def test_classification_policies_are_coherent() -> None:
    for contract in declared_memory_contracts():
        if MemoryClassification.STATELESS in contract.classifications:
            assert contract.growth_expectation is MemoryGrowthExpectation.CONSTANT
            assert contract.history_policy is HistoryPolicy.NONE
            assert contract.cache_policy is CachePolicy.NONE
        if MemoryClassification.CACHED in contract.classifications:
            assert contract.resource_type is ResourceType.CACHE
            assert contract.cache_policy is not CachePolicy.NONE
        if MemoryClassification.PERSISTENT in contract.classifications:
            assert contract.resource_type is ResourceType.HISTORY
            assert contract.history_policy is not HistoryPolicy.NONE
        if MemoryClassification.RESOURCE_EXTERNAL in contract.classifications:
            assert contract.external_dependencies
            assert contract.ownership is MemoryOwnership.EXTERNAL_SYSTEM
            assert contract.release_policy is ReleasePolicy.EXTERNAL
