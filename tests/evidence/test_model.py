"""Unit tests for A04-E00 evidence and dependency semantic domain models."""

from __future__ import annotations

import pytest

from epip.core.integrity import (
    DataIntegrityError,
    MissingFieldError,
    NumericIntegrityError,
)
from epip.evidence.model import (
    DependencyType,
    DiagnosticCode,
    DiagnosticReason,
    DispositionAxis,
    EvidenceCategory,
    EvidenceRequirement,
    EvidenceTaxonomy,
    EvidenceTypeDefinition,
    ProvenanceAxis,
    ProvenanceReference,
    ResolutionProfile,
    RetentionAxis,
    SemanticIdentity,
    TemporalAxis,
)


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
