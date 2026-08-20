"""Immutable A04 evidence and dependency semantic models without execution logic.

Implementation architecture: Programme A A04, Work Package A04-E00.
Governing contracts: ADR-EPIP017-01, ADR-EPIP017-02, ADR-EPIP017-03, ADR-EPIP017-04,
ADR-EPIP017-08, ADR-EPIP017-09, ADR-EPIP017-11, and ADR-EPIP017-17.
Responsibility: intrinsic structural integrity of immutable evidence definitions,
taxonomy, requirements, profiles, and diagnostic metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from epip.core.integrity import (
    DataIntegrityError,
    MissingFieldError,
    NumericIntegrityError,
    require_text,
)


class ProvenanceAxis(str, Enum):
    """Classification of evidence origin along the provenance axis."""

    PRIMARY = "PRIMARY"
    DERIVED = "DERIVED"
    SECONDARY = "SECONDARY"
    SYNTHETIC = "SYNTHETIC"
    COMPOSITE = "COMPOSITE"


class DispositionAxis(str, Enum):
    """Status of evidence eligibility for a declared use."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class TemporalAxis(str, Enum):
    """Interpretation of evidence relative to the logical boundary."""

    HISTORICAL = "HISTORICAL"
    CURRENT = "CURRENT"


class RetentionAxis(str, Enum):
    """Scope of persistence and lifecycle eligibility."""

    TRANSIENT = "TRANSIENT"
    PERSISTENT = "PERSISTENT"


class EvidenceCategory(str, Enum):
    """Governed primary semantic categories for evidence types."""

    STRUCTURAL = "STRUCTURAL"
    LIQUIDITY = "LIQUIDITY"
    TREND = "TREND"
    VOLATILITY = "VOLATILITY"
    PATTERN = "PATTERN"
    WAVE = "WAVE"
    MACRO = "MACRO"
    SESSION = "SESSION"
    CALENDAR = "CALENDAR"
    EXECUTION = "EXECUTION"
    RISK = "RISK"
    EXTERNAL = "EXTERNAL"


class DependencyType(str, Enum):
    """Classification of consumer dependency requirements."""

    MANDATORY = "MANDATORY"
    OPTIONAL = "OPTIONAL"
    CONDITIONAL = "CONDITIONAL"
    DERIVED = "DERIVED"
    TRANSITIVE = "TRANSITIVE"
    FORBIDDEN = "FORBIDDEN"


class DiagnosticCode(str, Enum):
    """Stable, versioned diagnostic reason codes for dependency resolution."""

    MISSING_MANDATORY_DEPENDENCY = "MISSING_MANDATORY_DEPENDENCY"
    ABSENT_OPTIONAL_DEPENDENCY = "ABSENT_OPTIONAL_DEPENDENCY"
    INVALID_DEPENDENCY = "INVALID_DEPENDENCY"
    INCOMPATIBLE_DEPENDENCY = "INCOMPATIBLE_DEPENDENCY"
    CONFLICTING_DEPENDENCY = "CONFLICTING_DEPENDENCY"
    REDUNDANT_DEPENDENCY = "REDUNDANT_DEPENDENCY"
    DUPLICATE_DEPENDENCY = "DUPLICATE_DEPENDENCY"
    OBSOLETE_DEPENDENCY = "OBSOLETE_DEPENDENCY"
    AMBIGUOUS_DEPENDENCY = "AMBIGUOUS_DEPENDENCY"
    UNSUPPORTED_DEPENDENCY = "UNSUPPORTED_DEPENDENCY"
    FORBIDDEN_DEPENDENCY = "FORBIDDEN_DEPENDENCY"
    CYCLIC_DEPENDENCY = "CYCLIC_DEPENDENCY"
    SEMANTIC_INCONSISTENCY = "SEMANTIC_INCONSISTENCY"
    CARDINALITY_VIOLATION = "CARDINALITY_VIOLATION"
    COMPLETENESS_VIOLATION = "COMPLETENESS_VIOLATION"
    PROVENANCE_VIOLATION = "PROVENANCE_VIOLATION"
    HIDDEN_CONVERSION_ATTEMPT = "HIDDEN_CONVERSION_ATTEMPT"
    INELIGIBLE_PROVIDER = "INELIGIBLE_PROVIDER"
    EXPIRED_OR_REVOKED_CERTIFICATION = "EXPIRED_OR_REVOKED_CERTIFICATION"


