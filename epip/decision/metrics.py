"""Immutable Decision Engine metrics."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionMetrics:
    decisions: int = 0
    long_decisions: int = 0
    short_decisions: int = 0
    wait_decisions: int = 0
    invalid_decisions: int = 0
    average_score: float = 0.0
    processing_time_seconds: float = 0.0
    maximum_processing_time_seconds: float = 0.0
