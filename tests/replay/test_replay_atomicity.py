"""Failure-injection coverage for Replay session atomicity."""

from __future__ import annotations

import pytest

from epip.core.event_bus import EventBus
from epip.features.feature_store import FeatureStore
from epip.marketdata.providers.fake_provider import FakeProvider
from epip.replay.replay_config import ReplayConfig
from epip.replay.replay_engine import ReplayEngine
from epip.replay.replay_session import ReplaySession
from epip.replay.replay_state import ReplayState
from epip.replay.replay_transaction import ReplaySessionTransaction


def _runtime() -> tuple[ReplayEngine, ReplaySession, FeatureStore, EventBus]:
    store = FeatureStore()
    bus = EventBus()
    engine = ReplayEngine(
        market_data=FakeProvider(symbols=("EURUSD",), timeframes=("M1",), candles_per_series=3),
        feature_store=store,
        event_bus=bus,
    )
    session = engine.create_session(
        ReplayConfig(symbols=("EURUSD",), timeframes=("M1",), page_size=2)
    )
    return engine, session, store, bus


def _assert_pristine(session: ReplaySession, store: FeatureStore, bus: EventBus) -> None:
    assert session.state() == ReplayState.CREATED
    assert session.contexts() == {}
    assert session.clock.now() is None
    assert session.clock.step() == 0
    metrics = session.statistics.snapshot()
    assert metrics.processed_candles == 0
    assert metrics.processed_events == 0
    assert metrics.processed_features == 0
    assert store.cache_size() == 0
    assert store.history() == ()
    assert bus.event_history() == ()


def test_feature_store_failure_rolls_back_complete_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, session, store, bus = _runtime()
    original = store.build_feature_set
    calls = 0

    def fail_after_mutation(*args: object, **kwargs: object) -> object:
        nonlocal calls
        result = original(*args, **kwargs)  # type: ignore[arg-type]
        calls += 1
        if calls == 2:
            raise RuntimeError("feature failure")
        return result

    monkeypatch.setattr(store, "build_feature_set", fail_after_mutation)
    with pytest.raises(RuntimeError, match="feature failure"):
        engine.run(session)

    _assert_pristine(session, store, bus)


def test_statistics_failure_restores_clock_scheduler_and_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, session, store, bus = _runtime()
    original = session.statistics.record_candle

    def fail_after_record(latency: float, *, peak_memory: int = 0) -> None:
        original(latency, peak_memory=peak_memory)
        raise RuntimeError("statistics failure")

    monkeypatch.setattr(session.statistics, "record_candle", fail_after_record)
    with pytest.raises(RuntimeError, match="statistics failure"):
        engine.run(session)

    _assert_pristine(session, store, bus)


def test_commit_failure_rolls_back_and_emits_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, session, store, bus = _runtime()

    def fail_commit(self: ReplaySessionTransaction) -> None:
        raise RuntimeError("commit failure")

    monkeypatch.setattr(ReplaySessionTransaction, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="commit failure"):
        engine.run(session)

    _assert_pristine(session, store, bus)


def test_checkpoint_preparation_failure_releases_transaction_locks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, session, store, bus = _runtime()

    def fail_checkpoint() -> object:
        raise RuntimeError("prepare failure")

    monkeypatch.setattr(store, "_checkpoint", fail_checkpoint)
    with pytest.raises(RuntimeError, match="prepare failure"):
        engine.run(session)

    _assert_pristine(session, store, bus)
    assert session._lock.acquire(timeout=0.1)
    session._lock.release()


def test_success_commits_before_replay_events_become_observable() -> None:
    engine, session, store, bus = _runtime()
    observed_states: list[ReplayState] = []
    bus.subscribe(object, lambda event: observed_states.append(session.state()))

    metrics = engine.run(session)

    assert metrics.processed_candles == 3
    assert observed_states
    assert set(observed_states) == {ReplayState.FINISHED}
    assert store.cache_size() == 3
