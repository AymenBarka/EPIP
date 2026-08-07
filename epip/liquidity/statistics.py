"""Thread-safe liquidity statistics."""

from threading import RLock

from epip.liquidity.metrics import LiquidityMetrics


class LiquidityStatistics:
    def __init__(self) -> None:
        self._counts: list[int] = [0, 0, 0, 0, 0, 0]
        self._elapsed = 0.0
        self._lock = RLock()

    def record(
        self, *, pools: int, sweeps: int, highs: int, lows: int, stop_hunts: int, elapsed: float
    ) -> None:
        with self._lock:
            for i, value in enumerate((pools, sweeps, highs, lows, stop_hunts)):
                self._counts[i] += value
            self._elapsed += elapsed

    def record_false_detection(self) -> None:
        with self._lock:
            self._counts[5] += 1

    def snapshot(self) -> LiquidityMetrics:
        with self._lock:
            return LiquidityMetrics(
                pools=self._counts[0],
                sweeps=self._counts[1],
                equal_highs=self._counts[2],
                equal_lows=self._counts[3],
                stop_hunts=self._counts[4],
                false_detections=self._counts[5],
                processing_time_seconds=self._elapsed,
            )
