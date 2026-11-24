"""Research pipeline: causal events plus frozen F01 qualification, and the
prefix-invariance checker (G00 section 12, blocking)."""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from research.elliott_causal.contracts import (
    CountSearch,
    EngineConfig,
    Event,
    PriceBar,
    require,
)
from research.elliott_causal.engine import CausalElliottEngine
from research.elliott_causal.frozen import Qualification, SnapshotMode, qualify

HOUR_MS = 3_600_000


@dataclass(frozen=True, slots=True)
class Published:
    """Everything published at ``available_index``: one research event and,
    for a count search with a primary, its frozen F01 outcome in both modes."""

    available_index: int
    event: Event
    qualifications: tuple[Qualification, ...]


def run_pipeline(
    bars: Sequence[PriceBar],
    *,
    symbol: str = "EURUSD",
    timeframe: str = "H1",
    config: EngineConfig | None = None,
    qualify_counts: bool = True,
) -> tuple[Published, ...]:
    engine = CausalElliottEngine(config)
    out: list[Published] = []
    for bar in bars:
        for event in engine.push(bar):
            outcomes: tuple[Qualification, ...] = ()
            if qualify_counts and isinstance(event, CountSearch) and event.primary is not None:
                outcomes = tuple(
                    qualify(event, symbol, timeframe, mode)
                    for mode in (SnapshotMode.FAITHFUL, SnapshotMode.PRIMARY_ONLY)
                )
            out.append(Published(event.available_index, event, outcomes))
    return tuple(out)


Producer = Callable[[Sequence[PriceBar]], tuple[Published, ...]]


def prefix_invariance_violations(
    producer: Producer, bars: Sequence[PriceBar], checkpoints: Sequence[int]
) -> tuple[int, ...]:
    """Bars ``t`` whose truncated-series output differs from what the full
    series published up to ``t``. Empty means 100 % prefix invariance."""
    full = producer(bars)
    violations = []
    for t in checkpoints:
        require(0 <= t < len(bars), "checkpoint outside the series")
        truncated = producer(bars[: t + 1])
        expected = tuple(item for item in full if item.available_index <= t)
        if truncated != expected:
            violations.append(t)
    return tuple(violations)


def generated_bars(
    count: int, seed: int, *, start_ms: int = 1_331_510_400_000, base: float = 1.3
) -> tuple[PriceBar, ...]:
    """Deterministic synthetic H1 series (random walk with volatility regimes)."""
    rng = random.Random(seed)
    price = base
    out: list[PriceBar] = []
    vol = 0.0015
    for i in range(count):
        if rng.random() < 0.02:
            vol = rng.choice((0.0008, 0.0015, 0.003))
        drift = rng.gauss(0.0, vol)
        open_ = price
        close = max(open_ * (1.0 + drift), 1e-6)
        wick = abs(rng.gauss(0.0, vol * 0.6))
        high = max(open_, close) * (1.0 + wick)
        low = min(open_, close) * (1.0 - abs(rng.gauss(0.0, vol * 0.6)))
        out.append(
            PriceBar(
                i, start_ms + i * HOUR_MS, start_ms + (i + 1) * HOUR_MS, open_, high, low, close
            )
        )
        price = close
    return tuple(out)
