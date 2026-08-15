"""A03-V2-E07 complete public governance lifecycle verification."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

from epip.governance.model import (
    GovernanceAction,
    GovernanceEpoch,
    GovernanceManifest,
    GovernanceRejection,
    RegistryEntry,
    RegistrySnapshot,
)
from epip.governance.reduction import _GovernanceReducer, _ReductionResult
from epip.governance.registry import GovernanceRegistry
from epip.governance.snapshot import _SnapshotBuilder
from epip.governance.store import GovernanceStore
from tests.governance.test_model import _entry
from tests.governance.test_reduction import (
    _base_snapshot,
    _certification_operation,
    _compatibility_operation,
    _operation_manifest,
    _reduction_action,
    _structural_admission_operation,
)


def _accepted(result: RegistrySnapshot | GovernanceRejection) -> RegistrySnapshot:
    assert isinstance(result, RegistrySnapshot)
    return result


def _entry_by_identity(snapshot: RegistrySnapshot, identity: str) -> RegistryEntry:
    matches = tuple(entry for entry in snapshot.entries if entry.producer_identity == identity)
    assert len(matches) == 1
    return matches[0]


def _advance_certification_operation(
    snapshot: RegistrySnapshot,
    *,
    sequence: int,
    action_type: str,
    verdict: str,
    record_identity: str,
    relationship: str | None,
) -> tuple[GovernanceAction, GovernanceManifest]:
    action, manifest = _certification_operation(
        snapshot,
        action_type=action_type,
        verdict=verdict,
        record_identity=record_identity,
        relationship=relationship,
    )
    epoch = GovernanceEpoch(sequence)
    advanced_action = replace(
        action,
        action_identity=f"action-{sequence:03d}",
        effective_epoch=epoch,
    )
    advanced_record = replace(manifest.certification_records[0], effective_epoch=epoch)
    return advanced_action, replace(
        manifest,
        manifest_identity=f"manifest-{sequence:03d}",
        governance_epoch=epoch,
        actions=(advanced_action,),
        certification_records=(advanced_record,),
    )


def _advance_compatibility_operation(
    *,
    sequence: int,
    action_type: str,
    decision_identity: str,
    revocation_reference: str | None = None,
) -> tuple[GovernanceAction, GovernanceManifest]:
    action, manifest = _compatibility_operation(
        action_type=action_type,
        decision_identity=decision_identity,
        revocation_reference=revocation_reference,
    )
    epoch = GovernanceEpoch(sequence)
    advanced_action = replace(
        action,
        action_identity=f"action-{sequence:03d}",
        effective_epoch=epoch,
    )
    advanced_decision = replace(manifest.compatibility_decisions[0], effective_epoch=epoch)
    return advanced_action, replace(
        manifest,
        manifest_identity=f"manifest-{sequence:03d}",
        governance_epoch=epoch,
        actions=(advanced_action,),
        compatibility_decisions=(advanced_decision,),
    )


def test_public_admission_creates_authoritative_entry_once_and_rejects_replay() -> None:
    starting, action, manifest = _structural_admission_operation()
    registry = GovernanceRegistry(starting)
    proposed = manifest.proposed_registry_entries[0]

    admitted = _accepted(registry.apply(action, manifest, action.effective_epoch))

    assert registry.current_snapshot is admitted
    assert admitted.entries == (proposed,)
    assert admitted.entries[0] is proposed
    assert admitted.governance_action_references == (
        *starting.governance_action_references,
        action.action_identity,
    )
    assert starting.entries == ()

    rejected = registry.apply(action, manifest, action.effective_epoch)
    assert isinstance(rejected, GovernanceRejection)
    assert registry.current_snapshot is admitted
    assert admitted.entries == (proposed,)


def test_public_certification_lifecycle_preserves_append_only_history() -> None:
    starting = _base_snapshot(
        entries=(_entry(lifecycle_standing="Registered", certification_records=()),)
    )
    registry = GovernanceRegistry(starting)

    issued_action, issued_manifest = _advance_certification_operation(
        starting,
        sequence=2,
        action_type="certification_issued",
        verdict="passed",
        record_identity="certification-issuance",
        relationship=None,
    )
    issued = _accepted(
        registry.apply(issued_action, issued_manifest, issued_action.effective_epoch)
    )
    issued_record = _entry_by_identity(issued, "producer-001").certification_records[0]

    suspended_action, suspended_manifest = _advance_certification_operation(
        issued,
        sequence=3,
        action_type="certification_suspended",
        verdict="suspended",
        record_identity="certification-suspension",
        relationship=issued_record.record_identity,
    )
    suspended = _accepted(
        registry.apply(
            suspended_action,
            suspended_manifest,
            suspended_action.effective_epoch,
        )
    )

    revoked_action, revoked_manifest = _advance_certification_operation(
        suspended,
        sequence=4,
        action_type="certification_revoked",
        verdict="revoked",
        record_identity="certification-revocation",
        relationship="certification-suspension",
    )
    revoked = _accepted(
        registry.apply(revoked_action, revoked_manifest, revoked_action.effective_epoch)
    )

    records = _entry_by_identity(revoked, "producer-001").certification_records
    assert tuple(record.verdict for record in records) == ("passed", "suspended", "revoked")
    assert records[0] is issued_record
    assert len({record.record_identity for record in records}) == 3
    assert revoked.governance_action_references == (
        "action-001",
        "action-002",
        "action-003",
        "action-004",
    )
    assert starting.entries[0].certification_records == ()


def test_public_compatibility_lifecycle_preserves_direction_and_history() -> None:
    producer = _entry(compatibility_decisions=())
    consumer = _entry(producer_identity="consumer-001", compatibility_decisions=())
    starting = _base_snapshot(entries=(producer, consumer))
    registry = GovernanceRegistry(starting)

    approval_action, approval_manifest = _advance_compatibility_operation(
        sequence=2,
        action_type="compatibility_approved",
        decision_identity="compatibility-approval",
    )
    approved = _accepted(
        registry.apply(approval_action, approval_manifest, approval_action.effective_epoch)
    )
    approved_decision = _entry_by_identity(approved, "producer-001").compatibility_decisions[0]

    revocation_action, revocation_manifest = _advance_compatibility_operation(
        sequence=3,
        action_type="compatibility_revoked",
        decision_identity="compatibility-revocation",
        revocation_reference=approved_decision.decision_identity,
    )
    revoked = _accepted(
        registry.apply(
            revocation_action,
            revocation_manifest,
            revocation_action.effective_epoch,
        )
    )

    decisions = _entry_by_identity(revoked, "producer-001").compatibility_decisions
    assert decisions[0] is approved_decision
    assert decisions[1].revocation_reference == approved_decision.decision_identity
    directed_facts = tuple(
        (decision.source_reference, decision.target_reference, decision.direction)
        for decision in decisions
    )
    assert directed_facts == (directed_facts[0], directed_facts[0])
    assert starting.entries[0].compatibility_decisions == ()


def test_public_lifecycle_and_trust_transitions_preserve_authority_separation() -> None:
    selected = _entry(
        lifecycle_standing="Declared",
        trust_standing="Untrusted",
        certification_records=(),
        compatibility_decisions=(),
    )
    unaffected = _entry(
        producer_identity="producer-other",
        lifecycle_standing="Declared",
        trust_standing="Untrusted",
    )
    starting = _base_snapshot(entries=(selected, unaffected))
    registry = GovernanceRegistry(starting)

    lifecycle_action = _reduction_action()
    lifecycle_manifest = _operation_manifest(lifecycle_action)
    registered = _accepted(
        registry.apply(
            lifecycle_action,
            lifecycle_manifest,
            lifecycle_action.effective_epoch,
        )
    )
    registered_entry = _entry_by_identity(registered, "producer-001")
    assert registered_entry.lifecycle_standing == "Registered"
    assert registered_entry.trust_standing == "Untrusted"

    trust_epoch = GovernanceEpoch(3)
    trust_action = _reduction_action(
        action_identity="action-003",
        action_type="trust_granted",
        authority_identity="security-authority",
        authority_role="security_authority",
        subject_references=("producer-001", "capability-001"),
        prior_standing="Untrusted",
        resulting_standing="Trusted",
        effective_epoch=trust_epoch,
    )
    trust_manifest = _operation_manifest(
        trust_action,
        manifest_identity="manifest-003",
    )
    trusted = _accepted(registry.apply(trust_action, trust_manifest, trust_epoch))
    trusted_entry = _entry_by_identity(trusted, "producer-001")

    assert trusted_entry.lifecycle_standing == "Registered"
    assert trusted_entry.trust_standing == "Trusted"
    assert _entry_by_identity(trusted, "producer-other") is unaffected
    assert lifecycle_action.authority_role == "registry_authority"
    assert trust_action.authority_role == "security_authority"
    assert lifecycle_action.authority_identity != trust_action.authority_identity


def test_public_rejection_is_atomic_deterministic_and_appends_nothing() -> None:
    starting = _base_snapshot()
    action = _reduction_action(prior_standing="Enabled")
    manifest = _operation_manifest(action)
    first_registry = GovernanceRegistry(starting)
    second_registry = GovernanceRegistry(starting)

    first = first_registry.apply(action, manifest, action.effective_epoch)
    second = second_registry.apply(action, manifest, action.effective_epoch)

    assert isinstance(first, GovernanceRejection)
    assert first == second
    assert first_registry.current_snapshot is starting
    assert second_registry.current_snapshot is starting
    assert starting.governance_action_references == ("action-001",)


def test_public_workflow_has_no_intermediate_authoritative_state() -> None:
    starting = _base_snapshot()
    registry = GovernanceRegistry(starting)
    action = _reduction_action()
    manifest = _operation_manifest(action)
    trace: list[str] = []
    reduction_result: _ReductionResult | None = None
    candidate: RegistrySnapshot | None = None
    original_reduce = _GovernanceReducer.reduce
    original_build = _SnapshotBuilder.build
    original_publish = GovernanceStore.replace_snapshot

    def reduce_once(
        snapshot: RegistrySnapshot,
        selected_action: GovernanceAction,
        selected_manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> _ReductionResult | GovernanceRejection:
        nonlocal reduction_result
        trace.append("reduce")
        assert registry.current_snapshot is starting
        outcome = original_reduce(snapshot, selected_action, selected_manifest, epoch)
        assert isinstance(outcome, _ReductionResult)
        reduction_result = outcome
        return outcome

    def build_once(
        reduction: _ReductionResult,
        selected_manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> RegistrySnapshot | GovernanceRejection:
        nonlocal candidate
        trace.append("build")
        assert reduction is reduction_result
        assert registry.current_snapshot is starting
        outcome = original_build(reduction, selected_manifest, epoch)
        assert isinstance(outcome, RegistrySnapshot)
        candidate = outcome
        return outcome

    def publish_once(
        store: GovernanceStore,
        selected_candidate: RegistrySnapshot,
    ) -> RegistrySnapshot | GovernanceRejection:
        trace.append("publish")
        assert selected_candidate is candidate
        assert registry.current_snapshot is starting
        return original_publish(store, selected_candidate)

    with (
        patch.object(_GovernanceReducer, "reduce", side_effect=reduce_once),
        patch.object(_SnapshotBuilder, "build", side_effect=build_once),
        patch.object(
            GovernanceStore,
            "replace_snapshot",
            autospec=True,
            side_effect=publish_once,
        ),
    ):
        published = _accepted(registry.apply(action, manifest, action.effective_epoch))

    assert trace == ["reduce", "build", "publish"]
    assert published is candidate
    assert registry.current_snapshot is published


def test_identical_public_lifecycles_produce_identical_terminal_identity() -> None:
    starting, action, manifest = _structural_admission_operation()

    first = _accepted(GovernanceRegistry(starting).apply(action, manifest, action.effective_epoch))
    second = _accepted(GovernanceRegistry(starting).apply(action, manifest, action.effective_epoch))

    assert first == second
    assert first.snapshot_identity == second.snapshot_identity
