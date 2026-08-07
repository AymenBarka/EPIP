"""Manual EPIP-015 portfolio benchmark."""

from time import perf_counter

from epip.portfolio.allocation import calculate_allocations
from epip.portfolio.exposure import calculate_exposure
from epip.portfolio.models import PortfolioPosition, PositionDirection


def benchmark_portfolios(iterations: int = 100_000) -> dict[str, float]:
    positions = (
        PortfolioPosition("EURUSD", 10, PositionDirection.LONG, 100, 100),
        PortfolioPosition("GBPUSD", 5, PositionDirection.SHORT, 120, 120),
    )
    started = perf_counter()
    for _ in range(iterations):
        calculate_exposure(positions, 100_000)
        calculate_allocations(positions, ())
    elapsed = perf_counter() - started
    return {
        "iterations": float(iterations),
        "seconds": elapsed,
        "throughput": iterations / elapsed,
        "latency": elapsed / iterations,
        "estimated_bytes": float(iterations * 128),
    }


if __name__ == "__main__":
    print(benchmark_portfolios(100_000))
    print(benchmark_portfolios(1_000_000))
