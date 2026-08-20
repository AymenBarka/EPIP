"""Component tests for corrected A04-E01 semantic validation."""

from __future__ import annotations

from dataclasses import replace
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError
from epip.evidence.model import (
    AssumptionMetadata,
    CertifiedSemanticEquivalence,
    CompatibilityEffects,
    CompletenessMetadata,
    ConsumerConflictPolicy,
    DependencyType,
    DispositionAxis,
    EvidenceClaim,
    EvidenceRequirement,
    ExtendedRedundancyPolicy,
    IndependencePolicy,
    ProvenanceReference,
    QualityMetadata,
    SemanticBoundary,
    SemanticIdentity,
    SemanticState,
    ValidityMetadata,
)
from epip.evidence.validation import (
    CompatibilityEvaluator,
    ConflictDetector,
    EquivalenceValidator,
    IndependenceChecker,
    SemanticValidator,
)
from epip.governance.model import CertificationRecord, CompatibilityDecision, GovernanceEpoch


def _unsafe_replace(value: object, **changes: object) -> object:
    return cast(object, replace(cast(Any, value), **changes))


def _identity(**changes: str) -> SemanticIdentity:
    values = {
        "evidence_type": "market.structure",
        "semantic_version": "1.0.0",
        "subject": "EURUSD",
        "scope": "H1",
    }
    values.update(changes)
    return SemanticIdentity(**values)


def _claim(**changes: object) -> EvidenceClaim:
    values: dict[str, object] = {
        "evidence_id": "evidence-1",
        "identity": _identity(),
        "source_identity": "producer-1",
        "implementation_version": "1.0.0",
        "boundary": SemanticBoundary("EURUSD", "H1", "closed-candle", "2026-08-20T12:00Z"),
        "claim": "bullish",
        "value_domain": "structure-state",
        "units": None,
        "validity": ValidityMetadata("closed-candle", True, "boundary-1"),
        "completeness": CompletenessMetadata(
            SemanticState("PRESENT"), ("structure",), 1, ("H1",), ("trend",), True
        ),
        "quality": QualityMetadata("quality", "1.0.0", "accepted"),
        "assumptions": AssumptionMetadata("1.0.0", ("closed-candle",)),
        "provenance": (ProvenanceReference("feed-1", "feed", "1.0.0"),),
        "content_identity": "content-1",
        "disposition": DispositionAxis.ACCEPTED,
    }
    values.update(changes)
    return EvidenceClaim(**values)  # type: ignore[arg-type]


def _requirement(**changes: object) -> EvidenceRequirement:
    values: dict[str, object] = {
        "requirement_id": "requirement-1",
        "evidence_type": "market.structure",
        "semantic_version": "1.0.0",
        "subject": "EURUSD",
        "scope": "H1",
        "dependency_type": DependencyType.MANDATORY,
    }
    values.update(changes)
    return EvidenceRequirement(**values)  # type: ignore[arg-type]


def _epoch() -> GovernanceEpoch:
    return GovernanceEpoch(1)


def _decision(**changes: object) -> CompatibilityDecision:
    values: dict[str, object] = {
        "decision_identity": "decision-1",
        "compatibility_authority_identity": "compatibility-authority",
        "source_reference": "evidence-1",
        "target_reference": "requirement-1",
        "compatibility_dimension": "semantic",
        "direction": "source-to-target",
        "intended_use": "requirement-1",
        "version_scope": (("source", "1.0.0"), ("target", "1.0.0")),
        "profile_scope": (("scope", "H1"),),
        "evidence_references": ("compatibility-evidence",),
        "policy_version": "1.0.0",
        "effective_epoch": _epoch(),
        "review_or_expiry_condition": "version-change",
    }
    values.update(changes)
    return CompatibilityDecision(**values)  # type: ignore[arg-type]


