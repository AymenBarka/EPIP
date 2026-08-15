"""A03-V2-E02 manifest-aware immutable reduction tests."""

from __future__ import annotations

from dataclasses import replace
from typing import cast
from unittest.mock import patch

import pytest

from epip.governance.model import (
    GovernanceAction,
    GovernanceEpoch,
    GovernanceManifest,
    GovernanceRejection,
    RegistrySnapshot,
)
from epip.governance.reduction import _GovernanceReducer, _ReductionResult
from epip.governance.validation import (
    _AdmissionValidator,
    _AuthorityValidator,
    _ValidationAcceptance,
)
from tests.governance.test_model import (
    _action,
    _admission,
    _certification,
    _compatibility,
    _entry,
    _fact_reference,
    _manifest,
    _profile,
    _snapshot,
)
from tests.producer.test_contract import _contract


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


def _operation_manifest(action: GovernanceAction, **overrides: object) -> GovernanceManifest:
    values: dict[str, object] = {
        "manifest_identity": "manifest-002",
        "governance_epoch": action.effective_epoch,
        "actions": (action,),
        "policy_versions": action.policy_versions,
        "authority_facts": (f"{action.authority_identity}:{action.authority_role}",),
    }
    values.update(overrides)
    return _manifest(**values)


def _reduce(
    snapshot: RegistrySnapshot,
    action: GovernanceAction,
    manifest: GovernanceManifest | None = None,
) -> _ReductionResult | GovernanceRejection:
    operation = manifest if manifest is not None else _operation_manifest(action)
    return _GovernanceReducer.reduce(snapshot, action, operation, action.effective_epoch)


def _accepted(result: _ReductionResult | GovernanceRejection) -> _ReductionResult:
    assert isinstance(result, _ReductionResult)
    return result


def _rejection(result: object) -> GovernanceRejection:
    assert isinstance(result, GovernanceRejection)
    return result


def _certification_operation(
    snapshot: RegistrySnapshot,
    *,
    action_type: str = "certification_issued",
    verdict: str = "passed",
    record_identity: str = "certification-new",
    relationship: str | None = None,
) -> tuple[GovernanceAction, GovernanceManifest]:
    epoch = GovernanceEpoch(2)
    profile = _profile()
    record = _certification(
        record_identity=record_identity,
        verdict=verdict,
        effective_epoch=epoch,
        status_relationship_reference=relationship,
    )
    action = _reduction_action(
        action_type=action_type,
        authority_identity="certification-authority",
        authority_role="certification_authority",
        subject_references=(record.record_identity,),
    )
    manifest = _operation_manifest(
        action,
        certification_profiles=(profile,),
        certification_records=(record,),
        fact_references=(
            _fact_reference(
                identity_domain="certification",
                artifact_identity=profile.profile_identity,
                artifact_version=profile.profile_version,
                fact_type="certification_profile",
                relationship_role="certification_profile_input",
            ),
            _fact_reference(
                identity_domain="certification",
                artifact_identity=record.record_identity,
                artifact_version=record.certification_suite_version,
                fact_type="certification_record",
                relationship_role="certification_record_input",
            ),
        ),
    )
    assert snapshot.entries
    return action, manifest


def _compatibility_operation(
    *,
    action_type: str = "compatibility_approved",
    decision_identity: str = "compatibility-new",
    revocation_reference: str | None = None,
) -> tuple[GovernanceAction, GovernanceManifest]:
    epoch = GovernanceEpoch(2)
    decision = _compatibility(
        decision_identity=decision_identity,
        effective_epoch=epoch,
        revocation_reference=revocation_reference,
    )
    action = _reduction_action(
        action_type=action_type,
        authority_identity="compatibility-authority",
        authority_role="compatibility_authority",
        subject_references=(decision.decision_identity,),
    )
    manifest = _operation_manifest(
        action,
        compatibility_decisions=(decision,),
        fact_references=(
            _fact_reference(
                identity_domain="validation",
                artifact_identity=decision.decision_identity,
                artifact_version=decision.policy_version,
                fact_type="compatibility_decision",
                relationship_role="compatibility_input",
            ),
        ),
    )
    return action, manifest


