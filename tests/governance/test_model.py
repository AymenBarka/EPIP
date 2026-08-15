"""A03 Increment 1 and A03-MP-01 model tests governed by ADR-03 and ADR-09."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import FrozenInstanceError, replace

import pytest

from epip.core.integrity import DataIntegrityError
from epip.governance import (
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


def _epoch(**overrides: object) -> GovernanceEpoch:
    values: dict[str, object] = {"sequence": 1}
    values.update(overrides)
    return GovernanceEpoch(**values)  # type: ignore[arg-type]


def _action(**overrides: object) -> GovernanceAction:
    values: dict[str, object] = {
        "action_identity": "action-001",
        "action_type": "admission_requested",
        "authority_identity": "owner-001",
        "authority_role": "producer_owner",
        "subject_references": ("producer-001",),
        "prior_standing": None,
        "resulting_standing": "declared",
        "policy_versions": (("admission", "1.0.0"),),
        "contract_versions": (("producer", "1.0.0"),),
        "effective_epoch": _epoch(),
        "reason_code": "ADMISSION_REQUESTED",
        "evidence_references": ("evidence-001",),
        "approval_references": (),
        "separation_attestations": (),
    }
    values.update(overrides)
    return GovernanceAction(**values)  # type: ignore[arg-type]


def _fact_reference(**overrides: object) -> GovernanceFactReference:
    values: dict[str, object] = {
        "identity_domain": "producer",
        "artifact_identity": "request-001",
        "artifact_version": "1.0.0",
        "fact_type": "admission_request",
        "relationship_role": "admission_input",
    }
    values.update(overrides)
    return GovernanceFactReference(**values)  # type: ignore[arg-type]


def _manifest(**overrides: object) -> GovernanceManifest:
    values: dict[str, object] = {
        "manifest_schema_version": "1.0.0",
        "identity_domain_version": "1.0.0",
        "canonicalization_profile_identity": "governance-manifest",
        "canonicalization_profile_version": "1.0.0",
        "digest_profile_identity": "governance-manifest",
        "digest_profile_version": "1.0.0",
        "manifest_identity": "manifest-001",
        "governance_epoch": _epoch(),
        "actions": (_action(),),
        "admission_requests": (),
        "producer_contracts": (),
        "proposed_registry_entries": (),
        "certification_profiles": (),
        "certification_records": (),
        "compatibility_decisions": (),
        "fact_references": (),
        "policy_versions": (("admission", "1.0.0"),),
        "authority_facts": ("owner-001:producer_owner",),
    }
    values.update(overrides)
    return GovernanceManifest(**values)  # type: ignore[arg-type]


def _admission(**overrides: object) -> AdmissionRequest:
    values: dict[str, object] = {
        "request_identity": "request-001",
        "producer_identity": "producer-001",
        "producer_version": "1.0.0",
        "owner_identity": "owner-001",
        "maintainer_identities": ("maintainer-001",),
        "producer_contract_version": "1.0.0",
        "implementation_identity": "build-001",
        "capability_references": (("market.structure", "1.0.0"),),
        "schema_versions": (
            ("input", "1.0.0"),
            ("output", "1.0.0"),
            ("context", "1.0.0"),
            ("failure", "1.0.0"),
            ("diagnostic", "1.0.0"),
        ),
        "profile_references": (
            ("execution", "bounded"),
            ("resource", "bounded"),
            ("isolation", "invocation-local"),
            ("determinism", "output-deterministic"),
            ("replay", "historical-input"),
        ),
        "security_classification": "least-privilege",
        "requested_privileges": ("read-declared-input",),
        "external_boundaries": (),
        "certification_profile_reference": "cert-profile-001",
        "evidence_references": ("evidence-001",),
    }
    values.update(overrides)
    return AdmissionRequest(**values)  # type: ignore[arg-type]


def _profile(**overrides: object) -> CertificationProfile:
    values: dict[str, object] = {
        "profile_identity": "cert-profile-001",
        "profile_version": "1.0.0",
        "required_evidence": ("descriptor", "real-execution"),
        "test_classes": ("contract", "determinism"),
        "repeat_count": 3,
        "environmental_constraints": ("python-3.13",),
        "acceptance_criteria": ("all-required-tests-pass",),
        "failure_criteria": ("unknown-behaviour",),
        "expiry_rules": ("profile-change",),
        "recertification_triggers": ("implementation-change",),
    }
    values.update(overrides)
    return CertificationProfile(**values)  # type: ignore[arg-type]


def _certification(**overrides: object) -> CertificationRecord:
    values: dict[str, object] = {
        "record_identity": "certification-001",
        "certification_authority_identity": "certification-authority",
        "producer_identity": "producer-001",
        "producer_version": "1.0.0",
        "implementation_identity": "build-001",
        "producer_contract_version": "1.0.0",
        "capability_references": (("market.structure", "1.0.0"),),
        "configuration_profile": "default-v1",
        "schema_versions": (("input", "1.0.0"), ("output", "1.0.0")),
        "temporal_profile": "closed-boundary",
        "determinism_profile": "output-deterministic",
        "replay_profile": "historical-input",
        "execution_profile": "bounded",
        "isolation_profile": "invocation-local",
        "resource_profile": "bounded",
        "privilege_scope": ("read-declared-input",),
        "certification_profile_reference": "cert-profile-001@1.0.0",
        "certification_suite_version": "1.0.0",
        "evidence_references": ("cert-evidence-001",),
        "verdict": "passed",
        "effective_epoch": _epoch(),
        "expiration_or_review_condition": "profile-change",
    }
    values.update(overrides)
    return CertificationRecord(**values)  # type: ignore[arg-type]


def _compatibility(**overrides: object) -> CompatibilityDecision:
    values: dict[str, object] = {
        "decision_identity": "compatibility-001",
        "compatibility_authority_identity": "compatibility-authority",
        "source_reference": "producer-001@1.0.0",
        "target_reference": "consumer-001@1.0.0",
        "compatibility_dimension": "producer-contract",
        "direction": "source-to-target",
        "intended_use": "authoritative-planning",
        "version_scope": (("source", "1.0.0"), ("target", "1.0.0")),
        "profile_scope": (("determinism", "output-deterministic"),),
        "evidence_references": ("compatibility-evidence-001",),
        "policy_version": "1.0.0",
        "effective_epoch": _epoch(),
        "review_or_expiry_condition": "bound-version-change",
    }
    values.update(overrides)
    return CompatibilityDecision(**values)  # type: ignore[arg-type]


def _entry(**overrides: object) -> RegistryEntry:
    values: dict[str, object] = {
        "producer_identity": "producer-001",
        "producer_version": "1.0.0",
        "descriptor_reference": "descriptor-001",
        "owner_identity": "owner-001",
        "producer_contract_version": "1.0.0",
        "implementation_identity": "build-001",
        "capability_references": (("market.structure", "1.0.0"),),
        "trust_standing": "trusted",
        "certification_records": (_certification(),),
        "compatibility_decisions": (_compatibility(),),
        "lifecycle_standing": "enabled",
        "governance_provenance": ("action-001",),
    }
    values.update(overrides)
    return RegistryEntry(**values)  # type: ignore[arg-type]


def _snapshot(**overrides: object) -> RegistrySnapshot:
    values: dict[str, object] = {
        "snapshot_identity": "snapshot-001",
        "manifest_reference": "manifest-001",
        "governance_epoch": _epoch(),
        "entries": (_entry(),),
        "governance_action_references": ("action-001",),
        "policy_versions": (("admission", "1.0.0"),),
    }
    values.update(overrides)
    return RegistrySnapshot(**values)  # type: ignore[arg-type]


def _rejection(**overrides: object) -> GovernanceRejection:
    values: dict[str, object] = {
        "reason_code": "UNKNOWN_IDENTITY",
        "affected_references": ("producer-001",),
        "diagnostic_details": (("field", "producer_identity"),),
    }
    values.update(overrides)
    return GovernanceRejection(**values)  # type: ignore[arg-type]


def test_public_inventory_is_exactly_the_approved_increment() -> None:
    from epip import governance

    assert set(governance.__all__) == {
        "AdmissionRequest",
        "CertificationProfile",
        "CertificationRecord",
        "CompatibilityDecision",
        "GovernanceAction",
        "GovernanceEpoch",
        "GovernanceFactReference",
        "GovernanceManifest",
        "GovernanceRejection",
        "RegistryEntry",
        "RegistrySnapshot",
    }


def test_all_models_are_frozen_value_objects_with_deterministic_equality() -> None:
    models = (
        _epoch(),
        _action(),
        _fact_reference(),
        _manifest(),
        _admission(),
        _profile(),
        _certification(),
        _compatibility(),
        _entry(),
        _snapshot(),
        _rejection(),
    )
    equal_models = (
        _epoch(),
        _action(),
        _fact_reference(),
        _manifest(),
        _admission(),
        _profile(),
        _certification(),
        _compatibility(),
        _entry(),
        _snapshot(),
        _rejection(),
    )

    assert models == equal_models
    assert tuple(hash(model) for model in models) == tuple(hash(model) for model in equal_models)
    for model in models:
        with pytest.raises((FrozenInstanceError, TypeError)):
            setattr(model, next(iter(model.__dataclass_fields__)), "changed")


@pytest.mark.parametrize(
    ("factory", "overrides"),
    (
        (_epoch, {"sequence": -1}),
        (_epoch, {"sequence": True}),
        (_action, {"action_identity": ""}),
        (_fact_reference, {"artifact_version": ""}),
        (_manifest, {"manifest_identity": " "}),
        (_admission, {"producer_version": ""}),
        (_profile, {"profile_version": 1}),
        (_certification, {"certification_suite_version": ""}),
        (_compatibility, {"policy_version": None}),
        (_entry, {"owner_identity": ""}),
        (_snapshot, {"snapshot_identity": ""}),
        (_rejection, {"reason_code": ""}),
    ),
)
def test_invalid_identifiers_versions_and_epochs_fail_closed(
    factory: Callable[..., object], overrides: dict[str, object]
) -> None:
    with pytest.raises(DataIntegrityError):
        factory(**overrides)


@pytest.mark.parametrize(
    ("factory", "overrides"),
    (
        (_action, {"subject_references": []}),
        (_manifest, {"actions": []}),
        (_admission, {"capability_references": []}),
        (_profile, {"required_evidence": []}),
        (_certification, {"privilege_scope": []}),
        (_compatibility, {"version_scope": []}),
        (_entry, {"certification_records": []}),
        (_snapshot, {"entries": []}),
        (_rejection, {"diagnostic_details": []}),
    ),
)
def test_mutable_collections_are_rejected(
    factory: Callable[..., object], overrides: dict[str, object]
) -> None:
    with pytest.raises(DataIntegrityError, match="immutable tuple"):
        factory(**overrides)


@pytest.mark.parametrize(
    ("factory", "overrides"),
    (
        (_action, {"subject_references": ()}),
        (_manifest, {"policy_versions": ()}),
        (_admission, {"schema_versions": ()}),
        (_profile, {"test_classes": ()}),
        (_certification, {"capability_references": ()}),
        (_compatibility, {"evidence_references": ()}),
        (_entry, {"governance_provenance": ()}),
        (_snapshot, {"policy_versions": ()}),
        (_rejection, {"affected_references": ()}),
    ),
)
def test_missing_mandatory_collections_are_rejected(
    factory: Callable[..., object], overrides: dict[str, object]
) -> None:
    with pytest.raises(DataIntegrityError, match="must not be empty"):
        factory(**overrides)


@pytest.mark.parametrize(
    ("factory", "overrides"),
    (
        (_action, {"policy_versions": (("admission", "1"), ("admission", "1"))}),
        (_manifest, {"authority_facts": ("owner", "owner")}),
        (_admission, {"maintainer_identities": ("maintainer", "maintainer")}),
        (_profile, {"failure_criteria": ("failure", "failure")}),
        (_certification, {"schema_versions": (("input", "1"), ("input", "1"))}),
        (_compatibility, {"profile_scope": (("replay", "1"), ("replay", "1"))}),
        (_entry, {"capability_references": (("capability", "1"), ("capability", "1"))}),
        (_snapshot, {"governance_action_references": ("action", "action")}),
        (_rejection, {"affected_references": ("subject", "subject")}),
    ),
)
def test_duplicate_structural_references_are_rejected(
    factory: Callable[..., object], overrides: dict[str, object]
) -> None:
    with pytest.raises(DataIntegrityError, match="duplicates"):
        factory(**overrides)


def test_nested_values_must_use_immutable_supported_models_and_pairs() -> None:
    with pytest.raises(DataIntegrityError, match="immutable pairs"):
        _admission(capability_references=(("capability", "1", "extra"),))
    with pytest.raises(DataIntegrityError, match="unsupported value"):
        _manifest(actions=(object(),))
    with pytest.raises(DataIntegrityError, match="unsupported value"):
        _entry(certification_records=(object(),))
    with pytest.raises(DataIntegrityError, match="unsupported value"):
        _entry(compatibility_decisions=(object(),))
    with pytest.raises(DataIntegrityError, match="unsupported value"):
        _snapshot(entries=(object(),))


def test_optional_relationships_accept_none_but_reject_empty_text() -> None:
    assert _action().prior_standing is None
    assert _certification().status_relationship_reference is None
    assert _compatibility().revocation_reference is None

    with pytest.raises(DataIntegrityError):
        _action(prior_standing="")
    with pytest.raises(DataIntegrityError):
        _action(resulting_snapshot_reference="")
    with pytest.raises(DataIntegrityError):
        _certification(status_relationship_reference="")
    with pytest.raises(DataIntegrityError):
        _compatibility(revocation_reference="")
    with pytest.raises(DataIntegrityError):
        _compatibility(supersession_reference="")


@pytest.mark.parametrize("repeat_count", (0, -1, True, "3"))
def test_certification_repeat_count_is_strictly_structural(repeat_count: object) -> None:
    with pytest.raises(DataIntegrityError):
        _profile(repeat_count=repeat_count)

    assert replace(_profile(), repeat_count=None).repeat_count is None


@pytest.mark.parametrize(
    ("factory", "field"),
    (
        (_action, "effective_epoch"),
        (_manifest, "governance_epoch"),
        (_certification, "effective_epoch"),
        (_compatibility, "effective_epoch"),
        (_snapshot, "governance_epoch"),
    ),
)
def test_epoch_fields_reject_untyped_values(factory: Callable[..., object], field: str) -> None:
    with pytest.raises(DataIntegrityError, match="GovernanceEpoch"):
        factory(**{field: 1})


def test_models_store_no_mutable_collection_or_runtime_collaborator() -> None:
    snapshot = _snapshot()
    manifest = _manifest()

    assert isinstance(snapshot.entries, tuple)
    assert isinstance(snapshot.entries[0].certification_records, tuple)
    assert isinstance(snapshot.entries[0].compatibility_decisions, tuple)
    assert isinstance(manifest.actions, tuple)
    assert not hasattr(snapshot, "save")
    assert not hasattr(snapshot, "publish")
    assert not hasattr(manifest, "derive")
    assert not hasattr(_admission(), "approve")
    assert not hasattr(_certification(), "certify")
    assert not hasattr(_compatibility(), "evaluate")


def test_manifest_schema_is_exact_and_ordered() -> None:
    assert tuple(GovernanceManifest.__dataclass_fields__) == (
        "manifest_schema_version",
        "identity_domain_version",
        "canonicalization_profile_identity",
        "canonicalization_profile_version",
        "digest_profile_identity",
        "digest_profile_version",
        "manifest_identity",
        "governance_epoch",
        "actions",
        "admission_requests",
        "producer_contracts",
        "proposed_registry_entries",
        "certification_profiles",
        "certification_records",
        "compatibility_decisions",
        "fact_references",
        "policy_versions",
        "authority_facts",
    )


def test_fact_reference_schema_is_exact_and_ordered() -> None:
    assert tuple(GovernanceFactReference.__dataclass_fields__) == (
        "identity_domain",
        "artifact_identity",
        "artifact_version",
        "fact_type",
        "relationship_role",
    )


def test_manifest_requires_exactly_one_action_at_its_epoch() -> None:
    with pytest.raises(DataIntegrityError, match="exactly one action"):
        _manifest(actions=())
    with pytest.raises(DataIntegrityError, match="exactly one action"):
        _manifest(actions=(_action(), _action(action_identity="action-002")))
    with pytest.raises(DataIntegrityError, match="action epoch"):
        _manifest(actions=(_action(effective_epoch=GovernanceEpoch(2)),))


def test_manifest_requires_exact_local_fact_references() -> None:
    admission = _admission()
    reference = _fact_reference()

    manifest = _manifest(
        admission_requests=(admission,),
        fact_references=(reference,),
    )
    assert manifest.admission_requests == (admission,)
    assert manifest.fact_references == (reference,)

    with pytest.raises(DataIntegrityError, match="resolve every contained fact exactly"):
        _manifest(admission_requests=(admission,))
    with pytest.raises(DataIntegrityError, match="resolve every contained fact exactly"):
        _manifest(fact_references=(reference,))


def test_manifest_rejects_incorrect_fact_reference_identity_domain() -> None:
    with pytest.raises(DataIntegrityError, match="resolve every contained fact exactly"):
        _manifest(
            admission_requests=(_admission(),),
            fact_references=(_fact_reference(identity_domain="certification"),),
        )


def test_manifest_distinguishes_references_by_relationship_role() -> None:
    references = (
        _fact_reference(),
        _fact_reference(relationship_role="secondary_admission_input"),
    )
    manifest = _manifest(
        admission_requests=(_admission(),),
        fact_references=references,
    )
    assert manifest.fact_references == references


@pytest.mark.parametrize(
    "field",
    (
        "actions",
        "admission_requests",
        "producer_contracts",
        "proposed_registry_entries",
        "certification_profiles",
        "certification_records",
        "compatibility_decisions",
        "fact_references",
    ),
)
def test_manifest_rejects_mutable_model_sections(field: str) -> None:
    with pytest.raises(DataIntegrityError, match="immutable tuple"):
        _manifest(**{field: []})


def test_manifest_rejects_duplicate_typed_facts_and_references() -> None:
    admission = _admission()
    reference = _fact_reference()
    with pytest.raises(DataIntegrityError, match="duplicates"):
        _manifest(admission_requests=(admission, admission))
    with pytest.raises(DataIntegrityError, match="duplicates"):
        _manifest(fact_references=(reference, reference))


def test_manifest_resolves_every_supported_typed_fact_locally() -> None:
    from tests.producer.test_contract import _contract

    admission = _admission()
    contract = _contract()
    entry = _entry()
    profile = _profile()
    certification = _certification()
    compatibility = _compatibility()
    references = (
        _fact_reference(),
        _fact_reference(
            artifact_identity=contract.producer_identity,
            artifact_version=contract.producer_version,
            fact_type="producer_contract",
            relationship_role="producer_contract_input",
        ),
        _fact_reference(
            artifact_identity=entry.producer_identity,
            artifact_version=entry.producer_version,
            fact_type="registry_entry",
            relationship_role="proposed_entry",
        ),
        _fact_reference(
            artifact_identity=profile.profile_identity,
            artifact_version=profile.profile_version,
            fact_type="certification_profile",
            relationship_role="certification_profile_input",
            identity_domain="certification",
        ),
        _fact_reference(
            artifact_identity=certification.record_identity,
            artifact_version=certification.certification_suite_version,
            fact_type="certification_record",
            relationship_role="certification_record_input",
            identity_domain="certification",
        ),
        _fact_reference(
            artifact_identity=compatibility.decision_identity,
            artifact_version=compatibility.policy_version,
            fact_type="compatibility_decision",
            relationship_role="compatibility_input",
            identity_domain="validation",
        ),
    )

    manifest = _manifest(
        admission_requests=(admission,),
        producer_contracts=(contract,),
        proposed_registry_entries=(entry,),
        certification_profiles=(profile,),
        certification_records=(certification,),
        compatibility_decisions=(compatibility,),
        fact_references=references,
    )

    assert manifest.fact_references == references


def test_manifest_requires_all_epoch_bound_facts_to_match_its_epoch() -> None:
    with pytest.raises(DataIntegrityError, match="certification epoch"):
        _manifest(
            certification_records=(_certification(effective_epoch=GovernanceEpoch(2)),),
        )
    with pytest.raises(DataIntegrityError, match="compatibility epoch"):
        _manifest(
            compatibility_decisions=(_compatibility(effective_epoch=GovernanceEpoch(2)),),
        )
