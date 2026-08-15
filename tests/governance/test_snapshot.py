"""A03 Increment 4 snapshot builder tests governed by ADR-03 and ADR-09."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from epip.governance.model import (
    GovernanceEpoch,
    GovernanceManifest,
    GovernanceRejection,
    RegistryEntry,
    RegistrySnapshot,
)
from epip.governance.snapshot import _canonical_value, _SnapshotBuilder
from tests.governance.test_model import _action, _entry, _manifest


def _accepted(result: RegistrySnapshot | GovernanceRejection) -> RegistrySnapshot:
    assert isinstance(result, RegistrySnapshot)
    return result


def _rejection(result: RegistrySnapshot | GovernanceRejection) -> GovernanceRejection:
    assert isinstance(result, GovernanceRejection)
    return result


def test_builder_is_deterministic_reproducible_and_pure() -> None:
    entries = (_entry(),)
    manifest = _manifest()
    epoch = GovernanceEpoch(1)
    before = (entries, manifest, epoch)
    first = _accepted(_SnapshotBuilder.build(entries, manifest, epoch))
    second = _accepted(_SnapshotBuilder.build(entries, manifest, epoch))
    assert first == second
    assert first.snapshot_identity == second.snapshot_identity
    assert first.snapshot_identity.startswith("registry-snapshot:1:1:epip-json-v1:sha256-v1:")
    assert (entries, manifest, epoch) == before
    assert first.entries[0] is entries[0]
    with pytest.raises(FrozenInstanceError):
        first.manifest_reference = "changed"  # type: ignore[misc]


def test_builder_canonicalizes_entries_and_policies() -> None:
    later = _entry(producer_identity="producer-z", producer_version="2.0.0")
    earlier = _entry(producer_identity="producer-a", producer_version="1.0.0")
    action = _action(
        action_identity="action-z",
        effective_epoch=GovernanceEpoch(1),
        policy_versions=(("z-policy", "1.0.0"),),
    )
    manifest = _manifest(
        actions=(action,),
        policy_versions=(("z-policy", "1.0.0"), ("a-policy", "1.0.0")),
    )
    result = _accepted(_SnapshotBuilder.build((later, earlier), manifest, GovernanceEpoch(1)))
    assert tuple(entry.producer_identity for entry in result.entries) == (
        "producer-a",
        "producer-z",
    )
    assert result.governance_action_references == ("action-z",)
    assert result.policy_versions == (
        ("a-policy", "1.0.0"),
        ("z-policy", "1.0.0"),
    )


def test_input_order_does_not_change_snapshot_identity() -> None:
    first_entry = _entry(producer_identity="producer-a")
    second_entry = _entry(producer_identity="producer-z")
    manifest = _manifest(actions=(_action(action_identity="action-a"),))
    first = _accepted(
        _SnapshotBuilder.build((first_entry, second_entry), manifest, GovernanceEpoch(1))
    )
    second = _accepted(
        _SnapshotBuilder.build((second_entry, first_entry), manifest, GovernanceEpoch(1))
    )
    assert first.snapshot_identity == second.snapshot_identity
    assert first == second


def test_canonical_content_change_changes_snapshot_identity() -> None:
    manifest = _manifest()
    original = _accepted(_SnapshotBuilder.build((_entry(),), manifest, GovernanceEpoch(1)))
    changed = _accepted(
        _SnapshotBuilder.build(
            (_entry(trust_standing="Experimental"),), manifest, GovernanceEpoch(1)
        )
    )
    assert original.snapshot_identity != changed.snapshot_identity


@pytest.mark.parametrize(
    ("entries", "manifest", "epoch"),
    [
        (cast(tuple[RegistryEntry, ...], []), _manifest(), GovernanceEpoch(1)),
        ((cast(RegistryEntry, object()),), _manifest(), GovernanceEpoch(1)),
        ((), cast(GovernanceManifest, object()), GovernanceEpoch(1)),
        ((), _manifest(), cast(GovernanceEpoch, object())),
    ],
)
def test_builder_rejects_mutable_or_invalid_inputs(
    entries: tuple[RegistryEntry, ...],
    manifest: GovernanceManifest,
    epoch: GovernanceEpoch,
) -> None:
    assert _rejection(_SnapshotBuilder.build(entries, manifest, epoch)).reason_code == (
        "GOV_INVALID_MODEL"
    )


def test_builder_rejects_duplicate_entry_identities() -> None:
    entry = _entry()
    duplicate_entries = _rejection(
        _SnapshotBuilder.build((entry, entry), _manifest(), GovernanceEpoch(1))
    )
    assert duplicate_entries.diagnostic_details == (("fact", "duplicate_registry_entry_identity"),)


def test_builder_rejects_epoch_mismatch() -> None:
    mismatch = _rejection(_SnapshotBuilder.build((_entry(),), _manifest(), GovernanceEpoch(2)))
    assert mismatch.diagnostic_details == (("fact", "governance_epoch_mismatch"),)


def test_builder_rejects_manifest_policy_and_authority_mismatch() -> None:
    policy_mismatch = _manifest(policy_versions=(("other", "1.0.0"),))
    assert _rejection(
        _SnapshotBuilder.build((_entry(),), policy_mismatch, GovernanceEpoch(1))
    ).diagnostic_details == (("fact", "inconsistent_governance_manifest"),)
    authority_mismatch = _manifest(authority_facts=("other:producer_owner",))
    assert _rejection(
        _SnapshotBuilder.build((_entry(),), authority_mismatch, GovernanceEpoch(1))
    ).diagnostic_details == (("fact", "inconsistent_governance_manifest"),)


def test_manifest_authority_facts_participate_in_reproducible_identity() -> None:
    first = _accepted(_SnapshotBuilder.build((_entry(),), _manifest(), GovernanceEpoch(1)))
    second = _accepted(
        _SnapshotBuilder.build(
            (_entry(),),
            _manifest(authority_facts=("owner-001:producer_owner", "reviewer:observer")),
            GovernanceEpoch(1),
        )
    )
    assert first.snapshot_identity != second.snapshot_identity


def test_canonical_projection_fails_closed_for_unsupported_value() -> None:
    with pytest.raises(TypeError, match="unsupported canonical snapshot value"):
        _canonical_value(object())
