# mypy: disable-error-code="arg-type,no-untyped-call,no-untyped-def"
from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError, dataclass, fields, replace

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *
from epip.strategy_runtime.mtf import TimeframeRole
from epip.swing import SwingSequence


def _instrument(identity: str = "eurusd") -> InstrumentBinding:
    return InstrumentBinding.create(identity, "EURUSD", (), "1")


def _source(index: int = 1, *, instrument: InstrumentBinding | None = None):
    instrument = instrument or _instrument()
    source_id = f"swing-{index}"
    return AnalyticalSourceBinding.create(
        source_kind=AnalyticalSourceKind.SWING,
        source_contract_version="swing-v1",
        source_object_id=source_id,
        instrument=instrument,
        timeframe="H1",
        observation_timestamp="2026-01-01T10:00:00Z",
        availability_timestamp="2026-01-01T10:01:00Z",
        as_of_timestamp="2026-01-01T10:02:00Z",
        revision=RevisionIdentity(f"series-{index}", f"revision-{index}", 0, None),
        superseded_at=None,
        closed=True,
        provenance_ref=source_id,
        payload=SwingSequence("EURUSD", "H1", ()),
    )


def _context(rule, semantic_profile, sources):
    return SemanticRuleInvocationContext(
        "evaluation",
        "2026-01-01T10:03:00Z",
        semantic_profile.identity,
        rule,
        sources[0].instrument.binding_id,
        "H1",
        TimeframeRole.PRIMARY,
        tuple(source.source_binding_id for source in sources),
        tuple(source.provenance_ref for source in sources),
    )


def _candidate(rule, source, value: float, role=SemanticCandidateRole.ANCHOR_START):
    return SemanticCandidate.create(
        source_binding_id=source.source_binding_id,
        provenance_ref=source.provenance_ref,
        instrument_binding_id=source.instrument.binding_id,
        timeframe=source.timeframe,
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.PRICE, float_value=value),
        role=role,
    )


@dataclass(frozen=True)
class _ApplicabilityRule:
    identity: RuleIdentity
    expected_request: type[object]
    wrong_result: bool = False
    family: SemanticRuleFamily = SemanticRuleFamily.APPLICABILITY
    invocation_kind: SemanticInvocationKind = SemanticInvocationKind.STRUCTURAL_APPLICABILITY
    result_kind: SemanticResultKind = SemanticResultKind.APPLICABILITY
    implementation_id: str = "structural-set-v1"
    calls: list[object] | None = None

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        if self.calls is not None:
            self.calls.append(request)
        assert type(request) is self.expected_request
        if self.wrong_result:
            return CandidateRuleResult(SemanticRuleState.NO_MATCH, (), None)
        return ApplicabilityResult(SemanticRuleState.SUCCESS, (), True)


def _resolved(rule, expected_request, *, wrong_result=False, calls=None):
    declaration = SemanticRuleDeclaration(
        rule,
        SemanticRuleFamily.APPLICABILITY,
        SemanticInvocationKind.STRUCTURAL_APPLICABILITY,
        SemanticResultKind.APPLICABILITY,
        "structural-set-v1",
    )
    implementation = _ApplicabilityRule(rule, expected_request, wrong_result, calls=calls)
    return ResolvedSemanticRuleSet(ResolvedRuleManifest.create((declaration,)), (implementation,))


def test_exact_public_shape_and_defaults(rule, semantic_profile):
    source = _source()
    context = _context(rule, semantic_profile, (source,))
    request = StructuralApplicabilitySetRequest(context, sources=(source,))
    assert tuple(field.name for field in fields(request)) == ("context", "candidates", "sources")
    assert request.candidates == () and request.sources == (source,)
    assert not hasattr(request, "direction")


def test_one_and_many_candidates_and_sources(rule, semantic_profile):
    sources = (_source(1), _source(2))
    context = _context(rule, semantic_profile, sources)
    candidates = (
        _candidate(rule, sources[0], 1.0),
        _candidate(rule, sources[1], 2.0, SemanticCandidateRole.ANCHOR_END),
    )
    assert len(StructuralApplicabilitySetRequest(context, candidates[:1]).candidates) == 1
    request = StructuralApplicabilitySetRequest(context, candidates, sources)
    assert len(request.candidates) == 2 and len(request.sources) == 2


