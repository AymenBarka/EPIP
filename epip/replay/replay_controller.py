"""Replay control surface for session state changes."""

from __future__ import annotations

from epip.replay.replay_clock import ReplayClock
from epip.replay.replay_session import ReplaySession
from epip.replay.replay_state import ReplayState


class ReplayController:
    """High-level controller exposing replay lifecycle operations."""

    def __init__(self, session: ReplaySession) -> None:
        self._session = session

    @property
    def clock(self) -> ReplayClock:
        return self._session.clock

    def play(self) -> None:
        self._session.clock.play()
        self._session.set_state(ReplayState.RUNNING)

    def pause(self) -> None:
        self._session.clock.pause()
        self._session.set_state(ReplayState.PAUSED)

    def resume(self) -> None:
        self._session.clock.resume()
        self._session.set_state(ReplayState.RUNNING)

    def stop(self) -> None:
        self._session.clock.stop()
        self._session.set_state(ReplayState.STOPPED)

    def restart(self) -> None:
        self._session.scheduler.reset()
        self._session.clock.stop()
        self._session.clock.seek(self._session.config.start_date or "", step=0)
        self._session.set_state(ReplayState.READY)

    def seek(self, timestamp: str, *, step: int | None = None) -> None:
        self._session.clock.seek(timestamp, step=step)
