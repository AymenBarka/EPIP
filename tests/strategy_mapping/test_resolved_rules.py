# mypy: disable-error-code="no-untyped-def,no-untyped-call"
from dataclasses import dataclass

import pytest

from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *
from epip.strategy_runtime.mtf import TimeframeRole
from epip.swing import SwingSequence


@dataclass(frozen=True)
class SyntheticRule:
    identity: RuleIdentity
    family: SemanticRuleFamily
    invocation_kind: SemanticInvocationKind
    result_kind: SemanticResultKind
    implementation_id: str

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        return CandidateRuleResult(
            SemanticRuleState.NO_MATCH, (SemanticRuleDiagnosticCode.SELECTOR_NO_MATCH,), None
        )


def _resolved(rule):
    declaration = SemanticRuleDeclaration(
        rule,
        SemanticRuleFamily.SOURCE_EXTRACTION,
        SemanticInvocationKind.SOURCE_EXTRACTION,
        SemanticResultKind.CANDIDATES,
        "synthetic-v1",
    )
    manifest = ResolvedRuleManifest.create((declaration,))
    implementation = SyntheticRule(
        rule,
        declaration.family,
        declaration.invocation_kind,
        declaration.result_kind,
        declaration.implementation_id,
    )
    return ResolvedSemanticRuleSet(manifest, (implementation,))


def test_manifest_and_rule_set_identity_are_deterministic(rule):
    first = _resolved(rule)
    second = _resolved(rule)
    assert first == second and hash(first) == hash(second)
    assert first.resolve(rule).identity == rule


def test_manifest_tamper_and_duplicate_fail(rule):
    declaration = SemanticRuleDeclaration(
        rule,
        SemanticRuleFamily.SOURCE_EXTRACTION,
        SemanticInvocationKind.SOURCE_EXTRACTION,
        SemanticResultKind.CANDIDATES,
        "x",
    )
    with pytest.raises(DataIntegrityError):
        ResolvedRuleManifest(EXECUTION_SCHEMA_VERSION, "0" * 64, (declaration,))
    with pytest.raises(DataIntegrityError):
        ResolvedRuleManifest.create((declaration, declaration))


def test_family_kind_mismatch_fails(rule):
    with pytest.raises(DataIntegrityError):
        SemanticRuleDeclaration(
            rule,
            SemanticRuleFamily.CONFIDENCE,
            SemanticInvocationKind.DIRECTION,
            SemanticResultKind.DIRECTION,
            "x",
        )


def test_runtime_declaration_mismatch_fails(rule):
    resolved = _resolved(rule)
    implementation = resolved.implementations[0]
    bad = SyntheticRule(
        rule,
        SemanticRuleFamily.CONFIDENCE,
        implementation.invocation_kind,
        implementation.result_kind,
        implementation.implementation_id,
    )
    with pytest.raises(DataIntegrityError):
        ResolvedSemanticRuleSet(resolved.manifest, (bad,))
    with pytest.raises(DataIntegrityError):
        ResolvedSemanticRuleSet(resolved.manifest, ())
    with pytest.raises(DataIntegrityError):
        ResolvedSemanticRuleSet(resolved.manifest, (implementation, implementation))


def test_exact_profile_closure_rejects_incompatible_foundation_fixture(rule, semantic_profile):
    with pytest.raises(DataIntegrityError):
        _resolved(rule).validate_profile_closure(semantic_profile)


@dataclass(frozen=True)
class _DispatchRule:
    identity: RuleIdentity
    family: SemanticRuleFamily
    invocation_kind: SemanticInvocationKind
    result_kind: SemanticResultKind
    implementation_id: str = "dispatch-v1"
    calls: list[object] | None = None

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        if self.calls is not None:
            self.calls.append(request)
        if self.result_kind is SemanticResultKind.APPLICABILITY:
            return ApplicabilityResult(SemanticRuleState.SUCCESS, (), True)
        if self.result_kind is SemanticResultKind.BOUNDARY:
            return BoundaryRuleResult(
                SemanticRuleState.SUCCESS,
                (),
                SemanticValue(SemanticValueKind.PRICE, float_value=1.0),
            )
        if self.result_kind is SemanticResultKind.PRICE_TRANSFORMATION:
            assert isinstance(request, DirectionalCandidateSourceSetRequest)
            return PriceTransformationResult(SemanticRuleState.SUCCESS, (), request.candidates[0])
        raise AssertionError("rejected dispatch invoked implementation")


