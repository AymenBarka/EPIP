"""Thread-safe Elliott statistics."""

from threading import RLock

from epip.elliott.metrics import ElliottMetrics
from epip.elliott.models import CountStatus, WaveSnapshot


class ElliottStatistics:
    def __init__(self) -> None:
        self._analyses = 0
        self._valid = 0
        self._invalid = 0
        self._alternates = 0
        self._probability = 0.0
        self._elapsed = 0.0
        self._maximum = 0.0
        self._lock = RLock()

    def record(self, snapshot: WaveSnapshot, elapsed: float) -> None:
        with self._lock:
            primary = snapshot.analysis.primary
            self._analyses += 1
            self._valid += int(primary.status == CountStatus.VALID)
            self._invalid += int(primary.status == CountStatus.INVALID)
            self._alternates += len(snapshot.analysis.alternates)
            self._probability += primary.probability
            self._elapsed += elapsed
            self._maximum = max(self._maximum, elapsed)

    def snapshot(self) -> ElliottMetrics:
        with self._lock:
            return ElliottMetrics(
                self._analyses,
                self._valid,
                self._invalid,
                self._alternates,
                self._probability / self._analyses if self._analyses else 0.0,
                self._elapsed,
                self._maximum,
            )