def test_population_order_is_canonical_and_permutation_invariant(rule, semantic_profile):
    sources = (_source(1), _source(2))
    context = _context(rule, semantic_profile, sources)
    candidates = (_candidate(rule, sources[0], 2.0), _candidate(rule, sources[1], 1.0))
    forward = StructuralApplicabilitySetRequest(context, candidates, sources)
    reverse = StructuralApplicabilitySetRequest(context, candidates[::-1], sources[::-1])
    assert forward == reverse
    assert hash(forward) == hash(reverse)
    assert to_json(forward) == to_json(reverse)
    assert tuple(x.candidate_id for x in forward.candidates) == tuple(
        sorted(x.candidate_id for x in candidates)
    )
    assert tuple(x.source_binding_id for x in forward.sources) == tuple(
        sorted(x.source_binding_id for x in sources)
    )


@pytest.mark.parametrize("member", [[], [object()], (object(),)])
def test_candidate_population_requires_exact_typed_tuple(rule, semantic_profile, member):
    source = _source()
    context = _context(rule, semantic_profile, (source,))
    with pytest.raises(DataIntegrityError):
        StructuralApplicabilitySetRequest(context, member, (source,))


@pytest.mark.parametrize("member", [[], [object()], (object(),)])
def test_source_population_requires_exact_typed_tuple(rule, semantic_profile, member):
    source = _source()
    context = _context(rule, semantic_profile, (source,))
    with pytest.raises(DataIntegrityError):
        StructuralApplicabilitySetRequest(context, (), member)


def test_empty_total_input_is_rejected_but_either_population_may_be_empty(rule, semantic_profile):
    source = _source()
    context = _context(rule, semantic_profile, (source,))
    candidate = _candidate(rule, source, 1.0)
    assert StructuralApplicabilitySetRequest(context, (candidate,), ()).sources == ()
    assert StructuralApplicabilitySetRequest(context, (), (source,)).candidates == ()
    with pytest.raises(DataIntegrityError):
        StructuralApplicabilitySetRequest(context)


def test_duplicate_candidate_and_source_identities_fail_closed(rule, semantic_profile):
    source = _source()
    context = _context(rule, semantic_profile, (source,))
    candidate = _candidate(rule, source, 1.0)
    with pytest.raises(DataIntegrityError):
        StructuralApplicabilitySetRequest(context, (candidate, candidate))
    with pytest.raises(DataIntegrityError):
        StructuralApplicabilitySetRequest(context, (), (source, source))


def test_repeated_roles_remain_visible(rule, semantic_profile):
    sources = (_source(1), _source(2))
    context = _context(rule, semantic_profile, sources)
    candidates = tuple(
        _candidate(rule, source, float(index)) for index, source in enumerate(sources, 1)
    )
    request = StructuralApplicabilitySetRequest(context, candidates, sources)
    assert [item.role for item in request.candidates] == [SemanticCandidateRole.ANCHOR_START] * 2


@pytest.mark.parametrize(
    "candidate_change",
    [
        {"source_binding_id": "missing"},
        {"provenance_ref": "missing"},
        {"instrument_binding_id": "missing"},
        {"timeframe": "M5"},
    ],
)
def test_candidate_must_be_admitted_by_context(rule, semantic_profile, candidate_change):
    source = _source()
    context = _context(rule, semantic_profile, (source,))
    values = {
        "source_binding_id": source.source_binding_id,
        "provenance_ref": source.provenance_ref,
        "instrument_binding_id": source.instrument.binding_id,
        "timeframe": source.timeframe,
    }
    values.update(candidate_change)
    candidate = SemanticCandidate.create(
        **values,
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.PRICE, float_value=1.0),
    )
    with pytest.raises(DataIntegrityError):
        StructuralApplicabilitySetRequest(context, (candidate,))


def test_context_requires_exact_type(rule):
    with pytest.raises(DataIntegrityError):
        StructuralApplicabilitySetRequest(object(), (), (_source(),))


@pytest.mark.parametrize(
    "context_change",
    [
        {"source_binding_ids": ("missing",)},
        {"provenance_refs": ("missing",)},
        {"instrument_binding_id": "missing"},
        {"timeframe": "M5"},
    ],
)
def test_source_must_be_admitted_by_context(rule, semantic_profile, context_change):
    source = _source()
    context = replace(_context(rule, semantic_profile, (source,)), **context_change)
    with pytest.raises(DataIntegrityError):
        StructuralApplicabilitySetRequest(context, (), (source,))


def test_candidates_must_map_to_supplied_sources(rule, semantic_profile):
    sources = (_source(1), _source(2))
    context = _context(rule, semantic_profile, sources)
    candidate = _candidate(rule, sources[1], 1.0)
    with pytest.raises(DataIntegrityError):
        StructuralApplicabilitySetRequest(context, (candidate,), sources[:1])