@dataclass(frozen=True, slots=True)
class ProvenanceReference:
    """Stable, non-navigable identity reference for lineage audit."""

    source_id: str
    source_type: str
    semantic_version: str
    content_digest: str | None = None

    def __post_init__(self) -> None:
        require_text(self.source_id, "source_id")
        require_text(self.source_type, "source_type")
        require_text(self.semantic_version, "semantic_version")
        if self.content_digest is not None:
            require_text(self.content_digest, "content_digest")


@dataclass(frozen=True, slots=True)
class EvidenceTaxonomy:
    """Orthogonal multi-axis classification of an evidence artifact."""

    provenance: ProvenanceAxis
    disposition: DispositionAxis
    temporal: TemporalAxis
    retention: RetentionAxis

    def __post_init__(self) -> None:
        if not isinstance(self.provenance, ProvenanceAxis):
            raise DataIntegrityError("provenance must be an instance of ProvenanceAxis")
        if not isinstance(self.disposition, DispositionAxis):
            raise DataIntegrityError("disposition must be an instance of DispositionAxis")
        if not isinstance(self.temporal, TemporalAxis):
            raise DataIntegrityError("temporal must be an instance of TemporalAxis")
        if not isinstance(self.retention, RetentionAxis):
            raise DataIntegrityError("retention must be an instance of RetentionAxis")


@dataclass(frozen=True, slots=True)
class SemanticIdentity:
    """Canonical domain identification of a semantic evidence contract."""

    evidence_type: str
    semantic_version: str
    subject: str
    scope: str

    def __post_init__(self) -> None:
        require_text(self.evidence_type, "evidence_type")
        require_text(self.semantic_version, "semantic_version")
        require_text(self.subject, "subject")
        require_text(self.scope, "scope")


@dataclass(frozen=True, slots=True)
class ResolutionProfile:
    """Immutable governance policy constraining provider selection and tie-breaking."""

    profile_id: str
    profile_version: str
    pinned_producer_id: str | None = None
    allow_redundancy: bool = False
    allow_multi_provider: bool = False

    def __post_init__(self) -> None:
        require_text(self.profile_id, "profile_id")
        require_text(self.profile_version, "profile_version")
        if self.pinned_producer_id is not None:
            require_text(self.pinned_producer_id, "pinned_producer_id")
        if not isinstance(self.allow_redundancy, bool):
            raise DataIntegrityError("allow_redundancy must be a boolean")
        if not isinstance(self.allow_multi_provider, bool):
            raise DataIntegrityError("allow_multi_provider must be a boolean")


