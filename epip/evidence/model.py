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
