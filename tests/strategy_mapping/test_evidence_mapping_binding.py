# mypy: disable-error-code="arg-type,no-untyped-call,no-untyped-def"
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *


@dataclass(frozen=True)
class _Rule:
    identity: RuleIdentity
    family: SemanticRuleFamily
    invocation_kind: SemanticInvocationKind
    result_kind: SemanticResultKind
    implementation_id: str

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        return CandidateRuleResult(SemanticRuleState.NO_MATCH, (), None)


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


def _identity(name: str) -> RuleIdentity:
    return RuleIdentity(name, "1", FOUNDATION_SCHEMA_VERSION, sha256(name.encode()).hexdigest())


def _closure(mapping_rules: tuple[RuleIdentity, ...] = ()):
    identities = {
        name: _identity(name)
        for name in (
            "mtf",
            "entry-select",
            "entry-apply",
            "entry-rank",
            "entry-boundary",
            "stop-select",
            "stop-apply",
            "stop-precedence",
            "stop-buffer",
            "target-select",
            "target-apply",
            "target-rank",
            "confidence",
            "extract",
            "validity",
            "revision",
            "ordering",
        )
    }
    rules = mapping_rules or (_identity("mapping"),)
    profile = object.__new__(StrategySemanticMappingProfile)
    object.__setattr__(profile, "direction_policies", ())
    object.__setattr__(
        profile, "mtf_direction_policy", SimpleNamespace(rule_identity=identities["mtf"])
    )
    for name, extra in (
        (
            "entry_policy",
            {
                "ranking_rule": identities["entry-rank"],
                "required_boundary_rule": identities["entry-boundary"],
            },
        ),
        (
            "stop_policy",
            {
                "precedence_rule": identities["stop-precedence"],
                "buffer_rule": identities["stop-buffer"],
                "volatility_adjustment_rule": None,
            },
        ),
        (
            "target_policy",
            {
                "ranking_rule": identities["target-rank"],
                "threshold_rule": None,
                "extension_rule": None,
            },
        ),
    ):
        prefix = name.split("_")[0]
        object.__setattr__(
            profile,
            name,
            SimpleNamespace(
                allowed_selectors=(),
                candidate_selector=identities[f"{prefix}-select"],
                direction_applicability_rule=identities[f"{prefix}-apply"],
                **extra,
            ),
        )
    object.__setattr__(
        profile,
        "confidence_policy",
        SimpleNamespace(
            inputs=(
                SimpleNamespace(
                    source_selector=SimpleNamespace(selector_rule=identities["extract"])
                ),
            ),
            model_identity=identities["confidence"],
            calibration_identity=None,
        ),
    )
    keys = tuple(
        SimpleNamespace(
            source_selector=SimpleNamespace(selector_rule=identities["extract"]),
            mapping_rule=rule,
            temporal_eligibility_policy=SimpleNamespace(
                validity_rule=identities["validity"], revision_rule=identities["revision"]
            ),
        )
        for rule in rules
    )
    object.__setattr__(
        profile,
        "evidence_taxonomy",
        SimpleNamespace(keys=keys, ordering_rule=identities["ordering"]),
    )
    families = {
        identities["mtf"]: SemanticRuleFamily.MTF_AGGREGATION,
        identities["entry-select"]: SemanticRuleFamily.CANDIDATE_SELECTION,
        identities["entry-apply"]: SemanticRuleFamily.APPLICABILITY,
        identities["entry-rank"]: SemanticRuleFamily.CANDIDATE_RANKING,
        identities["entry-boundary"]: SemanticRuleFamily.BOUNDARY_SELECTION,
        identities["stop-select"]: SemanticRuleFamily.CANDIDATE_SELECTION,
        identities["stop-apply"]: SemanticRuleFamily.APPLICABILITY,
        identities["stop-precedence"]: SemanticRuleFamily.PRECEDENCE,
        identities["stop-buffer"]: SemanticRuleFamily.PRICE_TRANSFORMATION,
        identities["target-select"]: SemanticRuleFamily.CANDIDATE_SELECTION,
        identities["target-apply"]: SemanticRuleFamily.APPLICABILITY,
        identities["target-rank"]: SemanticRuleFamily.CANDIDATE_RANKING,
        identities["confidence"]: SemanticRuleFamily.CONFIDENCE,
        identities["extract"]: SemanticRuleFamily.SOURCE_EXTRACTION,
        identities["validity"]: SemanticRuleFamily.TEMPORAL_ELIGIBILITY,
        identities["revision"]: SemanticRuleFamily.TEMPORAL_ELIGIBILITY,
        identities["ordering"]: SemanticRuleFamily.EVIDENCE_ORDERING,
        **{rule: SemanticRuleFamily.EVIDENCE_MAPPING for rule in rules},
    }
    return profile, families