def _dispatch_request(rule, semantic_profile):
    instrument = InstrumentBinding.create("eurusd", "EURUSD", (), "1")
    source = AnalyticalSourceBinding.create(
        source_kind=AnalyticalSourceKind.SWING,
        source_contract_version="1",
        source_object_id="source",
        instrument=instrument,
        timeframe="H1",
        observation_timestamp="2026-01-01T10:00:00Z",
        availability_timestamp="2026-01-01T10:01:00Z",
        as_of_timestamp="2026-01-01T10:02:00Z",
        revision=RevisionIdentity("series", "revision", 0, None),
        superseded_at=None,
        closed=True,
        provenance_ref="source",
        payload=SwingSequence("EURUSD", "H1", ()),
    )
    context = SemanticRuleInvocationContext(
        "evaluation",
        "2026-01-01T10:03:00Z",
        semantic_profile.identity,
        rule,
        instrument.binding_id,
        "H1",
        TimeframeRole.PRIMARY,
        (source.source_binding_id,),
        (source.provenance_ref,),
    )
    candidate = SemanticCandidate.create(
        source_binding_id=source.source_binding_id,
        provenance_ref=source.provenance_ref,
        instrument_binding_id=instrument.binding_id,
        timeframe="H1",
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.PRICE, float_value=1.0),
    )
    return DirectionalCandidateSourceSetRequest(
        context, (candidate,), (source,), StrategyDirection.BUY
    )


@pytest.mark.parametrize(
    ("family", "invocation_kind", "result_kind"),
    [
        (
            SemanticRuleFamily.APPLICABILITY,
            SemanticInvocationKind.APPLICABILITY,
            SemanticResultKind.APPLICABILITY,
        ),
        (
            SemanticRuleFamily.BOUNDARY_SELECTION,
            SemanticInvocationKind.BOUNDARY,
            SemanticResultKind.BOUNDARY,
        ),
        (
            SemanticRuleFamily.PRICE_TRANSFORMATION,
            SemanticInvocationKind.PRICE_TRANSFORMATION,
            SemanticResultKind.PRICE_TRANSFORMATION,
        ),
    ],
)
def test_directional_set_dispatch_is_admitted_for_exact_governed_kinds(
    rule, semantic_profile, family, invocation_kind, result_kind
):
    declaration = SemanticRuleDeclaration(rule, family, invocation_kind, result_kind, "dispatch-v1")
    implementation = _DispatchRule(rule, family, invocation_kind, result_kind)
    resolved = ResolvedSemanticRuleSet(
        ResolvedRuleManifest.create((declaration,)), (implementation,)
    )
    assert resolved.invoke(rule, _dispatch_request(rule, semantic_profile)).state is (
        SemanticRuleState.SUCCESS
    )


@pytest.mark.parametrize(
    ("family", "invocation_kind", "result_kind"),
    [
        (
            SemanticRuleFamily.SOURCE_EXTRACTION,
            SemanticInvocationKind.SOURCE_EXTRACTION,
            SemanticResultKind.CANDIDATES,
        ),
        (
            SemanticRuleFamily.DIRECTION_MAPPING,
            SemanticInvocationKind.DIRECTION,
            SemanticResultKind.DIRECTION,
        ),
        (
            SemanticRuleFamily.CANDIDATE_SELECTION,
            SemanticInvocationKind.SELECTION,
            SemanticResultKind.SELECTION,
        ),
        (
            SemanticRuleFamily.CANDIDATE_RANKING,
            SemanticInvocationKind.RANKING,
            SemanticResultKind.RANKING,
        ),
        (
            SemanticRuleFamily.APPLICABILITY,
            SemanticInvocationKind.STRUCTURAL_APPLICABILITY,
            SemanticResultKind.APPLICABILITY,
        ),
        (
            SemanticRuleFamily.CONFIDENCE,
            SemanticInvocationKind.CONFIDENCE,
            SemanticResultKind.CONFIDENCE,
        ),
        (
            SemanticRuleFamily.TEMPORAL_ELIGIBILITY,
            SemanticInvocationKind.TEMPORAL_ELIGIBILITY,
            SemanticResultKind.TEMPORAL_ELIGIBILITY,
        ),
        (
            SemanticRuleFamily.EVIDENCE_MAPPING,
            SemanticInvocationKind.EVIDENCE_MAPPING,
            SemanticResultKind.EVIDENCE_MAPPING,
        ),
        (
            SemanticRuleFamily.EVIDENCE_ORDERING,
            SemanticInvocationKind.EVIDENCE_ORDERING,
            SemanticResultKind.EVIDENCE_ORDERING,
        ),
        (
            SemanticRuleFamily.MTF_AGGREGATION,
            SemanticInvocationKind.MTF_AGGREGATION,
            SemanticResultKind.MTF_AGGREGATION,
        ),
    ],
)
def test_directional_set_dispatch_rejects_every_other_kind_before_invocation(
    rule, semantic_profile, family, invocation_kind, result_kind
):
    declaration = SemanticRuleDeclaration(rule, family, invocation_kind, result_kind, "dispatch-v1")
    calls: list[object] = []
    implementation = _DispatchRule(rule, family, invocation_kind, result_kind, calls=calls)
    resolved = ResolvedSemanticRuleSet(
        ResolvedRuleManifest.create((declaration,)), (implementation,)
    )
    with pytest.raises(DataIntegrityError):
        resolved.invoke(rule, _dispatch_request(rule, semantic_profile))
    assert calls == []
