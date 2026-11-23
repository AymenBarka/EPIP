"""Deterministic UTC bar derivation from ticks, one price side at a time.

Intervals are half-open ``[start, end)``; a tick exactly on a boundary belongs
to the next interval. Intervals without ticks produce no bar. A bar is
COMPLETE only when every source hour it spans is POPULATED or an
EXPECTED_CLOSURE; otherwise it is INCOMPLETE. Tick count is the number of
contributing records; quoted volumes are never aggregated as trade volume.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from research.datasets.contracts import (
    COMPLETE_HOUR_STATUSES,
    MS_PER_HOUR,
    Bar,
    BarCoverage,
    Granularity,
    HourStatus,
    PriceSide,
    Tick,
    require,
)

INTERVAL_HOURS = {Granularity.H1: 1, Granularity.H4: 4}


def interval_start(timestamp_ms: int, granularity: Granularity) -> int:
    span = INTERVAL_HOURS[granularity] * MS_PER_HOUR
    return timestamp_ms - timestamp_ms % span


def aggregate(
    ticks: Sequence[Tick],
    side: PriceSide,
    granularity: Granularity,
    hour_status: Mapping[int, HourStatus],
) -> tuple[Bar, ...]:
    require(type(side) is PriceSide, "side invalid")
    require(granularity in INTERVAL_HOURS, "granularity must be H1 or H4")
    hours = INTERVAL_HOURS[granularity]
    span = hours * MS_PER_HOUR
    groups: dict[int, list[int]] = {}
    previous = -1
    for tick in ticks:
        require(tick.timestamp_ms >= previous, "ticks must be in chronological order")
        previous = tick.timestamp_ms
        hour = tick.timestamp_ms - tick.timestamp_ms % MS_PER_HOUR
        require(
            hour_status.get(hour) is HourStatus.POPULATED,
            "tick belongs to an hour not classified POPULATED",
        )
        price = tick.bid_points if side is PriceSide.BID else tick.ask_points
        groups.setdefault(tick.timestamp_ms - tick.timestamp_ms % span, []).append(price)
    bars: list[Bar] = []
    for start in sorted(groups):
        prices = groups[start]
        spanned = [start + i * MS_PER_HOUR for i in range(hours)]
        complete = all(hour_status.get(h) in COMPLETE_HOUR_STATUSES for h in spanned)
        bars.append(
            Bar(
                start,
                start + span,
                side,
                prices[0],
                max(prices),
                min(prices),
                prices[-1],
                len(prices),
                BarCoverage.COMPLETE if complete else BarCoverage.INCOMPLETE,
            )
        )
    return tuple(bars)
