"""Unit tests for A04-E00 evidence and dependency semantic domain models."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from typing import Any, cast

import pytest

from epip.core.integrity import (
    DataIntegrityError,
    MissingFieldError,
    NumericIntegrityError,
)
from epip.evidence.model import (
    AssumptionMetadata,
    CertifiedSemanticEquivalence,
    CompatibilityEffects,
    CompletenessMetadata,
    ConsumerConflictPolicy,
    DependencyType,
    DiagnosticCode,
    DiagnosticReason,
    DispositionAxis,
    EvidenceCategory,
    EvidenceClaim,
    EvidenceRequirement,
    EvidenceTaxonomy,
    EvidenceTypeDefinition,
    ExtendedRedundancyPolicy,
    IndependencePolicy,
    ProvenanceAxis,
    ProvenanceReference,
    QualityMetadata,
    ResolutionProfile,
    RetentionAxis,
    SemanticBoundary,
    SemanticIdentity,
    SemanticState,
    TemporalAxis,
    ValidityMetadata,
)


def _unsafe_replace(value: object, **changes: object) -> object:
    """Construct deliberately invalid dataclass values for negative tests."""

    return cast(object, replace(cast(Any, value), **changes))


def test_taxonomy_axes_and_categories_enum_members() -> None:
    """Verify all defined taxonomy axes and evidence categories."""
    assert set(ProvenanceAxis) == {
        ProvenanceAxis.PRIMARY,
        ProvenanceAxis.DERIVED,
        ProvenanceAxis.SECONDARY,
        ProvenanceAxis.SYNTHETIC,
        ProvenanceAxis.COMPOSITE,
    }
    assert set(DispositionAxis) == {DispositionAxis.ACCEPTED, DispositionAxis.REJECTED}
    assert set(TemporalAxis) == {TemporalAxis.HISTORICAL, TemporalAxis.CURRENT}
    assert set(RetentionAxis) == {RetentionAxis.TRANSIENT, RetentionAxis.PERSISTENT}
    assert len(EvidenceCategory) == 12
    assert EvidenceCategory.STRUCTURAL == "STRUCTURAL"
    assert EvidenceCategory.WAVE == "WAVE"


def test_dependency_type_and_diagnostic_codes() -> None:
    """Verify dependency types and diagnostic reason codes."""
    assert set(DependencyType) == {
        DependencyType.MANDATORY,
        DependencyType.OPTIONAL,
        DependencyType.CONDITIONAL,
        DependencyType.DERIVED,
        DependencyType.TRANSITIVE,
        DependencyType.FORBIDDEN,
    }
    assert DiagnosticCode.MISSING_MANDATORY_DEPENDENCY == "MISSING_MANDATORY_DEPENDENCY"
    assert DiagnosticCode.CYCLIC_DEPENDENCY == "CYCLIC_DEPENDENCY"
    assert DiagnosticCode.AMBIGUOUS_DEPENDENCY == "AMBIGUOUS_DEPENDENCY"


def test_provenance_reference_integrity_and_immutability() -> None:
    """Verify ProvenanceReference validation, immutability, and equality."""
    ref = ProvenanceReference(
        source_id="src-001",
        source_type="PRODUCER",
        semantic_version="1.0.0",
        content_digest="sha256:abc",
    )
    assert ref.source_id == "src-001"
    assert ref.content_digest == "sha256:abc"

    # Immutability check
    with pytest.raises((AttributeError, TypeError)):
        ref.source_id = "mutated"  # type: ignore[misc]

    # Validation checks
    with pytest.raises(MissingFieldError):
        ProvenanceReference(source_id="", source_type="PRODUCER", semantic_version="1.0.0")
    with pytest.raises(MissingFieldError):
        ProvenanceReference(source_id="src", source_type="  ", semantic_version="1.0.0")
    with pytest.raises(MissingFieldError):
        ProvenanceReference(source_id="src", source_type="PRODUCER", semantic_version="")
    with pytest.raises(MissingFieldError):
        ProvenanceReference(
            source_id="src", source_type="PRODUCER", semantic_version="1.0.0", content_digest=""
        )


def test_evidence_taxonomy_integrity() -> None:
    """Verify EvidenceTaxonomy validation and immutability."""
    taxonomy = EvidenceTaxonomy(
        provenance=ProvenanceAxis.PRIMARY,
        disposition=DispositionAxis.ACCEPTED,
        temporal=TemporalAxis.CURRENT,
        retention=RetentionAxis.TRANSIENT,
    )
    assert taxonomy.provenance == ProvenanceAxis.PRIMARY

    with pytest.raises((AttributeError, TypeError)):
        taxonomy.provenance = ProvenanceAxis.DERIVED  # type: ignore[misc]

    with pytest.raises(DataIntegrityError):
        EvidenceTaxonomy(
            provenance="INVALID",  # type: ignore[arg-type]
            disposition=DispositionAxis.ACCEPTED,
            temporal=TemporalAxis.CURRENT,
            retention=RetentionAxis.TRANSIENT,
        )
    with pytest.raises(DataIntegrityError):
        EvidenceTaxonomy(
            provenance=ProvenanceAxis.PRIMARY,
            disposition="INVALID",  # type: ignore[arg-type]
            temporal=TemporalAxis.CURRENT,
            retention=RetentionAxis.TRANSIENT,
        )
    with pytest.raises(DataIntegrityError):
        EvidenceTaxonomy(
            provenance=ProvenanceAxis.PRIMARY,
            disposition=DispositionAxis.ACCEPTED,
            temporal="INVALID",  # type: ignore[arg-type]
            retention=RetentionAxis.TRANSIENT,
        )
    with pytest.raises(DataIntegrityError):
        EvidenceTaxonomy(
            provenance=ProvenanceAxis.PRIMARY,
            disposition=DispositionAxis.ACCEPTED,
            temporal=TemporalAxis.CURRENT,
            retention="INVALID",  # type: ignore[arg-type]
        )


def test_semantic_identity_integrity() -> None:
    """Verify SemanticIdentity validation and immutability."""
    identity = SemanticIdentity(
        evidence_type="SWING_PIVOT",
        semantic_version="1.2.0",
        subject="EURUSD",
        scope="M15",
    )
    assert identity.evidence_type == "SWING_PIVOT"

    with pytest.raises(MissingFieldError):
        SemanticIdentity(
            evidence_type="",
            semantic_version="1.2.0",
            subject="EURUSD",
            scope="M15",
        )
    with pytest.raises(MissingFieldError):
        SemanticIdentity(
            evidence_type="SWING_PIVOT",
            semantic_version="",
            subject="EURUSD",
            scope="M15",
        )
    with pytest.raises(MissingFieldError):
        SemanticIdentity(
            evidence_type="SWING_PIVOT",
            semantic_version="1.2.0",
            subject="",
            scope="M15",
        )
    with pytest.raises(MissingFieldError):
        SemanticIdentity(
            evidence_type="SWING_PIVOT",
            semantic_version="1.2.0",
            subject="EURUSD",
            scope="",
        )


def test_resolution_profile_integrity() -> None:
    """Verify ResolutionProfile validation and immutability."""
    profile = ResolutionProfile(
        profile_id="profile-strict",
        profile_version="1.0.0",
        pinned_producer_id="producer-swing-v1",
        allow_redundancy=True,
        allow_multi_provider=False,
    )
    assert profile.pinned_producer_id == "producer-swing-v1"
    assert profile.allow_redundancy is True

    with pytest.raises(MissingFieldError):
        ResolutionProfile(profile_id="", profile_version="1.0.0")

    with pytest.raises(MissingFieldError):
        ResolutionProfile(profile_id="p1", profile_version="")

    with pytest.raises(MissingFieldError):
        ResolutionProfile(profile_id="p1", profile_version="1.0.0", pinned_producer_id="")

    with pytest.raises(DataIntegrityError):
        ResolutionProfile(
            profile_id="p1",
            profile_version="1.0.0",
            allow_redundancy="not-a-bool",  # type: ignore[arg-type]
        )

    with pytest.raises(DataIntegrityError):
        ResolutionProfile(
            profile_id="p1",
            profile_version="1.0.0",
            allow_multi_provider="not-a-bool",  # type: ignore[arg-type]
        )


def test_evidence_requirement_cardinality_and_validation() -> None:
    """Verify EvidenceRequirement validation, cardinality constraints, and immutability."""
    ref = ProvenanceReference(source_id="s1", source_type="PRODUCER", semantic_version="1.0.0")
    req = EvidenceRequirement(
        requirement_id="req-001",
        evidence_type="SWING_PIVOT",
        semantic_version="1.0.0",
        subject="BTCUSD",
        scope="H1",
        dependency_type=DependencyType.MANDATORY,
        min_cardinality=1,
        max_cardinality=2,
        exact_cardinality=None,
        resolution_profile_id="prof-1",
        absence_semantics="NULL_ALLOWED",
        predicate="COND_TRUE",
        provenance_constraints=(ref,),
    )
    assert req.requirement_id == "req-001"
    assert req.resolution_profile_id == "prof-1"
    assert req.absence_semantics == "NULL_ALLOWED"
    assert req.predicate == "COND_TRUE"
    assert len(req.provenance_constraints) == 1

    # Exact cardinality match
    req_exact = EvidenceRequirement(
        requirement_id="req-002",
        evidence_type="SWING_PIVOT",
        semantic_version="1.0.0",
        subject="BTCUSD",
        scope="H1",
        dependency_type=DependencyType.MANDATORY,
        min_cardinality=3,
        max_cardinality=3,
        exact_cardinality=3,
    )
    assert req_exact.exact_cardinality == 3

    # String errors
    with pytest.raises(MissingFieldError):
        EvidenceRequirement(
            requirement_id="",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
        )
    with pytest.raises(MissingFieldError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
        )
    with pytest.raises(MissingFieldError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
        )
    with pytest.raises(MissingFieldError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
        )
    with pytest.raises(MissingFieldError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="",
            dependency_type=DependencyType.MANDATORY,
        )

    # Optional string field empty errors
    with pytest.raises(MissingFieldError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            resolution_profile_id="",
        )
    with pytest.raises(MissingFieldError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            absence_semantics="",
        )
    with pytest.raises(MissingFieldError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            predicate="",
        )

    # Cardinality errors
    with pytest.raises(NumericIntegrityError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            min_cardinality=True,
        )
    with pytest.raises(NumericIntegrityError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            min_cardinality=-1,
        )
    with pytest.raises(NumericIntegrityError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            max_cardinality=False,
        )
    with pytest.raises(NumericIntegrityError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            min_cardinality=5,
            max_cardinality=2,
        )
    with pytest.raises(NumericIntegrityError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            exact_cardinality=True,
        )
    with pytest.raises(NumericIntegrityError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            min_cardinality=1,
            max_cardinality=1,
            exact_cardinality=-1,
        )
    with pytest.raises(DataIntegrityError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            min_cardinality=1,
            max_cardinality=2,
            exact_cardinality=3,
        )

    with pytest.raises(DataIntegrityError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type="NOT_A_DEP_TYPE",  # type: ignore[arg-type]
        )

    with pytest.raises(DataIntegrityError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            provenance_constraints=["not-a-tuple"],  # type: ignore[arg-type]
        )

    with pytest.raises(DataIntegrityError):
        EvidenceRequirement(
            requirement_id="r1",
            evidence_type="T",
            semantic_version="1",
            subject="S",
            scope="SC",
            dependency_type=DependencyType.MANDATORY,
            provenance_constraints=("not-a-provenance-ref",),  # type: ignore[arg-type]
        )


def test_diagnostic_reason_integrity() -> None:
    """Verify DiagnosticReason validation and immutability."""
    diag = DiagnosticReason(
        code=DiagnosticCode.INCOMPATIBLE_DEPENDENCY,
        requirement_id="req-123",
        reason="Unit mismatch between radians and degrees",
        candidate_id="cand-001",
        semantic_version="2.0.0",
    )
    assert diag.code == DiagnosticCode.INCOMPATIBLE_DEPENDENCY
    assert diag.candidate_id == "cand-001"
    assert diag.semantic_version == "2.0.0"
    assert (
        DiagnosticReason(
            code=DiagnosticCode.AMBIGUOUS_DEPENDENCY,
            requirement_id="req-optional-version",
            reason="No candidate supplied",
            candidate_id="cand-optional-version",
        ).semantic_version
        is None
    )

    with pytest.raises(DataIntegrityError):
        DiagnosticReason(
            code="INVALID_CODE",  # type: ignore[arg-type]
            requirement_id="req",
            reason="some reason",
        )

    with pytest.raises(MissingFieldError):
        DiagnosticReason(
            code=DiagnosticCode.AMBIGUOUS_DEPENDENCY,
            requirement_id="",
            reason="some reason",
        )

    with pytest.raises(MissingFieldError):
        DiagnosticReason(
            code=DiagnosticCode.AMBIGUOUS_DEPENDENCY,
            requirement_id="req",
            reason="",
        )

    with pytest.raises(MissingFieldError):
        DiagnosticReason(
            code=DiagnosticCode.AMBIGUOUS_DEPENDENCY,
            requirement_id="req",
            reason="some reason",
            candidate_id="",
        )

    with pytest.raises(MissingFieldError):
        DiagnosticReason(
            code=DiagnosticCode.AMBIGUOUS_DEPENDENCY,
            requirement_id="req",
            reason="some reason",
            semantic_version="",
        )


def test_evidence_type_definition_integrity() -> None:
    """Verify EvidenceTypeDefinition validation and immutability."""
    taxonomy = EvidenceTaxonomy(
        provenance=ProvenanceAxis.DERIVED,
        disposition=DispositionAxis.ACCEPTED,
        temporal=TemporalAxis.CURRENT,
        retention=RetentionAxis.PERSISTENT,
    )
    definition = EvidenceTypeDefinition(
        evidence_type="ORDER_BLOCK",
        semantic_version="1.0.0",
        category=EvidenceCategory.LIQUIDITY,
        taxonomy=taxonomy,
        value_domain="price_interval",
        units="USD",
        description="Institutional order block zone",
    )
    assert definition.category == EvidenceCategory.LIQUIDITY
    assert definition.units == "USD"
    assert definition.description == "Institutional order block zone"

    with pytest.raises(MissingFieldError):
        EvidenceTypeDefinition(
            evidence_type="",
            semantic_version="1.0.0",
            category=EvidenceCategory.LIQUIDITY,
            taxonomy=taxonomy,
            value_domain="price_interval",
        )

    with pytest.raises(MissingFieldError):
        EvidenceTypeDefinition(
            evidence_type="ORDER_BLOCK",
            semantic_version="",
            category=EvidenceCategory.LIQUIDITY,
            taxonomy=taxonomy,
            value_domain="price_interval",
        )

    with pytest.raises(MissingFieldError):
        EvidenceTypeDefinition(
            evidence_type="ORDER_BLOCK",
            semantic_version="1.0.0",
            category=EvidenceCategory.LIQUIDITY,
            taxonomy=taxonomy,
            value_domain="",
        )

    with pytest.raises(MissingFieldError):
        EvidenceTypeDefinition(
            evidence_type="ORDER_BLOCK",
            semantic_version="1.0.0",
            category=EvidenceCategory.LIQUIDITY,
            taxonomy=taxonomy,
            value_domain="price_interval",
            units="",
        )

    with pytest.raises(MissingFieldError):
        EvidenceTypeDefinition(
            evidence_type="ORDER_BLOCK",
            semantic_version="1.0.0",
            category=EvidenceCategory.LIQUIDITY,
            taxonomy=taxonomy,
            value_domain="price_interval",
            description=None,  # type: ignore[arg-type]
        )

    with pytest.raises(DataIntegrityError):
        EvidenceTypeDefinition(
            evidence_type="ORDER_BLOCK",
            semantic_version="1.0.0",
            category="INVALID_CAT",  # type: ignore[arg-type]
            taxonomy=taxonomy,
            value_domain="price_interval",
        )

    with pytest.raises(DataIntegrityError):
        EvidenceTypeDefinition(
            evidence_type="ORDER_BLOCK",
            semantic_version="1.0.0",
            category=EvidenceCategory.LIQUIDITY,
            taxonomy="INVALID_TAXONOMY",  # type: ignore[arg-type]
            value_domain="price_interval",
        )


def _amended_models() -> dict[str, object]:
    identity = SemanticIdentity("SWING_PIVOT", "1.0.0", "EURUSD", "M15")
    boundary = SemanticBoundary("EURUSD", "M15", "context:session", "window:2026-08-20")
    state = SemanticState("PRESENT", "complete observation")
    validity = ValidityMetadata("valid within the frozen boundary", True, "boundary:1")
    completeness = CompletenessMetadata(
        state,
        ("price", "direction"),
        1,
        ("window:2026-08-20",),
        ("pivot",),
        True,
    )
    quality = QualityMetadata(
        "quality:strict",
        "1.0.0",
        "CERTIFIED",
        (("confidence-band", "declared"),),
    )
    assumptions = AssumptionMetadata("1.0.0", ("frozen-input-boundary",))
    provenance = ProvenanceReference("producer:1", "PRODUCER", "1.0.0", "sha256:source")
    equivalence = CertifiedSemanticEquivalence(
        "equivalence:1",
        "1.0.0",
        "certification:1",
        identity,
        identity,
        "consumer:validation",
        ("type", "scope", "units", "temporal"),
        ("evidence:certification",),
        True,
    )
    effects = CompatibilityEffects(
        "compatibility:1",
        "1.0.0",
        None,
        None,
        None,
        "UNCHANGED",
        "PRESERVED",
        "SAME_BOUNDARY",
        "PRESERVED",
        "PRESERVED",
        (),
    )
    conflict_policy = ConsumerConflictPolicy(
        "conflict:strict",
        "1.0.0",
        "REJECT",
        1,
        2,
        ("CANONICAL_IDENTITY",),
        "NO_OUTPUT_ON_CONFLICT",
    )
    redundancy_policy = ExtendedRedundancyPolicy(
        "redundancy:retain",
        "1.0.0",
        "RETAIN_FOR_CORROBORATION",
        True,
        2,
    )
    independence_policy = IndependencePolicy(
        "independence:source",
        "1.0.0",
        ("PRODUCER",),
        ("DERIVED",),
    )
    claim = EvidenceClaim(
        "evidence:1",
        identity,
        "producer:1",
        "implementation:1.0.0",
        boundary,
        "swing pivot at the frozen boundary",
        "price-point",
        "USD",
        validity,
        completeness,
        quality,
        assumptions,
        (provenance,),
        "sha256:evidence",
        DispositionAxis.ACCEPTED,
    )
    return {
        "boundary": boundary,
        "validity": validity,
        "state": state,
        "completeness": completeness,
        "quality": quality,
        "assumptions": assumptions,
        "equivalence": equivalence,
        "effects": effects,
        "conflict_policy": conflict_policy,
        "redundancy_policy": redundancy_policy,
        "independence_policy": independence_policy,
        "claim": claim,
    }


def test_amended_models_are_frozen_slotted_hashable_and_deterministic() -> None:
    for value in _amended_models().values():
        assert is_dataclass(value)
        assert hasattr(type(value), "__slots__")
        duplicate = _unsafe_replace(value)
        assert hash(value) == hash(duplicate)
        assert value == duplicate
        first_field = fields(value)[0].name
        with pytest.raises(FrozenInstanceError):
            setattr(value, first_field, getattr(value, first_field))


def test_semantic_states_remain_distinct() -> None:
    states = {
        SemanticState(name)
        for name in (
            "PRESENT",
            "ABSENT",
            "VALID_EMPTY",
            "PARTIAL",
            "REJECTED",
            "INVALID",
            "UNAVAILABLE",
        )
    }
    assert len(states) == 7
    assert states == {SemanticState(name) for name in SemanticState.ALLOWED_STATES}


@pytest.mark.parametrize("field", ["subject", "scope", "context_boundary", "temporal_boundary"])
def test_semantic_boundary_rejects_missing_metadata(field: str) -> None:
    boundary = _amended_models()["boundary"]
    assert isinstance(boundary, SemanticBoundary)
    with pytest.raises(MissingFieldError):
        _unsafe_replace(boundary, **{field: ""})


def test_validity_metadata_rejects_invalid_inputs() -> None:
    validity = _amended_models()["validity"]
    assert isinstance(validity, ValidityMetadata)
    with pytest.raises(MissingFieldError):
        replace(validity, semantics="")
    with pytest.raises(DataIntegrityError):
        replace(validity, is_valid="yes")  # type: ignore[arg-type]
    with pytest.raises(MissingFieldError):
        replace(validity, boundary_reference="")


def test_semantic_state_rejects_unknown_or_empty_detail() -> None:
    with pytest.raises(DataIntegrityError):
        SemanticState("UNKNOWN")
    with pytest.raises(MissingFieldError):
        SemanticState("PRESENT", "")


def test_completeness_metadata_rejects_invalid_inputs() -> None:
    completeness = _amended_models()["completeness"]
    assert isinstance(completeness, CompletenessMetadata)
    with pytest.raises(DataIntegrityError):
        replace(completeness, state="PRESENT")  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        replace(completeness, dimensions=["price"])  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        replace(completeness, dimensions=(object(),))  # type: ignore[arg-type]
    with pytest.raises(MissingFieldError):
        replace(completeness, dimensions=("",))
    with pytest.raises(DataIntegrityError):
        replace(completeness, dimensions=("price", "price"))
    with pytest.raises(NumericIntegrityError):
        replace(completeness, cardinality=True)
    with pytest.raises(NumericIntegrityError):
        replace(completeness, cardinality=-1)
    with pytest.raises(DataIntegrityError):
        replace(completeness, temporal_windows=["window"])  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        replace(completeness, facets=["facet"])  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        replace(completeness, provenance_complete="yes")  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["profile_id", "profile_version", "grade"])
def test_quality_metadata_rejects_missing_identity(field: str) -> None:
    quality = _amended_models()["quality"]
    assert isinstance(quality, QualityMetadata)
    with pytest.raises(MissingFieldError):
        _unsafe_replace(quality, **{field: ""})


def test_quality_metadata_rejects_invalid_measurements() -> None:
    quality = _amended_models()["quality"]
    assert isinstance(quality, QualityMetadata)
    with pytest.raises(DataIntegrityError):
        _unsafe_replace(quality, measurements=[])
    with pytest.raises(DataIntegrityError):
        _unsafe_replace(quality, measurements=(("name",),))
    with pytest.raises(MissingFieldError):
        replace(quality, measurements=(("", "value"),))
    with pytest.raises(MissingFieldError):
        replace(quality, measurements=(("name", ""),))
    with pytest.raises(DataIntegrityError):
        replace(quality, measurements=(("name", "one"), ("name", "two")))


def test_assumption_metadata_requires_versioned_nonempty_assumptions() -> None:
    assumptions = _amended_models()["assumptions"]
    assert isinstance(assumptions, AssumptionMetadata)
    with pytest.raises(MissingFieldError):
        replace(assumptions, assumption_version="")
    with pytest.raises(MissingFieldError):
        replace(assumptions, assumptions=())


@pytest.mark.parametrize(
    "field",
    ["decision_id", "decision_version", "certification_id", "consumer_scope"],
)
def test_equivalence_requires_complete_identity(field: str) -> None:
    equivalence = _amended_models()["equivalence"]
    assert isinstance(equivalence, CertifiedSemanticEquivalence)
    with pytest.raises(MissingFieldError):
        _unsafe_replace(equivalence, **{field: ""})


def test_equivalence_requires_certified_scope_and_dimensions() -> None:
    equivalence = _amended_models()["equivalence"]
    assert isinstance(equivalence, CertifiedSemanticEquivalence)
    with pytest.raises(DataIntegrityError):
        replace(equivalence, left="identity")  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        replace(equivalence, right="identity")  # type: ignore[arg-type]
    with pytest.raises(MissingFieldError):
        replace(equivalence, dimensions=())
    with pytest.raises(MissingFieldError):
        replace(equivalence, evidence_references=())
    with pytest.raises(DataIntegrityError):
        replace(equivalence, symmetric="yes")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field",
    [
        "decision_reference",
        "effects_version",
        "unit_effect",
        "completeness_effect",
        "temporal_effect",
        "quality_effect",
        "provenance_effect",
    ],
)
def test_compatibility_effects_require_complete_metadata(field: str) -> None:
    effects = _amended_models()["effects"]
    assert isinstance(effects, CompatibilityEffects)
    with pytest.raises(MissingFieldError):
        _unsafe_replace(effects, **{field: ""})


@pytest.mark.parametrize("field", ["conversion", "narrowing", "widening"])
def test_compatibility_effects_reject_empty_optional_effect(field: str) -> None:
    effects = _amended_models()["effects"]
    assert isinstance(effects, CompatibilityEffects)
    with pytest.raises(MissingFieldError):
        _unsafe_replace(effects, **{field: ""})


def test_compatibility_effects_accept_declared_transformations_and_losses() -> None:
    effects = _amended_models()["effects"]
    assert isinstance(effects, CompatibilityEffects)
    transformed = replace(
        effects,
        conversion="DECLARED",
        narrowing="SCOPE",
        widening="NONE",
        declared_losses=("precision",),
    )
    assert transformed.conversion == "DECLARED"
    with pytest.raises(DataIntegrityError):
        replace(effects, declared_losses=["precision"])  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field",
    ["policy_id", "policy_version", "interpretation", "output_semantics"],
)
def test_conflict_policy_requires_complete_metadata(field: str) -> None:
    policy = _amended_models()["conflict_policy"]
    assert isinstance(policy, ConsumerConflictPolicy)
    with pytest.raises(MissingFieldError):
        _unsafe_replace(policy, **{field: ""})


@pytest.mark.parametrize(
    ("field", "value"),
    [("min_cardinality", True), ("max_cardinality", -1)],
)
def test_conflict_policy_rejects_invalid_cardinality(field: str, value: object) -> None:
    policy = _amended_models()["conflict_policy"]
    assert isinstance(policy, ConsumerConflictPolicy)
    with pytest.raises(NumericIntegrityError):
        _unsafe_replace(policy, **{field: value})


def test_conflict_policy_rejects_inverted_cardinality_or_missing_order() -> None:
    policy = _amended_models()["conflict_policy"]
    assert isinstance(policy, ConsumerConflictPolicy)
    with pytest.raises(NumericIntegrityError):
        replace(policy, min_cardinality=3, max_cardinality=2)
    with pytest.raises(MissingFieldError):
        replace(policy, ordering=())


@pytest.mark.parametrize("field", ["policy_id", "policy_version"])
def test_redundancy_policy_requires_identity(field: str) -> None:
    policy = _amended_models()["redundancy_policy"]
    assert isinstance(policy, ExtendedRedundancyPolicy)
    with pytest.raises(MissingFieldError):
        _unsafe_replace(policy, **{field: ""})


def test_redundancy_policy_rejects_invalid_disposition_or_limits() -> None:
    policy = _amended_models()["redundancy_policy"]
    assert isinstance(policy, ExtendedRedundancyPolicy)
    with pytest.raises(DataIntegrityError):
        replace(policy, disposition="IGNORE")
    with pytest.raises(DataIntegrityError):
        replace(policy, corroboration_required="yes")  # type: ignore[arg-type]
    with pytest.raises(NumericIntegrityError):
        replace(policy, max_redundant_inputs=True)
    with pytest.raises(NumericIntegrityError):
        replace(policy, max_redundant_inputs=-1)


@pytest.mark.parametrize("field", ["policy_id", "policy_version"])
def test_independence_policy_requires_identity(field: str) -> None:
    policy = _amended_models()["independence_policy"]
    assert isinstance(policy, IndependencePolicy)
    with pytest.raises(MissingFieldError):
        _unsafe_replace(policy, **{field: ""})


def test_independence_policy_requires_immutable_material_rules() -> None:
    policy = _amended_models()["independence_policy"]
    assert isinstance(policy, IndependencePolicy)
    with pytest.raises(DataIntegrityError):
        replace(policy, material_source_types=["PRODUCER"])  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        replace(policy, material_derivation_types=["DERIVED"])  # type: ignore[arg-type]
    with pytest.raises(MissingFieldError):
        replace(policy, material_source_types=(), material_derivation_types=())


@pytest.mark.parametrize(
    "field",
    [
        "evidence_id",
        "source_identity",
        "implementation_version",
        "claim",
        "value_domain",
        "content_identity",
    ],
)
def test_evidence_claim_requires_mandatory_text(field: str) -> None:
    claim = _amended_models()["claim"]
    assert isinstance(claim, EvidenceClaim)
    with pytest.raises(MissingFieldError):
        _unsafe_replace(claim, **{field: ""})


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("identity", "identity"),
        ("boundary", "boundary"),
        ("validity", "validity"),
        ("completeness", "completeness"),
        ("quality", "quality"),
        ("assumptions", "assumptions"),
        ("disposition", "ACCEPTED"),
    ],
)
def test_evidence_claim_requires_typed_semantic_metadata(field: str, invalid: object) -> None:
    claim = _amended_models()["claim"]
    assert isinstance(claim, EvidenceClaim)
    with pytest.raises(DataIntegrityError):
        _unsafe_replace(claim, **{field: invalid})


def test_evidence_claim_requires_immutable_typed_provenance() -> None:
    claim = _amended_models()["claim"]
    assert isinstance(claim, EvidenceClaim)
    assert replace(claim, units=None).units is None
    with pytest.raises(DataIntegrityError):
        _unsafe_replace(claim, provenance=[])
    with pytest.raises(DataIntegrityError):
        _unsafe_replace(claim, provenance=("source",))
    with pytest.raises(MissingFieldError):
        replace(claim, units="")


def test_amended_models_expose_no_execution_behaviour() -> None:
    forbidden = {
        "execute",
        "resolve",
        "select_provider",
        "enumerate_candidates",
        "lookup_registry",
        "orchestrate",
    }
    for value in _amended_models().values():
        assert forbidden.isdisjoint(dir(value))
