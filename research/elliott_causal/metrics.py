"""Technical research metrics (E00 prompt section 10). No economic metric:
no return, R-multiple, win rate, profit factor or drawdown is computed."""

from __future__ import annotations

import statistics
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from research.elliott_causal.contracts import (
    CountInvalidated,
    CountSearch,
    EngineConfig,
    PivotConfirmed,
    PriceBar,
)
from research.elliott_causal.frozen import (
    OutcomeClass,
    SnapshotMode,
    fibonacci_snapshot,
    wave_snapshot,
)
from research.elliott_causal.pipeline import Published, prefix_invariance_violations, run_pipeline


def _day(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=UTC).strftime("%Y-%m-%d")


def anchor_continuity_failures(published: Sequence[Published], symbol: str) -> int:
    """Primaries whose frozen Fibonacci anchors or direction differ from W1."""
    failures = 0
    for item in published:
        event = item.event
        if not isinstance(event, CountSearch) or event.primary is None:
            continue
        ws = wave_snapshot(event, symbol, "H1", SnapshotMode.FAITHFUL)
        fs = fibonacci_snapshot(event.primary, event.available_ms, symbol, "H1")
        w1 = ws.analysis.primary.sequence.waves[0]
        bullish = w1.direction == "UP"
        same = (
            fs.retracement.start_price == w1.start_price
            and fs.retracement.end_price == w1.end_price
            and fs.extension.start_price == w1.start_price
            and fs.extension.end_price == w1.end_price
            and (fs.direction.value == "BULLISH") is bullish
            and fs.retracement.direction is fs.direction
        )
        failures += 0 if same else 1
    return failures


def technical_metrics(
    bars: Sequence[PriceBar], symbol: str, config: EngineConfig, *, check_prefix: bool = True
) -> dict[str, Any]:
    published = run_pipeline(bars, symbol=symbol, config=config)
    pivots = [p.event.pivot for p in published if isinstance(p.event, PivotConfirmed)]
    searches = [p for p in published if isinstance(p.event, CountSearch)]
    latencies = [p.latency_bars for p in pivots]
    rejections: Counter[str] = Counter()
    outcomes: Counter[str] = Counter()
    restrictions: Counter[str] = Counter()
    per_day: Counter[str] = Counter()
    for item in searches:
        event = item.event
        assert isinstance(event, CountSearch)
        for reason, n in event.rejections:
            rejections[reason.value] += n
        per_day[_day(event.available_ms)] += event.eligible
        for q in item.qualifications:
            outcomes[f"{q.mode.value}:{q.outcome.value}"] += 1
            if q.outcome is not OutcomeClass.C_ACCEPTED and q.restriction:
                restrictions[f"{q.mode.value}:{q.restriction}"] += 1
    with_primary = [s for s in searches if isinstance(s.event, CountSearch) and s.event.primary]
    enumerated = [s.event.enumerated for s in searches if isinstance(s.event, CountSearch)]
    violations = (
        prefix_invariance_violations(
            lambda b: run_pipeline(b, symbol=symbol, config=config), bars, range(len(bars))
        )
        if check_prefix
        else None
    )
    return {
        "bars": len(bars),
        "observation_start_utc": _iso(bars[0].start_ms) if bars else None,
        "observation_end_utc": _iso(bars[-1].end_ms) if bars else None,
        "confirmed_pivots": len(pivots),
        "pivot_confirmation_latency_bars": {
            "min": min(latencies, default=0),
            "median": statistics.median(latencies) if latencies else 0,
            "max": max(latencies, default=0),
        },
        "count_searches": len(searches),
        "searches_with_eligible_count": len(with_primary),
        "eligible_w1w2_candidates": sum(
            s.event.eligible for s in searches if isinstance(s.event, CountSearch)
        ),
        "eligible_candidates_per_utc_day": dict(sorted(per_day.items())),
        "count_search_complexity": {
            "window_pivots": config.window_pivots,
            "enumerated_pairs_total": sum(enumerated),
            "enumerated_pairs_max": max(enumerated, default=0),
        },
        "rejection_categories": dict(sorted(rejections.items())),
        "frozen_f01_outcomes": dict(sorted(outcomes.items())),
        "frozen_f01_restrictions": dict(sorted(restrictions.items())),
        "invalidations": sum(1 for p in published if isinstance(p.event, CountInvalidated)),
        "anchor_continuity_failures": anchor_continuity_failures(published, symbol),
        "prefix_invariance": (
            None
            if violations is None
            else {"checked_bars": len(bars), "violations": len(violations)}
        ),
    }


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