def test_distinct_producers_and_provenance_are_not_merged(rule, semantic_profile):
    sources = (_source(1), _source(2))
    context = _context(rule, semantic_profile, sources)
    candidates = tuple(
        _candidate(rule, source, float(index)) for index, source in enumerate(sources, 1)
    )
    request = StructuralApplicabilitySetRequest(context, candidates, sources)
    assert {item.source_binding_id for item in request.candidates} == {
        item.source_binding_id for item in sources
    }
    assert {item.provenance_ref for item in request.sources} == {"swing-1", "swing-2"}
    assert request.context is context


def test_request_is_frozen_and_tuple_backed(rule, semantic_profile):
    source = _source()
    request = StructuralApplicabilitySetRequest(
        _context(rule, semantic_profile, (source,)), (), (source,)
    )
    assert type(request.candidates) is tuple and type(request.sources) is tuple
    with pytest.raises(FrozenInstanceError):
        request.sources = ()  # type: ignore[misc]


def test_serialization_round_trip_and_tampering(rule, semantic_profile):
    sources = (_source(1), _source(2))
    context = _context(rule, semantic_profile, sources)
    candidates = tuple(
        _candidate(rule, source, float(index)) for index, source in enumerate(sources, 1)
    )
    request = StructuralApplicabilitySetRequest(context, candidates, sources)
    assert from_json(StructuralApplicabilitySetRequest, to_json(request)) == request
    assert from_dict(StructuralApplicabilitySetRequest, to_dict(request)) == request
    payload = copy.deepcopy(to_dict(request))
    payload["fields"]["sources"]["$tuple"].append(payload["fields"]["sources"]["$tuple"][0])
    with pytest.raises(DataIntegrityError):
        from_dict(StructuralApplicabilitySetRequest, payload)


def test_old_request_positional_keyword_identity_serialization(rule, semantic_profile):
    source = _source()
    context = _context(rule, semantic_profile, (source,))
    candidate = _candidate(rule, source, 1.0)
    positional = StructuralApplicabilityRequest(context, candidate)
    keyword = StructuralApplicabilityRequest(context=context, candidate=candidate)
    assert positional == keyword and hash(positional) == hash(keyword)
    assert tuple(field.name for field in fields(positional)) == ("context", "candidate")
    assert from_json(StructuralApplicabilityRequest, to_json(positional)) == positional


@pytest.mark.parametrize("request_kind", ["old", "set"])
def test_exact_dispatch_accepts_both_structural_requests(rule, semantic_profile, request_kind):
    source = _source()
    context = _context(rule, semantic_profile, (source,))
    candidate = _candidate(rule, source, 1.0)
    request = (
        StructuralApplicabilityRequest(context, candidate)
        if request_kind == "old"
        else StructuralApplicabilitySetRequest(context, (candidate,), (source,))
    )
    result = _resolved(rule, type(request)).invoke(rule, request)
    assert type(result) is ApplicabilityResult and result.applicable is True


def test_wrong_request_fails_before_implementation(rule, semantic_profile):
    source = _source()
    context = _context(rule, semantic_profile, (source,))
    candidate = _candidate(rule, source, 1.0)
    calls: list[object] = []
    resolved = _resolved(rule, StructuralApplicabilitySetRequest, calls=calls)
    with pytest.raises(DataIntegrityError):
        resolved.invoke(rule, CandidateSelectionRequest(context, (candidate,), None))
    assert calls == []


def test_result_type_validation_remains_fail_closed(rule, semantic_profile):
    source = _source()
    request = StructuralApplicabilitySetRequest(
        _context(rule, semantic_profile, (source,)), (), (source,)
    )
    with pytest.raises(DataIntegrityError):
        _resolved(rule, StructuralApplicabilitySetRequest, wrong_result=True).invoke(rule, request)


def test_generic_role_pair_fit_uses_ids_not_tuple_position(rule, semantic_profile):
    source = _source()
    context = _context(rule, semantic_profile, (source,))
    start = _candidate(rule, source, 1.0, SemanticCandidateRole.ANCHOR_START)
    end = _candidate(rule, source, 2.0, SemanticCandidateRole.ANCHOR_END)
    request = StructuralApplicabilitySetRequest(context, (end, start), (source,))
    selected = SelectionRuleResult(
        SemanticRuleState.SUCCESS, (), (end.candidate_id, start.candidate_id)
    )
    assert selected.selected_candidate_ids is not None
    by_id = {item.candidate_id: item.role for item in request.candidates}
    assert {by_id[item] for item in selected.selected_candidate_ids} == {
        SemanticCandidateRole.ANCHOR_START,
        SemanticCandidateRole.ANCHOR_END,
    }
