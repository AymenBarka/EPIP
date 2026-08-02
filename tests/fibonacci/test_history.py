import pytest

from epip.fibonacci.exceptions import FibonacciVersionError
from epip.fibonacci.history import FibonacciHistory
from epip.fibonacci.models import (
    FibonacciDirection,
    FibonacciExtension,
    FibonacciRetracement,
    FibonacciSnapshot,
)


def snap(v: int) -> FibonacciSnapshot:
    return FibonacciSnapshot(
        str(v),
        "X",
        "M1",
        v,
        FibonacciDirection.RANGE,
        FibonacciRetracement(1, 2, FibonacciDirection.RANGE, ()),
        FibonacciExtension(1, 2, ()),
        (),
    )


def test_history_serialization() -> None:
    h = FibonacciHistory().append(snap(1)).append(snap(2))
    assert h.by_version(1) == snap(1)
    assert h.by_timestamp("2") == snap(2)
    assert tuple(h.replay()) == h.snapshots
    assert FibonacciHistory.from_json(h.to_json()) == h
    with pytest.raises(FibonacciVersionError):
        h.append(snap(4))
