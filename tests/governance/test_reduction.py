"""A03 Increment 3 immutable reducer tests governed by ADR-03 and ADR-09."""

from __future__ import annotations

from typing import cast

from epip.governance.model import (
    GovernanceAction,
    GovernanceEpoch,
    GovernanceRejection,
    RegistrySnapshot,
)
from epip.governance.reduction import _GovernanceReducer
from tests.governance.test_model import _action, _entry, _snapshot


def _reduction_action(**overrides: object) -> GovernanceAction:
    values: dict[str, object] = {
        "action_identity": "action-002",
        "action_type": "lifecycle_transitioned",
        "authority_identity": "registry-authority",
        "authority_role": "registry_authority",
        "subject_references": ("producer-001",),
        "prior_standing": "Declared",
        "resulting_standing": "Registered",
        "effective_epoch": GovernanceEpoch(2),
        "resulting_snapshot_reference": "snapshot-002",
    }
    values.update(overrides)
    return _action(**values)


def _base_snapshot(**overrides: object) -> RegistrySnapshot:
    values: dict[str, object] = {
        "entries": (_entry(lifecycle_standing="Declared", trust_standing="Untrusted"),),
    }
    values.update(overrides)
    return _snapshot(**values)


def _rejection(result: RegistrySnapshot | GovernanceRejection) -> GovernanceRejection:
    assert isinstance(result, GovernanceRejection)
    return result


def _accepted(result: RegistrySnapshot | GovernanceRejection) -> RegistrySnapshot:
    assert isinstance(result, RegistrySnapshot)
    return result


def test_reduction_is_deterministic_pure_immutable_and_append_only() -> None:
    snapshot = _base_snapshot()
    action = _reduction_action()
    before_snapshot = snapshot
    before_entry = snapshot.entries[0]
    first = _accepted(_GovernanceReducer.reduce(snapshot, action))
    second = _accepted(_GovernanceReducer.reduce(snapshot, action))
    assert first == second
    assert snapshot == before_snapshot
    assert snapshot.entries[0] is before_entry
    assert first is not snapshot
    assert first.entries[0] is not before_entry
    assert first.entries[0].lifecycle_standing == "Registered"
    assert first.entries[0].governance_provenance == ("action-001", "action-002")
    assert first.governance_action_references == ("action-001", "action-002")
    assert first.governance_epoch == GovernanceEpoch(2)
    assert first.snapshot_identity == "snapshot-002"


def test_reduction_preserves_canonical_entry_and_policy_ordering() -> None:
    later = _entry(
        producer_identity="producer-z",
        producer_version="2.0.0",
        lifecycle_standing="Declared",
    )
    earlier = _entry(
        producer_identity="producer-a",
        producer_version="1.0.0",
        lifecycle_standing="Declared",
    )
    snapshot = _base_snapshot(
        entries=(later, earlier),
        policy_versions=(("z-policy", "1.0.0"), ("a-policy", "1.0.0")),
    )
    action = _reduction_action(
        subject_references=("producer-z",),
        policy_versions=(("m-policy", "1.0.0"),),
    )
    result = _accepted(_GovernanceReducer.reduce(snapshot, action))
    assert tuple(entry.producer_identity for entry in result.entries) == (
        "producer-a",
        "producer-z",
    )
    assert result.policy_versions == (
        ("a-policy", "1.0.0"),
        ("m-policy", "1.0.0"),
        ("z-policy", "1.0.0"),
    )


def test_reducer_rejects_invalid_models_authority_and_preconditions() -> None:
    snapshot = _base_snapshot()
    action = _reduction_action()
    assert (
        _rejection(_GovernanceReducer.reduce(cast(RegistrySnapshot, object()), action)).reason_code
        == "GOV_INVALID_MODEL"
    )
    assert (
        _rejection(
            _GovernanceReducer.reduce(snapshot, cast(GovernanceAction, object()))
        ).reason_code
        == "GOV_INVALID_MODEL"
    )
    assert (
        _rejection(
            _GovernanceReducer.reduce(snapshot, _reduction_action(authority_role="producer_owner"))
        ).reason_code
        == "GOV_UNAUTHORIZED_AUTHORITY"
    )
    assert (
        _rejection(
            _GovernanceReducer.reduce(
                snapshot, _reduction_action(resulting_snapshot_reference=None)
            )
        ).reason_code
        == "GOV_MISSING_MANDATORY_FACT"
    )
    assert _rejection(
        _GovernanceReducer.reduce(snapshot, _reduction_action(action_identity="action-001"))
    ).diagnostic_details == (("fact", "governance_action_reference"),)
    assert _rejection(
        _GovernanceReducer.reduce(snapshot, _reduction_action(effective_epoch=GovernanceEpoch(1)))
    ).diagnostic_details == (("fact", "governance_epoch_order"),)


