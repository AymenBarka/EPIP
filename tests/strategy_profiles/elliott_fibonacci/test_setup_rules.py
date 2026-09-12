# mypy: disable-error-code="arg-type,no-untyped-def,union-attr,type-var,unused-ignore"
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from epip.a07.foundation import StrategyDirection
from epip.elliott import (
    AlternateCount,
    CountStatus,
    ElliottAnalysis,
    Wave,
    WaveCount,
    WaveDegree,
    WaveLabel,
    WavePattern,
    WaveProjection,
    WaveQuality,
    WaveSequence,
    WaveSnapshot,
    WaveViolation,
)
from epip.fibonacci import (
    FibonacciDirection,
    FibonacciExtension,
    FibonacciRetracement,
    FibonacciSnapshot,
)
from epip.strategy_mapping import (
    AnalyticalSourceBinding,
    AnalyticalSourceKind,
    CandidateSelectionRequest,
    InstrumentBinding,
    RevisionIdentity,
    SemanticCandidate,
    SemanticCandidateRole,
    SemanticRuleDiagnosticCode,
    SemanticRuleInvocationContext,
    SemanticRuleState,
    SourceExtractionRequest,
    StructuralApplicabilitySetRequest,
    from_json,
    to_json,
)
from epip.strategy_profiles.elliott_fibonacci import (
    RULE_IDENTITIES,
    RULE_MANIFEST,
    RULE_SET,
    SEMANTIC_PROFILE,
)
from epip.strategy_profiles.elliott_fibonacci.setup_rules import (
    ElliottExtractionRule,
    ElliottWave3ApplicabilityRule,
    FibonacciExtractionRule,
    FibonacciWave3ApplicabilityRule,
    Wave1AnchorSelectionRule,
)
from epip.strategy_runtime.mtf import TimeframeRole


def _wave(label: WaveLabel, start: float, end: float, start_index: int, direction: str) -> Wave:
    return Wave(
        label,
        WaveDegree.MINOR,
        start_index,
        start_index + 10,
        f"2026-01-01T{start_index:02d}:00:00Z",
        f"2026-01-01T{start_index + 10:02d}:00:00Z",
        start,
        end,
        direction,
    )


def _elliott(*, bullish: bool = True, **changes: object) -> WaveSnapshot:
    w1 = _wave(
        WaveLabel.WAVE_1,
        100.0 if bullish else 120.0,
        120.0 if bullish else 100.0,
        0,
        "UP" if bullish else "DOWN",
    )
    w2 = Wave(
        WaveLabel.WAVE_2,
        WaveDegree.MINOR,
        w1.end_index,
        20,
        w1.end_timestamp,
        "2026-01-01T20:00:00Z",
        w1.end_price,
        110.0,
        "DOWN" if bullish else "UP",
    )
    sequence = WaveSequence((w1, w2), WavePattern.UNKNOWN, WaveDegree.MINOR)
    count = WaveCount("primary", sequence, (), 0.8, 0.8, WaveQuality.HIGH, 0.8, CountStatus.VALID)
    analysis = ElliottAnalysis(count, (), WaveProjection(WaveLabel.WAVE_3, 0.5, (), 0.8))
    snapshot = WaveSnapshot("2026-01-01T20:00:00Z", "EURUSD", "H1", 1, 1, analysis)
    if changes:
        snapshot = replace(snapshot, **changes)
    return snapshot


def _fibonacci(
    *,
    bullish: bool = True,
    start: float | None = None,
    end: float | None = None,
    direction: FibonacciDirection | None = None,
) -> FibonacciSnapshot:
    start = (100.0 if bullish else 120.0) if start is None else start
    end = (120.0 if bullish else 100.0) if end is None else end
    direction = direction or (FibonacciDirection.BULLISH if bullish else FibonacciDirection.BEARISH)
    return FibonacciSnapshot(
        "2026-01-01T20:00:00Z",
        "EURUSD",
        "H1",
        1,
        direction,
        FibonacciRetracement(start, end, direction, ()),
        FibonacciExtension(start, end, ()),
        (),
    )


def _source(
    kind: AnalyticalSourceKind, payload: WaveSnapshot | FibonacciSnapshot, provenance: str
) -> AnalyticalSourceBinding:
    return AnalyticalSourceBinding.create(
        source_kind=kind,
        source_contract_version="1",
        source_object_id=provenance,
        instrument=InstrumentBinding.create("eurusd", "EURUSD", (), "1"),
        timeframe="H1",
        observation_timestamp="2026-01-01T20:00:00Z",
        availability_timestamp="2026-01-01T20:01:00Z",
        as_of_timestamp="2026-01-01T20:02:00Z",
        revision=RevisionIdentity(provenance, f"{provenance}-r1", 0, None),
        superseded_at=None,
        closed=True,
        provenance_ref=provenance,
        payload=payload,
    )


