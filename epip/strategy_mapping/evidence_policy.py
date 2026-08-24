"""Evidence taxonomy, freshness, and temporal eligibility policy contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import boolean, exact, non_negative_int, text
from epip.strategy_mapping.direction_policy import NonAcceptanceAction, SourceSelector
from epip.strategy_mapping.rule_identity import RuleIdentity
from epip.strategy_runtime.mtf import TimeframeRole


class EvidenceRequirement(Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


class FreshnessBasis(Enum):
    OBSERVATION = "OBSERVATION"
    AVAILABILITY = "AVAILABILITY"


@dataclass(frozen=True, slots=True)
class FreshnessPolicy:
    policy_identity: RuleIdentity
    basis: FreshnessBasis
    max_age_seconds: int
    failure_action: NonAcceptanceAction

    def __post_init__(self) -> None:
        exact(self.policy_identity, RuleIdentity, "policy_identity")
        exact(self.basis, FreshnessBasis, "basis")
        non_negative_int(self.max_age_seconds, "max_age_seconds")
        exact(self.failure_action, NonAcceptanceAction, "failure_action")


@dataclass(frozen=True, slots=True)
class TemporalEligibilityPolicy:
    policy_identity: RuleIdentity
    required_timeframe_roles: tuple[TimeframeRole, ...]
    validity_rule: RuleIdentity
    revision_rule: RuleIdentity
    failure_action: NonAcceptanceAction

    def __post_init__(self) -> None:
        exact(self.policy_identity, RuleIdentity, "policy_identity")
        if type(self.required_timeframe_roles) is not tuple or any(
            type(item) is not TimeframeRole for item in self.required_timeframe_roles
        ):
            raise DataIntegrityError("required_timeframe_roles must contain TimeframeRole values")
        roles = tuple(sorted(set(self.required_timeframe_roles), key=lambda item: item.value))
        if not roles or len(roles) != len(self.required_timeframe_roles):
            raise DataIntegrityError("required timeframe roles must be non-empty and unique")
        object.__setattr__(self, "required_timeframe_roles", roles)
        exact(self.validity_rule, RuleIdentity, "validity_rule")
        exact(self.revision_rule, RuleIdentity, "revision_rule")
        exact(self.failure_action, NonAcceptanceAction, "failure_action")


@dataclass(frozen=True, slots=True)
class EvidenceKeyPolicy:
    evidence_key: str
    requirement: EvidenceRequirement
    source_selector: SourceSelector
    freshness_policy: FreshnessPolicy
    temporal_eligibility_policy: TemporalEligibilityPolicy
    require_provenance: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_key", text(self.evidence_key, "evidence_key"))
        exact(self.requirement, EvidenceRequirement, "requirement")
        exact(self.source_selector, SourceSelector, "source_selector")
        exact(self.freshness_policy, FreshnessPolicy, "freshness_policy")
        exact(
            self.temporal_eligibility_policy,
            TemporalEligibilityPolicy,
            "temporal_eligibility_policy",
        )
        if not boolean(self.require_provenance, "require_provenance"):
            raise DataIntegrityError("evidence policies require provenance")


@dataclass(frozen=True, slots=True)
class EvidenceTaxonomy:
    taxonomy_identity: RuleIdentity
    keys: tuple[EvidenceKeyPolicy, ...]
    unknown_source_action: NonAcceptanceAction
    duplicate_action: NonAcceptanceAction
    ordering_rule: RuleIdentity

    def __post_init__(self) -> None:
        exact(self.taxonomy_identity, RuleIdentity, "taxonomy_identity")
        if (
            type(self.keys) is not tuple
            or not self.keys
            or any(type(item) is not EvidenceKeyPolicy for item in self.keys)
        ):
            raise DataIntegrityError("keys must be a non-empty EvidenceKeyPolicy tuple")
        keys = tuple(sorted(self.keys, key=lambda item: item.evidence_key))
        if len({item.evidence_key for item in keys}) != len(keys):
            raise DataIntegrityError("evidence keys must be unique")
        object.__setattr__(self, "keys", keys)
        exact(self.unknown_source_action, NonAcceptanceAction, "unknown_source_action")
        exact(self.duplicate_action, NonAcceptanceAction, "duplicate_action")
        exact(self.ordering_rule, RuleIdentity, "ordering_rule")


__all__ = [
    "EvidenceKeyPolicy",
    "EvidenceRequirement",
    "EvidenceTaxonomy",
    "FreshnessBasis",
    "FreshnessPolicy",
    "TemporalEligibilityPolicy",
]