def test_reducer_fails_closed_for_unknown_or_publication_action() -> None:
    snapshot = _base_snapshot()
    unknown = _reduction_action(action_type="unknown")
    assert _rejection(_GovernanceReducer.reduce(snapshot, unknown)).reason_code == (
        "GOV_UNKNOWN_ACTION"
    )
    publication = _reduction_action(action_type="snapshot_published")
    assert _rejection(_GovernanceReducer.reduce(snapshot, publication)).reason_code == (
        "GOV_UNKNOWN_ACTION"
    )


def test_reducer_rejects_missing_or_ambiguous_subject_entry() -> None:
    snapshot = _base_snapshot()
    missing = _reduction_action(subject_references=("unknown-producer",))
    assert _rejection(_GovernanceReducer.reduce(snapshot, missing)).reason_code == (
        "GOV_INVALID_IDENTITY"
    )
    duplicate = _entry(
        producer_identity="producer-001",
        producer_version="2.0.0",
        lifecycle_standing="Declared",
        trust_standing="Untrusted",
    )
    ambiguous_snapshot = _base_snapshot(entries=(*snapshot.entries, duplicate))
    assert _rejection(
        _GovernanceReducer.reduce(ambiguous_snapshot, _reduction_action())
    ).reason_code == ("GOV_INVALID_IDENTITY")


def test_reducer_rejects_illegal_lifecycle_and_prior_standing() -> None:
    snapshot = _base_snapshot()
    wrong_prior = _reduction_action(prior_standing="Enabled")
    assert _rejection(_GovernanceReducer.reduce(snapshot, wrong_prior)).reason_code == (
        "GOV_ILLEGAL_LIFECYCLE_TRANSITION"
    )
    illegal = _reduction_action(resulting_standing="Enabled")
    assert _rejection(_GovernanceReducer.reduce(snapshot, illegal)).reason_code == (
        "GOV_ILLEGAL_LIFECYCLE_TRANSITION"
    )


def test_reducer_accepts_activation_and_governed_revocation_lifecycle_actions() -> None:
    certified = _base_snapshot(
        entries=(
            _entry(
                lifecycle_standing="Certified",
                trust_standing="Trusted",
            ),
        )
    )
    activation = _reduction_action(
        action_type="activated",
        prior_standing="Certified",
        resulting_standing="Enabled",
    )
    assert (
        _accepted(_GovernanceReducer.reduce(certified, activation)).entries[0].lifecycle_standing
        == "Enabled"
    )
    enabled = _base_snapshot(entries=(_entry(lifecycle_standing="Enabled"),))
    disabled = _reduction_action(
        action_type="disabled",
        prior_standing="Enabled",
        resulting_standing="Disabled",
    )
    assert (
        _accepted(_GovernanceReducer.reduce(enabled, disabled)).entries[0].lifecycle_standing
        == "Disabled"
    )
    deprecated = _base_snapshot(entries=(_entry(lifecycle_standing="Deprecated"),))
    retired = _reduction_action(
        action_type="retired",
        prior_standing="Deprecated",
        resulting_standing="Retired",
    )
    assert (
        _accepted(_GovernanceReducer.reduce(deprecated, retired)).entries[0].lifecycle_standing
        == "Retired"
    )


def test_reducer_propagates_revocation_validator_failure() -> None:
    snapshot = _base_snapshot(entries=(_entry(lifecycle_standing="Enabled"),))
    action = _reduction_action(
        action_type="disabled",
        authority_identity="wrong",
        authority_role="security_authority",
        prior_standing="Enabled",
        resulting_standing="Disabled",
    )
    assert _rejection(_GovernanceReducer.reduce(snapshot, action)).reason_code == (
        "GOV_UNAUTHORIZED_AUTHORITY"
    )


