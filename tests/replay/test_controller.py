from __future__ import annotations

from epip.marketdata.providers.fake_provider import FakeProvider
from epip.replay.replay_clock import ReplayClock
from epip.replay.replay_config import ReplayConfig
from epip.replay.replay_controller import ReplayController
from epip.replay.replay_scheduler import ReplayScheduler
from epip.replay.replay_session import ReplaySession
from epip.replay.replay_state import ReplayState
from epip.replay.replay_statistics import ReplayStatistics


def test_controller_transitions_session_state() -> None:
    provider = FakeProvider(symbols=("EURUSD",), timeframes=("M1",), candles_per_series=3)
    provider.connect()
    config = ReplayConfig(
        symbols=("EURUSD",), timeframes=("M1",), start_date="2024-01-01T00:00:00+00:00"
    )
    session = ReplaySession(
        config=config,
        clock=ReplayClock(),
        statistics=ReplayStatistics(),
        scheduler=ReplayScheduler(market_data=provider, config=config),
    )
    controller = ReplayController(session)

    controller.play()
    assert session.state() == ReplayState.RUNNING
    controller.pause()
    assert session.state() == ReplayState.PAUSED
    controller.resume()
    assert session.state() == ReplayState.RUNNING
    controller.seek("2024-01-01T00:01:00+00:00", step=2)
    assert controller.clock.now() == "2024-01-01T00:01:00+00:00"
    controller.restart()
    assert session.state() == ReplayState.READY
    controller.stop()
    assert session.state() == ReplayState.STOPPED
    provider.disconnect()
