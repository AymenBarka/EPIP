"""Thread-safe swing statistics accumulator."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from time import perf_counter

from epip.swing.metrics import SwingMetrics
from epip.swing.types import SwingClassification


@dataclass(frozen=True, slots=True)
class SwingStatistics:
    swings_count: int
    higher_high_count: int
    higher_low_count: int
    lower_high_count: int
    lower_low_count: int
    equal_high_count: int
    equal_low_count: int
    average_distance_bars: float
    average_duration_bars: float
    average_detection_latency_bars: float


class SwingStatisticsCollector:
    """Collects counters and timing metrics during streaming detection."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._started_at: float | None = None
        self._elapsed_override = 0.0
        self._peak_memory_bytes = 0
        self._swings_count = 0
        self._higher_high_count = 0
        self._higher_low_count = 0
        self._lower_high_count = 0
        self._lower_low_count = 0
        self._equal_high_count = 0
        self._equal_low_count = 0
        self._distance_sum = 0
        self._duration_sum = 0
        self._latency_sum = 0

    def mark_started(self) -> None:
        with self._lock:
            self._started_at = perf_counter()
            self._elapsed_override = 0.0

    def mark_finished(self) -> None:
        with self._lock:
            self._elapsed_override = self._elapsed_locked()
            self._started_at = None

    def observe_peak_memory(self, peak_memory_bytes: int) -> None:
        with self._lock:
            self._peak_memory_bytes = max(self._peak_memory_bytes, peak_memory_bytes)

    def record_swing(
        self,
        *,
        classification: SwingClassification,
        distance_from_previous: int,
        duration_bars: int,
        detection_latency_bars: int,
    ) -> None:
        with self._lock:
            self._swings_count += 1
            self._distance_sum += distance_from_previous
            self._duration_sum += duration_bars
            self._latency_sum += detection_latency_bars
            if classification == SwingClassification.HIGHER_HIGH:
                self._higher_high_count += 1
            elif classification == SwingClassification.HIGHER_LOW:
                self._higher_low_count += 1
            elif classification == SwingClassification.LOWER_HIGH:
                self._lower_high_count += 1
            elif classification == SwingClassification.LOWER_LOW:
                self._lower_low_count += 1
            elif classification == SwingClassification.EQUAL_HIGH:
                self._equal_high_count += 1
            elif classification == SwingClassification.EQUAL_LOW:
                self._equal_low_count += 1

    def snapshot_statistics(self) -> SwingStatistics:
        with self._lock:
            average_distance = (
                self._distance_sum / self._swings_count if self._swings_count else 0.0
            )
            average_duration = (
                self._duration_sum / self._swings_count if self._swings_count else 0.0
            )
            average_latency = self._latency_sum / self._swings_count if self._swings_count else 0.0
            return SwingStatistics(
                swings_count=self._swings_count,
                higher_high_count=self._higher_high_count,
                higher_low_count=self._higher_low_count,
                lower_high_count=self._lower_high_count,
                lower_low_count=self._lower_low_count,
                equal_high_count=self._equal_high_count,
                equal_low_count=self._equal_low_count,
                average_distance_bars=average_distance,
                average_duration_bars=average_duration,
                average_detection_latency_bars=average_latency,
            )

    def snapshot_metrics(self) -> SwingMetrics:
        with self._lock:
            elapsed = self._elapsed_locked()
            stats = self.snapshot_statistics()
            swings_per_second = stats.swings_count / elapsed if elapsed > 0.0 else 0.0
            return SwingMetrics(
                swings_count=stats.swings_count,
                higher_high_count=stats.higher_high_count,
                higher_low_count=stats.higher_low_count,
                lower_high_count=stats.lower_high_count,
                lower_low_count=stats.lower_low_count,
                equal_high_count=stats.equal_high_count,
                equal_low_count=stats.equal_low_count,
                average_distance_bars=stats.average_distance_bars,
                average_duration_bars=stats.average_duration_bars,
                average_detection_latency_bars=stats.average_detection_latency_bars,
                elapsed_time_seconds=elapsed,
                swings_per_second=swings_per_second,
                peak_memory_bytes=self._peak_memory_bytes,
            )

    def _elapsed_locked(self) -> float:
        if self._started_at is None:
            return self._elapsed_override
        return perf_counter() - self._started_at
