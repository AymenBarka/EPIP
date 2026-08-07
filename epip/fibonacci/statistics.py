from threading import RLock

from epip.fibonacci.metrics import FibonacciMetrics


class FibonacciStatistics:
    def __init__(self) -> None:
        self._count = 0
        self._elapsed = 0.0
        self._confluence = 0.0
        self._probability = 0.0
        self._projection_attempts = 0
        self._projection_hits = 0
        self._alignment_count = 0
        self._alignment = 0.0
        self._cluster_usage = 0
        self._lock = RLock()

    def record(self, elapsed: float, score: float, probability: float = 0.0) -> None:
        with self._lock:
            self._count += 1
            self._elapsed += elapsed
            self._confluence += score
            self._probability += probability

    def record_projection(self, accurate: bool) -> None:
        with self._lock:
            self._projection_attempts += 1
            self._projection_hits += int(accurate)

    def record_alignment(self, score: float) -> None:
        with self._lock:
            self._alignment_count += 1
            self._alignment += max(0.0, min(1.0, score))

    def record_cluster(self) -> None:
        with self._lock:
            self._cluster_usage += 1

    def snapshot(self) -> FibonacciMetrics:
        with self._lock:
            return FibonacciMetrics(
                self._count,
                self._count,
                self._count,
                self._count,
                self._elapsed,
                self._confluence / self._count if self._count else 0.0,
                (
                    self._projection_hits / self._projection_attempts
                    if self._projection_attempts
                    else 0.0
                ),
                self._probability / self._count if self._count else 0.0,
                self._alignment / self._alignment_count if self._alignment_count else 0.0,
                self._cluster_usage,
            )
