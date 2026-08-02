from epip.fibonacci.extensions import compute_extension
from epip.fibonacci.models import FibonacciDirection


def test_extensions() -> None:
    assert (
        compute_extension(2, 1, (0.5, 1.618), FibonacciDirection.BEARISH, 0.5).levels[0].ratio
        == 1.618
    )
