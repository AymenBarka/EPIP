"""E00 frozen-contract integration (requirements 12-16)."""

from __future__ import annotations

import pytest

from epip.elliott import (
    CountStatus,
    ElliottAnalysis,
    WaveDegree,
    WaveLabel,
    WavePattern,
    WaveSnapshot,
)
from epip.fibonacci import FibonacciDirection, FibonacciSnapshot
from epip.strategy_mapping import RuleIdentity, SemanticRuleDiagnosticCode, SemanticRuleState
from epip.strategy_profiles.elliott_fibonacci import RULE_IDENTITIES, RULE_SET
from research.elliott_causal.contracts import CountSearch, Direction
from research.elliott_causal.engine import CausalElliottEngine
from research.elliott_causal.frozen import (
    OutcomeClass,
    SnapshotMode,
    degree_for,
    fibonacci_snapshot,
    iso,
    qualify,
    wave_snapshot,
)
from research.elliott_causal.metrics import anchor_continuity_failures
from research.elliott_causal.pipeline import generated_bars, run_pipeline
from research.tests.e00_fixtures import TIGHT, UP_MIDS, bars_from_mids, mirrored, searches_of

F01_CHAIN = (
    "extract.elliott",
    "applicability.elliott-wave3",
    "extract.fibonacci",
    "applicability.fibonacci-wave3",
    "select.wave1-anchor",
)


def handcrafted(direction: Direction) -> CountSearch:
    mids = UP_MIDS if direction is Direction.UP else mirrored(UP_MIDS)
    search = searches_of(CausalElliottEngine(TIGHT).run(bars_from_mids(mids)))[-1]
    assert search.primary is not None and search.alternates == ()
    return search


def with_alternates() -> CountSearch:
    for seed in range(1, 20):
        for search in searches_of(CausalElliottEngine().run(generated_bars(1500, seed))):
            if search.alternates:
                return search
    raise AssertionError("no multi-count search found")  # pragma: no cover


# 14. frozen snapshot construction ---------------------------------------------------
@pytest.mark.parametrize("direction", [Direction.UP, Direction.DOWN])
def test_frozen_snapshots_are_built_through_public_constructors(direction: Direction) -> None:
    search = handcrafted(direction)
    ws = wave_snapshot(search, "EURUSD", "H1", SnapshotMode.FAITHFUL)
    assert type(ws) is WaveSnapshot and type(ws.analysis) is ElliottAnalysis
    assert WaveSnapshot.from_json(ws.to_json()) == ws
    primary = ws.analysis.primary
    w1, w2 = primary.sequence.waves
    assert primary.sequence.pattern is WavePattern.UNKNOWN
    assert (w1.label, w2.label) == (WaveLabel.WAVE_1, WaveLabel.WAVE_2)
    assert primary.status is CountStatus.VALID and primary.violations == ()
    assert (primary.probability, primary.confidence) == (0.0, 0.0)  # not estimated
    assert w1.degree is w2.degree is primary.sequence.degree is degree_for(3) is WaveDegree.MINOR
    assert (w2.start_index, w2.start_timestamp, w2.start_price) == (
        w1.end_index,
        w1.end_timestamp,
        w1.end_price,
    )
    assert w1.direction == direction.value and w2.direction != w1.direction
    assert ws.analysis.projection is not None
    assert ws.analysis.projection.next_wave is WaveLabel.WAVE_3
    assert ws.timestamp == iso(search.available_ms)
    fs = fibonacci_snapshot(search.primary, search.available_ms, "EURUSD", "H1")  # type: ignore[arg-type]
    assert type(fs) is FibonacciSnapshot
    assert FibonacciSnapshot.from_json(fs.to_json()) == fs


# 12. anchor equality, 13. direction continuity ---------------------------------------
@pytest.mark.parametrize("direction", [Direction.UP, Direction.DOWN])
def test_fibonacci_anchors_and_direction_follow_w1_exactly(direction: Direction) -> None:
    search = handcrafted(direction)
    assert search.primary is not None
    w1 = wave_snapshot(
        search, "EURUSD", "H1", SnapshotMode.FAITHFUL
    ).analysis.primary.sequence.waves[0]
    fs = fibonacci_snapshot(search.primary, search.available_ms, "EURUSD", "H1")
    assert (fs.retracement.start_price, fs.retracement.end_price) == (w1.start_price, w1.end_price)
    assert (fs.extension.start_price, fs.extension.end_price) == (w1.start_price, w1.end_price)
    expected = (
        FibonacciDirection.BULLISH if direction is Direction.UP else FibonacciDirection.BEARISH
    )
    assert fs.direction is fs.retracement.direction is expected
    golden = next(level for level in fs.retracement.levels if level.label == "0.618")
    assert golden.price == pytest.approx(w1.end_price - 0.618 * (w1.end_price - w1.start_price))


