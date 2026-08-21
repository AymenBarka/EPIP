"""Deterministic semantic validation for the A04-E01 authority boundary."""

from __future__ import annotations

from typing import NoReturn

from epip.core.integrity import DataIntegrityError
from epip.evidence.model import (
    CertifiedSemanticEquivalence,
    CompatibilityEffects,
    ConsumerConflictPolicy,
    DiagnosticCode,
    DispositionAxis,
    EvidenceClaim,
    EvidenceRequirement,
    ExtendedRedundancyPolicy,
    IndependencePolicy,
    ProvenanceReference,
    SemanticState,
)
from epip.governance.model import (
    CertificationRecord,
    CompatibilityDecision,
    RegistryEntry,
    RegistrySnapshot,
)


def _reject(code: DiagnosticCode, reason: str) -> NoReturn:
    raise DataIntegrityError(f"{code.value}: {reason}")


def _require_claim_matches_requirement(
    claim: EvidenceClaim, requirement: EvidenceRequirement
) -> None:
    if (
        claim.identity.evidence_type != requirement.evidence_type
        or claim.identity.semantic_version != requirement.semantic_version
        or claim.identity.subject != requirement.subject
        or claim.identity.scope != requirement.scope
        or claim.boundary.subject != requirement.subject
        or claim.boundary.scope != requirement.scope
    ):
        _reject(
            DiagnosticCode.SEMANTIC_INCONSISTENCY,
            "evidence identity or boundary does not match the requirement",
        )


class SemanticValidator:
    """Validate immutable evidence facts against one declared requirement."""

    __slots__ = ()

    @staticmethod
    def validate_requirement(requirement: EvidenceRequirement, claim: EvidenceClaim) -> None:
        _require_claim_matches_requirement(claim, requirement)
        if claim.disposition is not DispositionAxis.ACCEPTED:
            _reject(DiagnosticCode.INVALID_DEPENDENCY, "evidence disposition is rejected")
        if not claim.validity.is_valid:
            _reject(DiagnosticCode.INVALID_DEPENDENCY, "evidence validity is false")

    @staticmethod
    def validate_semantic_state(state: SemanticState) -> None:
        if state.state != "PRESENT":
            _reject(
                DiagnosticCode.COMPLETENESS_VIOLATION,
                f"semantic state {state.state} does not satisfy present evidence",
            )

    @classmethod
    def validate_completeness(
        cls,
        requirement: EvidenceRequirement,
        claims: tuple[EvidenceClaim, ...],
        *,
        required_dimensions: tuple[str, ...] = (),
        required_temporal_windows: tuple[str, ...] = (),
        required_facets: tuple[str, ...] = (),
    ) -> None:
        if not isinstance(claims, tuple) or not all(
            isinstance(claim, EvidenceClaim) for claim in claims
        ):
            _reject(DiagnosticCode.COMPLETENESS_VIOLATION, "claims must be immutable EvidenceClaim")
        expected = requirement.exact_cardinality
        if expected is not None:
            cardinality_valid = len(claims) == expected
        else:
            cardinality_valid = (
                requirement.min_cardinality <= len(claims) <= requirement.max_cardinality
            )
        if not cardinality_valid:
            _reject(DiagnosticCode.CARDINALITY_VIOLATION, "claim cardinality is unsatisfied")
        for claim in claims:
            cls.validate_requirement(requirement, claim)
            cls.validate_semantic_state(claim.completeness.state)
            completeness = claim.completeness
            if completeness.cardinality != len(claims):
                _reject(
                    DiagnosticCode.COMPLETENESS_VIOLATION,
                    "declared completeness cardinality does not match the evidence set",
                )
            if not set(required_dimensions) <= set(completeness.dimensions):
                _reject(DiagnosticCode.COMPLETENESS_VIOLATION, "required dimensions are incomplete")
            if not set(required_temporal_windows) <= set(completeness.temporal_windows):
                _reject(
                    DiagnosticCode.COMPLETENESS_VIOLATION,
                    "required temporal coverage is incomplete",
                )
            if not set(required_facets) <= set(completeness.facets):
                _reject(DiagnosticCode.COMPLETENESS_VIOLATION, "required facets are incomplete")
            if not completeness.provenance_complete:
                _reject(DiagnosticCode.PROVENANCE_VIOLATION, "provenance completeness is false")

    @staticmethod
    def is_duplicate(left: EvidenceClaim, right: EvidenceClaim) -> bool:
        return left.content_identity == right.content_identity

    @staticmethod
    def is_redundant(
        claims: tuple[EvidenceClaim, ...],
        requirement: EvidenceRequirement,
        equivalences: tuple[CertifiedSemanticEquivalence, ...],
        policy: ExtendedRedundancyPolicy,
    ) -> bool:
        if len(claims) < 2:
            return False
        if not isinstance(equivalences, tuple):
            _reject(
                DiagnosticCode.SEMANTIC_INCONSISTENCY,
                "equivalence certifications must be an immutable tuple",
            )
        ordered = tuple(
            sorted(claims, key=lambda claim: (claim.evidence_id, claim.content_identity))
        )
        if any(
            SemanticValidator.is_duplicate(left, right)
            for index, left in enumerate(ordered)
            for right in ordered[index + 1 :]
        ):
            return False
        anchor = ordered[0]
        for other_claim in ordered[1:]:
            if (
                anchor.identity == other_claim.identity
                and anchor.boundary == other_claim.boundary
                and anchor.claim != other_claim.claim
            ):
                _reject(
                    DiagnosticCode.SEMANTIC_INCONSISTENCY,
                    "conflicting claims cannot be classified as redundant",
                )
            certification = next(
                (
                    item
                    for item in equivalences
                    if {anchor.evidence_id, other_claim.evidence_id}
                    <= set(item.evidence_references)
                ),
                None,
            )
            if certification is None:
                _reject(
                    DiagnosticCode.SEMANTIC_INCONSISTENCY,
                    "every redundant claim requires certified equivalence",
                )
            if not EquivalenceValidator.equivalent(anchor, other_claim, certification):
                return False
        redundant_count = max(0, len(claims) - requirement.max_cardinality)
        if redundant_count == 0:
            return False
        if policy.disposition == "REJECT" or redundant_count > policy.max_redundant_inputs:
            _reject(
                DiagnosticCode.CARDINALITY_VIOLATION, "redundancy policy rejects the evidence set"
            )
        if policy.corroboration_required and policy.disposition != "RETAIN_FOR_CORROBORATION":
            _reject(
                DiagnosticCode.SEMANTIC_INCONSISTENCY,
                "corroboration requires the retain-for-corroboration disposition",
            )
        return True