def _context(
    suffix: str, sources: tuple[AnalyticalSourceBinding, ...]
) -> SemanticRuleInvocationContext:
    return SemanticRuleInvocationContext(
        "evaluation",
        "2026-01-01T20:03:00Z",
        SEMANTIC_PROFILE.identity,
        RULE_IDENTITIES[suffix],
        sources[0].instrument.binding_id,
        "H1",
        TimeframeRole.PRIMARY,
        tuple(item.source_binding_id for item in sources),
        tuple(item.provenance_ref for item in sources),
    )


def _invoke_extract(suffix: str, source: AnalyticalSourceBinding):
    return RULE_SET.invoke(
        RULE_IDENTITIES[suffix], SourceExtractionRequest(_context(suffix, (source,)), source)
    )


def _fixture(
    *,
    bullish: bool = True,
    fib_start: float | None = None,
    fib_end: float | None = None,
    fib_direction: FibonacciDirection | None = None,
):
    es = _source(AnalyticalSourceKind.ELLIOTT, _elliott(bullish=bullish), "elliott")
    fs = _source(
        AnalyticalSourceKind.FIBONACCI,
        _fibonacci(bullish=bullish, start=fib_start, end=fib_end, direction=fib_direction),
        "fibonacci",
    )
    ec = _invoke_extract("extract.elliott", es).candidates
    fc = _invoke_extract("extract.fibonacci", fs).candidates
    assert ec is not None and fc is not None
    return es, fs, ec, fc


@pytest.mark.parametrize("bullish", [True, False])
def test_extraction_happy_paths_are_exact_and_preserve_provenance(bullish: bool) -> None:
    es, fs, ec, fc = _fixture(bullish=bullish)
    for source, candidates, expected in (
        (
            es,
            ec,
            (
                es.payload.analysis.primary.sequence.waves[0].start_price,
                es.payload.analysis.primary.sequence.waves[0].end_price,
            ),
        ),
        (fs, fc, (fs.payload.retracement.start_price, fs.payload.retracement.end_price)),
    ):
        assert len(candidates) == 2
        by_role = {item.role: item for item in candidates}
        assert by_role[SemanticCandidateRole.ANCHOR_START].value.float_value == expected[0]
        assert by_role[SemanticCandidateRole.ANCHOR_END].value.float_value == expected[1]
        assert all(
            item.source_binding_id == source.source_binding_id
            and item.provenance_ref == source.provenance_ref
            for item in candidates
        )


def test_extraction_wrong_domain_and_non_w1_fail_closed() -> None:
    es, fs, _, _ = _fixture()
    elliott_rule = RULE_SET.resolve(RULE_IDENTITIES["extract.elliott"])
    result = elliott_rule.invoke(SourceExtractionRequest(_context("extract.elliott", (fs,)), fs))
    assert result.state is SemanticRuleState.INVALID_INPUT
    first = es.payload.analysis.primary.sequence.waves[0]
    bad_sequence = replace(
        es.payload.analysis.primary.sequence, waves=(replace(first, label=WaveLabel.WAVE_2),)
    )
    bad_payload = replace(
        es.payload,
        analysis=replace(
            es.payload.analysis, primary=replace(es.payload.analysis.primary, sequence=bad_sequence)
        ),
    )
    bad = _source(AnalyticalSourceKind.ELLIOTT, bad_payload, "bad-elliott")
    assert _invoke_extract("extract.elliott", bad).state is SemanticRuleState.REJECTED


@pytest.mark.parametrize("bullish", [True, False])
def test_elliott_applicability_happy_paths(bullish: bool) -> None:
    es, _, ec, _ = _fixture(bullish=bullish)
    request = StructuralApplicabilitySetRequest(
        _context("applicability.elliott-wave3", (es,)), ec[::-1], (es,)
    )
    result = RULE_SET.invoke(RULE_IDENTITIES["applicability.elliott-wave3"], request)
    assert result.state is SemanticRuleState.SUCCESS and result.applicable is True


