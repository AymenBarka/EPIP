from epip.fibonacci.models import FibonacciDirection
from epip.fibonacci.ote import ote_zones


def test_ote_golden() -> None:
    ote, golden = ote_zones(1, 2, FibonacciDirection.BULLISH, 0.618, 0.786, 0.618, 0.705, 0.8)
    assert ote.low < ote.high and golden.name == "GOLDEN"
