"""Immutable Elliott metrics."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ElliottMetrics:
    analyses: int = 0
    valid_counts: int = 0
    invalid_counts: int = 0
    alternates: int = 0
    average_probability: float = 0.0
    processing_time_seconds: float = 0.0
    maximum_processing_time_seconds: float = 0.0
