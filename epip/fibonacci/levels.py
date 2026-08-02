"""Fibonacci level calculations."""

from epip.fibonacci.models import FibonacciDirection, FibonacciLevel


def calculate_levels(
    start: float, end: float, ratios: tuple[float, ...], direction: FibonacciDirection
) -> tuple[FibonacciLevel, ...]:
    distance = abs(end - start)
    return tuple(
        FibonacciLevel(
            r,
            (end - distance * r if direction == FibonacciDirection.BULLISH else end + distance * r),
            f"{r:.3f}",
        )
        for r in ratios
    )
