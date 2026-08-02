"""Thread-safe Market Context statistics."""

from threading import RLock

from epip.context.metrics import MarketContextMetrics


class MarketContextStatistics:
    def __init__(self) -> None:
        self._contexts = 0
        self._updates = 0
        self._bias_changes = 0
        self._phase_changes = 0
        self._confluence = 0.0
        self._elapsed = 0.0
        self._maximum = 0.0
        self._lock = RLock()

    def record(
        self, elapsed: float, confluence: float, *, bias_changed: bool, phase_changed: bool
    ) -> None:
        with self._lock:
            self._contexts += 1
            self._updates += int(self._contexts > 1)
            self._bias_changes += int(bias_changed)
            self._phase_changes += int(phase_changed)
            self._confluence += confluence
            self._elapsed += elapsed
            self._maximum = max(self._maximum, elapsed)

    def snapshot(self) -> MarketContextMetrics:
        with self._lock:
            return MarketContextMetrics(
                self._contexts,
                self._updates,
                self._bias_changes,
                self._phase_changes,
                self._confluence / self._contexts if self._contexts else 0.0,
                self._elapsed,
                self._maximum,
            )