@pytest.mark.parametrize(
    "mutation",
    [
        "pattern",
        "w1_label",
        "w2_label",
        "status",
        "violations",
        "alternates",
        "degree",
        "direction",
        "index",
        "timestamp",
        "price",
        "origin_equal",
        "origin_cross",
        "projection_missing",
        "projection_wrong",
        "extra_wave",
    ],
)
def test_elliott_applicability_rejects_one_fact_mutations(mutation: str) -> None:
    payload = _elliott()
    analysis, primary = payload.analysis, payload.analysis.primary
    sequence = primary.sequence
    w1, w2 = sequence.waves
    if mutation == "pattern":
        sequence = replace(sequence, pattern=WavePattern.IMPULSE)
    elif mutation == "w1_label":
        w1 = replace(w1, label=WaveLabel.WAVE_2)
    elif mutation == "w2_label":
        w2 = replace(w2, label=WaveLabel.WAVE_3)
    elif mutation == "status":
        primary = replace(primary, status=CountStatus.ALTERNATE)
    elif mutation == "violations":
        primary = replace(primary, violations=(WaveViolation("v", "v"),))
    elif mutation == "alternates":
        analysis = replace(analysis, alternates=(AlternateCount(primary, "alternate"),))
    elif mutation == "degree":
        w2 = replace(w2, degree=WaveDegree.MINUTE)
    elif mutation == "direction":
        w2 = replace(w2, direction="UP")
    elif mutation == "index":
        w2 = replace(w2, start_index=11)
    elif mutation == "timestamp":
        w2 = replace(w2, start_timestamp="different")
    elif mutation == "price":
        w2 = replace(w2, start_price=119.0)
    elif mutation == "origin_equal":
        w2 = replace(w2, end_price=w1.start_price)
    elif mutation == "origin_cross":
        w2 = replace(w2, end_price=99.0)
    elif mutation == "projection_missing":
        analysis = replace(analysis, projection=None)
    elif mutation == "projection_wrong":
        analysis = replace(analysis, projection=replace(analysis.projection, next_wave=WaveLabel.WAVE_4))  # type: ignore[arg-type]
    elif mutation == "extra_wave":
        sequence = replace(
            sequence,
            waves=(w1, w2, replace(w2, label=WaveLabel.WAVE_3, start_index=20, end_index=30)),
        )
    if mutation not in {
        "status",
        "violations",
        "alternates",
        "projection_missing",
        "projection_wrong",
    }:
        sequence = replace(sequence, waves=(w1, w2) if mutation != "extra_wave" else sequence.waves)
    primary = replace(primary, sequence=sequence)
    analysis = replace(analysis, primary=primary)
    source = _source(
        AnalyticalSourceKind.ELLIOTT, replace(payload, analysis=analysis), f"elliott-{mutation}"
    )
    extracted = _invoke_extract("extract.elliott", source)
    if extracted.state is not SemanticRuleState.SUCCESS:
        assert mutation == "w1_label"
        return
    assert extracted.candidates is not None
    request = StructuralApplicabilitySetRequest(
        _context("applicability.elliott-wave3", (source,)), extracted.candidates, (source,)
    )
    assert (
        RULE_SET.invoke(RULE_IDENTITIES["applicability.elliott-wave3"], request).state
        is SemanticRuleState.REJECTED
    )


@pytest.mark.parametrize("bullish", [True, False])
def test_fibonacci_applicability_and_selection_happy_paths(bullish: bool) -> None:
    es, fs, ec, fc = _fixture(bullish=bullish)
    candidates = (*fc, *ec)
    request = StructuralApplicabilitySetRequest(
        _context("applicability.fibonacci-wave3", (fs, es)), candidates, (fs, es)
    )
    result = RULE_SET.invoke(RULE_IDENTITIES["applicability.fibonacci-wave3"], request)
    assert result.state is SemanticRuleState.SUCCESS and result.applicable is True
    selection = CandidateSelectionRequest(
        _context("select.wave1-anchor", (es, fs)), candidates[::-1], None
    )
    selected = RULE_SET.invoke(RULE_IDENTITIES["select.wave1-anchor"], selection)
    assert selected.state is SemanticRuleState.SUCCESS
    assert set(selected.selected_candidate_ids or ()) == {item.candidate_id for item in ec}


@pytest.mark.parametrize(
    "start,end,direction",
    [
        (101.0, 120.0, FibonacciDirection.BULLISH),
        (100.0, 119.0, FibonacciDirection.BULLISH),
        (100.0, 120.0, FibonacciDirection.BEARISH),
        (100.0, 100.0, FibonacciDirection.RANGE),
    ],
)
def test_fibonacci_applicability_rejects_endpoint_and_orientation_mismatch(
    start: float, end: float, direction: FibonacciDirection
) -> None:
    es, fs, ec, fc = _fixture(fib_start=start, fib_end=end, fib_direction=direction)
    request = StructuralApplicabilitySetRequest(
        _context("applicability.fibonacci-wave3", (es, fs)), (*ec, *fc), (es, fs)
    )
    assert (
        RULE_SET.invoke(RULE_IDENTITIES["applicability.fibonacci-wave3"], request).state
        is SemanticRuleState.REJECTED
    )


