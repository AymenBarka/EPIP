"""Immutable liquidity metrics."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LiquidityMetrics:
    pools: int = 0
    sweeps: int = 0
    equal_highs: int = 0
    equal_lows: int = 0
    stop_hunts: int = 0
    false_detections: int = 0
    processing_time_seconds: float = 0.0
    consumed_pools: int = 0
    average_lifetime: float = 0.0
    maximum_lifetime: float = 0.0
    average_confluence: float = 0.0
