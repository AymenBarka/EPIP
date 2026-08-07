from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FibonacciMetrics:
    computations: int = 0
    golden_zones: int = 0
    ote_zones: int = 0
    extensions: int = 0
    processing_time_seconds: float = 0.0
    average_confluence: float = 0.0
    projection_accuracy: float = 0.0
    average_probability: float = 0.0
    average_alignment: float = 0.0
    cluster_usage: int = 0
