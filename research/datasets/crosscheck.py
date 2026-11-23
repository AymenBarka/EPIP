"""Independent comparison of tick-derived H1 bars with Dukascopy H1 candles.

Policy ``xcheck-h1/1``: same provider and same quote stream, so OHLC are
expected to agree exactly; the tolerance is therefore 0 points per field.
Deviations are REPORTED, never corrected, and never alter derived values.
Provider candles with zero volume are provider filler (no quotes) and are
classified separately instead of being compared.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from research.datasets.contracts import (
    Bar,
    BarCoverage,
    PriceSide,
    require,
)
from research.datasets.dukascopy import ProviderCandle

CROSSCHECK_POLICY_VERSION = "xcheck-h1/1"
TOLERANCE_POINTS = 0
_FIELDS = ("open", "high", "low", "close")


@dataclass(frozen=True, slots=True)
class FieldDeviation:
    start_ms: int
    side: PriceSide
    field: str
    derived_points: int
    provider_points: int


@dataclass(frozen=True, slots=True)
class CrossCheckReport:
    policy_version: str
    tolerance_points: int
    window_start_ms: int
    window_end_ms: int
    compared: int
    matched: int
    deviations: tuple[FieldDeviation, ...]
    missing_in_derived: tuple[tuple[int, PriceSide], ...]
    missing_in_provider: tuple[tuple[int, PriceSide], ...]
    provider_filler: tuple[tuple[int, PriceSide], ...]
    incomplete_derived: tuple[tuple[int, PriceSide], ...]

    @property
    def status(self) -> str:
        clean = not (self.deviations or self.missing_in_derived or self.missing_in_provider)
        return "CONSISTENT" if clean else "DEVIATIONS_REPORTED"


def crosscheck_h1(
    derived: Sequence[Bar],
    provider: Sequence[ProviderCandle],
    window_start_ms: int,
    window_end_ms: int,
) -> CrossCheckReport:
    require(window_end_ms > window_start_ms, "cross-check window invalid")

    def inside(t: int) -> bool:
        return window_start_ms <= t < window_end_ms

    ours = {(b.start_ms, b.side): b for b in derived if inside(b.start_ms)}
    require(
        all(b.end_ms - b.start_ms == 3_600_000 for b in ours.values()),
        "cross-check expects H1 bars",
    )
    theirs: dict[tuple[int, PriceSide], ProviderCandle] = {}
    filler: list[tuple[int, PriceSide]] = []
    for c in provider:
        if not inside(c.start_ms):
            continue
        key = (c.start_ms, c.side)
        require(key not in theirs, "duplicate provider candle")
        if c.volume_micro == 0:
            filler.append(key)
        else:
            theirs[key] = c
    deviations: list[FieldDeviation] = []
    matched = 0
    compared = 0
    incomplete: list[tuple[int, PriceSide]] = []
    for key in sorted(set(ours) & set(theirs), key=lambda k: (k[0], k[1].value)):
        bar, candle = ours[key], theirs[key]
        compared += 1
        if bar.coverage is BarCoverage.INCOMPLETE:
            incomplete.append(key)
        pairs = (
            (bar.open_points, candle.open_points),
            (bar.high_points, candle.high_points),
            (bar.low_points, candle.low_points),
            (bar.close_points, candle.close_points),
        )
        local = [
            FieldDeviation(key[0], key[1], name, mine, other)
            for name, (mine, other) in zip(_FIELDS, pairs, strict=True)
            if abs(mine - other) > TOLERANCE_POINTS
        ]
        deviations.extend(local)
        matched += not local

    def order(keys: set[tuple[int, PriceSide]]) -> tuple[tuple[int, PriceSide], ...]:
        return tuple(sorted(keys, key=lambda k: (k[0], k[1].value)))

    filler_set = set(filler)
    return CrossCheckReport(
        CROSSCHECK_POLICY_VERSION,
        TOLERANCE_POINTS,
        window_start_ms,
        window_end_ms,
        compared,
        matched,
        tuple(deviations),
        order(set(theirs) - set(ours)),
        order(set(ours) - set(theirs)),
        order(filler_set),
        tuple(incomplete),
    )
