"""E00 causal swing producer and W1/W2 count search (requirements 1-11, 17, 18, 20, 21)."""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from itertools import pairwise

import pytest

from research.elliott_causal.contracts import (
    CountCandidate,
    CountInvalidated,
    CountSearch,
    Direction,
    EngineConfig,
    InvalidationReason,
    Pivot,
    PivotKind,
    PriceBar,
    RejectionReason,
    ResearchContractError,
)
from research.elliott_causal.engine import (
    CausalElliottEngine,
    count_identity,
    research_scale,
    search_counts,
)
from research.elliott_causal.pipeline import (
    HOUR_MS,
    Published,
    generated_bars,
    prefix_invariance_violations,
    run_pipeline,
)
from research.tests.e00_fixtures import (
    TIGHT,
    UP_MIDS,
    bars_from_mids,
    mirrored,
    pivot,
    pivots_of,
    searches_of,
)

SEEDS = (1, 2, 3, 5, 8)


def engine_events(bars: tuple[PriceBar, ...], config: EngineConfig = TIGHT) -> tuple[object, ...]:
    return CausalElliottEngine(config).run(bars)


# 2. pivot confirmation latency -------------------------------------------------
def test_handcrafted_pivots_are_confirmed_one_bar_after_their_extreme() -> None:
    bars = bars_from_mids(UP_MIDS)
    events = CausalElliottEngine(TIGHT).run(bars)
    got = [(p.kind, p.price, p.extreme_index, p.available_index) for p in pivots_of(events)]
    assert got == [
        (PivotKind.HIGH, 100.25, 0, 1),
        (PivotKind.LOW, 89.75, 5, 6),
        (PivotKind.HIGH, 110.25, 15, 16),
        (PivotKind.LOW, 99.75, 20, 21),
    ]
    for p in pivots_of(events):
        assert p.latency_bars == 1
        assert p.available_ms == bars[p.available_index].end_ms
        assert p.extreme_start_ms == bars[p.extreme_index].start_ms


@pytest.mark.parametrize("seed", SEEDS)
def test_every_pivot_is_available_strictly_after_its_extreme(seed: int) -> None:
    bars = generated_bars(1500, seed)
    events = CausalElliottEngine().run(bars)
    pivots = pivots_of(events)
    assert len(pivots) > 20
    for p in pivots:
        assert p.available_index > p.extreme_index
        assert p.available_ms == bars[p.available_index].end_ms
    for event in events:
        assert event.available_ms == bars[event.available_index].end_ms


def test_pivot_contract_refuses_same_bar_availability() -> None:
    with pytest.raises(ResearchContractError, match="never available on its extreme bar"):
        Pivot(0, PivotKind.HIGH, 1.0, 5, 0, 5, HOUR_MS, 1.0)


# 1. no future-bar access, 3. swing prefix invariance, 7 (G00) blocking criterion
@pytest.mark.parametrize("seed", SEEDS)
def test_prefix_invariance_on_every_bar_including_frozen_outcomes(seed: int) -> None:
    bars = generated_bars(260, seed)
    violations = prefix_invariance_violations(run_pipeline, bars, range(len(bars)))
    assert violations == ()
    assert any(p.qualifications for p in run_pipeline(bars))


@pytest.mark.parametrize("seed", (13, 21))
def test_prefix_invariance_on_long_series_at_sampled_bars(seed: int) -> None:
    bars = generated_bars(2500, seed)
    checkpoints = sorted({min(len(bars) - 1, (i * 7919) % len(bars)) for i in range(60)})
    assert prefix_invariance_violations(run_pipeline, bars, checkpoints) == ()


def test_future_bars_never_change_published_output() -> None:
    bars = generated_bars(400, 4)
    cut = 250
    adversarial = list(bars[: cut + 1])
    for i in range(cut + 1, 400):  # violent alternative future
        price = 0.5 if i % 2 else 3.0
        prev_end = adversarial[-1].end_ms
        adversarial.append(PriceBar(i, prev_end, prev_end + HOUR_MS, price, price, price, price))
    original = [p for p in run_pipeline(bars) if p.available_index <= cut]
    other = [p for p in run_pipeline(tuple(adversarial)) if p.available_index <= cut]
    assert original == other


