"""Canonical evidence-item and ordered evidence-set identity derivation."""

from __future__ import annotations

from hashlib import sha256

from epip.a07.foundation import StrategyEvidenceIdentity, StrategyIdentity
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import boolean, exact, text, unique_texts
from epip.strategy_mapping.profile import SemanticProfileIdentity
from epip.strategy_mapping.rule_identity import RuleIdentity
from epip.strategy_runtime._base import canonical_json
from epip.strategy_runtime.provenance import FactAdapterIdentity

EVIDENCE_ITEM_IDENTITY_DOMAIN = "epip.strategy-evidence-item.p02-f06-v1"
EVIDENCE_SET_IDENTITY_DOMAIN = "epip.strategy-evidence-set.p02-f06-v1"


def _common_payload(
    strategy_identity: StrategyIdentity,
    semantic_profile_identity: SemanticProfileIdentity,
    adapter_identity: FactAdapterIdentity,
    typed_bundle_id: str,
    provenance_manifest_id: str,
) -> dict[str, object]:
    exact(strategy_identity, StrategyIdentity, "strategy_identity")
    exact(semantic_profile_identity, SemanticProfileIdentity, "semantic_profile_identity")
    exact(adapter_identity, FactAdapterIdentity, "adapter_identity")
    return {
        "strategy_id": strategy_identity.strategy_id,
        "strategy_version": strategy_identity.strategy_version,
        "semantic_profile_identity": semantic_profile_identity,
        "adapter_identity": adapter_identity,
        "typed_bundle_id": text(typed_bundle_id, "typed_bundle_id"),
        "provenance_manifest_id": text(provenance_manifest_id, "provenance_manifest_id"),
    }


def derive_evidence_item_identity(
    *,
    strategy_identity: StrategyIdentity,
    semantic_profile_identity: SemanticProfileIdentity,
    adapter_identity: FactAdapterIdentity,
    typed_bundle_id: str,
    provenance_manifest_id: str,
    evidence_key: str,
    mapping_rule: RuleIdentity,
    validity_rule: RuleIdentity,
    revision_rule: RuleIdentity,
    selected_candidate_ids: tuple[str, ...],
    selected_source_binding_ids: tuple[str, ...],
    selected_provenance_refs: tuple[str, ...],
    fresh: bool,
    temporally_eligible: bool,
) -> StrategyEvidenceIdentity:
    """Derive one evidence member's identity from its complete semantic lineage."""
    payload = _common_payload(
        strategy_identity,
        semantic_profile_identity,
        adapter_identity,
        typed_bundle_id,
        provenance_manifest_id,
    )
    payload.update(
        {
            "domain": EVIDENCE_ITEM_IDENTITY_DOMAIN,
            "evidence_key": text(evidence_key, "evidence_key"),
            "mapping_rule": exact(mapping_rule, RuleIdentity, "mapping_rule"),
            "validity_rule": exact(validity_rule, RuleIdentity, "validity_rule"),
            "revision_rule": exact(revision_rule, RuleIdentity, "revision_rule"),
            "selected_candidate_ids": unique_texts(
                selected_candidate_ids, "selected_candidate_ids", allow_empty=False
            ),
            "selected_source_binding_ids": unique_texts(
                selected_source_binding_ids, "selected_source_binding_ids", allow_empty=False
            ),
            "selected_provenance_refs": unique_texts(
                selected_provenance_refs, "selected_provenance_refs", allow_empty=False
            ),
            "fresh": boolean(fresh, "fresh"),
            "temporally_eligible": boolean(temporally_eligible, "temporally_eligible"),
        }
    )
    evidence_id = sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return StrategyEvidenceIdentity(evidence_id, provenance_manifest_id)


def derive_evidence_set_identity(
    *,
    strategy_identity: StrategyIdentity,
    semantic_profile_identity: SemanticProfileIdentity,
    adapter_identity: FactAdapterIdentity,
    typed_bundle_id: str,
    provenance_manifest_id: str,
    entries: tuple[
        tuple[str, StrategyEvidenceIdentity, tuple[str, ...], tuple[str, ...], tuple[str, ...]],
        ...,
    ],
) -> StrategyEvidenceIdentity:
    """Derive the set identity while preserving the governed semantic order."""
    payload = _common_payload(
        strategy_identity,
        semantic_profile_identity,
        adapter_identity,
        typed_bundle_id,
        provenance_manifest_id,
    )
    if type(entries) is not tuple or not entries:
        raise DataIntegrityError("entries must be a non-empty tuple")
    normalized = []
    for entry in entries:
        if type(entry) is not tuple or len(entry) != 5:
            raise DataIntegrityError("evidence entry has invalid shape")
        key = text(entry[0], "evidence_key")
        item_identity = exact(entry[1], StrategyEvidenceIdentity, "evidence_item_identity")
        if item_identity.provenance != provenance_manifest_id:
            raise DataIntegrityError("evidence item provenance does not match manifest")
        normalized.append(
            (
                key,
                item_identity,
                unique_texts(entry[2], "selected_candidate_ids", allow_empty=False),
                unique_texts(entry[3], "selected_source_binding_ids", allow_empty=False),
                unique_texts(entry[4], "selected_provenance_refs", allow_empty=False),
            )
        )
    ordered = tuple(normalized)
    if len({x[0] for x in ordered}) != len(ordered):
        raise DataIntegrityError("evidence keys must be unique")
    if len({x[1] for x in ordered}) != len(ordered):
        raise DataIntegrityError("evidence item identities must be unique")
    payload.update({"domain": EVIDENCE_SET_IDENTITY_DOMAIN, "entries": ordered})
    evidence_id = sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return StrategyEvidenceIdentity(evidence_id, provenance_manifest_id)


__all__ = [
    "EVIDENCE_ITEM_IDENTITY_DOMAIN",
    "EVIDENCE_SET_IDENTITY_DOMAIN",
    "derive_evidence_item_identity",
    "derive_evidence_set_identity",
]
