from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from time import sleep
from typing import Any

import pytest

from epip.core.context import MarketContext
from epip.core.event_bus import EventBus
from epip.core.events import BaseEvent
from epip.core.external_effects import (
    EXTERNAL_EFFECT_CONTRACTS,
    ExternalBoundary,
    IdempotencyLevel,
    external_effect_contract,
)
from epip.core.identity import SystemClock, SystemIdGenerator
from epip.core.kernel import Kernel
from epip.core.plugin_context import PluginContext
from epip.core.plugin_result import PluginResult
from epip.core.registry import Registry
from epip.execution.engine import ExecutionEngine
from epip.execution.exceptions import BrokerUnavailableError
from epip.execution.models import BrokerResponse, Order
from epip.features.feature import Feature
from epip.features.feature_set import FeatureSet
from epip.features.feature_store import FeatureStore
from epip.features.providers.base_provider import BaseFeatureProvider
from epip.marketdata.datasource_models import ConnectionState
from epip.marketdata.exceptions import ProviderError
from epip.marketdata.providers.csv_provider import CSVProvider
from epip.marketdata.providers.fake_provider import FakeProvider
from epip.replay.replay_config import ReplayConfig
from epip.replay.replay_engine import ReplayEngine
from epip.replay.replay_state import ReplayState
from tests.execution.helpers import position_plan


def test_every_external_boundary_has_one_complete_contract() -> None:
    assert set(EXTERNAL_EFFECT_CONTRACTS) == set(ExternalBoundary)
    for boundary, contract in EXTERNAL_EFFECT_CONTRACTS.items():
        assert contract.boundary is boundary
        assert contract.responsibility.strip()
        assert contract.execution_order.strip()
        assert contract.observability.strip()
        assert contract.rollback.strip()
        assert contract.restrictions
        assert external_effect_contract(boundary) is contract


def test_no_external_write_claims_exactly_once_or_automatic_rollback() -> None:
    for contract in EXTERNAL_EFFECT_CONTRACTS.values():
        assert contract.transactional is False
        assert "exactly_once" not in contract.delivery.value
        assert contract.compensable is False
    assert (
        external_effect_contract(ExternalBoundary.BROKER_ADAPTER).idempotency
        is IdempotencyLevel.NON_IDEMPOTENT
    )


class _UnavailableFeatureProvider(BaseFeatureProvider):
    name = "unavailable"
    priority = 1

    def provide(
        self,
        *,
        symbol: str,
        timeframe: str,
        timestamp: str,
        payload: Mapping[str, Any] | None = None,
        feature_set: FeatureSet | None = None,
    ) -> FeatureSet:
        del symbol, timeframe, timestamp, payload, feature_set
        raise ConnectionError("provider unavailable")


class _SlowFeatureProvider(BaseFeatureProvider):
    name = "slow"
    priority = 1

    def provide(
        self,
        *,
        symbol: str,
        timeframe: str,
        timestamp: str,
        payload: Mapping[str, Any] | None = None,
        feature_set: FeatureSet | None = None,
    ) -> FeatureSet:
        del symbol, timeframe, timestamp, payload, feature_set
        sleep(0.01)
        return FeatureSet(
            (
                Feature(
                    id="slow-t",
                    name="slow",
                    category="external",
                    value=True,
                    timestamp="t",
                    metadata={},
                    quality_score=1.0,
                    source=self.name,
                ),
            )
        )


def test_unavailable_provider_does_not_partially_commit_feature_store() -> None:
    store = FeatureStore(providers=(_UnavailableFeatureProvider(),))

    with pytest.raises(ConnectionError, match="provider unavailable"):
        store.build_feature_set("EURUSD", "M1", "t")

    assert store.cache_size() == 0
    assert store.history() == ()


def test_slow_provider_commits_only_complete_feature_set() -> None:
    store = FeatureStore(providers=(_SlowFeatureProvider(),))

    result = store.build_feature_set("EURUSD", "M1", "t")

    feature = result.get("slow")
    assert feature is not None
    assert feature.value is True
    assert store.cache_size() == 1
    assert store.history() == (result,)


class _UnavailableBroker:
    def submit(self, order: Order) -> BrokerResponse:
        del order
        raise BrokerUnavailableError("broker unavailable")

    def cancel(self, order: Order) -> BrokerResponse:
        del order
        raise BrokerUnavailableError("broker unavailable")


def test_unavailable_broker_leaves_execution_engine_uncommitted() -> None:
    bus = EventBus()
    engine = ExecutionEngine(event_bus=bus, broker=_UnavailableBroker())

    with pytest.raises(BrokerUnavailableError, match="broker unavailable"):
        engine.execute(position_plan(), timestamp="t")

    assert engine.snapshot("EURUSD") is None
    assert engine.history("EURUSD").snapshots == ()
    assert bus.event_history() == ()


def test_user_callback_failure_preserves_eventbus_invariants() -> None:
    bus = EventBus()

    def fail(event: object) -> None:
        del event
        raise RuntimeError("callback failure")

    first = BaseEvent(id="first", timestamp="t")
    bus.subscribe(BaseEvent, fail)
    with pytest.raises(RuntimeError, match="callback failure"):
        bus.publish(first)
    bus.unsubscribe(BaseEvent, fail)
    second = BaseEvent(id="second", timestamp="t")
    bus.publish(second)

    assert bus.event_history() == (first, second)


class _FailingLogger(logging.Logger):
    def info(self, msg: object, *args: object, **kwargs: object) -> None:
        del msg, args, kwargs
        raise OSError("logging unavailable")


class _Plugin:
    name = "plugin"
    priority = 0

    def execute(self, context: PluginContext) -> PluginResult:
        del context
        return PluginResult(plugin=self.name, execution_time=0.0, success=True)


def test_logging_failure_cannot_leave_kernel_partially_advanced() -> None:
    registry = Registry()
    registry.register(_Plugin())
    kernel = Kernel(registry=registry, logger=_FailingLogger("failing"))

    with pytest.raises(OSError, match="logging unavailable"):
        kernel.run(MarketContext("EURUSD", "M1", "t"))

    assert kernel.event_bus.event_history() == ()


def test_inaccessible_filesystem_does_not_connect_csv_provider(tmp_path: Path) -> None:
    provider = CSVProvider(csv_path=str(tmp_path / "missing.csv"))

    with pytest.raises(ProviderError, match="CSV file not found"):
        provider.connect()

    assert provider.health().connection is ConnectionState.DISCONNECTED


def test_market_data_failure_preserves_replay_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeProvider(symbols=("EURUSD",), timeframes=("M1",), candles_per_series=2)
    store = FeatureStore()
    bus = EventBus()
    engine = ReplayEngine(market_data=provider, feature_store=store, event_bus=bus)
    session = engine.create_session(ReplayConfig(symbols=("EURUSD",), timeframes=("M1",)))

    def unavailable(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise ConnectionError("network unavailable")

    monkeypatch.setattr(provider, "history", unavailable)
    with pytest.raises(ConnectionError, match="network unavailable"):
        engine.run(session)

    assert session.state() is ReplayState.CREATED
    assert session.contexts() == {}
    assert store.cache_size() == 0
    assert bus.event_history() == ()


def test_system_clock_and_identity_are_valid_but_nondeterministic_boundaries() -> None:
    timestamp = SystemClock().now()
    identity = SystemIdGenerator().generate("external-boundary")

    assert timestamp
    assert len(identity) == 32
    assert external_effect_contract(ExternalBoundary.SYSTEM_CLOCK).deterministic is False
    assert external_effect_contract(ExternalBoundary.SYSTEM_IDENTITY).deterministic is False
