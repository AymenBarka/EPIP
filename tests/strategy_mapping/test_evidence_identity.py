# mypy: disable-error-code="arg-type,no-untyped-call,no-untyped-def"
from dataclasses import replace

import pytest

from epip.a07.foundation import StrategyEvidenceIdentity, StrategyIdentity
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import (
    EVIDENCE_ITEM_IDENTITY_DOMAIN,
    EVIDENCE_SET_IDENTITY_DOMAIN,
    derive_evidence_item_identity,
    derive_evidence_set_identity,
)
from epip.strategy_runtime.provenance import FactAdapterIdentity


def _common(semantic_profile):
    return {
        "strategy_identity": StrategyIdentity("s", "1"),
        "semantic_profile_identity": semantic_profile.identity,
        "adapter_identity": FactAdapterIdentity("a", "1", "p01-v1", "a" * 64),
        "typed_bundle_id": "bundle",
        "provenance_manifest_id": "manifest",
    }


def _item_args(semantic_profile, rule, key="alpha"):
    return {
        **_common(semantic_profile),
        "evidence_key": key,
        "mapping_rule": rule,
        "validity_rule": rule,
        "revision_rule": rule,
        "selected_candidate_ids": ("candidate",),
        "selected_source_binding_ids": ("source",),
        "selected_provenance_refs": ("provenance",),
        "fresh": True,
        "temporally_eligible": True,
    }


def test_item_identity_is_deterministic_and_commits_to_key_lineage_and_rules(
    semantic_profile, rule
) -> None:
    args = _item_args(semantic_profile, rule)
    identity = derive_evidence_item_identity(**args)
    assert identity == derive_evidence_item_identity(**args)
    assert identity.provenance == "manifest"
    assert EVIDENCE_ITEM_IDENTITY_DOMAIN == "epip.strategy-evidence-item.p02-f06-v1"
    variants = (
        {"evidence_key": "zeta"},
        {"selected_candidate_ids": ("other",)},
        {"selected_source_binding_ids": ("other",)},
        {"selected_provenance_refs": ("other",)},
        {"mapping_rule": replace(rule, rule_id="other")},
        {"provenance_manifest_id": "other"},
    )
    assert all(derive_evidence_item_identity(**(args | change)) != identity for change in variants)


def test_item_identity_canonicalizes_lineage_and_rejects_invalid_inputs(
    semantic_profile, rule
) -> None:
    args = _item_args(semantic_profile, rule)
    one = derive_evidence_item_identity(**(args | {"selected_candidate_ids": ("b", "a")}))
    two = derive_evidence_item_identity(**(args | {"selected_candidate_ids": ("a", "b")}))
    assert one == two
    for change in (
        {"selected_candidate_ids": ()},
        {"selected_source_binding_ids": ("x", "x")},
        {"fresh": 1},
        {"temporally_eligible": None},
        {"mapping_rule": object()},
    ):
        with pytest.raises(DataIntegrityError):
            derive_evidence_item_identity(**(args | change))


def test_complete_evidence_identity_is_permutation_invariant(semantic_profile, rule) -> None:
    """Retained predecessor node; F06 reverses its former permutation assertion."""
    common = _common(semantic_profile)
    alpha = derive_evidence_item_identity(**_item_args(semantic_profile, rule, "alpha"))
    zeta = derive_evidence_item_identity(**_item_args(semantic_profile, rule, "zeta"))
    a = ("alpha", alpha, ("ca",), ("sa",), ("pa",))
    z = ("zeta", zeta, ("cz",), ("sz",), ("pz",))
    semantic = derive_evidence_set_identity(**common, entries=(z, a))
    canonical = derive_evidence_set_identity(**common, entries=(a, z))
    assert semantic != canonical
    assert semantic == derive_evidence_set_identity(**common, entries=(z, a))
    assert semantic.provenance == "manifest"
    assert EVIDENCE_SET_IDENTITY_DOMAIN == "epip.strategy-evidence-set.p02-f06-v1"


def test_evidence_identity_rejects_duplicate_keys(
    semantic_profile, rule
) -> None:
    common = _common(semantic_profile)
    item = derive_evidence_item_identity(**_item_args(semantic_profile, rule))
    entry = ("alpha", item, ("c",), ("s",), ("p",))
    for entries in (
        (
            entry,
            (
                "alpha",
                StrategyEvidenceIdentity("b" * 64, "manifest"),
                ("d",),
                ("t",),
                ("q",),
            ),
        ),
        (entry, ("zeta", item, ("d",), ("t",), ("q",))),
        (("alpha", StrategyEvidenceIdentity("b" * 64, "other"), ("c",), ("s",), ("p",)),),
    ):
        with pytest.raises(DataIntegrityError):
            derive_evidence_set_identity(**common, entries=entries)
    for malformed_entries in ((), (("invalid",),)):
        with pytest.raises(DataIntegrityError):
            derive_evidence_set_identity(**common, entries=malformed_entries)
