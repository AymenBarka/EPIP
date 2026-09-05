# mypy: disable-error-code="arg-type,no-untyped-def,no-untyped-call"
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *
from epip.strategy_runtime.mtf import TimeframeRole


@dataclass(frozen=True)
class SyntheticRule:
    identity: RuleIdentity
    family: SemanticRuleFamily
    invocation_kind: SemanticInvocationKind
    result_kind: SemanticResultKind
    implementation_id: str

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        del request
        return CandidateRuleResult(
            SemanticRuleState.NO_MATCH,
            (SemanticRuleDiagnosticCode.SELECTOR_NO_MATCH,),
            None,
        )


_KINDS = {
    SemanticRuleFamily.SOURCE_EXTRACTION: (
        SemanticInvocationKind.SOURCE_EXTRACTION,
        SemanticResultKind.CANDIDATES,
    ),
    SemanticRuleFamily.CANDIDATE_SELECTION: (
        SemanticInvocationKind.SELECTION,
        SemanticResultKind.SELECTION,
    ),
    SemanticRuleFamily.CANDIDATE_RANKING: (
        SemanticInvocationKind.RANKING,
        SemanticResultKind.RANKING,
    ),
    SemanticRuleFamily.BOUNDARY_SELECTION: (
        SemanticInvocationKind.BOUNDARY,
        SemanticResultKind.BOUNDARY,
    ),
    SemanticRuleFamily.APPLICABILITY: (
        SemanticInvocationKind.APPLICABILITY,
        SemanticResultKind.APPLICABILITY,
    ),
    SemanticRuleFamily.PRECEDENCE: (
        SemanticInvocationKind.SELECTION,
        SemanticResultKind.SELECTION,
    ),
    SemanticRuleFamily.PRICE_TRANSFORMATION: (
        SemanticInvocationKind.PRICE_TRANSFORMATION,
        SemanticResultKind.PRICE_TRANSFORMATION,
    ),
    SemanticRuleFamily.CONFIDENCE: (
        SemanticInvocationKind.CONFIDENCE,
        SemanticResultKind.CONFIDENCE,
    ),
    SemanticRuleFamily.TEMPORAL_ELIGIBILITY: (
        SemanticInvocationKind.TEMPORAL_ELIGIBILITY,
        SemanticResultKind.TEMPORAL_ELIGIBILITY,
    ),
    SemanticRuleFamily.EVIDENCE_MAPPING: (
        SemanticInvocationKind.EVIDENCE_MAPPING,
        SemanticResultKind.EVIDENCE_MAPPING,
    ),
    SemanticRuleFamily.EVIDENCE_ORDERING: (
        SemanticInvocationKind.EVIDENCE_ORDERING,
        SemanticResultKind.EVIDENCE_ORDERING,
    ),
    SemanticRuleFamily.MTF_AGGREGATION: (
        SemanticInvocationKind.MTF_AGGREGATION,
        SemanticResultKind.MTF_AGGREGATION,
    ),
}


def _rule(name: str) -> RuleIdentity:
    return RuleIdentity(
        name, "1", FOUNDATION_SCHEMA_VERSION, sha256(name.encode("ascii")).hexdigest()
    )