def _structural_admission_operation() -> tuple[
    RegistrySnapshot,
    GovernanceAction,
    GovernanceManifest,
]:
    epoch = GovernanceEpoch(2)
    request = _admission(
        request_identity="request-new",
        producer_identity="producer-new",
    )
    contract = _contract(
        producer_identity=request.producer_identity,
        producer_version=request.producer_version,
        owner=request.owner_identity,
        contract_version=request.producer_contract_version,
        implementation_identity=request.implementation_identity,
    )
    proposed = _entry(
        producer_identity=request.producer_identity,
        producer_version=request.producer_version,
        owner_identity=request.owner_identity,
        producer_contract_version=request.producer_contract_version,
        implementation_identity=request.implementation_identity,
        capability_references=request.capability_references,
        trust_standing="Untrusted",
        certification_records=(),
        compatibility_decisions=(),
        lifecycle_standing="Registered",
        governance_provenance=("admission-evidence",),
    )
    architectural_fact = "architecture-001:architectural_authority"
    action = _reduction_action(
        action_type="structural_admission_approved",
        authority_identity="registry-authority",
        authority_role="registry_authority",
        subject_references=(proposed.producer_identity,),
        prior_standing=None,
        resulting_standing="Registered",
        effective_epoch=epoch,
        approval_references=(architectural_fact,),
        separation_attestations=("admission-authority-separation",),
    )
    manifest = _operation_manifest(
        action,
        admission_requests=(request,),
        producer_contracts=(contract,),
        proposed_registry_entries=(proposed,),
        fact_references=(
            _fact_reference(
                artifact_identity=request.request_identity,
                artifact_version=request.producer_version,
                fact_type="admission_request",
                relationship_role="admission_input",
            ),
            _fact_reference(
                artifact_identity=contract.producer_identity,
                artifact_version=contract.producer_version,
                fact_type="producer_contract",
                relationship_role="producer_contract_input",
            ),
            _fact_reference(
                artifact_identity=proposed.producer_identity,
                artifact_version=proposed.producer_version,
                fact_type="registry_entry",
                relationship_role="proposed_entry",
            ),
        ),
        authority_facts=(
            "registry-authority:registry_authority",
            f"{request.owner_identity}:producer_owner",
            architectural_fact,
        ),
    )
    return _base_snapshot(entries=()), action, manifest


def test_complete_input_contract_is_mandatory_and_bound() -> None:
    snapshot = _base_snapshot()
    action = _reduction_action()
    manifest = _operation_manifest(action)
    assert (
        _rejection(
            _GovernanceReducer.reduce(
                cast(RegistrySnapshot, object()), action, manifest, action.effective_epoch
            )
        ).reason_code
        == "GOV_INVALID_MODEL"
    )
    other = replace(action, action_identity="other-action")
    assert _rejection(
        _GovernanceReducer.reduce(
            snapshot, action, _operation_manifest(other), action.effective_epoch
        )
    ).diagnostic_details == (("fact", "complete_reducer_input_binding"),)


def test_supported_action_handling_is_deterministic_and_fail_closed() -> None:
    action = _reduction_action(action_type="unknown_action")
    first = _reduce(_base_snapshot(), action)
    second = _reduce(_base_snapshot(), action)
    assert first == second
    assert _rejection(first).reason_code == "GOV_UNKNOWN_ACTION"


def test_validator_selection_is_complete_and_deterministic() -> None:
    certification = tuple(
        validator.__qualname__
        for validator in _GovernanceReducer._applicable_validators("certification_revoked")
    )
    assert certification == (
        "_AuthorityValidator.validate_context",
        "_CertificationValidator.validate_context",
        "_RevocationValidator.validate_context",
    )
    assert certification == tuple(
        validator.__qualname__
        for validator in _GovernanceReducer._applicable_validators("certification_revoked")
    )
    structural_admission = tuple(
        validator.__qualname__
        for validator in _GovernanceReducer._applicable_validators("structural_admission_approved")
    )
    assert structural_admission == (
        "_AuthorityValidator.validate_context",
        "_AdmissionValidator.validate_context",
    )


