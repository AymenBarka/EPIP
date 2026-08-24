"""Immutable Strategy Profile identity and compatibility contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from epip.a07.foundation import StrategyIdentity
from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime._base import CONTRACT_VERSION, digest, require_digest, text, unique_texts


@dataclass(frozen=True, slots=True)
class StrategyProfileIdentity:
    profile_id: str
    profile_version: str
    contract_version: str
    fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", text(self.profile_id, "profile_id"))
        object.__setattr__(self, "profile_version", text(self.profile_version, "profile_version"))
        if self.contract_version != CONTRACT_VERSION:
            raise DataIntegrityError("unsupported profile contract version")
        object.__setattr__(self, "fingerprint", require_digest(self.fingerprint, "fingerprint"))


@dataclass(frozen=True, slots=True)
class StrategyProfile:
    identity: StrategyProfileIdentity
    strategy_identity: StrategyIdentity
    compatible_runtime_contract_versions: tuple[str, ...]
    compatible_adapter_contract_versions: tuple[str, ...]
    required_source_domains: tuple[str, ...]
    optional_source_domains: tuple[str, ...]
    required_evidence_keys: tuple[str, ...]
    optional_evidence_keys: tuple[str, ...]
    enabled_direction_facts: tuple[str, ...]
    enabled_geometry_sources: tuple[str, ...]
    confidence_model_reference: str
    evidence_taxonomy_reference: str
    mtf_requirement: str
    mapping_rules_reference: str

    def __post_init__(self) -> None:
        if type(self.identity) is not StrategyProfileIdentity:
            raise DataIntegrityError("identity must be a StrategyProfileIdentity")
        if type(self.strategy_identity) is not StrategyIdentity:
            raise DataIntegrityError("strategy_identity must be a StrategyIdentity")
        tuple_fields = (
            "compatible_runtime_contract_versions",
            "compatible_adapter_contract_versions",
            "required_source_domains",
            "optional_source_domains",
            "required_evidence_keys",
            "optional_evidence_keys",
            "enabled_direction_facts",
            "enabled_geometry_sources",
        )
        for name in tuple_fields:
            object.__setattr__(self, name, unique_texts(getattr(self, name), name))
        if set(self.required_source_domains) & set(self.optional_source_domains):
            raise DataIntegrityError("required and optional source domains must be disjoint")
        if set(self.required_evidence_keys) & set(self.optional_evidence_keys):
            raise DataIntegrityError("required and optional evidence keys must be disjoint")
        for name in (
            "confidence_model_reference",
            "evidence_taxonomy_reference",
            "mtf_requirement",
            "mapping_rules_reference",
        ):
            object.__setattr__(self, name, text(getattr(self, name), name))
        expected = digest(self, exclude=frozenset({"identity"}))
        if self.identity.fingerprint != expected:
            raise DataIntegrityError("profile fingerprint does not match canonical content")

    @classmethod
    def create(
        cls,
        *,
        profile_id: str,
        profile_version: str,
        strategy_identity: StrategyIdentity,
        compatible_runtime_contract_versions: tuple[str, ...],
        compatible_adapter_contract_versions: tuple[str, ...],
        required_source_domains: tuple[str, ...],
        optional_source_domains: tuple[str, ...],
        required_evidence_keys: tuple[str, ...],
        optional_evidence_keys: tuple[str, ...],
        enabled_direction_facts: tuple[str, ...],
        enabled_geometry_sources: tuple[str, ...],
        confidence_model_reference: str,
        evidence_taxonomy_reference: str,
        mtf_requirement: str,
        mapping_rules_reference: str,
    ) -> StrategyProfile:
        placeholder = StrategyProfileIdentity(
            profile_id, profile_version, CONTRACT_VERSION, "0" * 64
        )
        candidate = object.__new__(cls)
        values = {
            "strategy_identity": strategy_identity,
            "compatible_runtime_contract_versions": compatible_runtime_contract_versions,
            "compatible_adapter_contract_versions": compatible_adapter_contract_versions,
            "required_source_domains": required_source_domains,
            "optional_source_domains": optional_source_domains,
            "required_evidence_keys": required_evidence_keys,
            "optional_evidence_keys": optional_evidence_keys,
            "enabled_direction_facts": enabled_direction_facts,
            "enabled_geometry_sources": enabled_geometry_sources,
            "confidence_model_reference": confidence_model_reference,
            "evidence_taxonomy_reference": evidence_taxonomy_reference,
            "mtf_requirement": mtf_requirement,
            "mapping_rules_reference": mapping_rules_reference,
        }
        object.__setattr__(candidate, "identity", placeholder)
        for name, value in values.items():
            object.__setattr__(candidate, name, value)
        identity = StrategyProfileIdentity(
            profile_id,
            profile_version,
            CONTRACT_VERSION,
            digest(candidate, exclude=frozenset({"identity"})),
        )
        return cls(
            identity,
            strategy_identity,
            compatible_runtime_contract_versions,
            compatible_adapter_contract_versions,
            required_source_domains,
            optional_source_domains,
            required_evidence_keys,
            optional_evidence_keys,
            enabled_direction_facts,
            enabled_geometry_sources,
            confidence_model_reference,
            evidence_taxonomy_reference,
            mtf_requirement,
            mapping_rules_reference,
        )


class StrategyProfileRegistryProtocol(Protocol):
    def resolve(self, identity: StrategyProfileIdentity) -> StrategyProfile: ...
