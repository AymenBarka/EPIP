from __future__ import annotations

from epip.core.context import MarketContext
from epip.marketdata.providers.fake_provider import FakeProvider
from epip.replay.replay_clock import ReplayClock
from epip.replay.replay_config import ReplayConfig
from epip.replay.replay_scheduler import ReplayScheduler
from epip.replay.replay_session import ReplaySession
from epip.replay.replay_state import ReplayState
from epip.replay.replay_statistics import ReplayStatistics


def test_session_holds_state_contexts_and_windows() -> None:
    provider = FakeProvider(symbols=("EURUSD",), timeframes=("M1",), candles_per_series=3)
    provider.connect()
    config = ReplayConfig(symbols=("EURUSD",), timeframes=("M1",), warmup_bars=2)
    session = ReplaySession(
        config=config,
        clock=ReplayClock(),
        statistics=ReplayStatistics(),
        scheduler=ReplayScheduler(market_data=provider, config=config),
    )

    assert session.state() == ReplayState.CREATED
    session.set_state(ReplayState.READY)
    assert session.state() == ReplayState.READY

    window = session.window_for("EURUSD", "M1")
    assert window.maxlen == 3

    context = MarketContext(symbol="EURUSD", timeframe="M1", timestamp="2024-01-01T00:00:00+00:00")
    session.set_context(context)
    assert session.current_context("EURUSD", "M1") == context
    assert session.contexts()[("EURUSD", "M1")] == context
    provider.disconnect()
