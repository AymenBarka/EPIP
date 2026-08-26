# mypy: disable-error-code="arg-type,no-untyped-call,no-untyped-def"
from dataclasses import replace

import pytest

from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *
from epip.strategy_runtime.mtf import TimeframeRole


def _context(profile, rule):
    return SemanticRuleInvocationContext(
        "evaluation",
        "2026-08-26T00:00:00Z",
        profile.identity,
        rule,
        "instrument",
        None,
        None,
        ("source",),
        ("provenance",),
    )


def _candidate(rule, value, source="source"):
    return SemanticCandidate.create(
        source_binding_id=source,
        provenance_ref="provenance",
        instrument_binding_id="instrument",
        timeframe="H1",
        source_rule_identity=rule,
        value=value,
    )


def test_evidence_ordering_materializes_exact_governed_permutation(semantic_profile, rule) -> None:
    request = EvidenceOrderingRequest(_context(semantic_profile, rule), ("zeta", "alpha"))
    assert request.evidence_keys == ("alpha", "zeta")
    result = EvidenceOrderingResult(SemanticRuleState.SUCCESS, (), ("zeta", "alpha"))
    assert materialize_evidence_order(request, result) == ("zeta", "alpha")
    for bad in (("alpha",), ("alpha", "extra")):
        with pytest.raises(DataIntegrityError):
            materialize_evidence_order(
                request, EvidenceOrderingResult(SemanticRuleState.SUCCESS, (), bad)
            )
    with pytest.raises(DataIntegrityError):
        materialize_evidence_order(
            request, EvidenceOrderingResult(SemanticRuleState.NO_MATCH, (), None)
        )
    with pytest.raises(DataIntegrityError):
        materialize_evidence_order(object(), result)


def test_boundary_point_and_range_are_exact_without_width() -> None:
    point = BoundaryRuleResult(
        SemanticRuleState.SUCCESS,
        (),
        SemanticValue(SemanticValueKind.PRICE, float_value=100.0),
    )
    bounds = BoundaryRuleResult(
        SemanticRuleState.SUCCESS,
        (),
        SemanticValue(SemanticValueKind.PRICE_RANGE, range_lower=99.0, range_upper=101.0),
    )
    assert boundary_entry_range(point) == (100.0, 100.0)
    assert boundary_entry_range(bounds) == (99.0, 101.0)
    with pytest.raises(DataIntegrityError):
        boundary_entry_range(object())
    for kwargs in (
        {"range_lower": 2.0, "range_upper": 1.0},
        {"range_lower": float("nan"), "range_upper": 1.0},
        {"range_lower": 0.0, "range_upper": 1.0},
    ):
        with pytest.raises(DataIntegrityError):
            SemanticValue(SemanticValueKind.PRICE_RANGE, **kwargs)


def test_ranking_winner_requires_exact_permutation(semantic_profile, rule) -> None:
    a = _candidate(rule, SemanticValue(SemanticValueKind.PRICE, float_value=1.0), "a")
    z = _candidate(rule, SemanticValue(SemanticValueKind.PRICE, float_value=2.0), "z")
    request = CandidateRankingRequest(
        _context(semantic_profile, rule), (z, a), StrategyDirection.BUY
    )
    result = RankingRuleResult(SemanticRuleState.SUCCESS, (), (z.candidate_id, a.candidate_id))
    assert ranking_winner(request, result) == z
    for ids in ((a.candidate_id,), (a.candidate_id, "unknown")):
        with pytest.raises(DataIntegrityError):
            ranking_winner(request, RankingRuleResult(SemanticRuleState.SUCCESS, (), ids))
    with pytest.raises(DataIntegrityError):
        ranking_winner(object(), result)


def test_stop_and_target_selection_require_exactly_one_request_member(
    semantic_profile, rule
) -> None:
    price = _candidate(rule, SemanticValue(SemanticValueKind.PRICE, float_value=2.0), "price")
    text = _candidate(rule, SemanticValue(SemanticValueKind.TEXT, text_value="x"), "text")
    request = CandidateSelectionRequest(
        _context(semantic_profile, rule), (price, text), StrategyDirection.BUY
    )
    success = SelectionRuleResult(SemanticRuleState.SUCCESS, (), (price.candidate_id,))
    assert selection_winner(request, success) == price
    assert selection_winner(request, success, require_price=True) == price
    failures = (
        SelectionRuleResult(SemanticRuleState.NO_MATCH, (), None),
        SelectionRuleResult(SemanticRuleState.SUCCESS, (), (price.candidate_id, text.candidate_id)),
        SelectionRuleResult(SemanticRuleState.SUCCESS, (), ("unknown",)),
    )
    for result in failures:
        with pytest.raises(DataIntegrityError):
            selection_winner(request, result)
    with pytest.raises(DataIntegrityError):
        selection_winner(object(), success)
    with pytest.raises(DataIntegrityError):
        selection_winner(
            request,
            SelectionRuleResult(SemanticRuleState.SUCCESS, (), (text.candidate_id,)),
            require_price=True,
        )


def test_mtf_field_round_trip_fingerprint_and_future_request_sufficiency(
    semantic_profile, rule
) -> None:
    mtf = semantic_profile.mtf_direction_policy
    assert mtf.frame_direction_fact is DirectionFactName.PRIMARY
    assert from_json(MtfDirectionPolicyRef, to_json(mtf)) == mtf
    payload = to_dict(mtf)
    del payload["fields"]["frame_direction_fact"]
    with pytest.raises(DataIntegrityError):
        from_dict(MtfDirectionPolicyRef, payload)
    alternate = replace(mtf, frame_direction_fact=DirectionFactName.ALTERNATE)
    changed = StrategySemanticMappingProfile.create(
        semantic_profile_id="semantic",
        semantic_profile_version="1",
        parent_profile=semantic_profile.parent_profile,
        direction_policies=semantic_profile.direction_policies,
        mtf_direction_policy=alternate,
        entry_policy=semantic_profile.entry_policy,
        stop_policy=semantic_profile.stop_policy,
        target_policy=semantic_profile.target_policy,
        confidence_policy=semantic_profile.confidence_policy,
        evidence_taxonomy=semantic_profile.evidence_taxonomy,
        global_conflict_action=semantic_profile.global_conflict_action,
    )
    assert changed.identity.fingerprint != semantic_profile.identity.fingerprint
    direction = TimeframeDirectionValue(
        "H1", TimeframeRole.PRIMARY, StrategyDirection.BUY, ("source",), ("provenance",)
    )
    request = MtfAggregationRequest(
        _context(semantic_profile, rule),
        (direction,),
        mtf.required_roles,
        mtf.required_timeframes,
    )
    assert request.directions == (direction,)
