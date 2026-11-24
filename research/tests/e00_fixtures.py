"""Deterministic fixtures for the E00 causal Elliott tests."""

from __future__ import annotations

from research.elliott_causal.contracts import (
    CountSearch,
    EngineConfig,
    Event,
    Pivot,
    PivotConfirmed,
    PivotKind,
    PriceBar,
)
from research.elliott_causal.pipeline import HOUR_MS

TIGHT = EngineConfig(atr_period=2, threshold_atr=1.0)

# Hand-computed series (mid prices; high = mid + 0.25, low = mid - 0.25):
# HIGH 100.25 @0 (confirmed bar 1), LOW 89.75 @5 (bar 6), HIGH 110.25 @15
# (bar 16), LOW 99.75 @20 (bar 21) -> one UP count W1 89.75 -> 110.25,
# W2 -> 99.75, retracement 10.5 / 20.5.
UP_MIDS: tuple[float, ...] = (100, 98, 96, 94, 92, 90, 92, 94, 96, 98, 100, 102, 104, 106)
UP_MIDS += (108, 110, 108, 106, 104, 102, 100, 102, 104, 106, 108, 110, 112, 114)


def bars_from_mids(mids: tuple[float, ...], *, start_ms: int = 0) -> tuple[PriceBar, ...]:
    out = []
    for i, mid in enumerate(mids):
        m = float(mid)
        out.append(
            PriceBar(
                i, start_ms + i * HOUR_MS, start_ms + (i + 1) * HOUR_MS, m, m + 0.25, m - 0.25, m
            )
        )
    return tuple(out)


def mirrored(mids: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(200.0 - m for m in mids)


def pivots_of(events: tuple[Event, ...]) -> tuple[Pivot, ...]:
    return tuple(e.pivot for e in events if isinstance(e, PivotConfirmed))


def searches_of(events: tuple[Event, ...]) -> tuple[CountSearch, ...]:
    return tuple(e for e in events if isinstance(e, CountSearch))


def pivot(sequence: int, kind: PivotKind, price: float, *, atr: float = 1.0) -> Pivot:
    """Synthetic pivot for direct count-search tests (extreme at 10*seq)."""
    extreme = 10 * sequence
    return Pivot(
        sequence, kind, price, extreme, extreme * HOUR_MS, extreme + 1, (extreme + 2) * HOUR_MS, atr
    )