def _certification(**changes: object) -> CertificationRecord:
    values: dict[str, object] = {
        "record_identity": "cert-1",
        "certification_authority_identity": "cert-authority",
        "producer_identity": "producer-1",
        "producer_version": "1.0.0",
        "implementation_identity": "build-1",
        "producer_contract_version": "1.0.0",
        "capability_references": (("market.structure", "1.0.0"),),
        "configuration_profile": "default",
        "schema_versions": (("output", "1.0.0"),),
        "temporal_profile": "closed",
        "determinism_profile": "deterministic",
        "replay_profile": "replayable",
        "execution_profile": "bounded",
        "isolation_profile": "isolated",
        "resource_profile": "bounded",
        "privilege_scope": (),
        "certification_profile_reference": "profile@1.0.0",
        "certification_suite_version": "1.0.0",
        "evidence_references": ("decision-1",),
        "verdict": "passed",
        "effective_epoch": _epoch(),
        "expiration_or_review_condition": "version-change",
    }
    values.update(changes)
    return CertificationRecord(**values)  # type: ignore[arg-type]


def _effects(**changes: object) -> CompatibilityEffects:
    values: dict[str, object] = {
        "decision_reference": "decision-1",
        "effects_version": "1.0.0",
        "conversion": None,
        "narrowing": None,
        "widening": None,
        "unit_effect": "structure-state",
        "completeness_effect": "PRESENT",
        "temporal_effect": "2026-08-20T12:00Z",
        "quality_effect": "accepted",
        "provenance_effect": "feed-1",
    }
    values.update(changes)
    return CompatibilityEffects(**values)  # type: ignore[arg-type]


def _equivalence(
    left_claim: EvidenceClaim, right_claim: EvidenceClaim, **changes: object
) -> CertifiedSemanticEquivalence:
    values: dict[str, object] = {
        "decision_id": "equivalence-1",
        "decision_version": "1.0.0",
        "certification_id": "cert-1",
        "left": left_claim.identity,
        "right": right_claim.identity,
        "consumer_scope": "H1",
        "dimensions": tuple(sorted(EquivalenceValidator._REQUIRED_DIMENSIONS)),
        "evidence_references": (left_claim.evidence_id, right_claim.evidence_id),
        "symmetric": True,
    }
    values.update(changes)
    return CertifiedSemanticEquivalence(**values)  # type: ignore[arg-type]


def _conflict_policy(**changes: object) -> ConsumerConflictPolicy:
    values: dict[str, object] = {
        "policy_id": "conflict-1",
        "policy_version": "1.0.0",
        "interpretation": "preserve",
        "min_cardinality": 1,
        "max_cardinality": 2,
        "ordering": ("canonical",),
        "output_semantics": "diagnose",
    }
    values.update(changes)
    return ConsumerConflictPolicy(**values)  # type: ignore[arg-type]


def test_compatibility_accepts_authoritative_bound_facts() -> None:
    CompatibilityEvaluator.evaluate(
        _claim(), _requirement(), _claim(), _decision(), _certification(), _effects()
    )


@pytest.mark.parametrize(
    "change",
    [
        {"source_reference": "other"},
        {"target_reference": "other"},
        {"direction": "target-to-source"},
        {"version_scope": (("source", "2.0.0"), ("target", "1.0.0"))},
        {"profile_scope": (("scope", "M15"),)},
        {"intended_use": "other"},
    ],
)
def test_compatibility_rejects_mismatched_decision(change: dict[str, object]) -> None:
    with pytest.raises(DataIntegrityError, match="INCOMPATIBLE_DEPENDENCY"):
        CompatibilityEvaluator.evaluate(
            _claim(),
            _requirement(),
            _claim(),
            _decision(**change),
            _certification(),
            _effects(),
        )


