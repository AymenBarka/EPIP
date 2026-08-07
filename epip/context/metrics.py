"""Immutable Market Context metrics."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketContextMetrics:
    contexts: int = 0
    updates: int = 0
    bias_changes: int = 0
    phase_changes: int = 0
    average_confluence: float = 0.0
    processing_time_seconds: float = 0.0
    maximum_processing_time_seconds: float = 0.0
