"""Multi-timeframe alignment across institutional timeframes."""

from dataclasses import dataclass

from epip.fibonacci.models import FibonacciDirection, FibonacciSnapshot

SUPPORTED_TIMEFRAMES = ("M15", "H1", "H4", "D1")


@dataclass(frozen=True, slots=True)
class MultiTimeFrameAlignment:
    directions: tuple[tuple[str, FibonacciDirection], ...]
    alignment_score: float


def compute_alignment(snapshots: tuple[FibonacciSnapshot, ...]) -> MultiTimeFrameAlignment:
    selected = tuple(
        (snapshot.timeframe, snapshot.direction)
        for snapshot in snapshots
        if snapshot.timeframe in SUPPORTED_TIMEFRAMES
    )
    if not selected:
        return MultiTimeFrameAlignment((), 0.0)
    counts = {
        direction: sum(item[1] == direction for item in selected)
        for direction in FibonacciDirection
    }
    return MultiTimeFrameAlignment(selected, max(counts.values()) / len(selected))