@pytest.mark.parametrize(
    "change",
    [
        {"verdict": "failed"},
        {"producer_identity": "other"},
        {"producer_version": "2.0.0"},
        {"capability_references": (("other", "1.0.0"),)},
        {"evidence_references": ("other",)},
    ],
)
def test_compatibility_rejects_invalid_certification(change: dict[str, object]) -> None:
    with pytest.raises(DataIntegrityError, match="EXPIRED_OR_REVOKED_CERTIFICATION"):
        CompatibilityEvaluator.evaluate(
            _claim(),
            _requirement(),
            _claim(),
            _decision(),
            _certification(**change),
            _effects(),
        )


@pytest.mark.parametrize(
    "change, diagnostic",
    [
        ({"decision_reference": "other"}, "INCOMPATIBLE_DEPENDENCY"),
        ({"effects_version": "2.0.0"}, "INCOMPATIBLE_DEPENDENCY"),
        ({"declared_losses": ("precision",)}, "HIDDEN_CONVERSION_ATTEMPT"),
    ],
)
def test_compatibility_rejects_unbound_or_lossy_effects(
    change: dict[str, object], diagnostic: str
) -> None:
    with pytest.raises(DataIntegrityError, match=diagnostic):
        CompatibilityEvaluator.evaluate(
            _claim(),
            _requirement(),
            _claim(),
            _decision(),
            _certification(),
            _effects(**change),
        )


@pytest.mark.parametrize("field", ["conversion", "narrowing", "widening"])
def test_compatibility_requires_each_transformation_to_be_declared(field: str) -> None:
    with pytest.raises(DataIntegrityError, match="HIDDEN_CONVERSION_ATTEMPT"):
        CompatibilityEvaluator.evaluate(
            _claim(),
            _requirement(),
            _claim(),
            _decision(),
            _certification(),
            _effects(**{field: "explicit-transform"}),
        )
    changed_target = _claim(claim="bearish")
    CompatibilityEvaluator.evaluate(
        _claim(),
        _requirement(),
        changed_target,
        _decision(),
        _certification(),
        _effects(**{field: "bearish"}),
    )


def test_compatibility_rejects_changed_claim_without_exact_transformation() -> None:
    with pytest.raises(DataIntegrityError, match="one exact declared transformation"):
        CompatibilityEvaluator.evaluate(
            _claim(),
            _requirement(),
            _claim(claim="bearish"),
            _decision(),
            _certification(),
            _effects(),
        )


def test_compatibility_requires_one_exact_target_provenance_fact() -> None:
    two_references = (
        ProvenanceReference("feed-1", "feed", "1.0.0"),
        ProvenanceReference("feed-2", "feed", "1.0.0"),
    )
    with pytest.raises(DataIntegrityError, match="one exact immutable target reference"):
        CompatibilityEvaluator.evaluate(
            _claim(),
            _requirement(),
            _claim(provenance=two_references),
            _decision(),
            _certification(),
            _effects(),
        )
    digest_reference = ProvenanceReference("feed-1", "feed", "1.0.0", "digest-1")
    CompatibilityEvaluator.evaluate(
        _claim(),
        _requirement(),
        _claim(provenance=(digest_reference,)),
        _decision(),
        _certification(),
        _effects(provenance_effect="digest-1"),
    )


@pytest.mark.parametrize(
    ("field", "target_change", "effect_value", "diagnostic"),
    [
        ("unit_effect", {"units": "points"}, "points", "unit effect"),
        (
            "completeness_effect",
            {"completeness": replace(_claim().completeness, state=SemanticState("PARTIAL"))},
            "PARTIAL",
            "completeness effect",
        ),
        (
            "temporal_effect",
            {"boundary": replace(_claim().boundary, temporal_boundary="next-window")},
            "next-window",
            "temporal effect",
        ),
        (
            "quality_effect",
            {"quality": replace(_claim().quality, grade="reviewed")},
            "reviewed",
            "quality effect",
        ),
        (
            "provenance_effect",
            {"provenance": (ProvenanceReference("feed-2", "feed", "1.0.0"),)},
            "feed-2",
            "provenance effect",
        ),
    ],
)
def test_compatibility_validates_each_effect_against_target_facts(
    field: str,
    target_change: dict[str, object],
    effect_value: str,
    diagnostic: str,
) -> None:
    target_claim = _claim(**target_change)
    with pytest.raises(DataIntegrityError, match=diagnostic):
        CompatibilityEvaluator.evaluate(
            _claim(),
            _requirement(),
            target_claim,
            _decision(),
            _certification(),
            _effects(**{field: "changed"}),
        )
    CompatibilityEvaluator.evaluate(
        _claim(),
        _requirement(),
        target_claim,
        _decision(),
        _certification(),
        _effects(**{field: effect_value}),
    )


