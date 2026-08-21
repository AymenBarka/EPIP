"""Deterministic candidate enumeration and governance filtering for A04-E02."""

from __future__ import annotations

from typing import NamedTuple

from epip.core.integrity import DataIntegrityError
from epip.evidence.model import (
    CompatibilityEffects,
    DiagnosticCode,
    DiagnosticReason,
    EvidenceRequirement,
)
from epip.evidence.validation import CompatibilityEvaluator
from epip.governance import (
    GovernanceEpoch,
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
    rejections: tuple[DiagnosticReason, ...]


class CandidateEnumerator:
    """Enumerate immutable registry entries and evidence definitions without selection."""

    __slots__ = ()

    @staticmethod
    def _enumerate(snapshot: RegistrySnapshot) -> tuple[RegistryEntry, ...]:
        if not isinstance(snapshot, RegistrySnapshot):
            raise DataIntegrityError("snapshot must be an immutable RegistrySnapshot")
        return tuple(sorted(_require_entries(snapshot.entries), key=_candidate_key))

    @classmethod
    def _evidence_definitions(cls, snapshot: RegistrySnapshot) -> tuple[tuple[str, str], ...]:
        definitions = {
            capability
            for entry in cls._enumerate(snapshot)
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
        effects: tuple[CompatibilityEffects, ...],
        compatibility_dimension: str,
    ) -> CandidateDiagnostics:
        if not isinstance(requirement, EvidenceRequirement):
            raise DataIntegrityError("requirement must be an immutable EvidenceRequirement")
        if not isinstance(effects, tuple) or not all(
            isinstance(effect, CompatibilityEffects) for effect in effects
        ):
            raise DataIntegrityError("effects must be an immutable tuple of CompatibilityEffects")
        dimension = _require_text(compatibility_dimension, "compatibility_dimension")
        entries = cls._capabilities(
            CandidateEnumerator._enumerate(snapshot),
            requirement.evidence_type,
            requirement.semantic_version,
        )
        return _GovernanceFilter._apply(
            snapshot,
            entries,
            requirement,
            effects,
            dimension,
        )

    @staticmethod
    def _capabilities(
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
        effects: tuple[CompatibilityEffects, ...],
        compatibility_dimension: str,
    ) -> CandidateDiagnostics:
        candidates = _require_entries(entries)

        admitted: list[RegistryEntry] = []
        rejected: list[DiagnosticReason] = []
        for entry in sorted(candidates, key=_candidate_key):
            reason = cls._rejection_reason(
                snapshot,
                entry,
                requirement,
                effects,
                compatibility_dimension,
            )
            if reason is None:
                admitted.append(entry)
            else:
                rejected.append(
                    DiagnosticReason(
                        reason,
                        requirement.requirement_id,
                        cls._reason_text(reason),
                        entry.producer_identity,
                        entry.producer_version,
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
        effects: tuple[CompatibilityEffects, ...],
        compatibility_dimension: str,
    ) -> DiagnosticCode | None:
        if entry.lifecycle_standing not in cls._LIFECYCLE_STATES:
            raise DataIntegrityError("registry entry has an unknown lifecycle standing")
        if entry.trust_standing not in cls._TRUST_STATES:
            raise DataIntegrityError("registry entry has an unknown trust standing")
        if entry.lifecycle_standing == "Declared":
            return DiagnosticCode.INELIGIBLE_PROVIDER
        if entry.lifecycle_standing == "Disabled":
            return DiagnosticCode.INELIGIBLE_PROVIDER
        if entry.lifecycle_standing in {"Deprecated", "Retired"}:
            return DiagnosticCode.INELIGIBLE_PROVIDER
        if entry.lifecycle_standing != "Enabled":
            return DiagnosticCode.INELIGIBLE_PROVIDER
        if entry.trust_standing == "Revoked":
            return DiagnosticCode.INELIGIBLE_PROVIDER
        if entry.trust_standing != "Trusted":
            return DiagnosticCode.INELIGIBLE_PROVIDER
        try:
            CompatibilityEvaluator.validate_phase2(
                requirement,
                snapshot,
                entry,
                effects,
                compatibility_dimension,
            )
        except DataIntegrityError as error:
            return cls._diagnostic_code(error)
        return None

    @staticmethod
    def _diagnostic_code(error: DataIntegrityError) -> DiagnosticCode:
        message = str(error)
        return next(
            (code for code in DiagnosticCode if message.startswith(f"{code.value}:")),
            DiagnosticCode.INVALID_DEPENDENCY,
        )

    @staticmethod
    def _reason_text(code: DiagnosticCode) -> str:
        reasons = {
            DiagnosticCode.INELIGIBLE_PROVIDER: "provider failed mandatory governance eligibility",
            DiagnosticCode.EXPIRED_OR_REVOKED_CERTIFICATION: (
                "provider certification is expired or revoked"
            ),
            DiagnosticCode.INCOMPATIBLE_DEPENDENCY: (
                "provider has no active authoritative compatibility decision"
            ),
            DiagnosticCode.INVALID_DEPENDENCY: (
                "provider compatibility facts failed closed validation"
            ),
        }
        return reasons[code]