def test_reduction_requires_explicit_complete_acceptance() -> None:
    snapshot = _base_snapshot()
    action = _reduction_action()
    manifest = _operation_manifest(action)
    with patch.object(_AuthorityValidator, "validate_context", return_value=None):
        result = _GovernanceReducer.reduce(snapshot, action, manifest, action.effective_epoch)
    assert _rejection(result).diagnostic_details == (("fact", "validator_acceptance_completion"),)

    reduction_failure = GovernanceRejection("GOV_INVALID_MODEL", ("reduction",))
    with patch.object(_GovernanceReducer, "_reduce_entries", return_value=reduction_failure):
        result = _GovernanceReducer.reduce(snapshot, action, manifest, action.effective_epoch)
    assert result is reduction_failure


def test_reduction_result_is_immutable_deterministic_and_append_only() -> None:
    snapshot = _base_snapshot()
    action = _reduction_action()
    manifest = _operation_manifest(action)
    first = _accepted(_GovernanceReducer.reduce(snapshot, action, manifest, action.effective_epoch))
    second = _accepted(
        _GovernanceReducer.reduce(snapshot, action, manifest, action.effective_epoch)
    )
    assert first == second
    assert first.starting_snapshot is snapshot
    assert first.entries[0].lifecycle_standing == "Registered"
    assert first.governance_action_references == ("action-001", "action-002")
    assert first.entries[0].governance_provenance == ("action-001", "action-002")
    with pytest.raises(AttributeError):
        first.entries = ()  # type: ignore[misc]


def test_admission_creates_only_the_selected_immutable_entry() -> None:
    snapshot, action, manifest = _structural_admission_operation()
    proposed = manifest.proposed_registry_entries[0]
    result = _accepted(_reduce(snapshot, action, manifest))
    assert result.entries == (proposed,)
    assert result.entries[0] is proposed
    assert tuple(item.validator_identity for item in result.validation_acceptances) == (
        "authority",
        "admission",
    )


def test_structural_admission_requires_explicit_admission_acceptance() -> None:
    snapshot, action, manifest = _structural_admission_operation()
    with patch.object(_AdmissionValidator, "validate_context", return_value=None):
        authority_only = _GovernanceReducer.reduce(
            snapshot,
            action,
            manifest,
            action.effective_epoch,
        )
    assert _rejection(authority_only).diagnostic_details == (
        ("fact", "validator_acceptance_completion"),
    )
    assert snapshot.entries == ()

    rejection = GovernanceRejection("GOV_INCOMPLETE_DECLARATION", (action.action_identity,))
    with patch.object(_AdmissionValidator, "validate_context", return_value=rejection):
        first = _GovernanceReducer.reduce(snapshot, action, manifest, action.effective_epoch)
    with patch.object(_AdmissionValidator, "validate_context", return_value=rejection):
        second = _GovernanceReducer.reduce(snapshot, action, manifest, action.effective_epoch)
    assert first is rejection
    assert second is rejection
    assert snapshot.entries == ()


def test_reducer_consumes_without_recreating_admission_acceptance() -> None:
    snapshot, action, manifest = _structural_admission_operation()
    admission = _ValidationAcceptance(
        "admission", snapshot, action, manifest, action.effective_epoch
    )
    with patch.object(
        _AdmissionValidator,
        "validate_context",
        return_value=admission,
    ) as validator:
        result = _accepted(
            _GovernanceReducer.reduce(snapshot, action, manifest, action.effective_epoch)
        )
    validator.assert_called_once_with(snapshot, action, manifest, action.effective_epoch)
    assert result.validation_acceptances[1] is admission

    wrong_identity = _ValidationAcceptance(
        "authority",
        snapshot,
        action,
        manifest,
        action.effective_epoch,
    )
    with patch.object(
        _AdmissionValidator,
        "validate_context",
        return_value=wrong_identity,
    ):
        rejected = _GovernanceReducer.reduce(
            snapshot,
            action,
            manifest,
            action.effective_epoch,
        )
    assert _rejection(rejected).diagnostic_details == (("fact", "validator_input_binding"),)


