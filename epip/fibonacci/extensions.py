from epip.fibonacci.levels import calculate_levels
from epip.fibonacci.models import FibonacciDirection, FibonacciExtension


def compute_extension(
    start: float, end: float, ratios: tuple[float, ...], direction: FibonacciDirection, score: float
) -> FibonacciExtension:
    return FibonacciExtension(
        start,
        end,
        calculate_levels(start, end, tuple(x for x in ratios if x >= 1), direction),
        score,
    )