def _resolved(families):
    declarations = tuple(
        SemanticRuleDeclaration(identity, family, *_KINDS[family], "test-v1")
        for identity, family in families.items()
    )
    implementations = tuple(
        _Rule(
            item.identity,
            item.family,
            item.invocation_kind,
            item.result_kind,
            item.implementation_id,
        )
        for item in declarations
    )
    return ResolvedSemanticRuleSet(ResolvedRuleManifest.create(declarations), implementations)


def test_mapping_rule_is_mandatory_and_typed(policies):
    taxonomy = policies["evidence"]
    key = taxonomy.keys[0]
    assert type(key.mapping_rule) is RuleIdentity
    with pytest.raises(DataIntegrityError):
        replace(key, mapping_rule=object())


def test_mapping_rule_round_trips_and_is_canonical(policies):
    key = policies["evidence"].keys[0]
    payload = to_dict(key)
    assert payload["fields"]["mapping_rule"] == to_dict(key.mapping_rule)
    assert from_json(EvidenceKeyPolicy, to_json(key)) == key


def test_mapping_rule_participates_in_profile_fingerprint(semantic_profile):
    key = semantic_profile.evidence_taxonomy.keys[0]
    taxonomy = replace(
        semantic_profile.evidence_taxonomy,
        keys=(replace(key, mapping_rule=_identity("changed-mapping")),),
    )
    changed = StrategySemanticMappingProfile.create(
        semantic_profile_id=semantic_profile.identity.semantic_profile_id,
        semantic_profile_version=semantic_profile.identity.semantic_profile_version,
        parent_profile=semantic_profile.parent_profile,
        direction_policies=semantic_profile.direction_policies,
        mtf_direction_policy=semantic_profile.mtf_direction_policy,
        entry_policy=semantic_profile.entry_policy,
        stop_policy=semantic_profile.stop_policy,
        target_policy=semantic_profile.target_policy,
        confidence_policy=semantic_profile.confidence_policy,
        evidence_taxonomy=taxonomy,
        global_conflict_action=semantic_profile.global_conflict_action,
    )
    assert changed.identity.fingerprint != semantic_profile.identity.fingerprint


def test_profile_closure_includes_evidence_mapping_rule():
    profile, families = _closure()
    _resolved(families).validate_profile_closure(profile)


def test_profile_closure_rejects_missing_mapping_rule():
    profile, families = _closure()
    families.pop(_identity("mapping"))
    with pytest.raises(DataIntegrityError):
        _resolved(families).validate_profile_closure(profile)


def test_profile_closure_rejects_wrong_mapping_family():
    profile, families = _closure()
    families[_identity("mapping")] = SemanticRuleFamily.CONFIDENCE
    with pytest.raises(DataIntegrityError):
        _resolved(families).validate_profile_closure(profile)


def test_profile_closure_rejects_extra_mapping_rule():
    profile, families = _closure()
    families[_identity("extra-mapping")] = SemanticRuleFamily.EVIDENCE_MAPPING
    with pytest.raises(DataIntegrityError):
        _resolved(families).validate_profile_closure(profile)


def test_evidence_keys_may_share_one_mapping_rule():
    shared = _identity("shared-mapping")
    profile, families = _closure((shared, shared))
    _resolved(families).validate_profile_closure(profile)


def test_distinct_evidence_mapping_rules_are_both_required():
    profile, families = _closure((_identity("mapping-a"), _identity("mapping-b")))
    _resolved(families).validate_profile_closure(profile)
