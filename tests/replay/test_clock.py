from __future__ import annotations

from epip.replay.replay_clock import ReplayClock
from epip.replay.replay_state import ReplayState


def test_clock_lifecycle_and_navigation() -> None:
    clock = ReplayClock(total_steps=3, replay_speed=2.0)

    assert clock.now() is None
    assert clock.remaining() == 3
    assert clock.speed() == 2.0

    clock.play()
    assert clock.state() == ReplayState.RUNNING

    clock.advance("2024-01-01T00:00:00+00:00")
    assert clock.now() == "2024-01-01T00:00:00+00:00"
    assert clock.step() == 1
    assert clock.remaining() == 2

    clock.pause()
    assert clock.state() == ReplayState.PAUSED
    clock.resume()
    assert clock.state() == ReplayState.RUNNING

    clock.seek("2024-01-01T00:01:00+00:00", step=2)
    assert clock.now() == "2024-01-01T00:01:00+00:00"
    assert clock.remaining() == 1

    clock.rewind("2024-01-01T00:00:00+00:00")
    assert clock.step() == 1

    clock.advance("2024-01-01T00:02:00+00:00")
    clock.advance("2024-01-01T00:03:00+00:00")
    assert clock.finished() is True

    clock.stop()
    assert clock.state() == ReplayState.STOPPED
    assert clock.finished() is True


def test_clock_speed_validation() -> None:
    clock = ReplayClock()
    try:
        clock.speed(0)
        assert False
    except ValueError:
        assert True
