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
    GovernanceRejection,
    RegistryEntry,
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
)
from epip.producer import ProducerContract
from tests.governance.test_model import (
    _action,
    _admission,
    _certification,
    _compatibility,
    _entry,
    _profile,
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


def _code(result: GovernanceRejection | None) -> str:
    assert result is not None
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
