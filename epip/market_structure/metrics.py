"""Performance metrics for Market Structure Engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketStructureMetrics:
    """Runtime metrics snapshot."""

    processing_latency_seconds: float
    average_bos_detection_time_seconds: float
    average_choch_detection_time_seconds: float
    total_processed_swings: int
    peak_memory_bytes: int
    false_bos: int = 0
    false_choch: int = 0
    invalid_structures: int = 0
    duplicate_events: int = 0
    average_detection_time_seconds: float = 0.0
    maximum_detection_time_seconds: float = 0.0