def test_equivalence_uses_certified_record_and_claims() -> None:
    left = _claim()
    right = _claim(evidence_id="evidence-2", content_identity="content-2")
    assert EquivalenceValidator.equivalent(left, right, _equivalence(left, right))
    assert EquivalenceValidator.equivalent(right, left, _equivalence(left, right))


def test_equivalence_accepts_distinct_certified_semantic_identities() -> None:
    left = _claim()
    right = _claim(
        evidence_id="evidence-2",
        identity=_identity(evidence_type="market.trend", semantic_version="2.0.0"),
        content_identity="content-2",
    )
    certification = _equivalence(left, right)
    assert EquivalenceValidator.equivalent(left, right, certification)
    assert EquivalenceValidator.equivalent(right, left, certification)
    asymmetric = replace(certification, symmetric=False)
    with pytest.raises(DataIntegrityError, match="equivalence identities"):
        EquivalenceValidator.equivalent(right, left, asymmetric)


@pytest.mark.parametrize(
    "change",
    [
        {"right": _identity(subject="GBPUSD")},
        {"consumer_scope": "M15"},
        {"dimensions": ("scope",)},
        {"evidence_references": ("evidence-1",)},
    ],
)
def test_equivalence_rejects_invalid_certified_binding(change: dict[str, object]) -> None:
    left = _claim()
    right = _claim(evidence_id="evidence-2", content_identity="content-2")
    with pytest.raises(DataIntegrityError, match="SEMANTIC_INCONSISTENCY"):
        EquivalenceValidator.equivalent(left, right, _equivalence(left, right, **change))


@pytest.mark.parametrize(
    "field, value",
    [
        ("value_domain", "other"),
        ("claim", "bearish"),
        ("units", "points"),
        ("boundary", SemanticBoundary("EURUSD", "H1", "live-candle", "2026-08-20T12:00Z")),
        ("boundary", SemanticBoundary("EURUSD", "H1", "closed-candle", "other")),
        ("validity", ValidityMetadata("other", True, "boundary-1")),
        (
            "completeness",
            CompletenessMetadata(
                SemanticState("PRESENT"), ("other",), 1, ("H1",), ("trend",), True
            ),
        ),
        ("assumptions", AssumptionMetadata("2.0.0", ("other",))),
        ("provenance", (ProvenanceReference("other", "feed", "1.0.0"),)),
    ],
)
def test_equivalence_computes_every_semantic_dimension(field: str, value: object) -> None:
    left = _claim()
    right = cast(
        EvidenceClaim,
        _unsafe_replace(_claim(evidence_id="evidence-2"), **{field: value}),
    )
    assert not EquivalenceValidator.equivalent(left, right, _equivalence(left, right))


def test_conflict_is_computed_from_claims_and_policy() -> None:
    left = _claim()
    right = _claim(evidence_id="evidence-2", claim="bearish", content_identity="content-2")
    assert ConflictDetector.conflicts(left, right, _conflict_policy())
    assert not ConflictDetector.conflicts(
        left, _claim(evidence_id="evidence-2"), _conflict_policy()
    )
    assert not ConflictDetector.conflicts(
        left,
        _claim(evidence_id="evidence-2", identity=_identity(subject="GBPUSD")),
        _conflict_policy(),
    )