@dataclass(frozen=True, slots=True)
class EvidenceRequirement:
    """Explicit semantic dependency requirement declared by a consumer capability."""

    requirement_id: str
    evidence_type: str
    semantic_version: str
    subject: str
    scope: str
    dependency_type: DependencyType
    min_cardinality: int = 1
    max_cardinality: int = 1
    exact_cardinality: int | None = None
    resolution_profile_id: str | None = None
    absence_semantics: str | None = None
    predicate: str | None = None
    provenance_constraints: tuple[ProvenanceReference, ...] = ()

    def __post_init__(self) -> None:
        require_text(self.requirement_id, "requirement_id")
        require_text(self.evidence_type, "evidence_type")
        require_text(self.semantic_version, "semantic_version")
        require_text(self.subject, "subject")
        require_text(self.scope, "scope")

        if not isinstance(self.dependency_type, DependencyType):
            raise DataIntegrityError("dependency_type must be an instance of DependencyType")

        if isinstance(self.min_cardinality, bool) or not isinstance(self.min_cardinality, int):
            raise NumericIntegrityError("min_cardinality must be a non-negative integer")
        if self.min_cardinality < 0:
            raise NumericIntegrityError("min_cardinality must be non-negative")

        if isinstance(self.max_cardinality, bool) or not isinstance(self.max_cardinality, int):
            raise NumericIntegrityError("max_cardinality must be a positive integer")
        if self.max_cardinality < self.min_cardinality:
            raise NumericIntegrityError("max_cardinality cannot be less than min_cardinality")

        if self.exact_cardinality is not None:
            if isinstance(self.exact_cardinality, bool) or not isinstance(
                self.exact_cardinality, int
            ):
                raise NumericIntegrityError("exact_cardinality must be a non-negative integer")
            if self.exact_cardinality < 0:
                raise NumericIntegrityError("exact_cardinality must be non-negative")
            if (
                self.min_cardinality != self.exact_cardinality
                or self.max_cardinality != self.exact_cardinality
            ):
                raise DataIntegrityError(
                    "min_cardinality and max_cardinality must match exact_cardinality when specified"
                )

        if self.resolution_profile_id is not None:
            require_text(self.resolution_profile_id, "resolution_profile_id")
        if self.absence_semantics is not None:
            require_text(self.absence_semantics, "absence_semantics")
        if self.predicate is not None:
            require_text(self.predicate, "predicate")

        if not isinstance(self.provenance_constraints, tuple):
            raise DataIntegrityError("provenance_constraints must be an immutable tuple")
        for ref in self.provenance_constraints:
            if not isinstance(ref, ProvenanceReference):
                raise DataIntegrityError(
                    "provenance_constraints must contain only ProvenanceReference instances"
                )


@dataclass(frozen=True, slots=True)
class DiagnosticReason:
    """Immutable diagnostic explanation for a dependency resolution outcome or failure."""

    code: DiagnosticCode
    requirement_id: str
    reason: str
    candidate_id: str | None = None
    semantic_version: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, DiagnosticCode):
            raise DataIntegrityError("code must be an instance of DiagnosticCode")
        require_text(self.requirement_id, "requirement_id")
        require_text(self.reason, "reason")
        if self.candidate_id is not None:
            require_text(self.candidate_id, "candidate_id")
        if self.semantic_version is not None:
            require_text(self.semantic_version, "semantic_version")


@dataclass(frozen=True, slots=True)
class EvidenceTypeDefinition:
    """Canonical governance definition of an evidence type."""

    evidence_type: str
    semantic_version: str
    category: EvidenceCategory
    taxonomy: EvidenceTaxonomy
    value_domain: str
    units: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        require_text(self.evidence_type, "evidence_type")
        require_text(self.semantic_version, "semantic_version")
        if not isinstance(self.category, EvidenceCategory):
            raise DataIntegrityError("category must be an instance of EvidenceCategory")
        if not isinstance(self.taxonomy, EvidenceTaxonomy):
            raise DataIntegrityError("taxonomy must be an instance of EvidenceTaxonomy")
        require_text(self.value_domain, "value_domain")
        if self.units is not None:
            require_text(self.units, "units")
        if not isinstance(self.description, str):
            raise MissingFieldError("description must be a string")


def _require_text_tuple(value: object, field_name: str, *, required: bool = False) -> None:
    """Validate one immutable tuple of unique, non-empty text values."""

    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field_name} must be an immutable tuple")
    if required and not value:
        raise MissingFieldError(f"{field_name} must not be empty")
    for item in value:
        if not isinstance(item, str):
            raise DataIntegrityError(f"{field_name} must contain only strings")
        require_text(item, field_name)
    if len(set(value)) != len(value):
        raise DataIntegrityError(f"{field_name} must not contain duplicates")