class CompatibilityEvaluator:
    """Validate authoritative directional compatibility and declared effects."""

    __slots__ = ()

    _PHASE2_EXPIRY_CONDITIONS = frozenset({"version-change"})

    @classmethod
    def validate_phase2(
        cls,
        requirement: EvidenceRequirement,
        snapshot: RegistrySnapshot,
        entry: RegistryEntry,
        effects: tuple[CompatibilityEffects, ...],
        compatibility_dimension: str,
    ) -> None:
        """Validate pre-execution compatibility from immutable authoritative facts."""

        if not isinstance(requirement, EvidenceRequirement):
            _reject(DiagnosticCode.INVALID_DEPENDENCY, "requirement is not immutable evidence data")
        if not isinstance(snapshot, RegistrySnapshot):
            _reject(DiagnosticCode.INVALID_DEPENDENCY, "snapshot is not immutable registry data")
        if not isinstance(entry, RegistryEntry):
            _reject(DiagnosticCode.INVALID_DEPENDENCY, "candidate is not immutable registry data")
        if not isinstance(effects, tuple) or not all(
            isinstance(item, CompatibilityEffects) for item in effects
        ):
            _reject(
                DiagnosticCode.INVALID_DEPENDENCY, "effects are not immutable compatibility data"
            )
        if not isinstance(compatibility_dimension, str) or not compatibility_dimension.strip():
            _reject(DiagnosticCode.INVALID_DEPENDENCY, "compatibility dimension is absent")
        if snapshot.entries.count(entry) != 1:
            _reject(DiagnosticCode.INELIGIBLE_PROVIDER, "candidate is not uniquely registry-bound")

        capability = (requirement.evidence_type, requirement.semantic_version)
        if capability not in entry.capability_references:
            _reject(DiagnosticCode.INCOMPATIBLE_DEPENDENCY, "candidate capability is incompatible")

        applicable_certifications = tuple(
            record
            for record in entry.certification_records
            if record.producer_identity == entry.producer_identity
            and record.producer_version == entry.producer_version
            and capability in record.capability_references
        )
        if any(record.verdict in {"expired", "revoked"} for record in applicable_certifications):
            _reject(
                DiagnosticCode.EXPIRED_OR_REVOKED_CERTIFICATION,
                "candidate certification is expired or revoked",
            )
        certifications = tuple(
            record
            for record in applicable_certifications
            if record.verdict == "passed"
            and record.implementation_identity == entry.implementation_identity
            and record.producer_contract_version == entry.producer_contract_version
            and record.effective_epoch.sequence <= snapshot.governance_epoch.sequence
            and record.status_relationship_reference is None
            and record.expiration_or_review_condition in cls._PHASE2_EXPIRY_CONDITIONS
        )
        if len(certifications) != 1:
            _reject(
                DiagnosticCode.INELIGIBLE_PROVIDER,
                "candidate certification is absent, ambiguous, or unsupported",
            )
        certification = certifications[0]

        source_reference = f"{entry.producer_identity}@{entry.producer_version}"
        decisions = tuple(
            decision
            for decision in entry.compatibility_decisions
            if decision.source_reference == source_reference
            and decision.target_reference == requirement.requirement_id
        )
        if len(decisions) != 1:
            _reject(
                DiagnosticCode.INCOMPATIBLE_DEPENDENCY,
                "compatibility decision is absent or ambiguous",
            )
        decision = decisions[0]
        versions = dict(decision.version_scope)
        profiles = dict(decision.profile_scope)
        if (
            decision.direction != "source-to-target"
            or versions.get("source") != requirement.semantic_version
            or versions.get("target") != requirement.semantic_version
            or decision.intended_use != requirement.requirement_id
            or profiles.get("scope") != requirement.scope
            or decision.compatibility_dimension != compatibility_dimension
            or decision.effective_epoch.sequence > snapshot.governance_epoch.sequence
            or dict(snapshot.policy_versions).get("compatibility") != decision.policy_version
            or decision.review_or_expiry_condition not in cls._PHASE2_EXPIRY_CONDITIONS
            or decision.revocation_reference is not None
            or decision.supersession_reference is not None
            or decision.decision_identity not in certification.evidence_references
        ):
            _reject(
                DiagnosticCode.INCOMPATIBLE_DEPENDENCY,
                "compatibility decision is inconsistent, inactive, or unsupported",
            )

        matching_effects = tuple(
            item
            for item in effects
            if item.decision_reference == decision.decision_identity
            and item.effects_version == decision.policy_version
        )
        if len(matching_effects) != 1 or matching_effects[0].declared_losses:
            _reject(
                DiagnosticCode.INCOMPATIBLE_DEPENDENCY,
                "compatibility effects are absent, ambiguous, or decision-incompatible",
            )

    @staticmethod
    def evaluate(
        source: EvidenceClaim,
        target: EvidenceRequirement,
        target_claim: EvidenceClaim,
        decision: CompatibilityDecision,
        certification: CertificationRecord,
        effects: CompatibilityEffects,
    ) -> None:
        _require_claim_matches_requirement(target_claim, target)
        if (
            decision.source_reference != source.evidence_id
            or decision.target_reference != target.requirement_id
        ):
            _reject(
                DiagnosticCode.INCOMPATIBLE_DEPENDENCY, "compatibility endpoints are mismatched"
            )
        if decision.direction != "source-to-target":
            _reject(DiagnosticCode.INCOMPATIBLE_DEPENDENCY, "compatibility direction is invalid")
        versions = dict(decision.version_scope)
        if (
            versions.get("source") != source.identity.semantic_version
            or versions.get("target") != target.semantic_version
        ):
            _reject(
                DiagnosticCode.INCOMPATIBLE_DEPENDENCY, "compatibility version scope is mismatched"
            )
        profiles = dict(decision.profile_scope)
        if profiles.get("scope") != target.scope or decision.intended_use != target.requirement_id:
            _reject(
                DiagnosticCode.INCOMPATIBLE_DEPENDENCY, "compatibility consumer scope is mismatched"
            )
        if (
            certification.verdict != "passed"
            or certification.producer_identity != source.source_identity
            or certification.producer_version != source.implementation_version
            or (source.identity.evidence_type, source.identity.semantic_version)
            not in certification.capability_references
            or decision.decision_identity not in certification.evidence_references
        ):
            _reject(
                DiagnosticCode.EXPIRED_OR_REVOKED_CERTIFICATION,
                "compatibility certification is absent or mismatched",
            )
        if (
            effects.decision_reference != decision.decision_identity
            or effects.effects_version != decision.policy_version
        ):
            _reject(
                DiagnosticCode.INCOMPATIBLE_DEPENDENCY,
                "compatibility effects are not decision-bound",
            )
        if effects.declared_losses:
            _reject(DiagnosticCode.HIDDEN_CONVERSION_ATTEMPT, "compatibility declares meaning loss")
        transformations = tuple(
            effect
            for effect in (effects.conversion, effects.narrowing, effects.widening)
            if effect is not None
        )
        if source.claim == target_claim.claim:
            if transformations:
                _reject(
                    DiagnosticCode.HIDDEN_CONVERSION_ATTEMPT,
                    "unchanged claim meaning cannot declare a transformation",
                )
        elif len(transformations) != 1 or transformations[0] != target_claim.claim:
            _reject(
                DiagnosticCode.HIDDEN_CONVERSION_ATTEMPT,
                "changed claim meaning requires one exact declared transformation",
            )
        unit_semantics = target_claim.units or target_claim.value_domain
        if effects.unit_effect != unit_semantics:
            _reject(DiagnosticCode.INCOMPATIBLE_DEPENDENCY, "unit effect is inconsistent")
        if effects.completeness_effect != target_claim.completeness.state.state:
            _reject(DiagnosticCode.INCOMPATIBLE_DEPENDENCY, "completeness effect is inconsistent")
        if effects.temporal_effect != target_claim.boundary.temporal_boundary:
            _reject(DiagnosticCode.INCOMPATIBLE_DEPENDENCY, "temporal effect is inconsistent")
        if effects.quality_effect != target_claim.quality.grade:
            _reject(DiagnosticCode.INCOMPATIBLE_DEPENDENCY, "quality effect is inconsistent")
        if len(target_claim.provenance) != 1:
            _reject(
                DiagnosticCode.PROVENANCE_VIOLATION,
                "provenance effect requires one exact immutable target reference",
            )
        target_provenance = target_claim.provenance[0]
        provenance_semantics = target_provenance.content_digest or target_provenance.source_id
        if effects.provenance_effect != provenance_semantics:
            _reject(DiagnosticCode.PROVENANCE_VIOLATION, "provenance effect is inconsistent")


