# mypy: disable-error-code="no-untyped-call,no-untyped-def"
from dataclasses import dataclass, fields

import pytest

from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *
from epip.strategy_runtime.mtf import TimeframeRole


@dataclass(frozen=True)
class ApplicabilityRule:
    identity: RuleIdentity
    invocation_kind: SemanticInvocationKind
    expected_request: type[object]
    wrong_result: bool = False
    family: SemanticRuleFamily = SemanticRuleFamily.APPLICABILITY
    result_kind: SemanticResultKind = SemanticResultKind.APPLICABILITY
    implementation_id: str = "applicability-v1"

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        assert type(request) is self.expected_request
        if self.wrong_result:
            return CandidateRuleResult(SemanticRuleState.NO_MATCH, (), None)
        return ApplicabilityResult(SemanticRuleState.SUCCESS, (), True)


def _candidate(rule):
    return SemanticCandidate.create(
        source_binding_id="source",
        provenance_ref="provenance",
        instrument_binding_id="instrument",
        timeframe="H1",
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.BOOLEAN, bool_value=True),
    )


def _context(rule, semantic_profile):
    return SemanticRuleInvocationContext(
        "evaluation",
        "2025-01-01T00:00:00Z",
        semantic_profile.identity,
        rule,
        "instrument",
        "H1",
        TimeframeRole.PRIMARY,
        ("source",),
        ("provenance",),
    )


def _resolved(rule, invocation_kind, expected_request, *, wrong_result=False):
    declaration = SemanticRuleDeclaration(
        rule,
        SemanticRuleFamily.APPLICABILITY,
        invocation_kind,
        SemanticResultKind.APPLICABILITY,
        "applicability-v1",
    )
    implementation = ApplicabilityRule(
        rule, invocation_kind, expected_request, wrong_result=wrong_result
    )
    return ResolvedSemanticRuleSet(ResolvedRuleManifest.create((declaration,)), (implementation,))


def test_structural_request_is_exact_direction_neutral_and_serializable(rule, semantic_profile):
    request = StructuralApplicabilityRequest(_context(rule, semantic_profile), _candidate(rule))
    assert tuple(item.name for item in fields(request)) == ("context", "candidate")
    assert not hasattr(request, "direction")
    assert from_json(StructuralApplicabilityRequest, to_json(request)) == request
    with pytest.raises(DataIntegrityError):
        StructuralApplicabilityRequest(object(), request.candidate)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        StructuralApplicabilityRequest(request.context, object())  # type: ignore[arg-type]


def test_directional_applicability_is_unchanged(rule, semantic_profile):
    candidate = _candidate(rule)
    context = _context(rule, semantic_profile)
    request = ApplicabilityRequest(context, candidate, StrategyDirection.BUY)
    assert request.direction is StrategyDirection.BUY
    with pytest.raises(TypeError):
        ApplicabilityRequest(context, candidate)  # type: ignore[call-arg]
    with pytest.raises(DataIntegrityError):
        ApplicabilityRequest(context, candidate, None)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("invocation_kind", "request_type"),
    (
        (SemanticInvocationKind.APPLICABILITY, ApplicabilityRequest),
        (SemanticInvocationKind.STRUCTURAL_APPLICABILITY, StructuralApplicabilityRequest),
    ),
)
def test_checked_invocation_accepts_exact_request(
    rule, semantic_profile, invocation_kind, request_type
):
    candidate = _candidate(rule)
    context = _context(rule, semantic_profile)
    request = (
        request_type(context, candidate, StrategyDirection.BUY)
        if request_type is ApplicabilityRequest
        else request_type(context, candidate)
    )
    result = _resolved(rule, invocation_kind, request_type).invoke(rule, request)
    assert isinstance(result, ApplicabilityResult) and result.applicable is True


@pytest.mark.parametrize(
    ("invocation_kind", "expected_type", "request_type"),
    (
        (
            SemanticInvocationKind.APPLICABILITY,
            ApplicabilityRequest,
            StructuralApplicabilityRequest,
        ),
        (
            SemanticInvocationKind.STRUCTURAL_APPLICABILITY,
            StructuralApplicabilityRequest,
            ApplicabilityRequest,
        ),
    ),
)
def test_checked_invocation_rejects_wrong_request_before_rule(
    rule, semantic_profile, invocation_kind, expected_type, request_type
):
    candidate = _candidate(rule)
    context = _context(rule, semantic_profile)
    request = (
        request_type(context, candidate, StrategyDirection.BUY)
        if request_type is ApplicabilityRequest
        else request_type(context, candidate)
    )
    with pytest.raises(DataIntegrityError):
        _resolved(rule, invocation_kind, expected_type).invoke(rule, request)


def test_checked_invocation_rejects_wrong_result(rule, semantic_profile):
    request = StructuralApplicabilityRequest(_context(rule, semantic_profile), _candidate(rule))
    with pytest.raises(DataIntegrityError):
        _resolved(
            rule,
            SemanticInvocationKind.STRUCTURAL_APPLICABILITY,
            StructuralApplicabilityRequest,
            wrong_result=True,
        ).invoke(rule, request)


def test_structural_kind_is_only_compatible_with_applicability(rule):
    with pytest.raises(DataIntegrityError):
        SemanticRuleDeclaration(
            rule,
            SemanticRuleFamily.SOURCE_EXTRACTION,
            SemanticInvocationKind.STRUCTURAL_APPLICABILITY,
            SemanticResultKind.APPLICABILITY,
            "invalid-v1",
        )