@dataclass(frozen=True, slots=True)
class SemanticBoundary:
    """Immutable subject, scope, context, and temporal boundary metadata."""

    subject: str
    scope: str
    context_boundary: str
    temporal_boundary: str

    def __post_init__(self) -> None:
        require_text(self.subject, "subject")
        require_text(self.scope, "scope")
        require_text(self.context_boundary, "context_boundary")
        require_text(self.temporal_boundary, "temporal_boundary")


@dataclass(frozen=True, slots=True)
class ValidityMetadata:
    """Immutable validity semantics for one governed Evidence use."""

    semantics: str
    is_valid: bool
    boundary_reference: str

    def __post_init__(self) -> None:
        require_text(self.semantics, "validity.semantics")
        if not isinstance(self.is_valid, bool):
            raise DataIntegrityError("validity.is_valid must be a boolean")
        require_text(self.boundary_reference, "validity.boundary_reference")


@dataclass(frozen=True, slots=True)
class SemanticState:
    """Explicit semantic state without collapsing absence or failure meanings."""

    state: str
    detail: str | None = None

    ALLOWED_STATES: ClassVar[frozenset[str]] = frozenset(
        {"PRESENT", "ABSENT", "VALID_EMPTY", "PARTIAL", "REJECTED", "INVALID", "UNAVAILABLE"}
    )

    def __post_init__(self) -> None:
        if self.state not in self.ALLOWED_STATES:
            raise DataIntegrityError("semantic_state.state is unsupported")
        if self.detail is not None:
            require_text(self.detail, "semantic_state.detail")


@dataclass(frozen=True, slots=True)
class CompletenessMetadata:
    """Immutable, use-specific semantic completeness facts."""

    state: SemanticState
    dimensions: tuple[str, ...]
    cardinality: int
    temporal_windows: tuple[str, ...]
    facets: tuple[str, ...]
    provenance_complete: bool

    def __post_init__(self) -> None:
        if not isinstance(self.state, SemanticState):
            raise DataIntegrityError("completeness.state must be a SemanticState")
        _require_text_tuple(self.dimensions, "completeness.dimensions")
        if isinstance(self.cardinality, bool) or not isinstance(self.cardinality, int):
            raise NumericIntegrityError("completeness.cardinality must be a non-negative integer")
        if self.cardinality < 0:
            raise NumericIntegrityError("completeness.cardinality must be non-negative")
        _require_text_tuple(self.temporal_windows, "completeness.temporal_windows")
        _require_text_tuple(self.facets, "completeness.facets")
        if not isinstance(self.provenance_complete, bool):
            raise DataIntegrityError("completeness.provenance_complete must be a boolean")


@dataclass(frozen=True, slots=True)
class QualityMetadata:
    """Immutable governed quality facts without truth or selection authority."""

    profile_id: str
    profile_version: str
    grade: str
    measurements: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        require_text(self.profile_id, "quality.profile_id")
        require_text(self.profile_version, "quality.profile_version")
        require_text(self.grade, "quality.grade")
        if not isinstance(self.measurements, tuple):
            raise DataIntegrityError("quality.measurements must be an immutable tuple")
        names: list[str] = []
        for measurement in self.measurements:
            if not isinstance(measurement, tuple) or len(measurement) != 2:
                raise DataIntegrityError("quality.measurements must contain name/value pairs")
            name, value = measurement
            require_text(name, "quality.measurement.name")
            require_text(value, "quality.measurement.value")
            names.append(name)
        if len(set(names)) != len(names):
            raise DataIntegrityError("quality.measurements must not repeat names")


@dataclass(frozen=True, slots=True)
class AssumptionMetadata:
    """Immutable versioned assumptions attached to semantic meaning."""

    assumption_version: str
    assumptions: tuple[str, ...]

    def __post_init__(self) -> None:
        require_text(self.assumption_version, "assumption_version")
        _require_text_tuple(self.assumptions, "assumptions", required=True)


