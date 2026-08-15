"""A03 Increment 2 validator tests governed by ADR-01, ADR-02, and ADR-03."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest

from epip.governance.model import (
    AdmissionRequest,
    CertificationProfile,
    CertificationRecord,
    CompatibilityDecision,
    GovernanceAction,
    GovernanceEpoch,
    GovernanceFactReference,
    GovernanceManifest,
    GovernanceRejection,
    RegistryEntry,
    RegistrySnapshot,
)
from epip.governance.validation import (
    _ACTION_AUTHORITIES,
    _AdmissionValidator,
    _AuthorityValidator,
    _CertificationValidator,
    _CompatibilityValidator,
    _LifecycleValidator,
    _RevocationValidator,
    _StableReasonCodes,
    _TrustValidator,
    _ValidationAcceptance,
)
from epip.producer import ProducerContract
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


def _matching_contract(**overrides: object) -> ProducerContract:
    values: dict[str, object] = {
        "producer_identity": "producer-001",
        "producer_version": "1.0.0",
        "owner": "owner-001",
        "contract_version": "1.0.0",
        "implementation_identity": "build-001",
    }
    values.update(overrides)
    return _contract(**values)


def _reference_for(
    identity_domain: str,
    artifact_identity: str,
    artifact_version: str,
    fact_type: str,
    relationship_role: str,
) -> GovernanceFactReference:
    return _fact_reference(
        identity_domain=identity_domain,
        artifact_identity=artifact_identity,
        artifact_version=artifact_version,
        fact_type=fact_type,
        relationship_role=relationship_role,
    )


def _operation_manifest(
    action: GovernanceAction,
    **overrides: object,
) -> GovernanceManifest:
    values: dict[str, object] = {
        "manifest_identity": "manifest-validation-002",
        "governance_epoch": action.effective_epoch,
        "actions": (action,),
        "policy_versions": action.policy_versions,
        "authority_facts": (f"{action.authority_identity}:{action.authority_role}",),
    }
    values.update(overrides)
    return _manifest(**values)


def _starting_snapshot(**overrides: object) -> RegistrySnapshot:
    values: dict[str, object] = {"governance_epoch": GovernanceEpoch(1)}
    values.update(overrides)
    return _snapshot(**values)


def _structural_admission_context() -> tuple[
    RegistrySnapshot,
    GovernanceAction,
    GovernanceManifest,
    GovernanceEpoch,
]:
    epoch = GovernanceEpoch(2)
    request = _admission()
    contract = _matching_contract()
    proposed = _entry(
        trust_standing="Untrusted",
        certification_records=(),
        compatibility_decisions=(),
        lifecycle_standing="Registered",
        governance_provenance=("structural-admission-evidence",),
    )
    architectural_fact = "architecture-001:architectural_authority"
    action = _action(
        action_identity="action-structural-admission-002",
        action_type="structural_admission_approved",
        authority_identity="registry-001",
        authority_role="registry_authority",
        subject_references=(proposed.producer_identity,),
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
            _reference_for(
                "producer",
                request.request_identity,
                request.producer_version,
                "admission_request",
                "admission_input",
            ),
            _reference_for(
                "producer",
                contract.producer_identity,
                contract.producer_version,
                "producer_contract",
                "producer_contract_input",
            ),
            _reference_for(
                "producer",
                proposed.producer_identity,
                proposed.producer_version,
                "registry_entry",
                "proposed_entry",
            ),
        ),
        authority_facts=(
            "registry-001:registry_authority",
            "owner-001:producer_owner",
            architectural_fact,
        ),
    )
    return _starting_snapshot(entries=()), action, manifest, epoch


def _code(
    result: _ValidationAcceptance | GovernanceRejection | None,
) -> str:
    assert isinstance(result, GovernanceRejection)
    return result.reason_code


def test_reason_codes_are_stable_unique_and_immutable() -> None:
    values = tuple(code.value for code in _StableReasonCodes)
    assert values
    assert len(values) == len(set(values))
    assert all(value.startswith("GOV_") for value in values)
    with pytest.raises(AttributeError):
        _StableReasonCodes.INVALID_MODEL.value = "GOV_CHANGED"  # type: ignore[misc]
    with pytest.raises(TypeError):
        _ACTION_AUTHORITIES["new"] = frozenset({"authority"})  # type: ignore[index]


def test_admission_accepts_complete_declaration_without_mutation() -> None:
    request = _admission()
    contract = _matching_contract()
    before = (request, contract)
    assert _AdmissionValidator.validate(request, contract) is None
    assert (request, contract) == before
    assert _AdmissionValidator.validate(request, contract) is None


@pytest.mark.parametrize(
    ("admission", "contract", "entries"),
    [
        (cast(AdmissionRequest, object()), _matching_contract(), ()),
        (_admission(), cast(ProducerContract, object()), ()),
        (_admission(), _matching_contract(), cast(tuple[RegistryEntry, ...], [])),
        (_admission(), _matching_contract(), (cast(RegistryEntry, object()),)),
    ],
)
def test_admission_rejects_invalid_models(
    admission: AdmissionRequest,
    contract: ProducerContract,
    entries: tuple[RegistryEntry, ...],
) -> None:
    assert _code(_AdmissionValidator.validate(admission, contract, entries)) == (
        "GOV_INVALID_MODEL"
    )


def test_admission_rejects_identity_declarations_and_duplicate_owner() -> None:
    assert (
        _code(
            _AdmissionValidator.validate(_admission(owner_identity="other"), _matching_contract())
        )
        == "GOV_INVALID_IDENTITY"
    )
    request = _admission(schema_versions=_admission().schema_versions[:-1])
    assert _code(_AdmissionValidator.validate(request, _matching_contract())) == (
        "GOV_INCOMPLETE_DECLARATION"
    )
    request = _admission(profile_references=_admission().profile_references[:-1])
    assert _code(_AdmissionValidator.validate(request, _matching_contract())) == (
        "GOV_INCOMPLETE_DECLARATION"
    )
    assert (
        _code(
            _AdmissionValidator.validate(
                _admission(), _matching_contract(), (_entry(owner_identity="other"),)
            )
        )
        == "GOV_DUPLICATE_OWNERSHIP"
    )


def test_authority_validation_is_exact_and_fail_closed() -> None:
    assert _AuthorityValidator.validate(_action()) is None
    assert _code(_AuthorityValidator.validate(cast(GovernanceAction, object()))) == (
        "GOV_INVALID_MODEL"
    )
    assert _code(_AuthorityValidator.validate(_action(action_type="novel_action"))) == (
        "GOV_UNKNOWN_ACTION"
    )
    assert _code(_AuthorityValidator.validate(_action(authority_role="registry_authority"))) == (
        "GOV_UNAUTHORIZED_AUTHORITY"
    )


def test_certification_accepts_exact_registered_scope() -> None:
    assert (
        _CertificationValidator.validate(
            _certification(), _profile(), _entry(lifecycle_standing="Registered")
        )
        is None
    )


def test_certification_rejects_invalid_models_and_missing_profile() -> None:
    record = _certification()
    entry = _entry(lifecycle_standing="Registered")
    assert (
        _code(
            _CertificationValidator.validate(cast(CertificationRecord, object()), _profile(), entry)
        )
        == "GOV_INVALID_MODEL"
    )
    assert (
        _code(_CertificationValidator.validate(record, _profile(), cast(RegistryEntry, object())))
        == "GOV_INVALID_MODEL"
    )
    assert _code(_CertificationValidator.validate(record, None, entry)) == (
        "GOV_MISSING_CERTIFICATION_PROFILE"
    )
    assert (
        _code(_CertificationValidator.validate(record, cast(CertificationProfile, object()), entry))
        == "GOV_INVALID_MODEL"
    )


def test_certification_rejects_profile_scope_version_and_state() -> None:
    entry = _entry(lifecycle_standing="Registered")
    assert (
        _code(
            _CertificationValidator.validate(
                _certification(), _profile(profile_identity="other"), entry
            )
        )
        == "GOV_MISSING_CERTIFICATION_PROFILE"
    )
    assert (
        _code(
            _CertificationValidator.validate(
                _certification(producer_identity="other"), _profile(), entry
            )
        )
        == "GOV_INVALID_CERTIFICATION_SCOPE"
    )
    assert (
        _code(
            _CertificationValidator.validate(
                _certification(producer_version="2.0.0"), _profile(), entry
            )
        )
        == "GOV_INVALID_CERTIFICATION_VERSION"
    )
    assert (
        _code(
            _CertificationValidator.validate(_certification(verdict="pending"), _profile(), entry)
        )
        == "GOV_INVALID_CERTIFICATION_STATE"
    )
    assert (
        _code(
            _CertificationValidator.validate(
                _certification(), _profile(), _entry(lifecycle_standing="Enabled")
            )
        )
        == "GOV_INVALID_CERTIFICATION_STATE"
    )


def test_compatibility_accepts_known_directed_fact() -> None:
    decision = _compatibility()
    known = (decision.source_reference, decision.target_reference)
    assert _CompatibilityValidator.validate(decision, known) is None


def test_compatibility_rejects_invalid_or_unestablished_facts() -> None:
    decision = _compatibility()
    known = (decision.source_reference, decision.target_reference)
    assert (
        _code(_CompatibilityValidator.validate(cast(CompatibilityDecision, object()), known))
        == "GOV_INVALID_MODEL"
    )
    assert _code(_CompatibilityValidator.validate(decision, cast(tuple[str, ...], []))) == (
        "GOV_INVALID_MODEL"
    )
    assert (
        _code(_CompatibilityValidator.validate(decision, known, cast(tuple[str, ...], [])))
        == "GOV_INVALID_MODEL"
    )
    assert (
        _code(_CompatibilityValidator.validate(_compatibility(direction="unknown"), known))
        == "GOV_MISSING_COMPATIBILITY_DIRECTION"
    )
    same = _compatibility(target_reference=decision.source_reference)
    assert _code(_CompatibilityValidator.validate(same, known)) == (
        "GOV_INVALID_COMPATIBILITY_ENDPOINT"
    )
    assert (
        _code(_CompatibilityValidator.validate(decision, known, (decision.decision_identity,)))
        == "GOV_REVOKED_COMPATIBILITY"
    )
    assert _code(_CompatibilityValidator.validate(decision, (decision.source_reference,))) == (
        "GOV_UNKNOWN_COMPATIBILITY"
    )


def test_lifecycle_accepts_only_governed_transitions() -> None:
    assert _LifecycleValidator.validate(_entry(lifecycle_standing="Declared"), "Registered") is None
    assert (
        _LifecycleValidator.validate(_entry(lifecycle_standing="Registered"), "Registered") is None
    )
    assert (
        _LifecycleValidator.validate(
            _entry(lifecycle_standing="Certified"),
            "Enabled",
            certification_valid=True,
            trusted=True,
            compatibility_valid=True,
        )
        is None
    )
    assert (
        _LifecycleValidator.validate(
            _entry(lifecycle_standing="Deprecated"),
            "Enabled",
            certification_valid=True,
            trusted=True,
            compatibility_valid=True,
            recertification_approved=True,
        )
        is None
    )
    assert (
        _LifecycleValidator.validate(
            _entry(lifecycle_standing="Disabled"), "Registered", remediation_approved=True
        )
        is None
    )


def test_lifecycle_rejects_invalid_illegal_terminal_and_incomplete_transitions() -> None:
    assert (
        _code(_LifecycleValidator.validate(cast(RegistryEntry, object()), "Registered"))
        == "GOV_INVALID_MODEL"
    )
    assert _code(_LifecycleValidator.validate(_entry(), cast(str, 1))) == "GOV_INVALID_MODEL"
    assert _code(_LifecycleValidator.validate(_entry(lifecycle_standing="Unknown"), "Enabled")) == (
        "GOV_ILLEGAL_LIFECYCLE_TRANSITION"
    )
    assert _code(_LifecycleValidator.validate(_entry(lifecycle_standing="Retired"), "Enabled")) == (
        "GOV_RETIRED_IS_TERMINAL"
    )
    assert (
        _code(_LifecycleValidator.validate(_entry(lifecycle_standing="Certified"), "Enabled"))
        == "GOV_INVALID_ACTIVATION"
    )
    assert (
        _code(
            _LifecycleValidator.validate(
                _entry(lifecycle_standing="Deprecated"),
                "Enabled",
                certification_valid=True,
                trusted=True,
                compatibility_valid=True,
            )
        )
        == "GOV_INVALID_ACTIVATION"
    )
    assert (
        _code(_LifecycleValidator.validate(_entry(lifecycle_standing="Disabled"), "Certified"))
        == "GOV_ILLEGAL_LIFECYCLE_TRANSITION"
    )


def _trust_action(**overrides: object) -> GovernanceAction:
    values: dict[str, object] = {
        "action_type": "trust_granted",
        "authority_role": "security_authority",
        "subject_references": ("producer-001", "capability-001"),
        "prior_standing": "Untrusted",
        "resulting_standing": "Trusted",
    }
    values.update(overrides)
    return _action(**values)


def test_trust_accepts_scoped_authorized_transitions() -> None:
    assert _TrustValidator.validate(_trust_action(), "Untrusted") is None
    assert (
        _TrustValidator.validate(
            _trust_action(prior_standing="Experimental"),
            "Experimental",
            ("certification-001",),
        )
        is None
    )


def test_trust_rejects_invalid_authority_scope_transition_and_evidence() -> None:
    action = _trust_action()
    assert _code(_TrustValidator.validate(cast(GovernanceAction, object()), "Untrusted")) == (
        "GOV_INVALID_MODEL"
    )
    assert _code(_TrustValidator.validate(action, "Untrusted", cast(tuple[str, ...], []))) == (
        "GOV_INVALID_MODEL"
    )
    assert (
        _code(
            _TrustValidator.validate(
                _trust_action(authority_role="registry_authority"), "Untrusted"
            )
        )
        == "GOV_UNAUTHORIZED_AUTHORITY"
    )
    assert (
        _code(
            _TrustValidator.validate(
                _trust_action(subject_references=("producer-001",)), "Untrusted"
            )
        )
        == "GOV_INVALID_TRUST_SCOPE"
    )
    assert _code(_TrustValidator.validate(action, "Unknown")) == "GOV_INVALID_TRUST_TRANSITION"
    assert (
        _code(
            _TrustValidator.validate(_trust_action(prior_standing="Experimental"), "Experimental")
        )
        == "GOV_MISSING_MANDATORY_FACT"
    )


def _revocation_action(**overrides: object) -> GovernanceAction:
    values: dict[str, object] = {
        "action_type": "trust_revoked",
        "authority_role": "security_authority",
        "subject_references": ("producer-001", "capability-001"),
        "prior_standing": "Trusted",
        "resulting_standing": "Revoked",
    }
    values.update(overrides)
    return _action(**values)


def test_revocation_accepts_new_authorized_scope() -> None:
    assert _RevocationValidator.validate(_revocation_action()) is None


def test_revocation_rejects_invalid_authority_duplicate_and_revoked_scope() -> None:
    action = _revocation_action()
    assert _code(_RevocationValidator.validate(cast(GovernanceAction, object()))) == (
        "GOV_INVALID_MODEL"
    )
    assert (
        _code(_RevocationValidator.validate(action, cast(tuple[str, ...], [])))
        == "GOV_INVALID_MODEL"
    )
    assert (
        _code(_RevocationValidator.validate(action, (), cast(tuple[str, ...], [])))
        == "GOV_INVALID_MODEL"
    )
    assert (
        _code(_RevocationValidator.validate(_revocation_action(action_type="unknown")))
        == "GOV_INVALID_REVOCATION_AUTHORITY"
    )
    assert (
        _code(
            _RevocationValidator.validate(_revocation_action(authority_role="registry_authority"))
        )
        == "GOV_INVALID_REVOCATION_AUTHORITY"
    )
    assert _code(_RevocationValidator.validate(action, (action.action_identity,))) == (
        "GOV_DUPLICATE_REVOCATION"
    )
    assert _code(_RevocationValidator.validate(action, (), ("capability-001",))) == (
        "GOV_ALREADY_REVOKED_SCOPE"
    )


def test_validators_return_equal_deterministic_rejections() -> None:
    action = _action(action_type="unknown")
    first = _AuthorityValidator.validate(action)
    second = _AuthorityValidator.validate(replace(action))
    assert first == second


def test_authority_context_acceptance_binds_exact_immutable_inputs() -> None:
    epoch = GovernanceEpoch(2)
    action = _action(effective_epoch=epoch)
    manifest = _operation_manifest(action)
    snapshot = _starting_snapshot()

    first = _AuthorityValidator.validate_context(snapshot, action, manifest, epoch)
    second = _AuthorityValidator.validate_context(snapshot, action, manifest, epoch)

    assert isinstance(first, _ValidationAcceptance)
    assert first == second
    assert (first.snapshot, first.action, first.manifest, first.epoch) == (
        snapshot,
        action,
        manifest,
        epoch,
    )
    with pytest.raises(AttributeError):
        first.validator_identity = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("invalid_field", ("snapshot", "action", "manifest", "epoch"))
def test_authority_context_rejects_invalid_models(invalid_field: str) -> None:
    epoch = GovernanceEpoch(2)
    action = _action(effective_epoch=epoch)
    manifest = _operation_manifest(action)
    values: dict[str, object] = {
        "snapshot": _starting_snapshot(),
        "action": action,
        "manifest": manifest,
        "epoch": epoch,
    }
    values[invalid_field] = object()
    result = _AuthorityValidator.validate_context(
        cast(RegistrySnapshot, values["snapshot"]),
        cast(GovernanceAction, values["action"]),
        cast(GovernanceManifest, values["manifest"]),
        cast(GovernanceEpoch, values["epoch"]),
    )
    assert _code(result) == "GOV_INVALID_MODEL"


def test_authority_context_rejects_action_epoch_policy_and_authority_mismatch() -> None:
    epoch = GovernanceEpoch(2)
    action = _action(effective_epoch=epoch)
    snapshot = _starting_snapshot()

    other_action = _action(action_identity="other", effective_epoch=epoch)
    mismatch = _operation_manifest(other_action)
    assert _code(_AuthorityValidator.validate_context(snapshot, action, mismatch, epoch)) == (
        "GOV_INCOMPLETE_DECLARATION"
    )

    future_snapshot = _starting_snapshot(governance_epoch=GovernanceEpoch(3))
    manifest = _operation_manifest(action)
    assert (
        _code(_AuthorityValidator.validate_context(future_snapshot, action, manifest, epoch))
        == "GOV_ILLEGAL_LIFECYCLE_TRANSITION"
    )

    missing_policy = _operation_manifest(
        action,
        policy_versions=(("other", "1.0.0"),),
    )
    assert (
        _code(_AuthorityValidator.validate_context(snapshot, action, missing_policy, epoch))
        == "GOV_INCOMPLETE_DECLARATION"
    )

    missing_authority = _operation_manifest(
        action,
        authority_facts=("other:producer_owner",),
    )
    assert (
        _code(_AuthorityValidator.validate_context(snapshot, action, missing_authority, epoch))
        == "GOV_UNAUTHORIZED_AUTHORITY"
    )


def test_admission_context_validates_manifest_facts_snapshot_and_correspondence() -> None:
    epoch = GovernanceEpoch(2)
    action = _action(effective_epoch=epoch)
    request = _admission()
    contract = _matching_contract()
    references = (
        _reference_for(
            "producer",
            request.request_identity,
            request.producer_version,
            "admission_request",
            "admission_input",
        ),
        _reference_for(
            "producer",
            contract.producer_identity,
            contract.producer_version,
            "producer_contract",
            "producer_contract_input",
        ),
    )
    manifest = _operation_manifest(
        action,
        admission_requests=(request,),
        producer_contracts=(contract,),
        fact_references=references,
    )
    snapshot = _starting_snapshot(entries=())
    before = (snapshot, action, manifest, epoch)

    accepted = _AdmissionValidator.validate_context(snapshot, action, manifest, epoch)
    assert isinstance(accepted, _ValidationAcceptance)
    assert (snapshot, action, manifest, epoch) == before

    missing = _operation_manifest(action)
    assert _code(_AdmissionValidator.validate_context(snapshot, action, missing, epoch)) == (
        "GOV_MISSING_MANDATORY_FACT"
    )
    unrelated_action = replace(action, subject_references=("unrelated",))
    unrelated_manifest = _operation_manifest(
        unrelated_action,
        admission_requests=(request,),
        producer_contracts=(contract,),
        fact_references=references,
    )
    assert (
        _code(
            _AdmissionValidator.validate_context(
                snapshot,
                unrelated_action,
                unrelated_manifest,
                epoch,
            )
        )
        == "GOV_INCOMPLETE_DECLARATION"
    )


def test_admission_context_rejects_duplicate_authoritative_ownership() -> None:
    epoch = GovernanceEpoch(2)
    action = _action(effective_epoch=epoch)
    request = _admission()
    contract = _matching_contract()
    manifest = _operation_manifest(
        action,
        admission_requests=(request,),
        producer_contracts=(contract,),
        fact_references=(
            _reference_for(
                "producer",
                request.request_identity,
                request.producer_version,
                "admission_request",
                "admission_input",
            ),
            _reference_for(
                "producer",
                contract.producer_identity,
                contract.producer_version,
                "producer_contract",
                "producer_contract_input",
            ),
        ),
    )
    snapshot = _starting_snapshot(entries=(_entry(owner_identity="other"),))
    assert _code(_AdmissionValidator.validate_context(snapshot, action, manifest, epoch)) == (
        "GOV_DUPLICATE_OWNERSHIP"
    )


def test_structural_admission_acceptance_is_exact_immutable_and_deterministic() -> None:
    snapshot, action, manifest, epoch = _structural_admission_context()
    before = (snapshot, action, manifest, epoch)

    first = _AdmissionValidator.validate_context(snapshot, action, manifest, epoch)
    second = _AdmissionValidator.validate_context(snapshot, action, manifest, epoch)

    assert isinstance(first, _ValidationAcceptance)
    assert first == second
    assert first.validator_identity == "admission"
    assert (first.snapshot, first.action, first.manifest, first.epoch) == before
    assert (snapshot, action, manifest, epoch) == before


def test_structural_admission_validates_ownership_and_authority_dependencies() -> None:
    snapshot, action, manifest, epoch = _structural_admission_context()
    conflicting = replace(
        snapshot,
        entries=(_entry(owner_identity="other-owner"),),
    )
    assert (
        _code(_AdmissionValidator.validate_context(conflicting, action, manifest, epoch))
        == "GOV_DUPLICATE_OWNERSHIP"
    )

    no_architectural_approval = replace(action, approval_references=())
    no_approval_manifest = replace(manifest, actions=(no_architectural_approval,))
    assert (
        _code(
            _AdmissionValidator.validate_context(
                snapshot,
                no_architectural_approval,
                no_approval_manifest,
                epoch,
            )
        )
        == "GOV_MISSING_MANDATORY_FACT"
    )

    wrong_registry_scope = replace(action, authority_role="producer_owner")
    wrong_scope_manifest = replace(manifest, actions=(wrong_registry_scope,))
    assert (
        _code(
            _AdmissionValidator.validate_context(
                snapshot,
                wrong_registry_scope,
                wrong_scope_manifest,
                epoch,
            )
        )
        == "GOV_UNAUTHORIZED_AUTHORITY"
    )


def test_structural_admission_validates_entry_correspondence_and_policies() -> None:
    snapshot, action, manifest, epoch = _structural_admission_context()
    mismatched_entry = replace(
        manifest.proposed_registry_entries[0],
        implementation_identity="other-build",
    )
    mismatched_reference = replace(
        manifest.fact_references[2],
        relationship_role="proposed_entry",
    )
    mismatched_manifest = replace(
        manifest,
        proposed_registry_entries=(mismatched_entry,),
        fact_references=(
            manifest.fact_references[0],
            manifest.fact_references[1],
            mismatched_reference,
        ),
    )
    assert (
        _code(_AdmissionValidator.validate_context(snapshot, action, mismatched_manifest, epoch))
        == "GOV_INVALID_IDENTITY"
    )

    incorrect_role = replace(
        manifest.fact_references[2],
        relationship_role="unrelated_entry",
    )
    incorrect_reference_manifest = replace(
        manifest,
        fact_references=(
            manifest.fact_references[0],
            manifest.fact_references[1],
            incorrect_role,
        ),
    )
    first = _AdmissionValidator.validate_context(
        snapshot,
        action,
        incorrect_reference_manifest,
        epoch,
    )
    second = _AdmissionValidator.validate_context(
        snapshot,
        action,
        incorrect_reference_manifest,
        epoch,
    )
    assert _code(first) == "GOV_INCOMPLETE_DECLARATION"
    assert first == second

    incompatible_policy_snapshot = replace(
        snapshot,
        policy_versions=(("admission", "2.0.0"),),
    )
    assert (
        _code(
            _AdmissionValidator.validate_context(
                incompatible_policy_snapshot,
                action,
                manifest,
                epoch,
            )
        )
        == "GOV_INCOMPLETE_DECLARATION"
    )


def test_structural_admission_fails_closed_at_every_semantic_boundary() -> None:
    snapshot, action, manifest, epoch = _structural_admission_context()

    missing_entry = replace(
        manifest,
        proposed_registry_entries=(),
        fact_references=manifest.fact_references[:2],
    )
    assert (
        _code(_AdmissionValidator.validate_context(snapshot, action, missing_entry, epoch))
        == "GOV_MISSING_MANDATORY_FACT"
    )

    unrelated_action = replace(action, subject_references=("other-producer",))
    unrelated_manifest = replace(manifest, actions=(unrelated_action,))
    assert (
        _code(
            _AdmissionValidator.validate_context(
                snapshot,
                unrelated_action,
                unrelated_manifest,
                epoch,
            )
        )
        == "GOV_INCOMPLETE_DECLARATION"
    )

    trusted_entry = replace(manifest.proposed_registry_entries[0], trust_standing="Trusted")
    trusted_manifest = replace(manifest, proposed_registry_entries=(trusted_entry,))
    assert (
        _code(_AdmissionValidator.validate_context(snapshot, action, trusted_manifest, epoch))
        == "GOV_INCOMPLETE_DECLARATION"
    )

    missing_owner = replace(
        manifest,
        authority_facts=tuple(
            fact for fact in manifest.authority_facts if fact != "owner-001:producer_owner"
        ),
    )
    assert (
        _code(_AdmissionValidator.validate_context(snapshot, action, missing_owner, epoch))
        == "GOV_DUPLICATE_OWNERSHIP"
    )

    owner_architecture_fact = "owner-001:architectural_authority"
    unseparated_action = replace(action, approval_references=(owner_architecture_fact,))
    unseparated_manifest = replace(
        manifest,
        actions=(unseparated_action,),
        authority_facts=(
            "registry-001:registry_authority",
            "owner-001:producer_owner",
            owner_architecture_fact,
        ),
    )
    assert (
        _code(
            _AdmissionValidator.validate_context(
                snapshot,
                unseparated_action,
                unseparated_manifest,
                epoch,
            )
        )
        == "GOV_UNAUTHORIZED_AUTHORITY"
    )

    stale_snapshot = replace(snapshot, governance_epoch=epoch)
    assert (
        _code(_AdmissionValidator.validate_context(stale_snapshot, action, manifest, epoch))
        == "GOV_ILLEGAL_LIFECYCLE_TRANSITION"
    )


def test_certification_context_validates_selected_record_profile_and_snapshot() -> None:
    epoch = GovernanceEpoch(2)
    record = _certification(effective_epoch=epoch)
    profile = _profile()
    action = _action(
        action_type="certification_issued",
        authority_role="certification_authority",
        authority_identity="certification-authority",
        subject_references=(record.record_identity,),
        effective_epoch=epoch,
    )
    manifest = _operation_manifest(
        action,
        certification_profiles=(profile,),
        certification_records=(record,),
        fact_references=(
            _reference_for(
                "certification",
                profile.profile_identity,
                profile.profile_version,
                "certification_profile",
                "certification_profile_input",
            ),
            _reference_for(
                "certification",
                record.record_identity,
                record.certification_suite_version,
                "certification_record",
                "certification_record_input",
            ),
        ),
    )
    snapshot = _starting_snapshot(
        entries=(_entry(lifecycle_standing="Registered", certification_records=()),)
    )
    assert isinstance(
        _CertificationValidator.validate_context(snapshot, action, manifest, epoch),
        _ValidationAcceptance,
    )

    missing = _operation_manifest(action)
    assert _code(_CertificationValidator.validate_context(snapshot, action, missing, epoch)) == (
        "GOV_MISSING_MANDATORY_FACT"
    )


def test_compatibility_context_validates_direction_endpoints_and_correspondence() -> None:
    epoch = GovernanceEpoch(2)
    decision = _compatibility(effective_epoch=epoch)
    action = _action(
        action_type="compatibility_approved",
        authority_identity="compatibility-authority",
        authority_role="compatibility_authority",
        subject_references=(decision.decision_identity,),
        effective_epoch=epoch,
    )
    manifest = _operation_manifest(
        action,
        compatibility_decisions=(decision,),
        fact_references=(
            _reference_for(
                "validation",
                decision.decision_identity,
                decision.policy_version,
                "compatibility_decision",
                "compatibility_input",
            ),
        ),
    )
    snapshot = _starting_snapshot(
        entries=(
            _entry(
                producer_identity="producer-001",
                producer_version="1.0.0",
                compatibility_decisions=(),
            ),
            _entry(
                producer_identity="consumer-001",
                producer_version="1.0.0",
                compatibility_decisions=(),
            ),
        )
    )
    assert isinstance(
        _CompatibilityValidator.validate_context(snapshot, action, manifest, epoch),
        _ValidationAcceptance,
    )

    unrelated_action = replace(action, subject_references=("other",))
    unrelated_manifest = _operation_manifest(
        unrelated_action,
        compatibility_decisions=(decision,),
        fact_references=manifest.fact_references,
    )
    assert (
        _code(
            _CompatibilityValidator.validate_context(
                snapshot,
                unrelated_action,
                unrelated_manifest,
                epoch,
            )
        )
        == "GOV_INCOMPLETE_DECLARATION"
    )


def test_lifecycle_trust_and_revocation_contexts_use_authoritative_snapshot() -> None:
    epoch = GovernanceEpoch(2)
    lifecycle_action = _action(
        action_type="lifecycle_transitioned",
        authority_identity="registry-authority",
        authority_role="registry_authority",
        subject_references=("producer-001",),
        prior_standing="Certified",
        resulting_standing="Enabled",
        effective_epoch=epoch,
    )
    lifecycle_manifest = _operation_manifest(lifecycle_action)
    lifecycle_snapshot = _starting_snapshot(
        entries=(
            _entry(
                lifecycle_standing="Certified",
                trust_standing="Trusted",
            ),
        )
    )
    assert isinstance(
        _LifecycleValidator.validate_context(
            lifecycle_snapshot,
            lifecycle_action,
            lifecycle_manifest,
            epoch,
        ),
        _ValidationAcceptance,
    )

    trust_action = _trust_action(effective_epoch=epoch)
    trust_manifest = _operation_manifest(trust_action)
    trust_snapshot = _starting_snapshot(
        entries=(_entry(trust_standing="Untrusted"),),
    )
    assert isinstance(
        _TrustValidator.validate_context(trust_snapshot, trust_action, trust_manifest, epoch),
        _ValidationAcceptance,
    )

    revocation_action = _revocation_action(
        action_identity="action-revocation-002",
        effective_epoch=epoch,
    )
    revocation_manifest = _operation_manifest(revocation_action)
    assert isinstance(
        _RevocationValidator.validate_context(
            lifecycle_snapshot,
            revocation_action,
            revocation_manifest,
            epoch,
        ),
        _ValidationAcceptance,
    )


def test_certification_context_validates_authoritative_status_transition() -> None:
    epoch = GovernanceEpoch(2)
    prior = _certification()
    revoked = _certification(
        record_identity="certification-revocation-002",
        verdict="revoked",
        effective_epoch=epoch,
        status_relationship_reference=prior.record_identity,
    )
    profile = _profile()
    action = _action(
        action_type="certification_revoked",
        authority_identity="certification-authority",
        authority_role="certification_authority",
        subject_references=(revoked.record_identity,),
        effective_epoch=epoch,
    )
    manifest = _operation_manifest(
        action,
        certification_profiles=(profile,),
        certification_records=(revoked,),
        fact_references=(
            _reference_for(
                "certification",
                profile.profile_identity,
                profile.profile_version,
                "certification_profile",
                "certification_profile_input",
            ),
            _reference_for(
                "certification",
                revoked.record_identity,
                revoked.certification_suite_version,
                "certification_record",
                "certification_record_input",
            ),
        ),
    )
    snapshot = _starting_snapshot(
        entries=(
            _entry(
                lifecycle_standing="Registered",
                certification_records=(prior,),
            ),
        )
    )

    assert isinstance(
        _CertificationValidator.validate_context(snapshot, action, manifest, epoch),
        _ValidationAcceptance,
    )
    missing_history = _starting_snapshot(
        entries=(_entry(lifecycle_standing="Registered", certification_records=()),)
    )
    assert (
        _code(_CertificationValidator.validate_context(missing_history, action, manifest, epoch))
        == "GOV_INVALID_CERTIFICATION_STATE"
    )


def test_compatibility_context_validates_authoritative_revocation_transition() -> None:
    epoch = GovernanceEpoch(2)
    prior = _compatibility()
    revoked = _compatibility(
        decision_identity="compatibility-revocation-002",
        effective_epoch=epoch,
        revocation_reference=prior.decision_identity,
    )
    action = _action(
        action_type="compatibility_revoked",
        authority_identity="compatibility-authority",
        authority_role="compatibility_authority",
        subject_references=(revoked.decision_identity,),
        effective_epoch=epoch,
    )
    manifest = _operation_manifest(
        action,
        compatibility_decisions=(revoked,),
        fact_references=(
            _reference_for(
                "validation",
                revoked.decision_identity,
                revoked.policy_version,
                "compatibility_decision",
                "compatibility_input",
            ),
        ),
    )
    snapshot = _starting_snapshot(
        entries=(
            _entry(compatibility_decisions=(prior,)),
            _entry(
                producer_identity="consumer-001",
                compatibility_decisions=(),
            ),
        )
    )
    assert isinstance(
        _CompatibilityValidator.validate_context(snapshot, action, manifest, epoch),
        _ValidationAcceptance,
    )


def test_lifecycle_and_trust_context_reject_prior_standing_mismatch() -> None:
    epoch = GovernanceEpoch(2)
    lifecycle_action = _action(
        action_type="lifecycle_transitioned",
        authority_identity="registry-authority",
        authority_role="registry_authority",
        subject_references=("producer-001",),
        prior_standing="Declared",
        resulting_standing="Enabled",
        effective_epoch=epoch,
    )
    snapshot = _starting_snapshot(entries=(_entry(lifecycle_standing="Certified"),))
    assert (
        _code(
            _LifecycleValidator.validate_context(
                snapshot,
                lifecycle_action,
                _operation_manifest(lifecycle_action),
                epoch,
            )
        )
        == "GOV_ILLEGAL_LIFECYCLE_TRANSITION"
    )

    trust_action = _trust_action(prior_standing="Experimental", effective_epoch=epoch)
    assert (
        _code(
            _TrustValidator.validate_context(
                _starting_snapshot(entries=(_entry(trust_standing="Untrusted"),)),
                trust_action,
                _operation_manifest(trust_action),
                epoch,
            )
        )
        == "GOV_INVALID_TRUST_TRANSITION"
    )


def test_context_rejections_are_deterministic_and_inputs_remain_immutable() -> None:
    epoch = GovernanceEpoch(2)
    action = _action(effective_epoch=epoch)
    manifest = _operation_manifest(
        action,
        policy_versions=(("other", "1.0.0"),),
    )
    snapshot = _starting_snapshot()
    before = (snapshot, action, manifest, epoch)

    first = _AuthorityValidator.validate_context(snapshot, action, manifest, epoch)
    second = _AuthorityValidator.validate_context(snapshot, action, manifest, epoch)

    assert isinstance(first, GovernanceRejection)
    assert first == second
    assert (snapshot, action, manifest, epoch) == before


def test_authority_context_does_not_own_supported_action_validation() -> None:
    epoch = GovernanceEpoch(2)
    action = _action(
        action_type="future_governance_action",
        authority_identity="future-authority",
        authority_role="future_authority",
        effective_epoch=epoch,
    )
    manifest = _operation_manifest(action)

    result = _AuthorityValidator.validate_context(_starting_snapshot(), action, manifest, epoch)

    assert isinstance(result, _ValidationAcceptance)


def test_admission_context_uses_canonical_fact_roles_and_exact_selection() -> None:
    epoch = GovernanceEpoch(2)
    request = _admission()
    contract = _matching_contract()
    action = _action(effective_epoch=epoch)
    references = (
        _reference_for(
            "producer",
            request.request_identity,
            request.producer_version,
            "admission_request",
            "incorrect_role",
        ),
        _reference_for(
            "producer",
            contract.producer_identity,
            contract.producer_version,
            "producer_contract",
            "producer_contract_input",
        ),
    )
    incorrect_role = _operation_manifest(
        action,
        admission_requests=(request,),
        producer_contracts=(contract,),
        fact_references=references,
    )
    snapshot = _starting_snapshot(entries=())
    assert (
        _code(_AdmissionValidator.validate_context(snapshot, action, incorrect_role, epoch))
        == "GOV_INCOMPLETE_DECLARATION"
    )

    incorrect_action = replace(
        action,
        subject_references=("unrelated-fact",),
    )
    incorrect_selection = _operation_manifest(
        incorrect_action,
        admission_requests=(request,),
        producer_contracts=(contract,),
        fact_references=(
            replace(references[0], relationship_role="admission_input"),
            references[1],
        ),
    )
    assert (
        _code(
            _AdmissionValidator.validate_context(
                snapshot,
                incorrect_action,
                incorrect_selection,
                epoch,
            )
        )
        == "GOV_INCOMPLETE_DECLARATION"
    )


def test_authority_context_validates_authoritative_snapshot_policy() -> None:
    epoch = GovernanceEpoch(2)
    action = _action(effective_epoch=epoch)
    manifest = _operation_manifest(action)
    snapshot = _starting_snapshot(policy_versions=(("other", "1.0.0"),))

    result = _AuthorityValidator.validate_context(snapshot, action, manifest, epoch)

    assert _code(result) == "GOV_INCOMPLETE_DECLARATION"


def test_certification_context_accepts_authoritative_suspension() -> None:
    epoch = GovernanceEpoch(2)
    prior = _certification()
    suspended = _certification(
        record_identity="certification-suspension-002",
        verdict="suspended",
        effective_epoch=epoch,
        status_relationship_reference=prior.record_identity,
    )
    profile = _profile()
    action = _action(
        action_type="certification_suspended",
        authority_identity="certification-authority",
        authority_role="certification_authority",
        subject_references=(suspended.record_identity,),
        effective_epoch=epoch,
    )
    manifest = _operation_manifest(
        action,
        certification_profiles=(profile,),
        certification_records=(suspended,),
        fact_references=(
            _reference_for(
                "certification",
                profile.profile_identity,
                profile.profile_version,
                "certification_profile",
                "certification_profile_input",
            ),
            _reference_for(
                "certification",
                suspended.record_identity,
                suspended.certification_suite_version,
                "certification_record",
                "certification_record_input",
            ),
        ),
    )
    snapshot = _starting_snapshot(
        entries=(
            _entry(
                lifecycle_standing="Registered",
                certification_records=(prior,),
            ),
        )
    )

    result = _CertificationValidator.validate_context(snapshot, action, manifest, epoch)

    assert isinstance(result, _ValidationAcceptance)