def test_certification_issuance_appends_selected_fact_once() -> None:
    snapshot = _base_snapshot(
        entries=(_entry(lifecycle_standing="Registered", certification_records=()),)
    )
    action, manifest = _certification_operation(snapshot)
    result = _accepted(_reduce(snapshot, action, manifest))
    assert tuple(record.record_identity for record in result.entries[0].certification_records) == (
        "certification-new",
    )
    assert snapshot.entries[0].certification_records == ()


@pytest.mark.parametrize(
    ("action_type", "verdict", "identity"),
    [
        ("certification_suspended", "suspended", "certification-suspension"),
        ("certification_revoked", "revoked", "certification-revocation"),
    ],
)
def test_certification_status_changes_preserve_history(
    action_type: str,
    verdict: str,
    identity: str,
) -> None:
    prior = _certification()
    snapshot = _base_snapshot(
        entries=(_entry(lifecycle_standing="Registered", certification_records=(prior,)),)
    )
    action, manifest = _certification_operation(
        snapshot,
        action_type=action_type,
        verdict=verdict,
        record_identity=identity,
        relationship=prior.record_identity,
    )
    result = _accepted(_reduce(snapshot, action, manifest))
    assert result.entries[0].certification_records[0] is prior
    assert tuple(record.verdict for record in result.entries[0].certification_records) == (
        "passed",
        verdict,
    )


def test_compatibility_approval_and_revocation_preserve_history() -> None:
    producer = _entry(compatibility_decisions=())
    consumer = _entry(producer_identity="consumer-001", compatibility_decisions=())
    snapshot = _base_snapshot(entries=(producer, consumer))
    action, manifest = _compatibility_operation()
    approved = _accepted(_reduce(snapshot, action, manifest))
    prior = approved.entries[1].compatibility_decisions[0]

    revoked_snapshot = replace(
        snapshot,
        entries=approved.entries,
        governance_epoch=GovernanceEpoch(2),
        governance_action_references=approved.governance_action_references,
    )
    revoked_action, revoked_manifest = _compatibility_operation(
        action_type="compatibility_revoked",
        decision_identity="compatibility-revocation",
        revocation_reference=prior.decision_identity,
    )
    revoked_action = replace(
        revoked_action,
        action_identity="action-003",
        effective_epoch=GovernanceEpoch(3),
    )
    revoked_manifest = replace(
        revoked_manifest,
        governance_epoch=GovernanceEpoch(3),
        actions=(revoked_action,),
        compatibility_decisions=(
            replace(
                revoked_manifest.compatibility_decisions[0], effective_epoch=GovernanceEpoch(3)
            ),
        ),
    )
    result = _accepted(
        _GovernanceReducer.reduce(
            revoked_snapshot,
            revoked_action,
            revoked_manifest,
            GovernanceEpoch(3),
        )
    )
    assert result.entries[1].compatibility_decisions[0] is prior
    assert len(result.entries[1].compatibility_decisions) == 2


def test_lifecycle_and_trust_transform_only_selected_standing() -> None:
    other = _entry(producer_identity="producer-other", lifecycle_standing="Declared")
    snapshot = _base_snapshot(entries=(*_base_snapshot().entries, other))
    lifecycle = _accepted(_reduce(snapshot, _reduction_action()))
    assert lifecycle.entries[1] is other

    trust_action = _reduction_action(
        action_type="trust_granted",
        authority_identity="security-authority",
        authority_role="security_authority",
        subject_references=("producer-001", "capability-001"),
        prior_standing="Untrusted",
        resulting_standing="Trusted",
    )
    trusted = _accepted(_reduce(snapshot, trust_action))
    assert trusted.entries[0].trust_standing == "Trusted"
    assert trusted.entries[0].lifecycle_standing == "Declared"
    assert trusted.entries[1] is other


