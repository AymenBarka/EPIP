from __future__ import annotations

from epip.core.event_bus import EventBus
from epip.features.feature_store import FeatureStore
from epip.marketdata.providers.fake_provider import FakeProvider
from epip.replay.replay_config import ReplayConfig
from epip.replay.replay_engine import ReplayEngine
from epip.replay.replay_events import ReplayFinished, ReplayStarted
from epip.replay.replay_state import ReplayState


def test_engine_runs_and_publishes_replay_events() -> None:
    provider = FakeProvider(
        symbols=("EURUSD", "GBPUSD"),
        timeframes=("M1",),
        candles_per_series=5,
    )
    event_bus = EventBus()
    feature_store = FeatureStore()
    engine = ReplayEngine(
        market_data=provider,
        feature_store=feature_store,
        event_bus=event_bus,
        kernel=None,
    )
    session = engine.create_session(
        ReplayConfig(symbols=("EURUSD", "GBPUSD"), timeframes=("M1",), warmup_bars=1, page_size=2)
    )

    metrics = engine.run(session)

    assert metrics.processed_candles == 10
    assert metrics.processed_features > 0
    assert metrics.processed_events >= 10
    assert session.state() == ReplayState.FINISHED
    assert session.current_context("EURUSD", "M1") is not None
    assert session.current_context("GBPUSD", "M1") is not None

    history = event_bus.event_history()
    assert any(isinstance(event, ReplayStarted) for event in history)
    assert any(isinstance(event, ReplayFinished) for event in history)