class EquivalenceValidator:
    """Validate certified equivalence over every E00 semantic dimension."""

    __slots__ = ()

    _REQUIRED_DIMENSIONS = frozenset(
        {
            "evidence_type",
            "semantic_version",
            "subject",
            "scope",
            "claim",
            "value_domain",
            "units",
            "context_boundary",
            "temporal_boundary",
            "validity",
            "completeness",
            "assumptions",
            "provenance",
        }
    )

    @classmethod
    def equivalent(
        cls,
        left: EvidenceClaim,
        right: EvidenceClaim,
        certification: CertifiedSemanticEquivalence,
    ) -> bool:
        direct = (certification.left, certification.right) == (left.identity, right.identity)
        reverse = certification.symmetric and (
            certification.left,
            certification.right,
        ) == (right.identity, left.identity)
        if not (direct or reverse):
            _reject(DiagnosticCode.SEMANTIC_INCONSISTENCY, "equivalence identities are mismatched")
        if (
            certification.consumer_scope != left.identity.scope
            or certification.consumer_scope != right.identity.scope
        ):
            _reject(
                DiagnosticCode.SEMANTIC_INCONSISTENCY, "equivalence consumer scope is mismatched"
            )
        if frozenset(certification.dimensions) != cls._REQUIRED_DIMENSIONS:
            _reject(DiagnosticCode.SEMANTIC_INCONSISTENCY, "equivalence dimensions are incomplete")
        if not {left.evidence_id, right.evidence_id} <= set(certification.evidence_references):
            _reject(
                DiagnosticCode.SEMANTIC_INCONSISTENCY, "equivalence evidence binding is incomplete"
            )
        return (
            left.claim == right.claim
            and left.value_domain == right.value_domain
            and left.units == right.units
            and left.boundary == right.boundary
            and left.validity == right.validity
            and left.completeness == right.completeness
            and left.assumptions == right.assumptions
            and left.provenance == right.provenance
        )