@pytest.mark.parametrize("seed", (1, 2, 3, 5, 8))
def test_anchor_continuity_holds_for_every_published_primary(seed: int) -> None:
    published = run_pipeline(generated_bars(2000, seed))
    assert anchor_continuity_failures(published, "EURUSD") == 0


# 15. frozen F01 acceptance ----------------------------------------------------------
@pytest.mark.parametrize("direction", [Direction.UP, Direction.DOWN])
@pytest.mark.parametrize("mode", list(SnapshotMode))
def test_frozen_f01_chain_accepts_single_count(direction: Direction, mode: SnapshotMode) -> None:
    q = qualify(handcrafted(direction), "EURUSD", "H1", mode)
    assert q.outcome is OutcomeClass.C_ACCEPTED and q.restriction is None
    assert [s.rule for s in q.steps] == list(F01_CHAIN)
    assert all(s.state == "SUCCESS" and s.diagnostics == () for s in q.steps)
    assert q.wave_snapshot_id and q.fibonacci_snapshot_id


# 16. frozen F01 rejection diagnostics -------------------------------------------------
def test_alternates_are_a_documented_frozen_restriction_with_barrier() -> None:
    search = with_alternates()
    faithful = qualify(search, "XAUUSD", "H1", SnapshotMode.FAITHFUL)
    assert faithful.outcome is OutcomeClass.D_FROZEN_RESTRICTION
    assert faithful.restriction is not None and "alternates must be empty" in faithful.restriction
    assert [s.rule for s in faithful.steps] == list(F01_CHAIN[:2])  # barrier: no downstream call
    assert faithful.steps[1].state == "REJECTED"
    assert faithful.steps[1].diagnostics == ("RULE_REJECTED",)
    primary_only = qualify(search, "XAUUSD", "H1", SnapshotMode.PRIMARY_ONLY)
    assert primary_only.outcome is OutcomeClass.C_ACCEPTED
    assert faithful.wave_snapshot_id != primary_only.wave_snapshot_id


def test_unrepresentable_input_is_class_b_not_a_crash() -> None:
    search = handcrafted(Direction.UP)
    q = qualify(search, "", "H1", SnapshotMode.FAITHFUL)
    assert q.outcome is OutcomeClass.B_NOT_REPRESENTABLE and q.steps == ()
    assert q.restriction is not None


def test_each_f01_rejection_stage_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drive each later barrier with frozen-rule results the chain must honour.

    Only the research module's reference is replaced; the frozen RULE_SET
    object itself is never patched.
    """
    from research.elliott_causal import frozen

    search = handcrafted(Direction.UP)

    for failing in F01_CHAIN:

        class Gate:
            def invoke(self, identity: RuleIdentity, request: object, _f: str = failing) -> object:
                result = RULE_SET.invoke(identity, request)
                if identity is RULE_IDENTITIES[_f]:
                    return type(result)(
                        SemanticRuleState.REJECTED,
                        (SemanticRuleDiagnosticCode.RULE_REJECTED,),
                        None,
                    )
                return result

        monkeypatch.setattr(frozen, "RULE_SET", Gate())
        q = qualify(search, "EURUSD", "H1", SnapshotMode.FAITHFUL)
        assert q.outcome is OutcomeClass.D_FROZEN_RESTRICTION
        assert q.steps[-1].rule == failing and q.steps[-1].state == "REJECTED"
        assert len(q.steps) == F01_CHAIN.index(failing) + 1


def test_primary_only_mode_never_replaces_faithful_reporting() -> None:
    published = run_pipeline(generated_bars(1500, 2))
    for item in published:
        if item.qualifications:
            assert [q.mode for q in item.qualifications] == [
                SnapshotMode.FAITHFUL,
                SnapshotMode.PRIMARY_ONLY,
            ]


def test_degree_mapping_is_clamped() -> None:
    assert degree_for(-3) is WaveDegree.SUBMINUETTE
    assert degree_for(0) is WaveDegree.SUBMINUETTE
    assert degree_for(99) is WaveDegree.PRIMARY
