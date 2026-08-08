"""Thread-safe replay statistics accumulator."""

from __future__ import annotations

from threading import RLock
from time import perf_counter

from epip.replay.replay_metrics import ReplayMetrics


class ReplayStatistics:
    """Accumulates replay counters and latency metrics."""

    def __init__(self, *, normalize_runtime: bool = False) -> None:
        self._lock = RLock()
        self._started_at: float | None = None
        self._elapsed_override = 0.0
        self._processed_candles = 0
        self._processed_events = 0
        self._processed_features = 0
        self._total_latency = 0.0
        self._max_latency = 0.0
        self._peak_memory = 0
        self._normalize_runtime = normalize_runtime

    def mark_started(self) -> None:
        with self._lock:
            self._started_at = perf_counter()
            self._elapsed_override = 0.0

    def mark_finished(self) -> None:
        with self._lock:
            self._elapsed_override = self._compute_elapsed_locked()
            self._started_at = None

    def record_candle(self, latency: float, *, peak_memory: int = 0) -> None:
        with self._lock:
            self._processed_candles += 1
            self._total_latency += latency
            self._max_latency = max(self._max_latency, latency)
            self._peak_memory = max(self._peak_memory, peak_memory)

    def record_event(self, count: int = 1) -> None:
        with self._lock:
            self._processed_events += count

    def record_feature(self, count: int = 1) -> None:
        with self._lock:
            self._processed_features += count

    def observe_peak_memory(self, peak_memory: int) -> None:
        with self._lock:
            self._peak_memory = max(self._peak_memory, peak_memory)

    def snapshot(self) -> ReplayMetrics:
        with self._lock:
            if self._normalize_runtime:
                return ReplayMetrics(
                    elapsed_time=0.0,
                    candles_per_second=0.0,
                    average_latency=0.0,
                    max_latency=0.0,
                    peak_memory=0,
                    processed_candles=self._processed_candles,
                    processed_events=self._processed_events,
                    processed_features=self._processed_features,
                )
            elapsed = self._compute_elapsed_locked()
            average_latency = (
                self._total_latency / self._processed_candles if self._processed_candles else 0.0
            )
            candles_per_second = self._processed_candles / elapsed if elapsed > 0.0 else 0.0
            return ReplayMetrics(
                elapsed_time=elapsed,
                candles_per_second=candles_per_second,
                average_latency=average_latency,
                max_latency=self._max_latency,
                peak_memory=self._peak_memory,
                processed_candles=self._processed_candles,
                processed_events=self._processed_events,
                processed_features=self._processed_features,
            )

    def _compute_elapsed_locked(self) -> float:
        if self._started_at is None:
            return self._elapsed_override
        return perf_counter() - self._started_at
