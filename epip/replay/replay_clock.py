"""Thread-safe replay clock used as EPIP replay time source."""

from __future__ import annotations

from threading import RLock

from epip.replay.replay_state import ReplayState


class ReplayClock:
    """Stateful replay clock independent from wall-clock time."""

    def __init__(self, *, total_steps: int = 0, replay_speed: float = 1.0) -> None:
        self._lock = RLock()
        self._timestamp: str | None = None
        self._state = ReplayState.CREATED
        self._step = 0
        self._total_steps = max(total_steps, 0)
        self._speed = replay_speed

    def now(self) -> str | None:
        with self._lock:
            return self._timestamp

    def advance(self, timestamp: str) -> str:
        with self._lock:
            self._timestamp = timestamp
            self._step += 1
            if self._state in {ReplayState.CREATED, ReplayState.READY, ReplayState.PAUSED}:
                self._state = ReplayState.RUNNING
            if self._total_steps and self._step >= self._total_steps:
                self._state = ReplayState.FINISHED
            return self._timestamp

    def rewind(self, timestamp: str) -> str:
        with self._lock:
            self._timestamp = timestamp
            self._step = max(self._step - 1, 0)
            if self._state == ReplayState.FINISHED and self._total_steps:
                self._state = ReplayState.RUNNING
            return self._timestamp

    def seek(self, timestamp: str, *, step: int | None = None) -> str:
        with self._lock:
            self._timestamp = timestamp
            if step is not None:
                self._step = max(step, 0)
            return self._timestamp

    def play(self) -> None:
        with self._lock:
            self._state = ReplayState.RUNNING

    def pause(self) -> None:
        with self._lock:
            self._state = ReplayState.PAUSED

    def stop(self) -> None:
        with self._lock:
            self._state = ReplayState.STOPPED

    def resume(self) -> None:
        with self._lock:
            self._state = ReplayState.RUNNING

    def speed(self, value: float | None = None) -> float:
        with self._lock:
            if value is not None:
                if value <= 0:
                    raise ValueError("replay speed must be greater than zero")
                self._speed = value
            return self._speed

    def finished(self) -> bool:
        with self._lock:
            return self._state in {ReplayState.FINISHED, ReplayState.STOPPED} or (
                self._total_steps > 0 and self._step >= self._total_steps
            )

    def remaining(self) -> int | None:
        with self._lock:
            if self._total_steps <= 0:
                return None
            return max(self._total_steps - self._step, 0)

    def state(self) -> ReplayState:
        with self._lock:
            return self._state

    def step(self) -> int:
        with self._lock:
            return self._step