class ConflictDetector:
    """Compute and preserve claim conflicts under immutable consumer policy."""

    __slots__ = ()

    @staticmethod
    def conflicts(
        left: EvidenceClaim, right: EvidenceClaim, policy: ConsumerConflictPolicy
    ) -> bool:
        if not isinstance(policy, ConsumerConflictPolicy):
            _reject(
                DiagnosticCode.SEMANTIC_INCONSISTENCY,
                "conflict policy must be an immutable ConsumerConflictPolicy",
            )
        same_boundary = left.identity == right.identity and left.boundary == right.boundary
        conflict = same_boundary and (
            left.claim != right.claim
            or left.validity != right.validity
            or left.completeness.state != right.completeness.state
        )
        if conflict:
            claim_count = 2
            if not policy.min_cardinality <= claim_count <= policy.max_cardinality:
                _reject(
                    DiagnosticCode.CARDINALITY_VIOLATION,
                    "consumer conflict policy cannot cover the conflicting claims",
                )
        return conflict


class IndependenceChecker:
    """Compute independence from explicit immutable lineage and policy."""

    __slots__ = ()

    @staticmethod
    def independent(left: EvidenceClaim, right: EvidenceClaim, policy: IndependencePolicy) -> bool:
        material_types = set(policy.material_source_types) | set(policy.material_derivation_types)

        def material(lineage: tuple[ProvenanceReference, ...]) -> set[tuple[str, str]]:
            return {
                (reference.source_id, reference.semantic_version)
                for reference in lineage
                if reference.source_type in material_types
            }

        return material(left.provenance).isdisjoint(material(right.provenance))