def _profile(semantic_profile, model_kind=ConfidenceModelKind.DIRECT, *, shared=False):
    identities = {name: _rule(name) for name in "abcdefghijklmno"}
    source = identities["a"]

    def scoped(selector, rule=source, role=TimeframeRole.PRIMARY):
        return replace(selector, selector_rule=rule, frame_roles=(role,))

    directions = tuple(
        replace(item, selector=scoped(item.selector))
        for item in semantic_profile.direction_policies
    )
    entry = replace(
        semantic_profile.entry_policy,
        allowed_selectors=(scoped(semantic_profile.entry_policy.allowed_selectors[0]),),
        candidate_selector=identities["b"],
        ranking_rule=identities["c"],
        required_boundary_rule=identities["d"],
        direction_applicability_rule=identities["e"],
    )
    stop = replace(
        semantic_profile.stop_policy,
        allowed_selectors=(scoped(semantic_profile.stop_policy.allowed_selectors[0]),),
        candidate_selector=identities["b"],
        precedence_rule=identities["f"],
        buffer_rule=identities["g"],
        direction_applicability_rule=identities["e"],
    )
    target = replace(
        semantic_profile.target_policy,
        allowed_selectors=(scoped(semantic_profile.target_policy.allowed_selectors[0]),),
        candidate_selector=identities["b"],
        ranking_rule=identities["c"],
        direction_applicability_rule=identities["e"],
    )
    confidence_source = source if shared else identities["h"]
    inputs: tuple[ConfidenceInput, ...] = (
        ConfidenceInput(
            "alpha",
            scoped(
                semantic_profile.confidence_policy.inputs[0].source_selector,
                confidence_source,
            ),
            True,
        ),
    )
    if model_kind is not ConfidenceModelKind.DIRECT:
        inputs += (
            ConfidenceInput(
                "zeta",
                scoped(
                    semantic_profile.confidence_policy.inputs[0].source_selector,
                    confidence_source,
                    TimeframeRole.HIGHER,
                ),
                False,
            ),
        )
    confidence = replace(
        semantic_profile.confidence_policy,
        model_kind=model_kind,
        model_identity=identities["i"],
        inputs=inputs,
        calibration_identity=(
            identities["j"] if model_kind is ConfidenceModelKind.CALIBRATED else None
        ),
    )
    evidence_key = semantic_profile.evidence_taxonomy.keys[0]
    temporal = replace(
        evidence_key.temporal_eligibility_policy,
        validity_rule=identities["k"],
        revision_rule=identities["l"],
    )
    evidence = replace(
        semantic_profile.evidence_taxonomy,
        keys=(
            replace(
                evidence_key,
                source_selector=scoped(evidence_key.source_selector),
                mapping_rule=identities["m"],
                temporal_eligibility_policy=temporal,
            ),
        ),
        ordering_rule=identities["n"],
    )
    mtf = semantic_profile.mtf_direction_policy
    profile = StrategySemanticMappingProfile.create(
        semantic_profile_id=semantic_profile.identity.semantic_profile_id,
        semantic_profile_version=semantic_profile.identity.semantic_profile_version,
        parent_profile=semantic_profile.parent_profile,
        direction_policies=directions,
        mtf_direction_policy=mtf,
        entry_policy=entry,
        stop_policy=stop,
        target_policy=target,
        confidence_policy=confidence,
        evidence_taxonomy=evidence,
        global_conflict_action=semantic_profile.global_conflict_action,
    )
    return profile, confidence_source


