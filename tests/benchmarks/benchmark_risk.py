"""Manual EPIP-013 throughput benchmark."""

from time import perf_counter

from epip.risk.config import RiskConfig
from epip.risk.position_sizer import PositionSizer


def benchmark_position_plans(iterations: int = 100_000) -> dict[str, float]:
    sizer, config = PositionSizer(), RiskConfig()
    started = perf_counter()
    for _ in range(iterations):
        sizer.size(100.0, 99.0, 0.6, config)
    elapsed = perf_counter() - started
    return {
        "iterations": float(iterations),
        "seconds": elapsed,
        "throughput": iterations / elapsed,
        "latency": elapsed / iterations,
        "sizing_seconds": elapsed,
        "estimated_bytes": float(iterations * 64),
    }


if __name__ == "__main__":
    print(benchmark_position_plans(100_000))
    print(benchmark_position_plans(1_000_000))
