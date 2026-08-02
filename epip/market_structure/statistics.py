"""Thread-safe statistics and metrics accumulator for EPIP-007."""

from __future__ import annotations

from threading import RLock
from time import perf_counter

from epip.market_structure.metrics import MarketStructureMetrics
from epip.market_structure.models import StructureStatistics


class MarketStructureStatistics:
    """Collects structure counters and detection timing."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._started_at: float | None = None
        self._elapsed_override = 0.0
        self._number_of_bos = 0
        self._number_of_choch = 0
        self._trend_changes = 0
        self._ranges = 0
        self._processed_swings = 0
        self._bos_time_total = 0.0
        self._choch_time_total = 0.0
        self._bos_time_count = 0
        self._choch_time_count = 0
        self._false_bos = 0
        self._false_choch = 0
        self._invalid_structures = 0
        self._duplicate_events = 0
        self._detection_time_total = 0.0
        self._detection_time_count = 0
        self._detection_time_max = 0.0
        self._peak_memory_bytes = 0

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

    def record_processed_swings(self, count: int) -> None:
        with self._lock:
            self._processed_swings += max(0, count)

    def record_bos(self, detection_time_seconds: float) -> None:
        with self._lock:
            self._number_of_bos += 1
            self._bos_time_total += detection_time_seconds
            self._bos_time_count += 1

    def record_choch(self, detection_time_seconds: float) -> None:
        with self._lock:
            self._number_of_choch += 1
            self._choch_time_total += detection_time_seconds
            self._choch_time_count += 1

    def record_trend_change(self) -> None:
        with self._lock:
            self._trend_changes += 1

    def record_range(self) -> None:
        with self._lock:
            self._ranges += 1

    def record_false_bos(self) -> None:
        with self._lock:
            self._false_bos += 1

    def record_false_choch(self) -> None:
        with self._lock:
            self._false_choch += 1

    def record_invalid_structure(self) -> None:
        with self._lock:
            self._invalid_structures += 1

    def record_duplicate_event(self) -> None:
        with self._lock:
            self._duplicate_events += 1

    def record_detection_time(self, detection_time_seconds: float) -> None:
        with self._lock:
            self._detection_time_total += detection_time_seconds
            self._detection_time_count += 1
            self._detection_time_max = max(self._detection_time_max, detection_time_seconds)

    def snapshot_statistics(self) -> StructureStatistics:
        with self._lock:
            average_detection_time = (
                self._detection_time_total / self._detection_time_count
                if self._detection_time_count
                else 0.0
            )
            return StructureStatistics(
                number_of_bos=self._number_of_bos,
                number_of_choch=self._number_of_choch,
                trend_changes=self._trend_changes,
                ranges=self._ranges,
                processed_swings=self._processed_swings,
                processing_time_seconds=self._elapsed_locked(),
                false_bos=self._false_bos,
                false_choch=self._false_choch,
                invalid_structures=self._invalid_structures,
                duplicate_events=self._duplicate_events,
                average_detection_time_seconds=average_detection_time,
                maximum_detection_time_seconds=self._detection_time_max,
            )

    def snapshot_metrics(self) -> MarketStructureMetrics:
        with self._lock:
            return MarketStructureMetrics(
                processing_latency_seconds=self._elapsed_locked(),
                average_bos_detection_time_seconds=(
                    self._bos_time_total / self._bos_time_count if self._bos_time_count else 0.0
                ),
                average_choch_detection_time_seconds=(
                    self._choch_time_total / self._choch_time_count
                    if self._choch_time_count
                    else 0.0
                ),
                total_processed_swings=self._processed_swings,
                peak_memory_bytes=self._peak_memory_bytes,
                false_bos=self._false_bos,
                false_choch=self._false_choch,
                invalid_structures=self._invalid_structures,
                duplicate_events=self._duplicate_events,
                average_detection_time_seconds=(
                    self._detection_time_total / self._detection_time_count
                    if self._detection_time_count
                    else 0.0
                ),
                maximum_detection_time_seconds=self._detection_time_max,
            )

    def _elapsed_locked(self) -> float:
        if self._started_at is None:
            return self._elapsed_override
        return perf_counter() - self._started_at