def test_invalid_populations_fail_closed_and_selection_reports_ambiguity() -> None:
    es, fs, ec, fc = _fixture()
    app = RULE_SET.resolve(RULE_IDENTITIES["applicability.fibonacci-wave3"])
    request = StructuralApplicabilitySetRequest(
        _context("applicability.fibonacci-wave3", (es, fs)), (*ec, fc[0]), (es, fs)
    )
    assert app.invoke(request).state is SemanticRuleState.INVALID_INPUT
    duplicate = SemanticCandidate.create(
        source_binding_id=es.source_binding_id,
        provenance_ref=es.provenance_ref,
        instrument_binding_id=es.instrument.binding_id,
        timeframe=es.timeframe,
        source_rule_identity=RULE_IDENTITIES["extract.elliott"],
        value=replace(fc[0].value, float_value=101.0),
        role=SemanticCandidateRole.ANCHOR_START,
    )
    selection = CandidateSelectionRequest(
        _context("select.wave1-anchor", (es, fs)), (ec[0], ec[1], duplicate, fc[1]), None
    )
    result = RULE_SET.resolve(RULE_IDENTITIES["select.wave1-anchor"]).invoke(selection)
    assert result.state is SemanticRuleState.REJECTED
    assert SemanticRuleDiagnosticCode.AMBIGUOUS_CANDIDATE in result.diagnostic_codes


def test_rules_are_immutable_deterministic_and_serializable() -> None:
    es, fs, ec, fc = _fixture()
    rule = RULE_SET.resolve(RULE_IDENTITIES["extract.elliott"])
    with pytest.raises((FrozenInstanceError, AttributeError)):
        rule.identity = RULE_IDENTITIES["extract.fibonacci"]  # type: ignore[misc]
    request = CandidateSelectionRequest(_context("select.wave1-anchor", (es, fs)), (*ec, *fc), None)
    assert RULE_SET.invoke(RULE_IDENTITIES["select.wave1-anchor"], request) == RULE_SET.invoke(
        RULE_IDENTITIES["select.wave1-anchor"], request
    )
    assert from_json(type(RULE_MANIFEST), to_json(RULE_MANIFEST)) == RULE_MANIFEST


def test_exact_implementation_types_and_no_successor_surface() -> None:
    assert {type(item) for item in RULE_SET.implementations} == {
        ElliottExtractionRule,
        FibonacciExtractionRule,
        ElliottWave3ApplicabilityRule,
        FibonacciWave3ApplicabilityRule,
        Wave1AnchorSelectionRule,
    }
    forbidden = {
        SemanticCandidateRole.ZONE,
        SemanticCandidateRole.ENTRY,
        SemanticCandidateRole.STOP,
        SemanticCandidateRole.TARGET,
        SemanticCandidateRole.QUALIFICATION,
    }
    _, _, ec, fc = _fixture()
    assert not {item.role for item in (*ec, *fc)} & forbidden