def test_reducer_accepts_trust_and_trust_revocation_actions() -> None:
    snapshot = _base_snapshot()
    granted = _reduction_action(
        action_type="trust_granted",
        authority_identity="security-authority",
        authority_role="security_authority",
        subject_references=("producer-001", "capability-001"),
        prior_standing="Untrusted",
        resulting_standing="Trusted",
    )
    trusted = _accepted(_GovernanceReducer.reduce(snapshot, granted))
    assert trusted.entries[0].trust_standing == "Trusted"
    revoked = _reduction_action(
        action_identity="action-003",
        action_type="trust_revoked",
        authority_identity="security-authority",
        authority_role="security_authority",
        subject_references=("producer-001", "capability-001"),
        prior_standing="Trusted",
        resulting_standing="Revoked",
        effective_epoch=GovernanceEpoch(3),
        resulting_snapshot_reference="snapshot-003",
    )
    result = _accepted(_GovernanceReducer.reduce(trusted, revoked))
    assert result.entries[0].trust_standing == "Revoked"


def test_reducer_rejects_invalid_trust_prior_and_validator_failure() -> None:
    snapshot = _base_snapshot()
    wrong_prior = _reduction_action(
        action_type="trust_granted",
        authority_role="security_authority",
        subject_references=("producer-001", "capability-001"),
        prior_standing="Trusted",
        resulting_standing="Trusted",
    )
    assert _rejection(_GovernanceReducer.reduce(snapshot, wrong_prior)).reason_code == (
        "GOV_INVALID_TRUST_TRANSITION"
    )
    invalid_scope = _reduction_action(
        action_type="trust_granted",
        authority_role="security_authority",
        prior_standing="Untrusted",
        resulting_standing="Trusted",
    )
    assert _rejection(_GovernanceReducer.reduce(snapshot, invalid_scope)).reason_code == (
        "GOV_INVALID_TRUST_SCOPE"
    )
    missing_subject = _reduction_action(
        action_type="trust_granted",
        authority_role="security_authority",
        subject_references=("unknown-producer", "capability-001"),
        prior_standing="Untrusted",
        resulting_standing="Trusted",
    )
    assert _rejection(_GovernanceReducer.reduce(snapshot, missing_subject)).reason_code == (
        "GOV_INVALID_IDENTITY"
    )


def test_reducer_rejects_duplicate_ownership() -> None:
    snapshot = _base_snapshot()
    action = _reduction_action(
        action_type="admission_requested",
        authority_identity="different-owner",
        authority_role="producer_owner",
        prior_standing=None,
        resulting_standing="Declared",
    )
    assert _rejection(_GovernanceReducer.reduce(snapshot, action)).reason_code == (
        "GOV_DUPLICATE_OWNERSHIP"
    )


def test_reducer_accepts_audit_only_fact_without_changing_entries() -> None:
    snapshot = _base_snapshot()
    action = _reduction_action(
        action_type="admission_requested",
        authority_identity="owner-001",
        authority_role="producer_owner",
        prior_standing=None,
        resulting_standing="Declared",
    )
    result = _accepted(_GovernanceReducer.reduce(snapshot, action))
    assert result.entries == snapshot.entries
    assert result.entries[0] is snapshot.entries[0]
    confirmation = _reduction_action(
        action_identity="action-003",
        action_type="architectural_conformity_confirmed",
        authority_identity="architecture-authority",
        authority_role="architectural_authority",
        effective_epoch=GovernanceEpoch(3),
        resulting_snapshot_reference="snapshot-003",
    )
    assert isinstance(_GovernanceReducer.reduce(result, confirmation), RegistrySnapshot)


def test_reducer_rejects_duplicate_or_missing_certification_fact() -> None:
    snapshot = _base_snapshot()
    duplicate = _reduction_action(
        action_type="certification_issued",
        authority_role="certification_authority",
        subject_references=("certification-001",),
    )
    rejection = _rejection(_GovernanceReducer.reduce(snapshot, duplicate))
    assert rejection.reason_code == "GOV_INVALID_CERTIFICATION_STATE"
    assert rejection.diagnostic_details == (("fact", "duplicate_certification"),)
    missing = _reduction_action(
        action_type="certification_issued",
        authority_role="certification_authority",
        subject_references=("new-certification",),
    )
    assert _rejection(_GovernanceReducer.reduce(snapshot, missing)).diagnostic_details == (
        ("fact", "certification_record"),
    )


def test_reducer_rejects_missing_compatibility_fact() -> None:
    action = _reduction_action(
        action_type="compatibility_approved",
        authority_role="compatibility_authority",
        subject_references=("compatibility-new",),
    )
    assert _rejection(_GovernanceReducer.reduce(_base_snapshot(), action)).diagnostic_details == (
        ("fact", "compatibility_decision"),
    )
