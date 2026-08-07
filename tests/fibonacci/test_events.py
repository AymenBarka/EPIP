from epip.fibonacci.events import FibonacciComputed


def test_event() -> None:
    assert (
        FibonacciComputed(id="f", timestamp="t", symbol="X", timeframe="M1", version=1).version == 1
    )