def test_intentional_look_ahead_control_is_flagged() -> None:
    bars = generated_bars(120, 9)

    def leaky(series: Sequence[PriceBar]) -> tuple[Published, ...]:
        published = run_pipeline(series)
        # backdates every event to the extreme bar of the series' last pivot
        last = len(series) - 1
        return tuple(Published(min(p.available_index, last // 2), p.event, ()) for p in published)

    assert prefix_invariance_violations(leaky, bars, range(30, 120)) != ()


# 4. repeated confirmation stability -----------------------------------------------
@pytest.mark.parametrize("seed", SEEDS)
def test_each_pivot_is_confirmed_once_and_kinds_alternate(seed: int) -> None:
    pivots = pivots_of(CausalElliottEngine().run(generated_bars(1500, seed)))
    assert [p.sequence for p in pivots] == list(range(len(pivots)))
    assert all(a.kind is not b.kind for a, b in pairwise(pivots))
    extremes = [p.extreme_index for p in pivots]
    assert extremes == sorted(set(extremes))
    available = [p.available_index for p in pivots]
    assert available == sorted(set(available))


def test_outside_bar_does_not_confirm_until_order_is_known() -> None:
    config = EngineConfig(atr_period=2, threshold_atr=1.0)
    bars = [
        PriceBar(0, 0, HOUR_MS, 100.0, 100.5, 99.5, 100.0),
        PriceBar(1, HOUR_MS, 2 * HOUR_MS, 100.0, 104.0, 96.0, 100.0),  # new high and new low
        PriceBar(2, 2 * HOUR_MS, 3 * HOUR_MS, 100.0, 100.5, 99.5, 100.0),
        PriceBar(3, 3 * HOUR_MS, 4 * HOUR_MS, 100.0, 105.0, 99.8, 104.8),
    ]
    events = CausalElliottEngine(config).run(bars)
    pivots = pivots_of(events)
    assert len(pivots) == 1
    assert (pivots[0].kind, pivots[0].extreme_index, pivots[0].available_index) == (
        PivotKind.LOW,
        1,
        3,
    )


def test_extreme_bar_that_also_reverses_moves_the_extreme_first() -> None:
    mids = (100.0, 102.0, 104.0, 106.0, 108.0)
    bars = list(bars_from_mids(mids))
    prev_end = bars[-1].end_ms
    bars.extend(
        (
            PriceBar(5, prev_end, prev_end + HOUR_MS, 108.0, 112.0, 101.0, 102.0),
            PriceBar(6, prev_end + HOUR_MS, prev_end + 2 * HOUR_MS, 102.0, 102.5, 100.0, 100.5),
        )
    )
    pivots = pivots_of(CausalElliottEngine(TIGHT).run(tuple(bars)))
    assert [(p.kind, p.price, p.extreme_index, p.available_index) for p in pivots][-1] == (
        PivotKind.HIGH,
        112.0,
        5,
        6,
    )


# 5. rolling window -------------------------------------------------------------------
@pytest.mark.parametrize("seed", SEEDS)
def test_search_reads_only_the_recent_window_never_the_first_swings(seed: int) -> None:
    config = EngineConfig(window_pivots=8)
    events = CausalElliottEngine(config).run(generated_bars(3000, seed))
    pivots = pivots_of(events)
    for search in searches_of(events):
        expected = tuple(range(max(0, search.w2_end_sequence - 7), search.w2_end_sequence + 1))
        assert search.window_sequences == expected
        for count in (search.primary, *search.alternates):
            if count is not None:
                assert count.w1_start.sequence >= search.window_sequences[0]
    late = [s for s in searches_of(events) if s.primary and s.w2_end_sequence > 100]
    assert late, "counts keep appearing deep into a growing history"
    assert len(pivots) > 100


def test_count_search_enumeration_is_bounded_by_the_window() -> None:
    config = EngineConfig(window_pivots=10)
    for search in searches_of(CausalElliottEngine(config).run(generated_bars(3000, 3))):
        assert search.enumerated <= 4 * 5  # at most 5 starts x 5 ends in 10 alternating pivots


# 6. geometry, 7. direction, 9. degree, 18. multiple counts ----------------------------
def _check_geometry(count: CountCandidate, window: tuple[Pivot, ...]) -> None:
    sign = 1.0 if count.direction is Direction.UP else -1.0
    a, b, c = count.w1_start, count.w1_end, count.w2_end
    assert sign * (b.price - a.price) > 0 and sign * (c.price - a.price) > 0
    assert count.retracement == pytest.approx((b.price - c.price) / (b.price - a.price))
    inside = [p for p in window if a.sequence <= p.sequence <= c.sequence]
    assert all(sign * (p.price - b.price) <= 0 for p in inside)
    assert all(sign * (p.price - a.price) >= 0 for p in inside if p.sequence <= b.sequence)
    assert all(sign * (p.price - c.price) >= 0 for p in inside if p.sequence >= b.sequence)
    assert c.kind is (PivotKind.LOW if count.direction is Direction.UP else PivotKind.HIGH)
    assert abs(count.w1_scale - count.w2_scale) <= 1


@pytest.mark.parametrize("seed", SEEDS)
def test_every_eligible_count_satisfies_geometry_direction_and_degree(seed: int) -> None:
    engine = CausalElliottEngine()
    events = engine.run(generated_bars(2000, seed))
    by_seq = {p.sequence: p for p in engine.pivots}
    multi = 0
    for search in searches_of(events):
        window = tuple(by_seq[s] for s in search.window_sequences)
        counts = tuple(x for x in (search.primary, *search.alternates) if x is not None)
        assert len(search.alternates) <= engine.config.max_alternates
        assert search.eligible >= len(counts)
        multi += search.eligible > 1
        for count in counts:
            assert count.direction is search.direction
            _check_geometry(count, window)
    assert multi > 0


def test_handcrafted_up_and_mirrored_down_counts() -> None:
    for mids, direction in ((UP_MIDS, Direction.UP), (mirrored(UP_MIDS), Direction.DOWN)):
        searches = searches_of(CausalElliottEngine(TIGHT).run(bars_from_mids(mids)))
        primary = searches[-1].primary
        assert primary is not None and primary.direction is direction
        assert primary.retracement == pytest.approx(10.5 / 20.5)
        assert (primary.w1_scale, primary.w2_scale) == (3, 2)
        assert searches[-1].available_index == 21


# 10. deterministic ordering, 20. determinism, 21. concurrency/immutability ----------
@pytest.mark.parametrize("seed", SEEDS)
def test_candidates_are_ranked_with_deterministic_tie_breaking(seed: int) -> None:
    for search in searches_of(CausalElliottEngine().run(generated_bars(2000, seed))):
        ranked = tuple(x for x in (search.primary, *search.alternates) if x is not None)
        keys = [
            (-x.research_score, -x.w1_atr_multiple, -x.w1_start.sequence, -x.w1_end.sequence)
            for x in ranked
        ]
        assert keys == sorted(keys)
        assert len({x.count_id for x in ranked}) == len(ranked)


def test_tie_break_prefers_recent_anchors() -> None:
    cfg = EngineConfig(threshold_atr=1.0)
    window = (
        pivot(0, PivotKind.LOW, 10.0),
        pivot(1, PivotKind.HIGH, 20.0),
        pivot(2, PivotKind.LOW, 10.0),
        pivot(3, PivotKind.HIGH, 20.0),
        pivot(4, PivotKind.LOW, 13.82),
    )
    counts, enumerated, rejections = search_counts(window, window[-1], Direction.UP, cfg)
    assert enumerated == 3
    # equal geometry and score: the most recent W1 start ranks first
    assert [(c.w1_start.sequence, c.w1_end.sequence) for c in counts] == [(2, 3), (0, 3)]
    assert counts[0].research_score == counts[1].research_score
    assert dict(rejections) == {RejectionReason.W2_END_NOT_EXTREME: 1}


def test_same_input_same_output_and_thread_safety() -> None:
    bars = generated_bars(1200, 6)
    reference = run_pipeline(bars)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: run_pipeline(bars), range(8)))
    assert all(r == reference for r in results)
    event = reference[0].event
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.available_index = 0  # type: ignore[misc]


# 8. W2 non-invalidation and explicit invalidations ----------------------------------
def test_breach_of_w1_origin_emits_a_new_invalidation_event() -> None:
    mids = UP_MIDS + (112, 108, 104, 100, 96, 92, 88, 86)
    bars = bars_from_mids(mids)
    events = CausalElliottEngine(TIGHT).run(bars)
    counts = [s.primary for s in searches_of(events) if s.primary is not None]
    invalidations = [e for e in events if isinstance(e, CountInvalidated)]
    assert counts and invalidations
    first = counts[0]
    breach = next(i for i in invalidations if i.count_id == first.count_id)
    assert breach.reason is InvalidationReason.W1_ORIGIN_BREACHED
    assert bars[breach.available_index].low <= first.w1_start.price
    assert all(b.low > first.w1_start.price for b in bars[21 : breach.available_index])
    published_before = [e for e in events if e.available_index < breach.available_index]
    assert published_before == [
        e for e in CausalElliottEngine(TIGHT).run(bars[: breach.available_index])
    ]


# 11. hard-rule rejection ---------------------------------------------------------------
@pytest.mark.parametrize(
    ("prices", "reason"),
    [
        ((10.0, 9.0, 9.5), RejectionReason.W1_NOT_DIRECTIONAL),
        ((10.0, 20.0, 9.0, 18.0, 15.0), RejectionReason.W1_START_NOT_EXTREME),
        ((10.0, 20.0, 12.0, 25.0, 15.0), RejectionReason.W1_END_NOT_EXTREME),
        ((10.0, 20.0, 12.0, 18.0, 15.0), RejectionReason.W2_END_NOT_EXTREME),
        ((10.0, 20.0, 9.0), RejectionReason.W2_BEYOND_W1_ORIGIN),
        ((10.0, 20.0, 10.0), RejectionReason.W2_BEYOND_W1_ORIGIN),
        ((10.0, 74.0, 72.0), RejectionReason.DEGREE_INCONSISTENT),
    ],
)
def test_each_hard_rule_rejects_with_its_reason(
    prices: tuple[float, ...], reason: RejectionReason
) -> None:
    kinds = [PivotKind.LOW if i % 2 == 0 else PivotKind.HIGH for i in range(len(prices))]
    window = tuple(pivot(i, k, p) for i, (k, p) in enumerate(zip(kinds, prices, strict=True)))
    cfg = EngineConfig(threshold_atr=1.0)
    counts, enumerated, rejections = search_counts(window, window[-1], Direction.UP, cfg)
    first_pair = (window[0], window[1])
    assert enumerated >= 1
    assert rejections[reason] >= 1
    assert all((c.w1_start, c.w1_end) != first_pair for c in counts)


# 17. zero eligible counts -------------------------------------------------------------
def test_zero_eligible_counts_are_published_explicitly() -> None:
    searches = searches_of(CausalElliottEngine(TIGHT).run(bars_from_mids(UP_MIDS)))
    empty = [s for s in searches if s.primary is None]
    assert empty and all(s.alternates == () and s.eligible == 0 for s in empty)
    published = [p for p in run_pipeline(bars_from_mids(UP_MIDS), config=TIGHT)]
    assert all(
        p.qualifications == ()
        for p in published
        if isinstance(p.event, CountSearch) and p.event.primary is None
    )


# contract validation ------------------------------------------------------------------
def test_contracts_fail_closed() -> None:
    with pytest.raises(ResearchContractError):
        PriceBar(0, 0, HOUR_MS, 1.0, 0.9, 0.8, 1.0)
    with pytest.raises(ResearchContractError):
        PriceBar(0, HOUR_MS, HOUR_MS, 1.0, 1.0, 1.0, 1.0)
    with pytest.raises(ResearchContractError):
        PriceBar(0, 0, HOUR_MS, float("nan"), 1.0, 1.0, 1.0)
    for bad in (
        {"atr_period": 1},
        {"threshold_atr": 0.0},
        {"window_pivots": 2},
        {"max_alternates": 17},
        {"max_degree_gap": -1},
    ):
        with pytest.raises(ResearchContractError):
            EngineConfig(**bad)
    engine = CausalElliottEngine()
    bars = generated_bars(3, 1)
    with pytest.raises(ResearchContractError, match="index order"):
        engine.push(bars[1])
    engine.push(bars[0])
    with pytest.raises(ResearchContractError, match="increasing in time"):
        engine.push(PriceBar(1, bars[0].start_ms, bars[0].end_ms, 1.3, 1.3, 1.3, 1.3))
    with pytest.raises(ResearchContractError, match="PriceBar"):
        engine.push("bar")  # type: ignore[arg-type]
    with pytest.raises(ResearchContractError, match="newest pivot"):
        search_counts(
            (pivot(0, PivotKind.LOW, 1.0), pivot(1, PivotKind.HIGH, 2.0)),
            pivot(2, PivotKind.LOW, 1.5),
            Direction.UP,
            EngineConfig(),
        )
    a, b, c = (
        pivot(0, PivotKind.LOW, 1.0),
        pivot(1, PivotKind.HIGH, 2.0),
        pivot(2, PivotKind.LOW, 1.5),
    )
    good = CountCandidate(
        count_identity(Direction.UP, a, b, c), Direction.UP, a, b, c, 0.5, 1.0, 0.5, 0, 0, 0.5
    )
    for change in ({"retracement": 1.0}, {"research_score": 1.5}, {"w1_start": c}):
        with pytest.raises(ResearchContractError):
            dataclasses.replace(good, **change)


def test_research_scale_doubles() -> None:
    assert [research_scale(x, 3.0) for x in (3.0, 5.9, 6.0, 12.0, 24.0, 47.9)] == [0, 0, 1, 2, 3, 3]
