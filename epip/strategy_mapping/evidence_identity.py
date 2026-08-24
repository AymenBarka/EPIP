"""Canonical complete-evidence-set identity derivation."""

from __future__ import annotations

from hashlib import sha256

from epip.a07.foundation import StrategyEvidenceIdentity, StrategyIdentity
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import exact, text, unique_texts
from epip.strategy_mapping.profile import SemanticProfileIdentity
from epip.strategy_runtime._base import canonical_json
from epip.strategy_runtime.provenance import FactAdapterIdentity

EVIDENCE_SET_IDENTITY_DOMAIN = "epip.strategy-evidence-set.p02-f02-v1"


def derive_evidence_set_identity(
    *,
    strategy_identity: StrategyIdentity,
    semantic_profile_identity: SemanticProfileIdentity,
    adapter_identity: FactAdapterIdentity,
    typed_bundle_id: str,
    provenance_manifest_id: str,
    entries: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...],
) -> StrategyEvidenceIdentity:
    exact(strategy_identity, StrategyIdentity, "strategy_identity")
    exact(semantic_profile_identity, SemanticProfileIdentity, "semantic_profile_identity")
    exact(adapter_identity, FactAdapterIdentity, "adapter_identity")
    typed_bundle_id = text(typed_bundle_id, "typed_bundle_id")
    provenance_manifest_id = text(provenance_manifest_id, "provenance_manifest_id")
    if type(entries) is not tuple or not entries:
        raise DataIntegrityError("entries must be a non-empty tuple")
    normalized = []
    for entry in entries:
        if type(entry) is not tuple or len(entry) != 3:
            raise DataIntegrityError("evidence entry has invalid shape")
        key = text(entry[0], "evidence_key")
        sources = unique_texts(entry[1], "source_binding_ids", allow_empty=False)
        provenance = unique_texts(entry[2], "provenance_refs", allow_empty=False)
        normalized.append((key, sources, provenance))
    ordered = tuple(sorted(normalized, key=lambda item: item[0]))
    if len({x[0] for x in ordered}) != len(ordered):
        raise DataIntegrityError("evidence keys must be unique")
    payload = {
        "domain": EVIDENCE_SET_IDENTITY_DOMAIN,
        "strategy_id": strategy_identity.strategy_id,
        "strategy_version": strategy_identity.strategy_version,
        "semantic_profile_identity": semantic_profile_identity,
        "adapter_identity": adapter_identity,
        "typed_bundle_id": typed_bundle_id,
        "provenance_manifest_id": provenance_manifest_id,
        "entries": ordered,
    }
    evidence_id = sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return StrategyEvidenceIdentity(evidence_id, provenance_manifest_id)


__all__ = ["EVIDENCE_SET_IDENTITY_DOMAIN", "derive_evidence_set_identity"]