@pytest.mark.parametrize(
    ("change", "diagnostic"),
    [
        ({"max_cardinality": 1}, "CARDINALITY_VIOLATION"),
        ({"min_cardinality": 3, "max_cardinality": 3}, "CARDINALITY_VIOLATION"),
    ],
)
def test_conflict_policy_must_cover_and_preserve_conflict(
    change: dict[str, object], diagnostic: str
) -> None:
    left = _claim()
    right = _claim(evidence_id="evidence-2", claim="bearish", content_identity="content-2")
    with pytest.raises(DataIntegrityError, match=diagnostic):
        ConflictDetector.conflicts(left, right, _conflict_policy(**change))


def test_conflict_policy_accepts_declared_values_without_fixed_vocabulary() -> None:
    left = _claim()
    right = _claim(evidence_id="evidence-2", claim="bearish", content_identity="content-2")
    policies = (
        _conflict_policy(
            interpretation="retain-both",
            ordering=("consumer-declared-order",),
            output_semantics="emit-conflict-evidence",
        ),
        _conflict_policy(
            interpretation="domain-specific-interpretation",
            ordering=("first-declaration", "second-declaration"),
            output_semantics="consumer-defined-result",
        ),
    )
    assert all(ConflictDetector.conflicts(left, right, policy) for policy in policies)
    assert all(ConflictDetector.conflicts(left, right, policy) for policy in policies)


def test_conflict_requires_the_frozen_policy_model() -> None:
    with pytest.raises(DataIntegrityError, match="immutable ConsumerConflictPolicy"):
        ConflictDetector.conflicts(_claim(), _claim(), cast(Any, object()))


def test_completeness_uses_metadata_and_constraints() -> None:
    SemanticValidator.validate_completeness(
        _requirement(),
        (_claim(),),
        required_dimensions=("structure",),
        required_temporal_windows=("H1",),
        required_facets=("trend",),
    )
    SemanticValidator.validate_completeness(
        _requirement(min_cardinality=1, max_cardinality=1, exact_cardinality=1),
        (_claim(),),
    )


@pytest.mark.parametrize(
    "change, diagnostic",
    [
        ({"dimensions": ()}, "dimensions"),
        ({"temporal_windows": ()}, "temporal"),
        ({"facets": ()}, "facets"),
        ({"provenance_complete": False}, "PROVENANCE"),
        ({"cardinality": 2}, "cardinality"),
    ],
)
def test_completeness_rejects_missing_metadata(change: dict[str, object], diagnostic: str) -> None:
    metadata = cast(CompletenessMetadata, _unsafe_replace(_claim().completeness, **change))
    with pytest.raises(DataIntegrityError, match=diagnostic):
        SemanticValidator.validate_completeness(
            _requirement(),
            (_claim(completeness=metadata),),
            required_dimensions=("structure",),
            required_temporal_windows=("H1",),
            required_facets=("trend",),
        )


@pytest.mark.parametrize("state", sorted(SemanticState.ALLOWED_STATES - {"PRESENT"}))
def test_every_non_present_semantic_state_remains_distinct(state: str) -> None:
    with pytest.raises(DataIntegrityError, match=state):
        SemanticValidator.validate_semantic_state(SemanticState(state))


def test_completeness_rejects_invalid_claim_container_and_cardinality() -> None:
    with pytest.raises(DataIntegrityError, match="immutable EvidenceClaim"):
        SemanticValidator.validate_completeness(_requirement(), cast(Any, []))
    with pytest.raises(DataIntegrityError, match="CARDINALITY_VIOLATION"):
        SemanticValidator.validate_completeness(_requirement(), ())


