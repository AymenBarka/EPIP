"""Immutable metrics snapshot for Swing Engine runs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SwingMetrics:
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
    elapsed_time_seconds: float
    swings_per_second: float
    peak_memory_bytes: int
