"""Deterministic candidate enumeration and governance filtering for A04-E02."""

from __future__ import annotations

from typing import NamedTuple

from epip.core.integrity import DataIntegrityError
from epip.evidence.model import (
    CompatibilityEffects,
    EvidenceClaim,
    EvidenceRequirement,
)
from epip.evidence.validation import CompatibilityEvaluator
from epip.governance import (
    CertificationRecord,
    CompatibilityDecision,
    GovernanceEpoch,
    GovernanceRejection,
    RegistryEntry,
    RegistrySnapshot,
)


def _require_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataIntegrityError(f"{name} must be non-empty text")
    return value


def _require_entries(entries: object) -> tuple[RegistryEntry, ...]:
    if not isinstance(entries, tuple) or not all(
        isinstance(entry, RegistryEntry) for entry in entries
    ):
        raise DataIntegrityError("candidates must be an immutable tuple of RegistryEntry")
    identities = tuple((entry.producer_identity, entry.producer_version) for entry in entries)
    if len(set(identities)) != len(identities):
        raise DataIntegrityError("candidate producer identities must be unique")
    return entries


def _candidate_key(entry: RegistryEntry) -> tuple[str, str, str]:
    return (entry.producer_identity, entry.producer_version, entry.implementation_identity)


class CandidateDiagnostics(NamedTuple):
    """Immutable admitted candidates and preserved governance rejections."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    candidates: tuple[RegistryEntry, ...]
    rejections: tuple[GovernanceRejection, ...]


class CandidateEnumerator:
    """Enumerate immutable registry entries and evidence definitions without selection."""

    __slots__ = ()

    @staticmethod
    def enumerate(snapshot: RegistrySnapshot) -> tuple[RegistryEntry, ...]:
        if not isinstance(snapshot, RegistrySnapshot):
            raise DataIntegrityError("snapshot must be an immutable RegistrySnapshot")
        return tuple(sorted(_require_entries(snapshot.entries), key=_candidate_key))

    @classmethod
    def evidence_definitions(cls, snapshot: RegistrySnapshot) -> tuple[tuple[str, str], ...]:
        definitions = {
            capability
            for entry in cls.enumerate(snapshot)
            for capability in entry.capability_references
        }
        return tuple(sorted(definitions))


class CandidateFilter:
    """Own externally observable E02 capability and governance filtering."""

    __slots__ = ()

    @classmethod
    def filter(
        cls,
        snapshot: RegistrySnapshot,
        requirement: EvidenceRequirement,
        target_claim: EvidenceClaim,
        source_claims: tuple[EvidenceClaim, ...],
        effects: tuple[CompatibilityEffects, ...],
        compatibility_dimension: str,
    ) -> CandidateDiagnostics:
        if not isinstance(requirement, EvidenceRequirement):
            raise DataIntegrityError("requirement must be an immutable EvidenceRequirement")
        if not isinstance(target_claim, EvidenceClaim):
            raise DataIntegrityError("target_claim must be an immutable EvidenceClaim")
        if not isinstance(source_claims, tuple) or not all(
            isinstance(claim, EvidenceClaim) for claim in source_claims
        ):
            raise DataIntegrityError("source_claims must be an immutable tuple of EvidenceClaim")
        if not isinstance(effects, tuple) or not all(
            isinstance(effect, CompatibilityEffects) for effect in effects
        ):
            raise DataIntegrityError("effects must be an immutable tuple of CompatibilityEffects")
        dimension = _require_text(compatibility_dimension, "compatibility_dimension")
        entries = cls.capabilities(
            CandidateEnumerator.enumerate(snapshot),
            requirement.evidence_type,
            requirement.semantic_version,
        )
        return _GovernanceFilter._apply(
            snapshot,
            entries,
            requirement,
            target_claim,
            source_claims,
            effects,
            dimension,
        )

    @staticmethod
    def capabilities(
        entries: tuple[RegistryEntry, ...], evidence_type: str, semantic_version: str
    ) -> tuple[RegistryEntry, ...]:
        candidates = _require_entries(entries)
        capability = (
            _require_text(evidence_type, "evidence_type"),
            _require_text(semantic_version, "semantic_version"),
        )
        return tuple(
            sorted(
                (entry for entry in candidates if capability in entry.capability_references),
                key=_candidate_key,
            )
        )


class _GovernanceFilter:
    """Apply fail-closed A03 governance eligibility without selecting a provider."""

    __slots__ = ()

    _LIFECYCLE_STATES = frozenset(
        {"Declared", "Registered", "Certified", "Enabled", "Deprecated", "Disabled", "Retired"}
    )
    _TRUST_STATES = frozenset({"Untrusted", "Trusted", "Revoked"})

    @classmethod
    def _apply(
        cls,
        snapshot: RegistrySnapshot,
        entries: tuple[RegistryEntry, ...],
        requirement: EvidenceRequirement,
        target_claim: EvidenceClaim,
        source_claims: tuple[EvidenceClaim, ...],
        effects: tuple[CompatibilityEffects, ...],
        compatibility_dimension: str,
    ) -> CandidateDiagnostics:
        candidates = _require_entries(entries)

        admitted: list[RegistryEntry] = []
        rejected: list[GovernanceRejection] = []
        for entry in sorted(candidates, key=_candidate_key):
            reason = cls._rejection_reason(
                snapshot,
                entry,
                requirement,
                target_claim,
                source_claims,
                effects,
                compatibility_dimension,
            )
            if reason is None:
                admitted.append(entry)
            else:
                rejected.append(
                    GovernanceRejection(
                        reason,
                        (entry.producer_identity,),
                        (("producer_version", entry.producer_version),),
                    )
                )
        return CandidateDiagnostics(
            snapshot.snapshot_identity,
            snapshot.manifest_reference,
            snapshot.governance_epoch,
            tuple(admitted),
            tuple(rejected),
        )

    @classmethod
    def _rejection_reason(
        cls,
        snapshot: RegistrySnapshot,
        entry: RegistryEntry,
        requirement: EvidenceRequirement,
        target_claim: EvidenceClaim,
        source_claims: tuple[EvidenceClaim, ...],
        effects: tuple[CompatibilityEffects, ...],
        compatibility_dimension: str,
    ) -> str | None:
        if entry.lifecycle_standing not in cls._LIFECYCLE_STATES:
            raise DataIntegrityError("registry entry has an unknown lifecycle standing")
        if entry.trust_standing not in cls._TRUST_STATES:
            raise DataIntegrityError("registry entry has an unknown trust standing")
        if entry.lifecycle_standing == "Declared":
            return "E02_NOT_ADMITTED"
        if entry.lifecycle_standing == "Disabled":
            return "E02_DISABLED_PROVIDER"
        if entry.lifecycle_standing in {"Deprecated", "Retired"}:
            return "E02_EXPIRED_PROVIDER"
        if entry.lifecycle_standing != "Enabled":
            return "E02_NOT_ENABLED"
        if entry.trust_standing == "Revoked":
            return "E02_REVOKED_PROVIDER"
        if entry.trust_standing != "Trusted":
            return "E02_UNTRUSTED_PROVIDER"

        capability = (requirement.evidence_type, requirement.semantic_version)
        certifications = tuple(
            record
            for record in entry.certification_records
            if record.producer_identity == entry.producer_identity
            and record.producer_version == entry.producer_version
            and capability in record.capability_references
        )
        if any(record.verdict == "revoked" for record in certifications):
            return "E02_REVOKED_PROVIDER"
        if any(record.verdict == "expired" for record in certifications):
            return "E02_EXPIRED_PROVIDER"
        valid_certifications = tuple(
            record
            for record in certifications
            if cls._certification_matches(record, entry, snapshot)
        )
        if len(valid_certifications) != 1:
            return "E02_UNCERTIFIED_PROVIDER"

        matching_sources = tuple(
            claim
            for claim in source_claims
            if claim.source_identity == entry.producer_identity
            and claim.implementation_version == entry.producer_version
            and claim.identity.evidence_type == requirement.evidence_type
            and claim.identity.semantic_version == requirement.semantic_version
        )
        if len(matching_sources) != 1:
            return "E02_INCOMPATIBLE_PROVIDER"
        source_claim = matching_sources[0]
        decisions = tuple(
            decision
            for decision in entry.compatibility_decisions
            if decision.source_reference == source_claim.evidence_id
            and decision.target_reference == requirement.requirement_id
        )
        if len(decisions) != 1:
            return "E02_INCOMPATIBLE_PROVIDER"
        decision = decisions[0]
        matching_effects = tuple(
            effect for effect in effects if effect.decision_reference == decision.decision_identity
        )
        if len(matching_effects) != 1:
            return "E02_INCOMPATIBLE_PROVIDER"
        if not cls._decision_matches(
            decision,
            source_claim,
            requirement,
            compatibility_dimension,
            snapshot,
            valid_certifications[0],
        ):
            return "E02_INCOMPATIBLE_PROVIDER"
        try:
            CompatibilityEvaluator.evaluate(
                source_claim,
                requirement,
                target_claim,
                decision,
                valid_certifications[0],
                matching_effects[0],
            )
        except DataIntegrityError:
            return "E02_INCOMPATIBLE_PROVIDER"
        return None

    @staticmethod
    def _certification_matches(
        record: CertificationRecord, entry: RegistryEntry, snapshot: RegistrySnapshot
    ) -> bool:
        return (
            record.verdict == "passed"
            and record.implementation_identity == entry.implementation_identity
            and record.producer_contract_version == entry.producer_contract_version
            and record.effective_epoch.sequence <= snapshot.governance_epoch.sequence
        )

    @staticmethod
    def _decision_matches(
        decision: CompatibilityDecision,
        source_claim: EvidenceClaim,
        requirement: EvidenceRequirement,
        compatibility_dimension: str,
        snapshot: RegistrySnapshot,
        certification: CertificationRecord,
    ) -> bool:
        versions = dict(decision.version_scope)
        return (
            decision.source_reference == source_claim.evidence_id
            and decision.target_reference == requirement.requirement_id
            and decision.direction == "source-to-target"
            and versions.get("source") == source_claim.identity.semantic_version
            and versions.get("target") == requirement.semantic_version
            and decision.intended_use == requirement.requirement_id
            and dict(decision.profile_scope).get("scope") == requirement.scope
            and decision.compatibility_dimension == compatibility_dimension
            and decision.review_or_expiry_condition == certification.expiration_or_review_condition
            and decision.revocation_reference is None
            and decision.supersession_reference is None
            and decision.effective_epoch.sequence <= snapshot.governance_epoch.sequence
        )
