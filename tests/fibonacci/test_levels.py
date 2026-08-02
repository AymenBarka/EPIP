from epip.fibonacci.config import DEFAULT_LEVELS
from epip.fibonacci.levels import calculate_levels
from epip.fibonacci.models import FibonacciDirection


def test_configurable_levels() -> None:
    assert len(calculate_levels(1, 2, DEFAULT_LEVELS, FibonacciDirection.BULLISH)) == 16