def test_unrelated_manifest_facts_are_rejected_before_reduction() -> None:
    snapshot = _base_snapshot(
        entries=(_entry(lifecycle_standing="Registered", certification_records=()),)
    )
    action, manifest = _certification_operation(snapshot)
    unrelated = _entry(producer_identity="unrelated")
    manifest = replace(
        manifest,
        proposed_registry_entries=(unrelated,),
        fact_references=(
            *manifest.fact_references,
            _fact_reference(
                artifact_identity=unrelated.producer_identity,
                artifact_version=unrelated.producer_version,
                fact_type="registry_entry",
                relationship_role="proposed_entry",
            ),
        ),
    )
    result = _reduce(snapshot, action, manifest)
    assert _rejection(result).diagnostic_details == (("fact", "canonical_fact_selection"),)
    assert snapshot.entries[0].certification_records == ()


def test_rejected_operation_produces_no_result_or_input_mutation() -> None:
    snapshot = _base_snapshot()
    action = _reduction_action(prior_standing="Enabled")
    manifest = _operation_manifest(action)
    before = (snapshot, action, manifest)
    result = _reduce(snapshot, action, manifest)
    assert isinstance(result, GovernanceRejection)
    assert (snapshot, action, manifest) == before


def test_no_identifier_authority_or_fact_is_invented() -> None:
    snapshot = _base_snapshot()
    action = _reduction_action()
    manifest = _operation_manifest(action)
    result = _accepted(_reduce(snapshot, action, manifest))
    assert result.action is action
    assert result.manifest is manifest
    assert result.authority_facts == manifest.authority_facts
    assert result.governance_action_references[-1] == action.action_identity
    assert all(isinstance(item, _ValidationAcceptance) for item in result.validation_acceptances)


def test_admission_request_uses_complete_validator_set_without_state_change() -> None:
    snapshot = _base_snapshot(entries=())
    request = _admission()
    contract = _contract(
        producer_identity=request.producer_identity,
        producer_version=request.producer_version,
        owner=request.owner_identity,
        contract_version=request.producer_contract_version,
        implementation_identity=request.implementation_identity,
    )
    action = _reduction_action(
        action_type="admission_requested",
        authority_identity=request.owner_identity,
        authority_role="producer_owner",
        subject_references=(request.producer_identity,),
        prior_standing=None,
        resulting_standing="Declared",
    )
    manifest = _operation_manifest(
        action,
        admission_requests=(request,),
        producer_contracts=(contract,),
        fact_references=(
            _fact_reference(
                artifact_identity=request.request_identity,
                artifact_version=request.producer_version,
                fact_type="admission_request",
                relationship_role="admission_input",
            ),
            _fact_reference(
                artifact_identity=contract.producer_identity,
                artifact_version=contract.producer_version,
                fact_type="producer_contract",
                relationship_role="producer_contract_input",
            ),
        ),
    )
    result = _accepted(_reduce(snapshot, action, manifest))
    assert result.entries == ()
    assert tuple(item.validator_identity for item in result.validation_acceptances) == (
        "authority",
        "admission",
    )


def test_reducer_preconditions_and_acceptance_binding_fail_closed() -> None:
    snapshot = _base_snapshot()
    duplicate = _reduction_action(action_identity="action-001")
    assert _rejection(_reduce(snapshot, duplicate)).diagnostic_details == (
        ("fact", "governance_action_reference"),
    )
    stale = _reduction_action(effective_epoch=GovernanceEpoch(1))
    assert _rejection(_reduce(snapshot, stale)).diagnostic_details == (
        ("fact", "governance_epoch_order"),
    )

    action = _reduction_action()
    manifest = _operation_manifest(action)
    wrong = _ValidationAcceptance(
        "authority",
        snapshot,
        action,
        manifest,
        GovernanceEpoch(3),
    )
    with patch.object(_AuthorityValidator, "validate_context", return_value=wrong):
        result = _GovernanceReducer.reduce(snapshot, action, manifest, action.effective_epoch)
    assert _rejection(result).diagnostic_details == (("fact", "validator_input_binding"),)