@dataclass(frozen=True, slots=True)
class CertifiedSemanticEquivalence:
    """Immutable certified semantic-equivalence fact for one consumer scope."""

    decision_id: str
    decision_version: str
    certification_id: str
    left: SemanticIdentity
    right: SemanticIdentity
    consumer_scope: str
    dimensions: tuple[str, ...]
    evidence_references: tuple[str, ...]
    symmetric: bool

    def __post_init__(self) -> None:
        require_text(self.decision_id, "equivalence.decision_id")
        require_text(self.decision_version, "equivalence.decision_version")
        require_text(self.certification_id, "equivalence.certification_id")
        if not isinstance(self.left, SemanticIdentity) or not isinstance(
            self.right, SemanticIdentity
        ):
            raise DataIntegrityError("equivalence identities must be SemanticIdentity instances")
        require_text(self.consumer_scope, "equivalence.consumer_scope")
        _require_text_tuple(self.dimensions, "equivalence.dimensions", required=True)
        _require_text_tuple(
            self.evidence_references,
            "equivalence.evidence_references",
            required=True,
        )
        if not isinstance(self.symmetric, bool):
            raise DataIntegrityError("equivalence.symmetric must be a boolean")


@dataclass(frozen=True, slots=True)
class CompatibilityEffects:
    """Immutable semantic effects bound to an authoritative compatibility decision."""

    decision_reference: str
    effects_version: str
    conversion: str | None
    narrowing: str | None
    widening: str | None
    unit_effect: str
    completeness_effect: str
    temporal_effect: str
    quality_effect: str
    provenance_effect: str
    declared_losses: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_text(self.decision_reference, "compatibility_effects.decision_reference")
        require_text(self.effects_version, "compatibility_effects.effects_version")
        for name in ("conversion", "narrowing", "widening"):
            value = getattr(self, name)
            if value is not None:
                require_text(value, f"compatibility_effects.{name}")
        for name in (
            "unit_effect",
            "completeness_effect",
            "temporal_effect",
            "quality_effect",
            "provenance_effect",
        ):
            require_text(getattr(self, name), f"compatibility_effects.{name}")
        _require_text_tuple(self.declared_losses, "compatibility_effects.declared_losses")