def _requirements(profile):
    values = []

    def add(identity, family):
        values.append((identity, family))

    for item in profile.direction_policies:
        add(item.selector.selector_rule, SemanticRuleFamily.SOURCE_EXTRACTION)
        if item.strategy_rule is not None:
            add(item.strategy_rule, SemanticRuleFamily.DIRECTION_MAPPING)
    add(profile.mtf_direction_policy.rule_identity, SemanticRuleFamily.MTF_AGGREGATION)
    for item in (profile.entry_policy, profile.stop_policy, profile.target_policy):
        for selector in item.allowed_selectors:
            add(selector.selector_rule, SemanticRuleFamily.SOURCE_EXTRACTION)
        add(item.candidate_selector, SemanticRuleFamily.CANDIDATE_SELECTION)
        add(item.direction_applicability_rule, SemanticRuleFamily.APPLICABILITY)
    add(profile.entry_policy.ranking_rule, SemanticRuleFamily.CANDIDATE_RANKING)
    add(profile.entry_policy.required_boundary_rule, SemanticRuleFamily.BOUNDARY_SELECTION)
    add(profile.stop_policy.precedence_rule, SemanticRuleFamily.PRECEDENCE)
    add(profile.stop_policy.buffer_rule, SemanticRuleFamily.PRICE_TRANSFORMATION)
    add(profile.target_policy.ranking_rule, SemanticRuleFamily.CANDIDATE_RANKING)
    for item in profile.confidence_policy.inputs:
        add(item.source_selector.selector_rule, SemanticRuleFamily.SOURCE_EXTRACTION)
    add(profile.confidence_policy.model_identity, SemanticRuleFamily.CONFIDENCE)
    if profile.confidence_policy.calibration_identity is not None:
        add(profile.confidence_policy.calibration_identity, SemanticRuleFamily.CONFIDENCE)
    for item in profile.evidence_taxonomy.keys:
        add(item.source_selector.selector_rule, SemanticRuleFamily.SOURCE_EXTRACTION)
        add(item.mapping_rule, SemanticRuleFamily.EVIDENCE_MAPPING)
        add(item.temporal_eligibility_policy.validity_rule, SemanticRuleFamily.TEMPORAL_ELIGIBILITY)
        add(item.temporal_eligibility_policy.revision_rule, SemanticRuleFamily.TEMPORAL_ELIGIBILITY)
    add(profile.evidence_taxonomy.ordering_rule, SemanticRuleFamily.EVIDENCE_ORDERING)
    return dict(values)


def _resolved(requirements):
    declarations = []
    implementations = []
    for identity, family in requirements.items():
        invocation, result = _KINDS[family]
        declaration = SemanticRuleDeclaration(
            identity, family, invocation, result, identity.rule_id
        )
        declarations.append(declaration)
        implementations.append(
            SyntheticRule(identity, family, invocation, result, identity.rule_id)
        )
    return ResolvedSemanticRuleSet(
        ResolvedRuleManifest.create(tuple(declarations)), tuple(implementations)
    )


@pytest.mark.parametrize("kind", list(ConfidenceModelKind))
def test_each_confidence_variant_requires_extractions_and_model(semantic_profile, kind):
    profile, extraction = _profile(semantic_profile, kind)
    requirements = _requirements(profile)
    assert requirements[extraction] is SemanticRuleFamily.SOURCE_EXTRACTION
    assert requirements[profile.confidence_policy.model_identity] is SemanticRuleFamily.CONFIDENCE
    if kind is ConfidenceModelKind.CALIBRATED:
        assert (
            requirements[profile.confidence_policy.calibration_identity]
            is SemanticRuleFamily.CONFIDENCE
        )
    _resolved(requirements).validate_profile_closure(profile)


def test_missing_required_and_unrelated_extra_are_rejected(semantic_profile):
    profile, extraction = _profile(semantic_profile)
    requirements = _requirements(profile)
    missing = dict(requirements)
    del missing[extraction]
    with pytest.raises(DataIntegrityError):
        _resolved(missing).validate_profile_closure(profile)
    extra = dict(requirements)
    extra[_rule("p")] = SemanticRuleFamily.SOURCE_EXTRACTION
    with pytest.raises(DataIntegrityError):
        _resolved(extra).validate_profile_closure(profile)
    _resolved(requirements).validate_profile_closure(profile)


def test_duplicate_inputs_and_cross_stage_sharing_deduplicate(semantic_profile):
    profile, extraction = _profile(semantic_profile, ConfidenceModelKind.WEIGHTED, shared=True)
    requirements = _requirements(profile)
    references = tuple(
        item.source_selector.selector_rule for item in profile.confidence_policy.inputs
    )
    assert references == (extraction, extraction)
    assert tuple(requirements).count(extraction) == 1
    assert profile.entry_policy.allowed_selectors[0].selector_rule == extraction
    assert profile.evidence_taxonomy.keys[0].source_selector.selector_rule == extraction
    _resolved(requirements).validate_profile_closure(profile)


