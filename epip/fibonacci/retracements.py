from epip.fibonacci.levels import calculate_levels
from epip.fibonacci.models import FibonacciDirection, FibonacciRetracement


def compute_retracement(
    start: float, end: float, ratios: tuple[float, ...], direction: FibonacciDirection, score: float
) -> FibonacciRetracement:
    return FibonacciRetracement(
        start,
        end,
        direction,
        calculate_levels(start, end, tuple(x for x in ratios if x <= 1), direction),
        score,
    )