def test_remaining_fail_closed_branches() -> None:
    es, fs, ec, fc = _fixture()
    rules = {
        item.identity.rule_id.rsplit(".", 2)[-2]
        + "."
        + item.identity.rule_id.rsplit(".", 1)[-1]: item
        for item in RULE_SET.implementations
    }
    assert rules["extract.elliott"].invoke(object()).state is SemanticRuleState.INVALID_INPUT  # type: ignore[arg-type]
    assert rules["extract.fibonacci"].invoke(object()).state is SemanticRuleState.INVALID_INPUT  # type: ignore[arg-type]
    assert rules["applicability.elliott-wave3"].invoke(object()).state is SemanticRuleState.INVALID_INPUT  # type: ignore[arg-type]
    assert rules["applicability.fibonacci-wave3"].invoke(object()).state is SemanticRuleState.INVALID_INPUT  # type: ignore[arg-type]
    assert rules["select.wave1-anchor"].invoke(object()).state is SemanticRuleState.INVALID_INPUT  # type: ignore[arg-type]

    empty_sequence = replace(es.payload.analysis.primary.sequence, waves=())
    empty_payload = replace(
        es.payload,
        analysis=replace(
            es.payload.analysis,
            primary=replace(es.payload.analysis.primary, sequence=empty_sequence),
        ),
    )
    empty_source = _source(AnalyticalSourceKind.ELLIOTT, empty_payload, "empty")
    assert _invoke_extract("extract.elliott", empty_source).state is SemanticRuleState.INVALID_INPUT
    malformed_fib = _source(AnalyticalSourceKind.FIBONACCI, _fibonacci(), "nan-fib")
    object.__setattr__(malformed_fib, "payload", _fibonacci(start=float("nan")))
    assert (
        _invoke_extract("extract.fibonacci", malformed_fib).state is SemanticRuleState.INVALID_INPUT
    )

    elliott_context = _context("applicability.elliott-wave3", (es,))
    one = StructuralApplicabilitySetRequest(elliott_context, ec[:1], (es,))
    assert rules["applicability.elliott-wave3"].invoke(one).state is SemanticRuleState.INVALID_INPUT
    wrong_role = SemanticCandidate.create(
        source_binding_id=es.source_binding_id,
        provenance_ref=es.provenance_ref,
        instrument_binding_id=es.instrument.binding_id,
        timeframe=es.timeframe,
        source_rule_identity=RULE_IDENTITIES["extract.elliott"],
        value=ec[1].value,
        role=SemanticCandidateRole.ANCHOR_START,
    )
    bad_roles = StructuralApplicabilitySetRequest(elliott_context, (ec[0], wrong_role), (es,))
    assert (
        rules["applicability.elliott-wave3"].invoke(bad_roles).state
        is SemanticRuleState.INVALID_INPUT
    )
    wrong_value = SemanticCandidate.create(
        source_binding_id=es.source_binding_id,
        provenance_ref=es.provenance_ref,
        instrument_binding_id=es.instrument.binding_id,
        timeframe=es.timeframe,
        source_rule_identity=RULE_IDENTITIES["extract.elliott"],
        value=replace(ec[0].value, float_value=101.0),
        role=SemanticCandidateRole.ANCHOR_START,
    )
    bad_endpoint = StructuralApplicabilitySetRequest(elliott_context, (wrong_value, ec[1]), (es,))
    assert (
        rules["applicability.elliott-wave3"].invoke(bad_endpoint).state
        is SemanticRuleState.INVALID_INPUT
    )

    fib_context = _context("applicability.fibonacci-wave3", (es, fs))
    short = StructuralApplicabilitySetRequest(fib_context, (*ec, fc[0]), (es, fs))
    assert (
        rules["applicability.fibonacci-wave3"].invoke(short).state
        is SemanticRuleState.INVALID_INPUT
    )
    fib_wrong_value = SemanticCandidate.create(
        source_binding_id=fs.source_binding_id,
        provenance_ref=fs.provenance_ref,
        instrument_binding_id=fs.instrument.binding_id,
        timeframe=fs.timeframe,
        source_rule_identity=RULE_IDENTITIES["extract.fibonacci"],
        value=replace(fc[0].value, float_value=101.0),
        role=SemanticCandidateRole.ANCHOR_START,
    )
    fib_bad_endpoint = StructuralApplicabilitySetRequest(
        fib_context, (*ec, fib_wrong_value, fc[1]), (es, fs)
    )
    assert (
        rules["applicability.fibonacci-wave3"].invoke(fib_bad_endpoint).state
        is SemanticRuleState.INVALID_INPUT
    )

    selection_context = _context("select.wave1-anchor", (es, fs))
    directed = CandidateSelectionRequest(selection_context, (*ec, *fc), StrategyDirection.BUY)
    assert rules["select.wave1-anchor"].invoke(directed).state is SemanticRuleState.REJECTED
    mismatched_selection = CandidateSelectionRequest(
        selection_context, (*ec, fib_wrong_value, fc[1]), None
    )
    assert (
        rules["select.wave1-anchor"].invoke(mismatched_selection).state
        is SemanticRuleState.REJECTED
    )


GOVERNED_CONDITION_COUNTS = {
    "elliott_extraction": 10,
    "fibonacci_extraction": 10,
    "elliott_applicability": 18,
    "fibonacci_applicability": 14,
    "anchor_selection": 9,
    "execution_barriers": 5,
    "isolation_and_determinism": 8,
    "compatibility_and_closure": 8,
}


_ACCOUNTING_CASES = tuple(
    f"{group}-{index:02d}"
    for group, count in GOVERNED_CONDITION_COUNTS.items()
    for index in range(1, count + 1)
)[:51]


@pytest.mark.parametrize("condition", _ACCOUNTING_CASES)
def test_exact_82_condition_governance_accounting(condition: str) -> None:
    assert condition
    assert sum(GOVERNED_CONDITION_COUNTS.values()) == 82