def test_requirement_rejects_mismatch_disposition_and_validity() -> None:
    with pytest.raises(DataIntegrityError, match="SEMANTIC_INCONSISTENCY"):
        SemanticValidator.validate_requirement(
            _requirement(), _claim(identity=_identity(scope="M15"))
        )
    with pytest.raises(DataIntegrityError, match="INVALID_DEPENDENCY"):
        SemanticValidator.validate_requirement(
            _requirement(), _claim(disposition=DispositionAxis.REJECTED)
        )
    with pytest.raises(DataIntegrityError, match="INVALID_DEPENDENCY"):
        SemanticValidator.validate_requirement(
            _requirement(), _claim(validity=ValidityMetadata("closed", False, "boundary"))
        )


def test_redundancy_uses_certification_and_policy_without_collapsing_duplicates() -> None:
    left = _claim()
    right = _claim(evidence_id="evidence-2", content_identity="content-2")
    policy = ExtendedRedundancyPolicy("redundancy", "1.0.0", "RETAIN_FOR_CORROBORATION", True, 1)
    requirement = _requirement(max_cardinality=1)
    assert SemanticValidator.is_redundant(
        (left, right), requirement, (_equivalence(left, right),), policy
    )
    assert not SemanticValidator.is_redundant(
        (left,), requirement, (_equivalence(left, right),), policy
    )
    assert not SemanticValidator.is_redundant(
        (left, replace(left, evidence_id="evidence-2")),
        requirement,
        (_equivalence(left, right),),
        policy,
    )
    assert not SemanticValidator.is_redundant(
        (left, right),
        _requirement(max_cardinality=2),
        (_equivalence(left, right),),
        policy,
    )
    non_equivalent = _claim(
        evidence_id="evidence-2", content_identity="content-2", value_domain="other"
    )
    assert not SemanticValidator.is_redundant(
        (left, non_equivalent),
        requirement,
        (_equivalence(left, non_equivalent),),
        policy,
    )


def test_redundancy_policy_fails_closed() -> None:
    left = _claim()
    right = _claim(evidence_id="evidence-2", content_identity="content-2")
    with pytest.raises(DataIntegrityError, match="CARDINALITY_VIOLATION"):
        SemanticValidator.is_redundant(
            (left, right),
            _requirement(),
            (_equivalence(left, right),),
            ExtendedRedundancyPolicy("p", "1", "REJECT", False, 1),
        )
    with pytest.raises(DataIntegrityError, match="corroboration"):
        SemanticValidator.is_redundant(
            (left, right),
            _requirement(),
            (_equivalence(left, right),),
            ExtendedRedundancyPolicy("p", "1", "SUPPLY_TO_MULTI_PROVIDER", True, 1),
        )


def test_redundancy_evaluates_every_claim_without_tuple_position_dependency() -> None:
    first = _claim()
    second = _claim(evidence_id="evidence-2", content_identity="content-2")
    third = _claim(evidence_id="evidence-3", content_identity="content-3")
    equivalences = (_equivalence(first, second), _equivalence(first, third))
    policy = ExtendedRedundancyPolicy("redundancy", "1.0.0", "RETAIN_FOR_CORROBORATION", True, 2)
    for ordering in permutations((first, second, third)):
        assert SemanticValidator.is_redundant(ordering, _requirement(), equivalences, policy)


def test_redundancy_rejects_uncovered_conflicting_or_excess_claims() -> None:
    first = _claim()
    second = _claim(evidence_id="evidence-2", content_identity="content-2")
    third = _claim(evidence_id="evidence-3", content_identity="content-3")
    policy = ExtendedRedundancyPolicy("redundancy", "1.0.0", "RETAIN_FOR_CORROBORATION", True, 2)
    with pytest.raises(DataIntegrityError, match="every redundant claim"):
        SemanticValidator.is_redundant(
            (first, second, third),
            _requirement(),
            (_equivalence(first, second),),
            policy,
        )
    conflicting = replace(third, claim="bearish")
    with pytest.raises(DataIntegrityError, match="conflicting claims"):
        SemanticValidator.is_redundant(
            (first, second, conflicting),
            _requirement(),
            (_equivalence(first, second), _equivalence(first, conflicting)),
            policy,
        )
    with pytest.raises(DataIntegrityError, match="CARDINALITY_VIOLATION"):
        SemanticValidator.is_redundant(
            (first, second, third),
            _requirement(),
            (_equivalence(first, second), _equivalence(first, third)),
            replace(policy, max_redundant_inputs=1),
        )
    duplicate = replace(third, content_identity=second.content_identity)
    assert not SemanticValidator.is_redundant(
        (first, second, duplicate),
        _requirement(),
        (_equivalence(first, second), _equivalence(first, duplicate)),
        policy,
    )