@dataclass(frozen=True, slots=True)
class ConsumerConflictPolicy:
    """Immutable consumer-declared conflict interpretation policy."""

    policy_id: str
    policy_version: str
    interpretation: str
    min_cardinality: int
    max_cardinality: int
    ordering: tuple[str, ...]
    output_semantics: str

    def __post_init__(self) -> None:
        require_text(self.policy_id, "conflict_policy.policy_id")
        require_text(self.policy_version, "conflict_policy.policy_version")
        require_text(self.interpretation, "conflict_policy.interpretation")
        for name in ("min_cardinality", "max_cardinality"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise NumericIntegrityError(
                    f"conflict_policy.{name} must be a non-negative integer"
                )
        if self.max_cardinality < self.min_cardinality:
            raise NumericIntegrityError(
                "conflict_policy.max_cardinality cannot be below min_cardinality"
            )
        _require_text_tuple(self.ordering, "conflict_policy.ordering", required=True)
        require_text(self.output_semantics, "conflict_policy.output_semantics")


@dataclass(frozen=True, slots=True)
class ExtendedRedundancyPolicy:
    """Immutable policy for explicit redundant-Evidence disposition."""

    policy_id: str
    policy_version: str
    disposition: str
    corroboration_required: bool
    max_redundant_inputs: int

    ALLOWED_DISPOSITIONS: ClassVar[frozenset[str]] = frozenset(
        {"REJECT", "RETAIN_FOR_CORROBORATION", "SUPPLY_TO_MULTI_PROVIDER"}
    )

    def __post_init__(self) -> None:
        require_text(self.policy_id, "redundancy_policy.policy_id")
        require_text(self.policy_version, "redundancy_policy.policy_version")
        if self.disposition not in self.ALLOWED_DISPOSITIONS:
            raise DataIntegrityError("redundancy_policy.disposition is unsupported")
        if not isinstance(self.corroboration_required, bool):
            raise DataIntegrityError("redundancy_policy.corroboration_required must be a boolean")
        if isinstance(self.max_redundant_inputs, bool) or not isinstance(
            self.max_redundant_inputs, int
        ):
            raise NumericIntegrityError(
                "redundancy_policy.max_redundant_inputs must be a non-negative integer"
            )
        if self.max_redundant_inputs < 0:
            raise NumericIntegrityError(
                "redundancy_policy.max_redundant_inputs must be non-negative"
            )


@dataclass(frozen=True, slots=True)
class IndependencePolicy:
    """Immutable lineage materiality policy for semantic independence."""

    policy_id: str
    policy_version: str
    material_source_types: tuple[str, ...]
    material_derivation_types: tuple[str, ...]

    def __post_init__(self) -> None:
        require_text(self.policy_id, "independence_policy.policy_id")
        require_text(self.policy_version, "independence_policy.policy_version")
        _require_text_tuple(
            self.material_source_types,
            "independence_policy.material_source_types",
        )
        _require_text_tuple(
            self.material_derivation_types,
            "independence_policy.material_derivation_types",
        )
        if not self.material_source_types and not self.material_derivation_types:
            raise MissingFieldError("independence policy must declare at least one material rule")


@dataclass(frozen=True, slots=True)
class EvidenceClaim:
    """Immutable, attributable Evidence claim without execution or resolution authority."""

    evidence_id: str
    identity: SemanticIdentity
    source_identity: str
    implementation_version: str
    boundary: SemanticBoundary
    claim: str
    value_domain: str
    units: str | None
    validity: ValidityMetadata
    completeness: CompletenessMetadata
    quality: QualityMetadata
    assumptions: AssumptionMetadata
    provenance: tuple[ProvenanceReference, ...]
    content_identity: str
    disposition: DispositionAxis

    def __post_init__(self) -> None:
        require_text(self.evidence_id, "evidence.evidence_id")
        if not isinstance(self.identity, SemanticIdentity):
            raise DataIntegrityError("evidence.identity must be a SemanticIdentity")
        require_text(self.source_identity, "evidence.source_identity")
        require_text(self.implementation_version, "evidence.implementation_version")
        if not isinstance(self.boundary, SemanticBoundary):
            raise DataIntegrityError("evidence.boundary must be a SemanticBoundary")
        require_text(self.claim, "evidence.claim")
        require_text(self.value_domain, "evidence.value_domain")
        if self.units is not None:
            require_text(self.units, "evidence.units")
        if not isinstance(self.validity, ValidityMetadata):
            raise DataIntegrityError("evidence.validity must be ValidityMetadata")
        if not isinstance(self.completeness, CompletenessMetadata):
            raise DataIntegrityError("evidence.completeness must be CompletenessMetadata")
        if not isinstance(self.quality, QualityMetadata):
            raise DataIntegrityError("evidence.quality must be QualityMetadata")
        if not isinstance(self.assumptions, AssumptionMetadata):
            raise DataIntegrityError("evidence.assumptions must be AssumptionMetadata")
        if not isinstance(self.provenance, tuple):
            raise DataIntegrityError("evidence.provenance must be an immutable tuple")
        if not all(isinstance(reference, ProvenanceReference) for reference in self.provenance):
            raise DataIntegrityError(
                "evidence.provenance must contain only ProvenanceReference instances"
            )
        require_text(self.content_identity, "evidence.content_identity")
        if not isinstance(self.disposition, DispositionAxis):
            raise DataIntegrityError("evidence.disposition must be a DispositionAxis")