def test_internal_state_reduction_guards_are_fail_closed() -> None:
    snapshot = _base_snapshot()
    action = _reduction_action(
        action_type="structural_admission_approved",
        subject_references=("missing",),
    )
    empty = _operation_manifest(action)
    assert _rejection(
        _GovernanceReducer._reduce_admission(snapshot, action, empty)
    ).diagnostic_details == (("fact", "selected_proposed_registry_entry"),)

    proposed = snapshot.entries[0]
    admission_manifest = _operation_manifest(
        replace(action, subject_references=(proposed.producer_identity,)),
        proposed_registry_entries=(proposed,),
        fact_references=(
            _fact_reference(
                artifact_identity=proposed.producer_identity,
                artifact_version=proposed.producer_version,
                fact_type="registry_entry",
                relationship_role="proposed_entry",
            ),
        ),
    )
    reduced_without_semantic_revalidation = _GovernanceReducer._reduce_admission(
        snapshot,
        admission_manifest.actions[0],
        admission_manifest,
    )
    assert not isinstance(reduced_without_semantic_revalidation, GovernanceRejection)
    assert reduced_without_semantic_revalidation == (*snapshot.entries, proposed)

    certification_action = _reduction_action(
        action_type="certification_issued",
        authority_role="certification_authority",
    )
    assert _rejection(
        _GovernanceReducer._reduce_certification(
            snapshot,
            _operation_manifest(certification_action),
        )
    ).diagnostic_details == (("fact", "selected_certification_record"),)
    cert_snapshot = _base_snapshot(
        entries=(_entry(lifecycle_standing="Registered", certification_records=()),)
    )
    _, certification_manifest = _certification_operation(cert_snapshot)
    assert (
        _rejection(
            _GovernanceReducer._reduce_certification(
                replace(cert_snapshot, entries=()),
                certification_manifest,
            )
        ).reason_code
        == "GOV_INVALID_CERTIFICATION_SCOPE"
    )
    record = certification_manifest.certification_records[0]
    assert _rejection(
        _GovernanceReducer._reduce_certification(
            replace(
                cert_snapshot,
                entries=(replace(cert_snapshot.entries[0], certification_records=(record,)),),
            ),
            certification_manifest,
        )
    ).diagnostic_details == (("fact", "exactly_once_certification"),)

    compatibility_action = _reduction_action(
        action_type="compatibility_approved",
        authority_role="compatibility_authority",
    )
    assert _rejection(
        _GovernanceReducer._reduce_compatibility(
            snapshot,
            _operation_manifest(compatibility_action),
        )
    ).diagnostic_details == (("fact", "selected_compatibility_decision"),)
    _, compatibility_manifest = _compatibility_operation()
    assert (
        _rejection(
            _GovernanceReducer._reduce_compatibility(
                replace(snapshot, entries=()),
                compatibility_manifest,
            )
        ).reason_code
        == "GOV_UNKNOWN_COMPATIBILITY"
    )
    decision = compatibility_manifest.compatibility_decisions[0]
    duplicate_snapshot = replace(
        snapshot,
        entries=(replace(snapshot.entries[0], compatibility_decisions=(decision,)),),
    )
    assert _rejection(
        _GovernanceReducer._reduce_compatibility(
            duplicate_snapshot,
            compatibility_manifest,
        )
    ).diagnostic_details == (("fact", "exactly_once_compatibility"),)

    assert _rejection(
        _GovernanceReducer._reduce_standing(
            replace(snapshot, entries=()),
            _reduction_action(),
            lifecycle=True,
        )
    ).diagnostic_details == (("fact", "unique_subject_entry"),)
