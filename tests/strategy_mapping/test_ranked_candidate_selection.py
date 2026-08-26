# mypy: disable-error-code="arg-type,no-untyped-call,no-untyped-def"
from dataclasses import FrozenInstanceError

import pytest

from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import (
    CandidateSelectionRequest,
    RankedCandidateSelectionRequest,
    SelectionRuleResult,
    SemanticCandidate,
    SemanticRuleInvocationContext,
    SemanticRuleState,
    SemanticValue,
    SemanticValueKind,
    from_dict,
    from_json,
    selection_winner,
    to_dict,
    to_json,
)


def _context(profile, rule):
    return SemanticRuleInvocationContext(
        "evaluation",
        "2026-08-26T00:00:00Z",
        profile.identity,
        rule,
        "instrument",
        None,
        None,
        ("source-z", "source-a"),
        ("provenance",),
    )


def _candidate(rule, source, price):
    return SemanticCandidate.create(
        source_binding_id=source,
        provenance_ref="provenance",
        instrument_binding_id="instrument",
        timeframe="H1",
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.PRICE, float_value=price),
    )


def _ranked(profile, rule):
    candidate_z = _candidate(rule, "source-z", 2.0)
    candidate_a = _candidate(rule, "source-a", 1.0)
    ranked = tuple(
        sorted((candidate_z, candidate_a), key=lambda item: item.candidate_id, reverse=True)
    )
    canonical = tuple(sorted(ranked, key=lambda item: item.candidate_id))
    assert ranked != canonical
    return ranked, _context(profile, rule)


def test_canonical_selection_preserves_existing_unordered_normalization(semantic_profile, rule):
    ranked, context = _ranked(semantic_profile, rule)
    request = CandidateSelectionRequest(context, ranked, StrategyDirection.BUY)
    assert request.candidates == tuple(sorted(ranked, key=lambda item: item.candidate_id))


def test_ranked_selection_preserves_exact_order_and_is_immutable(semantic_profile, rule):
    ranked, context = _ranked(semantic_profile, rule)
    request = RankedCandidateSelectionRequest(context, ranked, StrategyDirection.BUY)
    assert request.candidates == ranked
    with pytest.raises(FrozenInstanceError):
        request.direction = StrategyDirection.SELL  # type: ignore[misc]


def test_ranked_selection_equality_and_hash_reflect_order(semantic_profile, rule):
    ranked, context = _ranked(semantic_profile, rule)
    forward = RankedCandidateSelectionRequest(context, ranked, StrategyDirection.BUY)
    reverse = RankedCandidateSelectionRequest(
        context, tuple(reversed(ranked)), StrategyDirection.BUY
    )
    assert forward != reverse
    assert hash(forward) != hash(reverse)


def test_ranked_selection_rejects_empty_duplicate_and_invalid_candidates(semantic_profile, rule):
    ranked, context = _ranked(semantic_profile, rule)
    for candidates in ((), (ranked[0], ranked[0]), (object(),)):
        with pytest.raises(DataIntegrityError):
            RankedCandidateSelectionRequest(context, candidates, StrategyDirection.BUY)


def test_ranked_selection_round_trip_preserves_exact_order(semantic_profile, rule):
    ranked, context = _ranked(semantic_profile, rule)
    request = RankedCandidateSelectionRequest(context, ranked, StrategyDirection.BUY)
    assert from_json(RankedCandidateSelectionRequest, to_json(request)) == request
    assert from_dict(RankedCandidateSelectionRequest, to_dict(request)).candidates == ranked


def test_ranked_selection_reordered_payload_reconstructs_as_supplied(semantic_profile, rule):
    ranked, context = _ranked(semantic_profile, rule)
    request = RankedCandidateSelectionRequest(context, ranked, StrategyDirection.BUY)
    payload = to_dict(request)
    encoded = payload["fields"]["candidates"]["$tuple"]
    payload["fields"]["candidates"]["$tuple"] = list(reversed(encoded))
    reconstructed = from_dict(RankedCandidateSelectionRequest, payload)
    assert reconstructed.candidates == tuple(reversed(ranked))


def test_ranked_selection_invalid_reconstruction_fails_closed(semantic_profile, rule):
    ranked, context = _ranked(semantic_profile, rule)
    payload = to_dict(RankedCandidateSelectionRequest(context, ranked, StrategyDirection.BUY))
    payload["fields"]["candidates"]["$tuple"] = []
    with pytest.raises(DataIntegrityError):
        from_dict(RankedCandidateSelectionRequest, payload)


def test_target_extension_selects_one_exact_ranked_request_member(semantic_profile, rule):
    ranked, context = _ranked(semantic_profile, rule)
    request = RankedCandidateSelectionRequest(context, ranked, StrategyDirection.BUY)
    result = SelectionRuleResult(SemanticRuleState.SUCCESS, (), (ranked[0].candidate_id,))
    assert selection_winner(request, result, require_price=True) is ranked[0]


@pytest.mark.parametrize(
    "selected",
    [None, (), ("unknown",), ("duplicate", "duplicate")],
)
def test_target_extension_invalid_winner_cardinality_or_reference_fails_closed(
    semantic_profile, rule, selected
):
    ranked, context = _ranked(semantic_profile, rule)
    request = RankedCandidateSelectionRequest(context, ranked, StrategyDirection.BUY)
    with pytest.raises(DataIntegrityError):
        result = SelectionRuleResult(
            SemanticRuleState.NO_MATCH if selected is None else SemanticRuleState.SUCCESS,
            (),
            selected,
        )
        selection_winner(request, result, require_price=True)


def test_target_extension_multiple_winners_fail_closed(semantic_profile, rule):
    ranked, context = _ranked(semantic_profile, rule)
    request = RankedCandidateSelectionRequest(context, ranked, StrategyDirection.BUY)
    result = SelectionRuleResult(
        SemanticRuleState.SUCCESS, (), tuple(item.candidate_id for item in ranked)
    )
    with pytest.raises(DataIntegrityError):
        selection_winner(request, result, require_price=True)
