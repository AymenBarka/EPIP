"""Deterministic provider selection over governed A04-E02 candidates."""

from __future__ import annotations

from typing import NamedTuple

from epip.core.integrity import DataIntegrityError
from epip.evidence.candidates import CandidateDiagnostics
from epip.evidence.model import (
    DependencyType,
    DiagnosticCode,
    DiagnosticReason,
    EvidenceRequirement,
    ResolutionProfile,
)
from epip.governance import GovernanceEpoch, RegistryEntry


def _candidate_key(entry: RegistryEntry) -> tuple[str, str, str]:
    return (entry.producer_identity, entry.producer_version, entry.implementation_identity)


def _require_candidates(value: object) -> CandidateDiagnostics:
    if not isinstance(value, CandidateDiagnostics):
        raise DataIntegrityError("candidates must be immutable CandidateDiagnostics")
    identities = tuple(
        (entry.producer_identity, entry.producer_version) for entry in value.candidates
    )
    if len(set(identities)) != len(identities):
        raise DataIntegrityError("governed candidate identities must be unique")
    return value


class SelectionPolicy(NamedTuple):
    """Immutable E03 policy binding one frozen E00 resolution profile."""

    resolution_profile: ResolutionProfile


class SelectionDiagnostics(NamedTuple):
    """Immutable selection outcome preserving snapshot and candidate diagnostics."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    considered_candidates: tuple[RegistryEntry, ...]
    selected_candidates: tuple[RegistryEntry, ...]
    diagnostics: tuple[DiagnosticReason, ...]


class SelectionEngine:
    """Apply pins and cardinality without repeating candidate governance."""

    __slots__ = ()

    @classmethod
    def select(
        cls,
        candidates: CandidateDiagnostics,
        requirement: EvidenceRequirement,
        policy: SelectionPolicy,
    ) -> SelectionDiagnostics:
        governed = _require_candidates(candidates)
        if not isinstance(requirement, EvidenceRequirement):
            raise DataIntegrityError("requirement must be immutable EvidenceRequirement")
        if not isinstance(policy, SelectionPolicy):
            raise DataIntegrityError("policy must be immutable SelectionPolicy")
        profile = policy.resolution_profile
        if not isinstance(profile, ResolutionProfile):
            raise DataIntegrityError("resolution_profile must be immutable ResolutionProfile")
        if (
            requirement.resolution_profile_id is not None
            and requirement.resolution_profile_id != profile.profile_id
        ):
            raise DataIntegrityError("selection policy does not match the requirement profile")

        ordered = tuple(sorted(governed.candidates, key=_candidate_key))
        selected, diagnostic = cls._select_candidates(ordered, requirement, profile)
        diagnostics = governed.rejections
        if diagnostic is not None:
            diagnostics = (*diagnostics, diagnostic)
        return SelectionDiagnostics(
            governed.snapshot_identity,
            governed.manifest_reference,
            governed.governance_epoch,
            ordered,
            selected,
            diagnostics,
        )

    @classmethod
    def _select_candidates(
        cls,
        candidates: tuple[RegistryEntry, ...],
        requirement: EvidenceRequirement,
        profile: ResolutionProfile,
    ) -> tuple[tuple[RegistryEntry, ...], DiagnosticReason | None]:
        pinned = profile.pinned_producer_id
        if pinned is not None:
            matching = tuple(entry for entry in candidates if entry.producer_identity == pinned)
            if len(matching) != 1:
                return (), cls._reason(
                    DiagnosticCode.MISSING_MANDATORY_DEPENDENCY,
                    requirement,
                    "the governed pinned provider is unavailable",
                    pinned,
                )
            return cls._validate_cardinality(matching, requirement)

        if not candidates:
            code = (
                DiagnosticCode.ABSENT_OPTIONAL_DEPENDENCY
                if requirement.dependency_type is DependencyType.OPTIONAL
                else DiagnosticCode.MISSING_MANDATORY_DEPENDENCY
            )
            return (), cls._reason(code, requirement, "no governed candidate is available")
        if len(candidates) == 1:
            return cls._validate_cardinality(candidates, requirement)
        if not profile.allow_multi_provider:
            return (), cls._reason(
                DiagnosticCode.AMBIGUOUS_DEPENDENCY,
                requirement,
                "multiple governed candidates remain without a selection rule",
            )
        if len(candidates) > requirement.max_cardinality:
            return (), cls._reason(
                DiagnosticCode.AMBIGUOUS_DEPENDENCY,
                requirement,
                "the policy cannot choose a deterministic candidate subset",
            )
        return cls._validate_cardinality(candidates, requirement)

    @classmethod
    def _validate_cardinality(
        cls,
        selected: tuple[RegistryEntry, ...],
        requirement: EvidenceRequirement,
    ) -> tuple[tuple[RegistryEntry, ...], DiagnosticReason | None]:
        count = len(selected)
        expected = requirement.exact_cardinality
        valid = (
            count == expected
            if expected is not None
            else requirement.min_cardinality <= count <= requirement.max_cardinality
        )
        if not valid:
            return (), cls._reason(
                DiagnosticCode.CARDINALITY_VIOLATION,
                requirement,
                "governed candidates do not satisfy required cardinality",
            )
        return selected, None

    @staticmethod
    def _reason(
        code: DiagnosticCode,
        requirement: EvidenceRequirement,
        reason: str,
        candidate_id: str | None = None,
    ) -> DiagnosticReason:
        return DiagnosticReason(
            code,
            requirement.requirement_id,
            reason,
            candidate_id,
            requirement.semantic_version,
        )