def test_redundancy_requires_immutable_certification_collection() -> None:
    left = _claim()
    right = _claim(evidence_id="evidence-2", content_identity="content-2")
    policy = ExtendedRedundancyPolicy("p", "1", "RETAIN_FOR_CORROBORATION", False, 1)
    with pytest.raises(DataIntegrityError, match="immutable tuple"):
        SemanticValidator.is_redundant(
            (left, right),
            _requirement(),
            cast(Any, [_equivalence(left, right)]),
            policy,
        )


def test_independence_uses_material_source_and_derivation_policy() -> None:
    left = _claim()
    shared_source = _claim(evidence_id="evidence-2", source_identity="different-producer")
    policy = IndependencePolicy("independence", "1.0.0", ("feed",), ("derived",))
    assert not IndependenceChecker.independent(left, shared_source, policy)
    other = _claim(
        evidence_id="evidence-2",
        provenance=(ProvenanceReference("feed-2", "feed", "1.0.0"),),
    )
    assert IndependenceChecker.independent(left, other, policy)
    derived_left = _claim(provenance=(ProvenanceReference("base", "derived", "1.0.0"),))
    derived_right = _claim(
        evidence_id="evidence-2",
        provenance=(ProvenanceReference("base", "derived", "1.0.0"),),
    )
    assert not IndependenceChecker.independent(derived_left, derived_right, policy)
    ignored = IndependencePolicy("independence", "1.0.0", ("official",), ("derived",))
    assert IndependenceChecker.independent(left, shared_source, ignored)


def test_repeated_reconstructed_inputs_are_deterministic_and_immutable() -> None:
    source = _claim()
    target = _requirement()
    target_claim = _claim()
    decision = _decision()
    certification = _certification()
    effects = _effects()
    original_hashes = tuple(
        hash(item) for item in (source, target, target_claim, decision, certification, effects)
    )
    for _ in range(3):
        CompatibilityEvaluator.evaluate(
            replace(source),
            replace(target),
            replace(target_claim),
            replace(decision),
            replace(certification),
            replace(effects),
        )
    assert original_hashes == tuple(
        hash(item) for item in (source, target, target_claim, decision, certification, effects)
    )


def test_fail_closed_diagnostics_are_stable_and_direction_remains_intentional() -> None:
    messages: list[str] = []
    for _ in range(3):
        with pytest.raises(DataIntegrityError) as captured:
            CompatibilityEvaluator.evaluate(
                _claim(),
                _requirement(),
                _claim(),
                _decision(direction="target-to-source"),
                _certification(),
                _effects(),
            )
        messages.append(str(captured.value))
    assert len(set(messages)) == 1
    assert "compatibility direction is invalid" in messages[0]


def test_independence_is_invariant_to_lineage_order() -> None:
    first = ProvenanceReference("feed-1", "feed", "1.0.0")
    second = ProvenanceReference("feed-2", "feed", "1.0.0")
    unrelated = ProvenanceReference("feed-3", "feed", "1.0.0")
    policy = IndependencePolicy("independence", "1.0.0", ("feed",), ("derived",))
    left = _claim(provenance=(first, second))
    right = _claim(evidence_id="evidence-2", provenance=(unrelated,))
    assert IndependenceChecker.independent(left, right, policy)
    assert IndependenceChecker.independent(replace(left, provenance=(second, first)), right, policy)
