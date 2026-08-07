from epip.fibonacci.models import FibonacciDirection
from epip.fibonacci.retracements import compute_retracement


def test_retracement() -> None:
    assert all(
        x.ratio <= 1
        for x in compute_retracement(1, 2, (0.5, 1.618), FibonacciDirection.BULLISH, 0.5).levels
    )
