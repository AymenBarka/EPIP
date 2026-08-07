"""Manual EPIP-014 order benchmark."""

from time import perf_counter

from epip.execution.config import ExecutionConfig
from epip.execution.order_manager import OrderManager
from epip.risk.models import (
    Exposure,
    Leverage,
    Margin,
    PositionPlan,
    PositionSize,
    RiskLevel,
    RiskQuality,
    RiskScore,
    SizingMethod,
    StopLoss,
)


def _position_plan() -> PositionPlan:
    return PositionPlan(
        "benchmark-plan",
        "benchmark-decision",
        "EURUSD",
        "LONG",
        100.0,
        PositionSize(10.0, 1000.0, 20.0, SizingMethod.FIXED_RISK),
        StopLoss(98.0, 2.0, "FIXED"),
        (),
        Exposure("EURUSD", 0.01, 0.0, 0.01),
        Leverage(0.01, 5.0),
        Margin(200.0, 200.0, 99_800.0, 499.0),
        RiskScore(80.0, RiskQuality.HIGH, RiskLevel.LOW, 0.7),
        True,
        (),
    )


def benchmark_orders(iterations: int = 100_000) -> dict[str, float]:
    manager, plan, config = OrderManager(), _position_plan(), ExecutionConfig()
    started = perf_counter()
    for _ in range(iterations):
        manager.create(plan, config)
    elapsed = perf_counter() - started
    return {
        "iterations": float(iterations),
        "seconds": elapsed,
        "throughput": iterations / elapsed,
        "latency": elapsed / iterations,
        "estimated_bytes": float(iterations * 96),
    }


if __name__ == "__main__":
    print(benchmark_orders(100_000))
    print(benchmark_orders(1_000_000))
