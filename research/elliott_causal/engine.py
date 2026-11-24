"""Event-driven causal swing producer and rolling W1/W2 count search.

Causality rules (G00 sections 11 and 12):

- the ATR and every threshold use bars up to and including the current closed
  bar only;
- a pivot is confirmed only on a bar **after** its extreme bar, when price has
  reversed by ``threshold_atr * ATR`` from the running extreme; a bar that both
  makes a new extreme and reverses is resolved conservatively (the extreme
  moves, no confirmation), because the intrabar order is unknown;
- every event is stamped with the close of the bar that produced it and is
  never rewritten; a later confirmation is a new event;
- the count search runs only when a W2-ending pivot confirms and reads only the
  last ``window_pivots`` confirmed pivots, never the first swings of history.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from research.elliott_causal.contracts import (
    CountCandidate,
    CountInvalidated,
    CountSearch,
    Direction,
    EngineConfig,
    Event,
    InvalidationReason,
    Pivot,
    PivotConfirmed,
    PivotKind,
    PriceBar,
    RejectionReason,
    require,
)

_FIB_TARGET = 0.618


@dataclass(slots=True)
class _Extreme:
    price: float
    index: int
    start_ms: int


def research_scale(atr_multiple: float, threshold_atr: float) -> int:
    """Amplitude scale: 0 for one threshold, +1 per doubling (research label)."""
    ratio = atr_multiple / threshold_atr
    return 0 if ratio < 2.0 else math.floor(math.log2(ratio))


def count_identity(direction: Direction, a: Pivot, b: Pivot, c: Pivot) -> str:
    text = "|".join(
        f"{p.kind.value}:{p.sequence}:{p.extreme_index}:{p.price!r}:{p.available_index}"
        for p in (a, b, c)
    )
    return hashlib.sha256(f"e00-count/1|{direction.value}|{text}".encode()).hexdigest()[:24]


class CausalElliottEngine:
    """Incremental engine: feed closed bars in order with :meth:`push`."""

    def __init__(self, config: EngineConfig | None = None) -> None:
        self.config = config or EngineConfig()
        self._next_index = 0
        self._last_end_ms: int | None = None
        self._prev_close: float | None = None
        self._tr_seed: list[float] = []
        self._atr: float | None = None
        self._leg: PivotKind | None = None  # kind of the pivot the current leg will produce
        self._extreme: _Extreme | None = None
        self._hi: _Extreme | None = None
        self._lo: _Extreme | None = None
        self._pivots: list[Pivot] = []
        self._active: dict[Direction, tuple[CountCandidate, ...]] = {
            Direction.UP: (),
            Direction.DOWN: (),
        }

    @property
    def pivots(self) -> tuple[Pivot, ...]:
        return tuple(self._pivots)

    # ------------------------------------------------------------------ ATR
    def _update_atr(self, bar: PriceBar) -> None:
        if self._prev_close is None:
            tr = bar.high - bar.low
        else:
            tr = max(
                bar.high - bar.low,
                abs(bar.high - self._prev_close),
                abs(bar.low - self._prev_close),
            )
        self._prev_close = bar.close
        period = self.config.atr_period
        if self._atr is None:
            self._tr_seed.append(tr)
            if len(self._tr_seed) == period:
                self._atr = sum(self._tr_seed) / period
        else:
            self._atr = (self._atr * (period - 1) + tr) / period

    # ----------------------------------------------------------------- push
    def push(self, bar: PriceBar) -> tuple[Event, ...]:
        require(type(bar) is PriceBar, "push expects a PriceBar")
        require(bar.index == self._next_index, "bars must be pushed in index order without gaps")
        require(
            self._last_end_ms is None or bar.start_ms >= self._last_end_ms,
            "bars must be strictly increasing in time",
        )
        self._next_index += 1
        self._last_end_ms = bar.end_ms
        self._update_atr(bar)
        events: list[Event] = list(self._invalidations(bar))
        pivot = self._advance_leg(bar)
        if pivot is not None:
            events.extend((PivotConfirmed(bar.index, bar.end_ms, pivot), self._search(pivot)))
        return tuple(events)

    def run(self, bars: Iterable[PriceBar]) -> tuple[Event, ...]:
        out: list[Event] = []
        for bar in bars:
            out.extend(self.push(bar))
        return tuple(out)

    # --------------------------------------------------------- invalidation
    def _invalidations(self, bar: PriceBar) -> Iterable[CountInvalidated]:
        for direction in (Direction.UP, Direction.DOWN):
            kept: list[CountCandidate] = []
            for count in self._active[direction]:
                origin = count.w1_start.price
                breached = bar.low <= origin if direction is Direction.UP else bar.high >= origin
                if breached:
                    yield CountInvalidated(
                        bar.index, bar.end_ms, count.count_id, InvalidationReason.W1_ORIGIN_BREACHED
                    )
                else:
                    kept.append(count)
            self._active[direction] = tuple(kept)

    # ------------------------------------------------------------- zig-zag
    def _confirm(self, kind: PivotKind, extreme: _Extreme, bar: PriceBar) -> Pivot:
        assert self._atr is not None
        pivot = Pivot(
            len(self._pivots),
            kind,
            extreme.price,
            extreme.index,
            extreme.start_ms,
            bar.index,
            bar.end_ms,
            self._atr,
        )
        self._pivots.append(pivot)
        return pivot

    def _advance_leg(self, bar: PriceBar) -> Pivot | None:
        high = _Extreme(bar.high, bar.index, bar.start_ms)
        low = _Extreme(bar.low, bar.index, bar.start_ms)
        if self._leg is None:
            self._hi = high if self._hi is None or bar.high > self._hi.price else self._hi
            self._lo = low if self._lo is None or bar.low < self._lo.price else self._lo
            if self._atr is None:
                return None
            hi, lo = self._hi, self._lo
            assert hi is not None and lo is not None
            if hi.price - lo.price < self.config.threshold_atr * self._atr:
                return None
            if hi.index == lo.index:
                return None  # outside bar: intrabar order unknown, wait
            if hi.index < lo.index:
                self._leg, self._extreme = PivotKind.LOW, lo
                return self._confirm(PivotKind.HIGH, hi, bar)
            self._leg, self._extreme = PivotKind.HIGH, hi
            return self._confirm(PivotKind.LOW, lo, bar)
        assert self._extreme is not None and self._atr is not None
        threshold = self.config.threshold_atr * self._atr
        if self._leg is PivotKind.HIGH:
            if bar.high > self._extreme.price:
                self._extreme = high
                return None
            if self._extreme.price - bar.low >= threshold:
                confirmed = self._extreme
                self._leg, self._extreme = PivotKind.LOW, low
                return self._confirm(PivotKind.HIGH, confirmed, bar)
            return None
        if bar.low < self._extreme.price:
            self._extreme = low
            return None
        if bar.high - self._extreme.price >= threshold:
            confirmed = self._extreme
            self._leg, self._extreme = PivotKind.HIGH, high
            return self._confirm(PivotKind.LOW, confirmed, bar)
        return None

    # -------------------------------------------------------- count search
    def _search(self, c: Pivot) -> CountSearch:
        direction = Direction.UP if c.kind is PivotKind.LOW else Direction.DOWN
        window = self._pivots[-self.config.window_pivots :]
        candidates, enumerated, rejections = search_counts(window, c, direction, self.config)
        primary = candidates[0] if candidates else None
        alternates = tuple(candidates[1 : 1 + self.config.max_alternates])
        self._active[direction] = tuple(candidates[: 1 + self.config.max_alternates])
        return CountSearch(
            c.available_index,
            c.available_ms,
            direction,
            c.sequence,
            tuple(p.sequence for p in window),
            enumerated,
            tuple(sorted(rejections.items())),
            primary,
            alternates,
            len(candidates),
        )


def search_counts(
    window: Sequence[Pivot], c: Pivot, direction: Direction, config: EngineConfig
) -> tuple[tuple[CountCandidate, ...], int, Counter[RejectionReason]]:
    """Enumerate every (W1 start, W1 end) pair before ``c`` inside ``window``.

    Hard rules, in order (first failure is recorded): W1 moves in
    ``direction``; W1 start is the most extreme opposite point of W1; W1 end is
    the most extreme point from W1 start to W2 end; W2 end is the most extreme
    point of W2; W2 never retraces beyond W1 origin (100 %); degree scales of W1
    and W2 differ by at most ``max_degree_gap``.
    """
    require(window[-1] is c, "the W2 end must be the newest pivot of the window")
    up = direction is Direction.UP
    start_kind = PivotKind.LOW if up else PivotKind.HIGH
    sign = 1.0 if up else -1.0
    rejections: Counter[RejectionReason] = Counter()
    eligible: list[tuple[Pivot, Pivot, float, float, float, int, int]] = []
    enumerated = 0
    positions = range(len(window) - 1)
    for j in positions:
        b = window[j]
        if b.kind is start_kind:
            continue
        for i in range(j):
            a = window[i]
            if a.kind is not start_kind:
                continue
            enumerated += 1
            reason = _first_violation(window, i, j, sign, config, c)
            if reason is not None:
                rejections[reason] += 1
                continue
            w1 = sign * (b.price - a.price)
            w2 = sign * (b.price - c.price)
            w1_atr, w2_atr = w1 / c.atr, w2 / c.atr
            eligible.append(
                (
                    a,
                    b,
                    w2 / w1,
                    w1_atr,
                    w2_atr,
                    research_scale(w1_atr, config.threshold_atr),
                    research_scale(w2_atr, config.threshold_atr),
                )
            )
    if not eligible:
        return (), enumerated, rejections
    largest = max(item[3] for item in eligible)
    built = [
        CountCandidate(
            count_identity(direction, a, b, c),
            direction,
            a,
            b,
            c,
            r,
            w1_atr,
            w2_atr,
            s1,
            s2,
            _score(r, w1_atr, largest),
        )
        for a, b, r, w1_atr, w2_atr, s1, s2 in eligible
    ]
    built.sort(
        key=lambda x: (
            -x.research_score,
            -x.w1_atr_multiple,
            -x.w1_start.sequence,
            -x.w1_end.sequence,
        )
    )
    return tuple(built), enumerated, rejections


def _score(retracement: float, w1_atr: float, largest: float) -> float:
    """Uncalibrated ranking score in [0, 1]: Fibonacci proximity and W1 size."""
    proximity = 1.0 - min(abs(retracement - _FIB_TARGET) / _FIB_TARGET, 1.0)
    return 0.5 * proximity + 0.5 * (w1_atr / largest)


def _first_violation(
    window: Sequence[Pivot], i: int, j: int, sign: float, config: EngineConfig, c: Pivot
) -> RejectionReason | None:
    a, b = window[i], window[j]
    if sign * (b.price - a.price) <= 0.0:
        return RejectionReason.W1_NOT_DIRECTIONAL
    if any(sign * (p.price - a.price) < 0.0 for p in window[i + 1 : j + 1]):
        return RejectionReason.W1_START_NOT_EXTREME
    if any(sign * (p.price - b.price) > 0.0 for p in window[i : len(window)] if p is not b):
        return RejectionReason.W1_END_NOT_EXTREME
    if any(sign * (p.price - c.price) < 0.0 for p in window[j + 1 : len(window) - 1]):
        return RejectionReason.W2_END_NOT_EXTREME
    if sign * (c.price - a.price) <= 0.0:
        return RejectionReason.W2_BEYOND_W1_ORIGIN
    w1_atr = sign * (b.price - a.price) / c.atr
    w2_atr = sign * (b.price - c.price) / c.atr
    gap = research_scale(w1_atr, config.threshold_atr) - research_scale(
        w2_atr, config.threshold_atr
    )
    if abs(gap) > config.max_degree_gap:
        return RejectionReason.DEGREE_INCONSISTENT
    return None