def test_conflicting_identity_reuse_fails_closed(semantic_profile):
    profile, extraction = _profile(semantic_profile)
    conflict = replace(
        profile.confidence_policy,
        model_identity=extraction,
    )
    conflicted = StrategySemanticMappingProfile.create(
        semantic_profile_id=profile.identity.semantic_profile_id,
        semantic_profile_version=profile.identity.semantic_profile_version,
        parent_profile=profile.parent_profile,
        direction_policies=profile.direction_policies,
        mtf_direction_policy=profile.mtf_direction_policy,
        entry_policy=profile.entry_policy,
        stop_policy=profile.stop_policy,
        target_policy=profile.target_policy,
        confidence_policy=conflict,
        evidence_taxonomy=profile.evidence_taxonomy,
        global_conflict_action=profile.global_conflict_action,
    )
    with pytest.raises(DataIntegrityError):
        _resolved(_requirements(profile)).validate_profile_closure(conflicted)


def test_frame_scope_changes_fingerprint_not_closure_membership(semantic_profile):
    primary, extraction = _profile(semantic_profile)
    higher_input = replace(
        primary.confidence_policy.inputs[0],
        source_selector=replace(
            primary.confidence_policy.inputs[0].source_selector,
            frame_roles=(TimeframeRole.HIGHER,),
        ),
    )
    higher_confidence = replace(primary.confidence_policy, inputs=(higher_input,))
    higher = StrategySemanticMappingProfile.create(
        semantic_profile_id=primary.identity.semantic_profile_id,
        semantic_profile_version=primary.identity.semantic_profile_version,
        parent_profile=primary.parent_profile,
        direction_policies=primary.direction_policies,
        mtf_direction_policy=primary.mtf_direction_policy,
        entry_policy=primary.entry_policy,
        stop_policy=primary.stop_policy,
        target_policy=primary.target_policy,
        confidence_policy=higher_confidence,
        evidence_taxonomy=primary.evidence_taxonomy,
        global_conflict_action=primary.global_conflict_action,
    )
    assert primary.identity.fingerprint != higher.identity.fingerprint
    assert _requirements(primary) == _requirements(higher)
    assert extraction in _requirements(higher)
    assert from_json(StrategySemanticMappingProfile, to_json(higher)) == higher


def test_execution_vocabulary_is_unchanged():
    assert "CONFIDENCE_SOURCE_EXTRACTION" not in SemanticRuleFamily.__members__
    assert "CONFIDENCE_SOURCE_EXTRACTION" not in SemanticInvocationKind.__members__
    assert "CONFIDENCE_SOURCE_EXTRACTION" not in SemanticResultKind.__members__
    assert SemanticRuleFamily.SOURCE_EXTRACTION.value == "SOURCE_EXTRACTION"
    assert SemanticInvocationKind.SOURCE_EXTRACTION.value == "SOURCE_EXTRACTION"
    assert SemanticResultKind.CANDIDATES.value == "CANDIDATES"


def test_confidence_extraction_family_mismatch_is_rejected(semantic_profile):
    profile, extraction = _profile(semantic_profile)
    requirements = _requirements(profile)
    requirements[extraction] = SemanticRuleFamily.CONFIDENCE
    with pytest.raises(DataIntegrityError):
        _resolved(requirements).validate_profile_closure(profile)


@pytest.mark.parametrize(
    ("invocation", "result"),
    [
        (SemanticInvocationKind.DIRECTION, SemanticResultKind.CANDIDATES),
        (SemanticInvocationKind.SOURCE_EXTRACTION, SemanticResultKind.DIRECTION),
    ],
)
def test_source_extraction_invocation_and_result_mismatch_are_rejected(invocation, result):
    with pytest.raises(DataIntegrityError):
        SemanticRuleDeclaration(
            _rule("mismatch"),
            SemanticRuleFamily.SOURCE_EXTRACTION,
            invocation,
            result,
            "mismatch",
        )
