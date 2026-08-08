"""Replay identity determinism tests."""

import json
from dataclasses import asdict, fields
from typing import Any, cast

from epip.core import DeterministicClock, DeterministicIdGenerator, Evidence, Kernel, PluginContext
from epip.core.event_bus import EventBus
from epip.core.registry import Registry
from epip.core.types import Direction
from epip.features.feature_store import FeatureStore
from epip.marketdata.providers.fake_provider import FakeProvider
from epip.replay import (
    ReplayClock,
    ReplayConfig,
    ReplayEngine,
    ReplayScheduler,
    ReplaySession,
    ReplayStatistics,
)


class _MarketData:
    def history(self, request: object) -> object:
        del request
        raise NotImplementedError


class _DeterministicPlugin:
    name = "deterministic"
    priority = 1

    def execute(self, context: PluginContext) -> Evidence:
        return Evidence(
            id=f"evidence-{context.market_context.timestamp}",
            source=self.name,
            category="replay",
            direction=Direction.BUY,
            confidence=0.8,
            timestamp=context.market_context.timestamp,
            clock=context.clock,
            id_generator=context.id_generator,
        )


def _session(seed: str) -> ReplaySession:
    config = ReplayConfig(symbols=("EURUSD",), timeframes=("M1",))
    return ReplaySession(
        config=config,
        clock=ReplayClock(),
        statistics=ReplayStatistics(),
        scheduler=ReplayScheduler(market_data=_MarketData(), config=config),  # type: ignore[arg-type]
        id_generator=DeterministicIdGenerator(seed),
    )


def test_replay_session_identity_is_reproducible() -> None:
    assert _session("same").session_id == _session("same").session_id
    assert _session("first").session_id != _session("second").session_id


def test_explicit_session_identity_is_preserved() -> None:
    session = _session("unused")
    explicit = ReplaySession(
        config=session.config,
        clock=session.clock,
        statistics=session.statistics,
        scheduler=session.scheduler,
        session_id="replay-fixed",
    )
    assert explicit.session_id == "replay-fixed"


def _complete_replay_json() -> bytes:
    clock = DeterministicClock("2025-01-01T00:00:00Z")
    ids = DeterministicIdGenerator("complete-replay")
    provider = FakeProvider(
        symbols=("EURUSD",),
        timeframes=("M1",),
        candles_per_series=4,
        clock=clock,
        id_generator=ids,
    )
    bus = EventBus()
    registry = Registry()
    registry.register(_DeterministicPlugin())
    engine = ReplayEngine(
        market_data=provider,
        feature_store=FeatureStore(),
        event_bus=bus,
        kernel=Kernel(
            registry=registry,
            event_bus=bus,
            clock=clock,
            id_generator=ids,
        ),
        clock=clock,
        id_generator=ids,
    )
    session = engine.create_session(
        ReplayConfig(symbols=("EURUSD",), timeframes=("M1",), page_size=2)
    )
    metrics = engine.run(session)
    events = [
        {item.name: getattr(event, item.name) for item in fields(cast(Any, event))}
        for event in bus.event_history()
    ]
    contexts = {"|".join(key): value.to_dict() for key, value in sorted(session.contexts().items())}
    payload = {"events": events, "contexts": contexts, "metrics": asdict(metrics)}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def test_complete_replay_is_byte_identical() -> None:
    assert _complete_replay_json() == _complete_replay_json()
