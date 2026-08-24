"""Immutable executable semantic mapping-profile schema; no rule execution."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import (
    FOUNDATION_SCHEMA_VERSION,
    digest,
    exact,
    require_digest,
    text,
    version,
)
from epip.strategy_mapping.confidence_policy import ConfidencePolicy
from epip.strategy_mapping.direction_policy import (
    DirectionFactName,
    DirectionFactPolicy,
    MtfDirectionPolicyRef,
    NonAcceptanceAction,
)
from epip.strategy_mapping.evidence_policy import EvidenceRequirement, EvidenceTaxonomy
from epip.strategy_mapping.geometry_policy import (
    EntrySourcePolicy,
    StopSourcePolicy,
    TargetSourcePolicy,
)
from epip.strategy_runtime.profile import StrategyProfile, StrategyProfileIdentity

_REQUIRED_DIRECTION_FACTS = frozenset(
    {
        DirectionFactName.ELLIOTT,
        DirectionFactName.TREND,
        DirectionFactName.STRUCTURE,
        DirectionFactName.PRIMARY,
        DirectionFactName.ALTERNATE,
    }
)


@dataclass(frozen=True, slots=True)
class SemanticProfileIdentity:
    semantic_profile_id: str
    semantic_profile_version: str
    mapping_schema_version: str
    parent_profile_identity: StrategyProfileIdentity
    fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "semantic_profile_id", text(self.semantic_profile_id, "semantic_profile_id")
        )
        object.__setattr__(
            self,
            "semantic_profile_version",
            text(self.semantic_profile_version, "semantic_profile_version"),
        )
        version(self.mapping_schema_version, "mapping_schema_version")
        exact(self.parent_profile_identity, StrategyProfileIdentity, "parent_profile_identity")
        object.__setattr__(self, "fingerprint", require_digest(self.fingerprint, "fingerprint"))

    @property
    def reference(self) -> str:
        return f"{self.semantic_profile_id}@{self.semantic_profile_version}"


@dataclass(frozen=True, slots=True)
class StrategySemanticMappingProfile:
    schema_version: str
    identity: SemanticProfileIdentity
    parent_profile: StrategyProfile
    direction_policies: tuple[DirectionFactPolicy, ...]
    mtf_direction_policy: MtfDirectionPolicyRef
    entry_policy: EntrySourcePolicy
    stop_policy: StopSourcePolicy
    target_policy: TargetSourcePolicy
    confidence_policy: ConfidencePolicy
    evidence_taxonomy: EvidenceTaxonomy
    global_conflict_action: NonAcceptanceAction

    def __post_init__(self) -> None:
        version(self.schema_version)
        exact(self.identity, SemanticProfileIdentity, "identity")
        exact(self.parent_profile, StrategyProfile, "parent_profile")
        if self.identity.parent_profile_identity != self.parent_profile.identity:
            raise DataIntegrityError("semantic and P01 parent profile identities differ")
        if type(self.direction_policies) is not tuple or any(
            type(item) is not DirectionFactPolicy for item in self.direction_policies
        ):
            raise DataIntegrityError("direction_policies must contain DirectionFactPolicy values")
        policies = tuple(sorted(self.direction_policies, key=lambda item: item.fact_name.value))
        if {item.fact_name for item in policies} != _REQUIRED_DIRECTION_FACTS or len(policies) != 5:
            raise DataIntegrityError(
                "semantic profile requires five unique non-MTF direction policies"
            )
        object.__setattr__(self, "direction_policies", policies)
        exact(self.mtf_direction_policy, MtfDirectionPolicyRef, "mtf_direction_policy")
        exact(self.entry_policy, EntrySourcePolicy, "entry_policy")
        exact(self.stop_policy, StopSourcePolicy, "stop_policy")
        exact(self.target_policy, TargetSourcePolicy, "target_policy")
        exact(self.confidence_policy, ConfidencePolicy, "confidence_policy")
        exact(self.evidence_taxonomy, EvidenceTaxonomy, "evidence_taxonomy")
        exact(self.global_conflict_action, NonAcceptanceAction, "global_conflict_action")
        self._validate_parent_references()
        expected = digest(self, exclude=frozenset({"identity"}))
        if self.identity.fingerprint != expected:
            raise DataIntegrityError("semantic profile fingerprint does not match its rules")

    def _validate_parent_references(self) -> None:
        if self.parent_profile.mapping_rules_reference != self.identity.reference:
            raise DataIntegrityError("P01 mapping reference does not match semantic profile")
        if (
            self.parent_profile.confidence_model_reference
            != self.confidence_policy.policy_identity.reference
        ):
            raise DataIntegrityError("P01 confidence reference does not match semantic profile")
        if (
            self.parent_profile.evidence_taxonomy_reference
            != self.evidence_taxonomy.taxonomy_identity.reference
        ):
            raise DataIntegrityError("P01 evidence reference does not match semantic profile")
        if self.parent_profile.mtf_requirement != self.mtf_direction_policy.rule_identity.reference:
            raise DataIntegrityError("P01 MTF reference does not match semantic profile")
        required = tuple(
            item.evidence_key
            for item in self.evidence_taxonomy.keys
            if item.requirement is EvidenceRequirement.REQUIRED
        )
        optional = tuple(
            item.evidence_key
            for item in self.evidence_taxonomy.keys
            if item.requirement is EvidenceRequirement.OPTIONAL
        )
        if (
            required != self.parent_profile.required_evidence_keys
            or optional != self.parent_profile.optional_evidence_keys
        ):
            raise DataIntegrityError("P01 evidence keys and semantic taxonomy differ")

    @classmethod
    def create(
        cls,
        *,
        semantic_profile_id: str,
        semantic_profile_version: str,
        parent_profile: StrategyProfile,
        direction_policies: tuple[DirectionFactPolicy, ...],
        mtf_direction_policy: MtfDirectionPolicyRef,
        entry_policy: EntrySourcePolicy,
        stop_policy: StopSourcePolicy,
        target_policy: TargetSourcePolicy,
        confidence_policy: ConfidencePolicy,
        evidence_taxonomy: EvidenceTaxonomy,
        global_conflict_action: NonAcceptanceAction,
    ) -> StrategySemanticMappingProfile:
        placeholder = SemanticProfileIdentity(
            semantic_profile_id,
            semantic_profile_version,
            FOUNDATION_SCHEMA_VERSION,
            parent_profile.identity,
            "0" * 64,
        )
        candidate = object.__new__(cls)
        values = (
            FOUNDATION_SCHEMA_VERSION,
            placeholder,
            parent_profile,
            tuple(sorted(direction_policies, key=lambda item: item.fact_name.value)),
            mtf_direction_policy,
            entry_policy,
            stop_policy,
            target_policy,
            confidence_policy,
            evidence_taxonomy,
            global_conflict_action,
        )
        for name, value in zip(cls.__dataclass_fields__, values, strict=True):
            object.__setattr__(candidate, name, value)
        identity = SemanticProfileIdentity(
            semantic_profile_id,
            semantic_profile_version,
            FOUNDATION_SCHEMA_VERSION,
            parent_profile.identity,
            digest(candidate, exclude=frozenset({"identity"})),
        )
        return cls(values[0], identity, *values[2:])


__all__ = ["SemanticProfileIdentity", "StrategySemanticMappingProfile"]
