"""A03-V2-E03 reduction-result-aware candidate construction tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from typing import cast

import pytest

from epip.governance.model import (
    GovernanceEpoch,
    GovernanceManifest,
    GovernanceRejection,
    RegistryEntry,
    RegistrySnapshot,
)
from epip.governance.reduction import _ReductionResult
from epip.governance.snapshot import _canonical_value, _SnapshotBuilder
from epip.governance.validation import _ValidationAcceptance
from tests.governance.test_model import _action, _entry, _manifest, _snapshot


def _accepted(result: RegistrySnapshot | GovernanceRejection) -> RegistrySnapshot:
    assert isinstance(result, RegistrySnapshot)
    return result


def _rejection(result: RegistrySnapshot | GovernanceRejection) -> GovernanceRejection:
    assert isinstance(result, GovernanceRejection)
    return result


def _construction_context(
    *,
    entries: tuple[RegistryEntry, ...] | None = None,
    policies: tuple[tuple[str, str], ...] = (("admission", "1.0.0"),),
    authority_facts: tuple[str, ...] = ("registry-authority:registry_authority",),
) -> tuple[_ReductionResult, GovernanceManifest, GovernanceEpoch]:
    epoch = GovernanceEpoch(2)
    action = _action(
        action_identity="action-002",
        action_type="lifecycle_transitioned",
        authority_identity="registry-authority",
        authority_role="registry_authority",
        effective_epoch=epoch,
        policy_versions=policies,
    )
    manifest = _manifest(
        manifest_identity="manifest-002",
        governance_epoch=epoch,
        actions=(action,),
        policy_versions=policies,
        authority_facts=authority_facts,
    )
    starting = _snapshot(
        governance_epoch=GovernanceEpoch(1),
        governance_action_references=("action-001",),
        policy_versions=(("admission", "1.0.0"),),
    )
    reduced_entries = entries if entries is not None else starting.entries
    acceptance = _ValidationAcceptance("authority", starting, action, manifest, epoch)
    reduction = _ReductionResult(
        starting_snapshot=starting,
        action=action,
        manifest=manifest,
        epoch=epoch,
        validation_acceptances=(acceptance,),
        entries=reduced_entries,
        governance_action_references=("action-001", "action-002"),
        policy_versions=policies,
        authority_facts=authority_facts,
    )
    return reduction, manifest, epoch


def test_builder_consumes_reduction_result_deterministically_and_purely() -> None:
    reduction, manifest, epoch = _construction_context()
    before = (reduction, manifest, epoch)

    first = _accepted(_SnapshotBuilder.build(reduction, manifest, epoch))
    second = _accepted(_SnapshotBuilder.build(reduction, manifest, epoch))

    assert first == second
    assert first.snapshot_identity.startswith("registry-snapshot:1:1:epip-json-v1:sha256-v1:")
    assert first.manifest_reference == manifest.manifest_identity
    assert first.governance_epoch is epoch
    assert (reduction, manifest, epoch) == before
    with pytest.raises(FrozenInstanceError):
        first.manifest_reference = "changed"  # type: ignore[misc]


def test_builder_preserves_history_unaffected_entries_and_canonical_order() -> None:
    later = _entry(producer_identity="producer-z", producer_version="2.0.0")
    earlier = _entry(producer_identity="producer-a", producer_version="1.0.0")
    reduction, manifest, epoch = _construction_context(
        entries=(later, earlier),
        policies=(("z-policy", "1.0.0"), ("a-policy", "1.0.0")),
    )

    result = _accepted(_SnapshotBuilder.build(reduction, manifest, epoch))

    assert result.entries == (earlier, later)
    assert result.entries[0] is earlier
    assert result.entries[1] is later
    assert result.governance_action_references == ("action-001", "action-002")
    assert result.policy_versions == (
        ("a-policy", "1.0.0"),
        ("z-policy", "1.0.0"),
    )
    assert reduction.starting_snapshot.governance_action_references == ("action-001",)


def test_equivalent_input_order_produces_identical_candidate_and_identity() -> None:
    first_entry = _entry(producer_identity="producer-a")
    second_entry = _entry(producer_identity="producer-z")
    first_reduction, first_manifest, epoch = _construction_context(
        entries=(first_entry, second_entry),
        policies=(("a-policy", "1.0.0"), ("z-policy", "1.0.0")),
        authority_facts=("a:observer", "z:registry_authority"),
    )
    second_reduction = first_reduction._replace(
        entries=(second_entry, first_entry),
        policy_versions=tuple(reversed(first_reduction.policy_versions)),
        authority_facts=tuple(reversed(first_reduction.authority_facts)),
    )

    first = _accepted(_SnapshotBuilder.build(first_reduction, first_manifest, epoch))
    second = _accepted(_SnapshotBuilder.build(second_reduction, first_manifest, epoch))

    assert first == second
    assert first.snapshot_identity == second.snapshot_identity


def test_every_identity_participating_change_changes_candidate_identity() -> None:
    reduction, manifest, epoch = _construction_context()
    original = _accepted(_SnapshotBuilder.build(reduction, manifest, epoch))

    changed_entry = replace(reduction.entries[0], trust_standing="Experimental")
    entry_result = _accepted(
        _SnapshotBuilder.build(reduction._replace(entries=(changed_entry,)), manifest, epoch)
    )
    authority_result = _accepted(
        _SnapshotBuilder.build(
            reduction._replace(authority_facts=(*reduction.authority_facts, "reviewer:observer")),
            manifest,
            epoch,
        )
    )

    assert original.snapshot_identity != entry_result.snapshot_identity
    assert original.snapshot_identity != authority_result.snapshot_identity


@pytest.mark.parametrize(
    "invalid_reduction",
    [
        cast(_ReductionResult, object()),
        _construction_context()[0]._replace(entries=cast(tuple[RegistryEntry, ...], [])),
        _construction_context()[0]._replace(entries=(cast(RegistryEntry, object()),)),
        _construction_context()[0]._replace(governance_action_references=cast(tuple[str, ...], [])),
        _construction_context()[0]._replace(policy_versions=cast(tuple[tuple[str, str], ...], [])),
        _construction_context()[0]._replace(authority_facts=cast(tuple[str, ...], [])),
    ],
)
def test_builder_rejects_invalid_or_mutable_reduction_content(
    invalid_reduction: _ReductionResult,
) -> None:
    _, manifest, epoch = _construction_context()
    assert (
        _rejection(_SnapshotBuilder.build(invalid_reduction, manifest, epoch)).reason_code
        == "GOV_INVALID_MODEL"
    )


def test_builder_rejects_mismatched_binding_duplicate_identity_and_history() -> None:
    reduction, manifest, epoch = _construction_context()
    other_manifest = replace(manifest, manifest_identity="other-manifest")
    assert _rejection(
        _SnapshotBuilder.build(reduction, other_manifest, epoch)
    ).diagnostic_details == (("fact", "reduction_manifest_epoch_binding"),)

    duplicate = reduction._replace(entries=(reduction.entries[0], reduction.entries[0]))
    assert _rejection(_SnapshotBuilder.build(duplicate, manifest, epoch)).diagnostic_details == (
        ("fact", "duplicate_registry_entry_identity"),
    )

    duplicate_history = reduction._replace(
        governance_action_references=("action-001", "action-002", "action-002")
    )
    assert _rejection(
        _SnapshotBuilder.build(duplicate_history, manifest, epoch)
    ).diagnostic_details == (("fact", "duplicate_governance_action_identity"),)

    incomplete_history = reduction._replace(governance_action_references=("action-002",))
    assert _rejection(
        _SnapshotBuilder.build(incomplete_history, manifest, epoch)
    ).diagnostic_details == (("fact", "governance_epoch_mismatch"),)

    stale = reduction._replace(
        starting_snapshot=replace(reduction.starting_snapshot, governance_epoch=epoch)
    )
    assert _rejection(_SnapshotBuilder.build(stale, manifest, epoch)).diagnostic_details == (
        ("fact", "governance_epoch_mismatch"),
    )


@pytest.mark.parametrize(
    ("field_name", "unsupported"),
    [
        ("manifest_schema_version", "2.0.0"),
        ("identity_domain_version", "2.0.0"),
        ("canonicalization_profile_identity", "other-canonicalization"),
        ("canonicalization_profile_version", "2.0.0"),
        ("digest_profile_identity", "other-digest"),
        ("digest_profile_version", "2.0.0"),
    ],
)
def test_builder_rejects_unsupported_frozen_profiles(
    field_name: str,
    unsupported: str,
) -> None:
    reduction, manifest, epoch = _construction_context()
    if field_name == "manifest_schema_version":
        changed = replace(manifest, manifest_schema_version=unsupported)
    elif field_name == "identity_domain_version":
        changed = replace(manifest, identity_domain_version=unsupported)
    elif field_name == "canonicalization_profile_identity":
        changed = replace(manifest, canonicalization_profile_identity=unsupported)
    elif field_name == "canonicalization_profile_version":
        changed = replace(manifest, canonicalization_profile_version=unsupported)
    elif field_name == "digest_profile_identity":
        changed = replace(manifest, digest_profile_identity=unsupported)
    else:
        changed = replace(manifest, digest_profile_version=unsupported)
    changed_reduction = reduction._replace(manifest=changed)

    assert _rejection(
        _SnapshotBuilder.build(changed_reduction, changed, epoch)
    ).diagnostic_details == (("fact", "inconsistent_governance_manifest"),)


def test_builder_does_not_repeat_governance_semantic_validation() -> None:
    first = _entry(producer_identity="producer-001", owner_identity="owner-a")
    second = _entry(
        producer_identity="producer-001",
        producer_version="2.0.0",
        owner_identity="owner-b",
    )
    reduction, manifest, epoch = _construction_context(entries=(first, second))

    result = _accepted(_SnapshotBuilder.build(reduction, manifest, epoch))

    assert result.entries == (first, second)


def test_candidate_has_exact_frozen_fields_and_is_not_published_or_orchestrated() -> None:
    reduction, manifest, epoch = _construction_context()
    candidate = _accepted(_SnapshotBuilder.build(reduction, manifest, epoch))

    assert tuple(field.name for field in fields(candidate)) == (
        "snapshot_identity",
        "manifest_reference",
        "governance_epoch",
        "entries",
        "governance_action_references",
        "policy_versions",
    )
    assert candidate is not reduction.starting_snapshot
    assert reduction.starting_snapshot.manifest_reference == "manifest-001"


def test_canonical_projection_fails_closed_for_unsupported_value() -> None:
    with pytest.raises(TypeError, match="unsupported canonical snapshot value"):
        _canonical_value(object())
