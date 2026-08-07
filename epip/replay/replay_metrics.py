"""Replay performance metrics snapshots."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReplayMetrics:
    """Immutable metrics snapshot for a replay run."""

    elapsed_time: float
    candles_per_second: float
    average_latency: float
    max_latency: float
    peak_memory: int
    processed_candles: int
    processed_events: int
    processed_features: int
