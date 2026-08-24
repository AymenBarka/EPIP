"""Immutable bridge between frozen P01 inputs and P02 execution contracts."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import digest, exact, require_digest, text
from epip.strategy_mapping.profile import SemanticProfileIdentity
from epip.strategy_mapping.rule_execution import EXECUTION_SCHEMA_VERSION
from epip.strategy_runtime.provenance import FactAdapterIdentity


@dataclass(frozen=True, slots=True)
class AdapterInvocationBinding:
    schema_version: str
    binding_id: str
    adapter_identity: FactAdapterIdentity
    semantic_profile_identity: SemanticProfileIdentity
    resolved_rule_set_id: str
    typed_bundle_id: str
    analytical_input_digest: str
    provenance_manifest_id: str
    instrument_binding_id: str

    def __post_init__(self) -> None:
        if self.schema_version != EXECUTION_SCHEMA_VERSION:
            raise DataIntegrityError("unsupported execution schema version")
        exact(self.adapter_identity, FactAdapterIdentity, "adapter_identity")
        exact(self.semantic_profile_identity, SemanticProfileIdentity, "semantic_profile_identity")
        object.__setattr__(
            self,
            "resolved_rule_set_id",
            require_digest(self.resolved_rule_set_id, "resolved_rule_set_id"),
        )
        object.__setattr__(
            self,
            "analytical_input_digest",
            require_digest(self.analytical_input_digest, "analytical_input_digest"),
        )
        for name in ("typed_bundle_id", "provenance_manifest_id", "instrument_binding_id"):
            object.__setattr__(self, name, text(getattr(self, name), name))
        if self.binding_id != digest(self, exclude=frozenset({"binding_id"})):
            raise DataIntegrityError("binding_id does not match invocation binding")

    @classmethod
    def create(
        cls,
        *,
        adapter_identity: FactAdapterIdentity,
        semantic_profile_identity: SemanticProfileIdentity,
        resolved_rule_set_id: str,
        typed_bundle_id: str,
        analytical_input_digest: str,
        provenance_manifest_id: str,
        instrument_binding_id: str,
    ) -> AdapterInvocationBinding:
        candidate = object.__new__(cls)
        values = (
            EXECUTION_SCHEMA_VERSION,
            "",
            adapter_identity,
            semantic_profile_identity,
            resolved_rule_set_id,
            typed_bundle_id,
            analytical_input_digest,
            provenance_manifest_id,
            instrument_binding_id,
        )
        for name, value in zip(cls.__dataclass_fields__, values, strict=True):
            object.__setattr__(candidate, name, value)
        return cls(values[0], digest(candidate, exclude=frozenset({"binding_id"})), *values[2:])


__all__ = ["AdapterInvocationBinding"]
