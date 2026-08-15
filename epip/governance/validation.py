"""Pure stateless A03 governance validators.

Implementation architecture: Programme A A03, Increment 2.
Governing contracts: ADR-EPIP017-01, ADR-EPIP017-02, ADR-EPIP017-03.
This module performs validation only; it owns no authority or state.
"""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import NamedTuple

from epip.governance.model import (
    AdmissionRequest,
    CertificationProfile,
    CertificationRecord,
    CompatibilityDecision,
    GovernanceAction,
    GovernanceEpoch,
    GovernanceManifest,
    GovernanceRejection,
    RegistryEntry,
    RegistrySnapshot,
)
from epip.producer import ProducerContract


class _StableReasonCodes(str, Enum):
    """Stable machine-readable A03 rejection identifiers."""

    INVALID_MODEL = "GOV_INVALID_MODEL"
    MISSING_MANDATORY_FACT = "GOV_MISSING_MANDATORY_FACT"
    INCOMPLETE_DECLARATION = "GOV_INCOMPLETE_DECLARATION"
    INVALID_IDENTITY = "GOV_INVALID_IDENTITY"
    DUPLICATE_OWNERSHIP = "GOV_DUPLICATE_OWNERSHIP"
    UNAUTHORIZED_AUTHORITY = "GOV_UNAUTHORIZED_AUTHORITY"
    UNKNOWN_ACTION = "GOV_UNKNOWN_ACTION"
    INVALID_CERTIFICATION_SCOPE = "GOV_INVALID_CERTIFICATION_SCOPE"
    INVALID_CERTIFICATION_VERSION = "GOV_INVALID_CERTIFICATION_VERSION"
    MISSING_CERTIFICATION_PROFILE = "GOV_MISSING_CERTIFICATION_PROFILE"
    INVALID_CERTIFICATION_STATE = "GOV_INVALID_CERTIFICATION_STATE"
    MISSING_COMPATIBILITY_DIRECTION = "GOV_MISSING_COMPATIBILITY_DIRECTION"
    INVALID_COMPATIBILITY_ENDPOINT = "GOV_INVALID_COMPATIBILITY_ENDPOINT"
    REVOKED_COMPATIBILITY = "GOV_REVOKED_COMPATIBILITY"
    UNKNOWN_COMPATIBILITY = "GOV_UNKNOWN_COMPATIBILITY"
    ILLEGAL_LIFECYCLE_TRANSITION = "GOV_ILLEGAL_LIFECYCLE_TRANSITION"
    RETIRED_IS_TERMINAL = "GOV_RETIRED_IS_TERMINAL"
    INVALID_ACTIVATION = "GOV_INVALID_ACTIVATION"
    INVALID_TRUST_TRANSITION = "GOV_INVALID_TRUST_TRANSITION"
    INVALID_TRUST_SCOPE = "GOV_INVALID_TRUST_SCOPE"
    DUPLICATE_REVOCATION = "GOV_DUPLICATE_REVOCATION"
    ALREADY_REVOKED_SCOPE = "GOV_ALREADY_REVOKED_SCOPE"
    INVALID_REVOCATION_AUTHORITY = "GOV_INVALID_REVOCATION_AUTHORITY"


_ACTION_AUTHORITIES = MappingProxyType(
    {
        "admission_requested": frozenset({"producer_owner", "maintainer"}),
        "architectural_conformity_confirmed": frozenset({"architectural_authority"}),
        "capability_admitted": frozenset({"architectural_authority"}),
        "structural_admission_approved": frozenset({"registry_authority"}),
        "structural_admission_rejected": frozenset({"registry_authority"}),
        "activated": frozenset({"registry_authority"}),
        "lifecycle_transitioned": frozenset({"registry_authority"}),
        "disabled": frozenset({"registry_authority"}),
        "retired": frozenset({"registry_authority"}),
        "snapshot_published": frozenset({"registry_authority"}),
        "certification_issued": frozenset({"certification_authority"}),
        "certification_suspended": frozenset({"certification_authority"}),
        "certification_expired": frozenset({"certification_authority"}),
        "certification_revoked": frozenset({"certification_authority"}),
        "trust_granted": frozenset({"security_authority"}),
        "trust_reassessed": frozenset({"security_authority"}),
        "trust_suspended": frozenset({"security_authority"}),
        "trust_revoked": frozenset({"security_authority"}),
        "privilege_scope_changed": frozenset({"security_authority"}),
        "emergency_suspended": frozenset({"security_authority"}),
        "compatibility_approved": frozenset({"compatibility_authority"}),
        "compatibility_revoked": frozenset({"compatibility_authority"}),
        "operational_suspension_requested": frozenset({"operational_authority"}),
    }
)

_LIFECYCLE_TRANSITIONS = MappingProxyType(
    {
        "Declared": frozenset({"Declared", "Registered"}),
        "Registered": frozenset({"Registered", "Certified", "Disabled"}),
        "Certified": frozenset({"Enabled", "Disabled"}),
        "Enabled": frozenset({"Deprecated", "Disabled"}),
        "Deprecated": frozenset({"Enabled", "Disabled", "Retired"}),
        "Disabled": frozenset({"Registered", "Certified", "Retired"}),
        "Retired": frozenset(),
    }
)

_TRUST_TRANSITIONS = MappingProxyType(
    {
        "Untrusted": frozenset({"Experimental", "Trusted"}),
        "Experimental": frozenset({"Trusted", "Untrusted", "Revoked"}),
        "Trusted": frozenset({"Untrusted", "Revoked"}),
        "Revoked": frozenset(),
    }
)

_REQUIRED_SCHEMA_FACTS = frozenset({"input", "output", "context", "failure", "diagnostic"})
_REQUIRED_PROFILE_FACTS = frozenset({"execution", "resource", "isolation", "determinism", "replay"})
_CERTIFICATION_VERDICTS = frozenset({"passed", "failed", "suspended", "expired", "revoked"})
_CERTIFIABLE_STATES = frozenset({"Registered", "Certified"})


def _reject(
    code: _StableReasonCodes,
    references: tuple[str, ...],
    details: tuple[tuple[str, str], ...] = (),
) -> GovernanceRejection:
    """Create one deterministic immutable rejection fact."""

    return GovernanceRejection(code.value, references, details)


class _ValidationAcceptance(NamedTuple):
    """Bind one explicit validator acceptance to the exact immutable inputs."""

    validator_identity: str
    snapshot: RegistrySnapshot
    action: GovernanceAction
    manifest: GovernanceManifest
    epoch: GovernanceEpoch


def _accept(
    validator_identity: str,
    snapshot: RegistrySnapshot,
    action: GovernanceAction,
    manifest: GovernanceManifest,
    epoch: GovernanceEpoch,
) -> _ValidationAcceptance:
    """Return one immutable deterministic acceptance for exact validated values."""

    return _ValidationAcceptance(validator_identity, snapshot, action, manifest, epoch)


def _invalid_context(
    snapshot: object,
    action: object,
    manifest: object,
    epoch: object,
    validator_identity: str,
) -> GovernanceRejection | None:
    """Reject context values that are not the required immutable A03 models."""

    if not isinstance(snapshot, RegistrySnapshot):
        return _reject(_StableReasonCodes.INVALID_MODEL, (validator_identity, "snapshot"))
    if not isinstance(action, GovernanceAction):
        return _reject(_StableReasonCodes.INVALID_MODEL, (validator_identity, "action"))
    if not isinstance(manifest, GovernanceManifest):
        return _reject(_StableReasonCodes.INVALID_MODEL, (validator_identity, "manifest"))
    if not isinstance(epoch, GovernanceEpoch):
        return _reject(_StableReasonCodes.INVALID_MODEL, (validator_identity, "epoch"))
    return None


def _entry_for_subject(
    snapshot: RegistrySnapshot,
    action: GovernanceAction,
) -> RegistryEntry | GovernanceRejection:
    """Resolve exactly one selected registry entry without external lookup."""

    matching = tuple(
        entry for entry in snapshot.entries if entry.producer_identity in action.subject_references
    )
    if len(matching) != 1:
        return _reject(
            _StableReasonCodes.INVALID_IDENTITY,
            (action.action_identity, *action.subject_references),
            (("fact", "selected_registry_entry"),),
        )
    return matching[0]


def _validate_fact_references(
    manifest: GovernanceManifest,
    expected: tuple[tuple[str, str, str], ...],
    action_identity: str,
) -> GovernanceRejection | None:
    """Validate semantic selection through complete canonical fact references."""

    actual = tuple(
        (reference.artifact_identity, reference.fact_type, reference.relationship_role)
        for reference in manifest.fact_references
    )
    if actual != expected:
        return _reject(
            _StableReasonCodes.INCOMPLETE_DECLARATION,
            (action_identity, manifest.manifest_identity),
            (("fact", "canonical_fact_selection"),),
        )
    return None


class _AdmissionValidator:
    """Validate immutable admission declarations without deciding admission."""

    @staticmethod
    def validate(
        request: AdmissionRequest,
        producer_contract: ProducerContract,
        existing_entries: tuple[RegistryEntry, ...] = (),
    ) -> GovernanceRejection | None:
        """Return a structural admission rejection or deterministic acceptance."""

        if not isinstance(request, AdmissionRequest) or not isinstance(
            producer_contract, ProducerContract
        ):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("admission",))
        if not isinstance(existing_entries, tuple) or any(
            not isinstance(entry, RegistryEntry) for entry in existing_entries
        ):
            return _reject(_StableReasonCodes.INVALID_MODEL, (request.request_identity,))
        expected = (
            producer_contract.producer_identity,
            producer_contract.producer_version,
            producer_contract.owner,
            producer_contract.contract_version,
            producer_contract.implementation_identity,
        )
        actual = (
            request.producer_identity,
            request.producer_version,
            request.owner_identity,
            request.producer_contract_version,
            request.implementation_identity,
        )
        if actual != expected:
            return _reject(
                _StableReasonCodes.INVALID_IDENTITY,
                (request.request_identity, request.producer_identity),
            )
        declared_schemas = frozenset(name for name, _ in request.schema_versions)
        declared_profiles = frozenset(name for name, _ in request.profile_references)
        if not _REQUIRED_SCHEMA_FACTS <= declared_schemas:
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (request.request_identity,),
                (("fact", "schema_versions"),),
            )
        if not _REQUIRED_PROFILE_FACTS <= declared_profiles:
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (request.request_identity,),
                (("fact", "profile_references"),),
            )
        matching = tuple(
            entry
            for entry in existing_entries
            if (entry.producer_identity, entry.producer_version)
            == (request.producer_identity, request.producer_version)
        )
        if len({entry.owner_identity for entry in matching} | {request.owner_identity}) > 1:
            return _reject(
                _StableReasonCodes.DUPLICATE_OWNERSHIP,
                (request.producer_identity, request.producer_version),
            )
        if matching:
            return _reject(
                _StableReasonCodes.DUPLICATE_OWNERSHIP,
                (request.producer_identity, request.producer_version),
            )
        return None

    @staticmethod
    def validate_context(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> _ValidationAcceptance | GovernanceRejection:
        """Validate admission semantics using only exact immutable operation facts."""

        invalid = _invalid_context(snapshot, action, manifest, epoch, "admission")
        if invalid is not None:
            return invalid
        if action.action_type not in {
            "admission_requested",
            "structural_admission_approved",
        }:
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity,),
                (("fact", "admission_action"),),
            )
        if len(manifest.admission_requests) != 1 or len(manifest.producer_contracts) != 1:
            return _reject(
                _StableReasonCodes.MISSING_MANDATORY_FACT,
                (action.action_identity,),
                (("fact", "admission_request_and_producer_contract"),),
            )
        request = manifest.admission_requests[0]
        contract = manifest.producer_contracts[0]
        if action.action_type == "structural_admission_approved":
            return _AdmissionValidator._validate_structural_admission(
                snapshot,
                action,
                manifest,
                epoch,
                request,
                contract,
            )
        if not {
            request.request_identity,
            request.producer_identity,
        }.intersection(action.subject_references):
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity, request.request_identity),
                (("fact", "action_to_admission_request"),),
            )
        reference_rejection = _validate_fact_references(
            manifest,
            (
                (request.request_identity, "admission_request", "admission_input"),
                (
                    contract.producer_identity,
                    "producer_contract",
                    "producer_contract_input",
                ),
            ),
            action.action_identity,
        )
        if reference_rejection is not None:
            return reference_rejection
        rejection = _AdmissionValidator.validate(request, contract, snapshot.entries)
        if rejection is not None:
            return rejection
        return _accept("admission", snapshot, action, manifest, epoch)

    @staticmethod
    def _validate_structural_admission(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
        request: AdmissionRequest,
        contract: ProducerContract,
    ) -> _ValidationAcceptance | GovernanceRejection:
        """Validate one explicit Registry Authority structural-admission decision."""

        if len(manifest.proposed_registry_entries) != 1:
            return _reject(
                _StableReasonCodes.MISSING_MANDATORY_FACT,
                (action.action_identity,),
                (("fact", "proposed_registry_entry"),),
            )
        proposed = manifest.proposed_registry_entries[0]
        if proposed.producer_identity not in action.subject_references:
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity, proposed.producer_identity),
                (("fact", "action_to_proposed_entry"),),
            )
        reference_rejection = _validate_fact_references(
            manifest,
            (
                (request.request_identity, "admission_request", "admission_input"),
                (
                    contract.producer_identity,
                    "producer_contract",
                    "producer_contract_input",
                ),
                (proposed.producer_identity, "registry_entry", "proposed_entry"),
            ),
            action.action_identity,
        )
        if reference_rejection is not None:
            return reference_rejection

        rejection = _AdmissionValidator.validate(request, contract, snapshot.entries)
        if rejection is not None:
            return rejection
        if (
            proposed.producer_identity,
            proposed.producer_version,
            proposed.owner_identity,
            proposed.producer_contract_version,
            proposed.implementation_identity,
            proposed.capability_references,
        ) != (
            request.producer_identity,
            request.producer_version,
            request.owner_identity,
            request.producer_contract_version,
            request.implementation_identity,
            request.capability_references,
        ):
            return _reject(
                _StableReasonCodes.INVALID_IDENTITY,
                (action.action_identity, proposed.producer_identity),
                (("fact", "proposed_entry_correspondence"),),
            )
        if (
            proposed.lifecycle_standing != "Registered"
            or proposed.trust_standing != "Untrusted"
            or proposed.certification_records
            or proposed.compatibility_decisions
        ):
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity, proposed.producer_identity),
                (("fact", "structural_admission_scope"),),
            )

        registry_authority_fact = f"{action.authority_identity}:registry_authority"
        owner_fact = f"{request.owner_identity}:producer_owner"
        architectural_facts = tuple(
            fact for fact in manifest.authority_facts if fact.endswith(":architectural_authority")
        )
        if (
            action.authority_role != "registry_authority"
            or registry_authority_fact not in manifest.authority_facts
        ):
            return _reject(
                _StableReasonCodes.UNAUTHORIZED_AUTHORITY,
                (action.action_identity, action.authority_identity),
                (("fact", "registry_authority_scope"),),
            )
        if (
            len(architectural_facts) != 1
            or architectural_facts[0] not in action.approval_references
        ):
            return _reject(
                _StableReasonCodes.MISSING_MANDATORY_FACT,
                (action.action_identity,),
                (("fact", "architectural_conformity"),),
            )
        if owner_fact not in manifest.authority_facts:
            return _reject(
                _StableReasonCodes.DUPLICATE_OWNERSHIP,
                (request.producer_identity, request.producer_version),
                (("fact", "authoritative_owner"),),
            )
        authority_identities = {
            action.authority_identity,
            request.owner_identity,
            architectural_facts[0].removesuffix(":architectural_authority"),
        }
        if len(authority_identities) != 3:
            return _reject(
                _StableReasonCodes.UNAUTHORIZED_AUTHORITY,
                (action.action_identity,),
                (("fact", "authority_separation"),),
            )
        if (
            action.effective_epoch != epoch
            or manifest.governance_epoch != epoch
            or snapshot.governance_epoch.sequence >= epoch.sequence
        ):
            return _reject(
                _StableReasonCodes.ILLEGAL_LIFECYCLE_TRANSITION,
                (action.action_identity, manifest.manifest_identity),
                (("fact", "governance_epoch"),),
            )
        if not set(action.policy_versions) <= set(manifest.policy_versions) or not set(
            action.policy_versions
        ) <= set(snapshot.policy_versions):
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity, manifest.manifest_identity),
                (("fact", "policy_versions"),),
            )
        return _accept("admission", snapshot, action, manifest, epoch)


class _AuthorityValidator:
    """Validate explicit action ownership without exercising authority."""

    @staticmethod
    def validate(action: GovernanceAction) -> GovernanceRejection | None:
        """Reject unknown actions and cross-authority submissions."""

        if not isinstance(action, GovernanceAction):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("authority",))
        permitted = _ACTION_AUTHORITIES.get(action.action_type)
        if permitted is None:
            return _reject(_StableReasonCodes.UNKNOWN_ACTION, (action.action_identity,))
        if action.authority_role not in permitted:
            return _reject(
                _StableReasonCodes.UNAUTHORIZED_AUTHORITY,
                (action.action_identity, action.authority_identity),
            )
        return None

    @staticmethod
    def validate_context(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> _ValidationAcceptance | GovernanceRejection:
        """Validate exact authority, snapshot, policy, action, and epoch binding."""

        invalid = _invalid_context(snapshot, action, manifest, epoch, "authority")
        if invalid is not None:
            return invalid
        if manifest.actions != (action,):
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity, manifest.manifest_identity),
                (("fact", "selected_manifest_action"),),
            )
        if (
            action.effective_epoch != epoch
            or manifest.governance_epoch != epoch
            or snapshot.governance_epoch.sequence > epoch.sequence
        ):
            return _reject(
                _StableReasonCodes.ILLEGAL_LIFECYCLE_TRANSITION,
                (action.action_identity, manifest.manifest_identity),
                (("fact", "governance_epoch"),),
            )
        if not set(action.policy_versions) <= set(manifest.policy_versions) or not set(
            action.policy_versions
        ) <= set(snapshot.policy_versions):
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity, manifest.manifest_identity),
                (("fact", "policy_versions"),),
            )
        authority_fact = f"{action.authority_identity}:{action.authority_role}"
        if authority_fact not in manifest.authority_facts:
            return _reject(
                _StableReasonCodes.UNAUTHORIZED_AUTHORITY,
                (action.action_identity, action.authority_identity),
            )
        permitted = _ACTION_AUTHORITIES.get(action.action_type)
        if permitted is not None and action.authority_role not in permitted:
            return _reject(
                _StableReasonCodes.UNAUTHORIZED_AUTHORITY,
                (action.action_identity, action.authority_identity),
            )
        return _accept("authority", snapshot, action, manifest, epoch)


class _CertificationValidator:
    """Validate certification facts without executing or issuing certification."""

    @staticmethod
    def validate(
        record: CertificationRecord,
        profile: CertificationProfile | None,
        entry: RegistryEntry,
    ) -> GovernanceRejection | None:
        """Validate exact certification scope, versions, profile, and state."""

        if not isinstance(record, CertificationRecord) or not isinstance(entry, RegistryEntry):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("certification",))
        if profile is None:
            return _reject(
                _StableReasonCodes.MISSING_CERTIFICATION_PROFILE,
                (record.record_identity,),
            )
        if not isinstance(profile, CertificationProfile):
            return _reject(_StableReasonCodes.INVALID_MODEL, (record.record_identity,))
        if record.certification_profile_reference not in {
            profile.profile_identity,
            f"{profile.profile_identity}@{profile.profile_version}",
        }:
            return _reject(
                _StableReasonCodes.MISSING_CERTIFICATION_PROFILE,
                (record.record_identity, record.certification_profile_reference),
            )
        if (
            record.producer_identity,
            record.implementation_identity,
            record.capability_references,
        ) != (
            entry.producer_identity,
            entry.implementation_identity,
            entry.capability_references,
        ):
            return _reject(
                _StableReasonCodes.INVALID_CERTIFICATION_SCOPE,
                (record.record_identity, entry.producer_identity),
            )
        if (record.producer_version, record.producer_contract_version) != (
            entry.producer_version,
            entry.producer_contract_version,
        ):
            return _reject(
                _StableReasonCodes.INVALID_CERTIFICATION_VERSION,
                (record.record_identity, entry.producer_identity),
            )
        if record.verdict not in _CERTIFICATION_VERDICTS or entry.lifecycle_standing not in (
            _CERTIFIABLE_STATES
        ):
            return _reject(
                _StableReasonCodes.INVALID_CERTIFICATION_STATE,
                (record.record_identity, entry.lifecycle_standing),
            )
        return None

    @staticmethod
    def validate_context(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> _ValidationAcceptance | GovernanceRejection:
        """Validate selected certification facts against authoritative state."""

        invalid = _invalid_context(snapshot, action, manifest, epoch, "certification")
        if invalid is not None:
            return invalid
        if not action.action_type.startswith("certification_"):
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity,),
                (("fact", "certification_action"),),
            )
        if len(manifest.certification_records) != 1:
            return _reject(
                _StableReasonCodes.MISSING_MANDATORY_FACT,
                (action.action_identity,),
                (("fact", "certification_record"),),
            )
        record = manifest.certification_records[0]
        if record.record_identity not in action.subject_references:
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity, record.record_identity),
                (("fact", "action_to_certification_record"),),
            )
        matching_entries = tuple(
            entry
            for entry in snapshot.entries
            if entry.producer_identity == record.producer_identity
        )
        if len(matching_entries) != 1:
            return _reject(
                _StableReasonCodes.INVALID_CERTIFICATION_SCOPE,
                (record.record_identity, record.producer_identity),
            )
        profiles = tuple(
            profile
            for profile in manifest.certification_profiles
            if record.certification_profile_reference
            in {
                profile.profile_identity,
                f"{profile.profile_identity}@{profile.profile_version}",
            }
        )
        profile = profiles[0] if len(profiles) == 1 else None
        if profile is not None:
            reference_rejection = _validate_fact_references(
                manifest,
                (
                    (
                        profile.profile_identity,
                        "certification_profile",
                        "certification_profile_input",
                    ),
                    (
                        record.record_identity,
                        "certification_record",
                        "certification_record_input",
                    ),
                ),
                action.action_identity,
            )
            if reference_rejection is not None:
                return reference_rejection
        rejection = _CertificationValidator.validate(record, profile, matching_entries[0])
        if rejection is not None:
            return rejection
        expected_verdicts = {
            "certification_issued": frozenset({"passed", "failed"}),
            "certification_suspended": frozenset({"suspended"}),
            "certification_expired": frozenset({"expired"}),
            "certification_revoked": frozenset({"revoked"}),
        }
        expected_verdict = expected_verdicts.get(action.action_type)
        if expected_verdict is None or record.verdict not in expected_verdict:
            return _reject(
                _StableReasonCodes.INVALID_CERTIFICATION_STATE,
                (record.record_identity, action.action_identity),
            )
        known_records = {
            existing.record_identity
            for entry in snapshot.entries
            for existing in entry.certification_records
        }
        if action.action_type == "certification_issued":
            if record.record_identity in known_records or record.status_relationship_reference:
                return _reject(
                    _StableReasonCodes.INVALID_CERTIFICATION_STATE,
                    (record.record_identity,),
                )
        elif record.status_relationship_reference not in known_records:
            return _reject(
                _StableReasonCodes.INVALID_CERTIFICATION_STATE,
                (record.record_identity,),
                (("fact", "prior_certification_record"),),
            )
        return _accept("certification", snapshot, action, manifest, epoch)


class _CompatibilityValidator:
    """Validate explicit compatibility facts without inferring compatibility."""

    @staticmethod
    def validate(
        decision: CompatibilityDecision,
        known_references: tuple[str, ...],
        revoked_decision_references: tuple[str, ...] = (),
    ) -> GovernanceRejection | None:
        """Validate direction, endpoints, revocation, and known scope."""

        if (
            not isinstance(decision, CompatibilityDecision)
            or not isinstance(known_references, tuple)
            or not isinstance(revoked_decision_references, tuple)
        ):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("compatibility",))
        if decision.direction.casefold() in {"unknown", "unspecified", "none"}:
            return _reject(
                _StableReasonCodes.MISSING_COMPATIBILITY_DIRECTION,
                (decision.decision_identity,),
            )
        if decision.source_reference == decision.target_reference:
            return _reject(
                _StableReasonCodes.INVALID_COMPATIBILITY_ENDPOINT,
                (decision.source_reference,),
            )
        if decision.decision_identity in revoked_decision_references:
            return _reject(
                _StableReasonCodes.REVOKED_COMPATIBILITY,
                (decision.decision_identity,),
            )
        if not {decision.source_reference, decision.target_reference} <= set(known_references):
            return _reject(
                _StableReasonCodes.UNKNOWN_COMPATIBILITY,
                (decision.source_reference, decision.target_reference),
            )
        return None

    @staticmethod
    def validate_context(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> _ValidationAcceptance | GovernanceRejection:
        """Validate one selected directional compatibility fact."""

        invalid = _invalid_context(snapshot, action, manifest, epoch, "compatibility")
        if invalid is not None:
            return invalid
        if not action.action_type.startswith("compatibility_"):
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity,),
                (("fact", "compatibility_action"),),
            )
        if len(manifest.compatibility_decisions) != 1:
            return _reject(
                _StableReasonCodes.MISSING_MANDATORY_FACT,
                (action.action_identity,),
                (("fact", "compatibility_decision"),),
            )
        decision = manifest.compatibility_decisions[0]
        if decision.decision_identity not in action.subject_references:
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity, decision.decision_identity),
                (("fact", "action_to_compatibility_decision"),),
            )
        reference_rejection = _validate_fact_references(
            manifest,
            (
                (
                    decision.decision_identity,
                    "compatibility_decision",
                    "compatibility_input",
                ),
            ),
            action.action_identity,
        )
        if reference_rejection is not None:
            return reference_rejection
        known_references = tuple(
            reference
            for entry in snapshot.entries
            for reference in (
                entry.producer_identity,
                f"{entry.producer_identity}@{entry.producer_version}",
            )
        )
        revoked = tuple(
            existing.decision_identity
            for entry in snapshot.entries
            for existing in entry.compatibility_decisions
            if existing.revocation_reference is not None
        )
        rejection = _CompatibilityValidator.validate(decision, known_references, revoked)
        if rejection is not None:
            return rejection
        known_decisions = {
            existing.decision_identity
            for entry in snapshot.entries
            for existing in entry.compatibility_decisions
        }
        if action.action_type == "compatibility_approved":
            if decision.decision_identity in known_decisions or decision.revocation_reference:
                return _reject(
                    _StableReasonCodes.REVOKED_COMPATIBILITY,
                    (decision.decision_identity,),
                )
        elif decision.revocation_reference not in known_decisions:
            return _reject(
                _StableReasonCodes.UNKNOWN_COMPATIBILITY,
                (decision.decision_identity,),
                (("fact", "prior_compatibility_decision"),),
            )
        return _accept("compatibility", snapshot, action, manifest, epoch)


class _LifecycleValidator:
    """Validate ADR-02 administrative transitions without applying them."""

    @staticmethod
    def validate(
        entry: RegistryEntry,
        target_standing: str,
        *,
        certification_valid: bool = False,
        trusted: bool = False,
        compatibility_valid: bool = False,
        remediation_approved: bool = False,
        recertification_approved: bool = False,
    ) -> GovernanceRejection | None:
        """Reject illegal, terminal, or incompletely governed transitions."""

        if not isinstance(entry, RegistryEntry) or not isinstance(target_standing, str):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("lifecycle",))
        current = entry.lifecycle_standing
        permitted = _LIFECYCLE_TRANSITIONS.get(current)
        if permitted is None or target_standing not in permitted:
            code = (
                _StableReasonCodes.RETIRED_IS_TERMINAL
                if current == "Retired"
                else _StableReasonCodes.ILLEGAL_LIFECYCLE_TRANSITION
            )
            return _reject(code, (entry.producer_identity, current, target_standing))
        if target_standing == "Enabled" and not (
            certification_valid and trusted and compatibility_valid
        ):
            return _reject(
                _StableReasonCodes.INVALID_ACTIVATION,
                (entry.producer_identity, target_standing),
            )
        if (
            current == "Deprecated"
            and target_standing == "Enabled"
            and not recertification_approved
        ):
            return _reject(
                _StableReasonCodes.INVALID_ACTIVATION,
                (entry.producer_identity, target_standing),
            )
        if (
            current == "Disabled"
            and target_standing in {"Registered", "Certified"}
            and not (remediation_approved)
        ):
            return _reject(
                _StableReasonCodes.ILLEGAL_LIFECYCLE_TRANSITION,
                (entry.producer_identity, current, target_standing),
            )
        return None

    @staticmethod
    def validate_context(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> _ValidationAcceptance | GovernanceRejection:
        """Validate one selected lifecycle transition from authoritative facts."""

        invalid = _invalid_context(snapshot, action, manifest, epoch, "lifecycle")
        if invalid is not None:
            return invalid
        selected = _entry_for_subject(snapshot, action)
        if isinstance(selected, GovernanceRejection):
            return selected
        if action.prior_standing != selected.lifecycle_standing:
            return _reject(
                _StableReasonCodes.ILLEGAL_LIFECYCLE_TRANSITION,
                (action.action_identity, selected.lifecycle_standing),
            )
        certification_valid = any(
            record.verdict == "passed" for record in selected.certification_records
        )
        trusted = selected.trust_standing == "Trusted"
        compatibility_valid = any(
            decision.revocation_reference is None for decision in selected.compatibility_decisions
        )
        remediation_approved = bool(action.approval_references)
        recertification_approved = bool(
            manifest.certification_records and action.approval_references
        )
        rejection = _LifecycleValidator.validate(
            selected,
            action.resulting_standing,
            certification_valid=certification_valid,
            trusted=trusted,
            compatibility_valid=compatibility_valid,
            remediation_approved=remediation_approved,
            recertification_approved=recertification_approved,
        )
        if rejection is not None:
            return rejection
        return _accept("lifecycle", snapshot, action, manifest, epoch)


class _TrustValidator:
    """Validate scoped trust transitions without granting trust."""

    @staticmethod
    def validate(
        action: GovernanceAction,
        current_standing: str,
        certification_evidence_references: tuple[str, ...] = (),
    ) -> GovernanceRejection | None:
        """Reject unauthorized, unscoped, or illegal trust transitions."""

        if not isinstance(action, GovernanceAction) or not isinstance(
            certification_evidence_references, tuple
        ):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("trust",))
        if action.authority_role != "security_authority":
            return _reject(
                _StableReasonCodes.UNAUTHORIZED_AUTHORITY,
                (action.action_identity, action.authority_identity),
            )
        if len(action.subject_references) < 2:
            return _reject(
                _StableReasonCodes.INVALID_TRUST_SCOPE,
                (action.action_identity,),
            )
        permitted = _TRUST_TRANSITIONS.get(current_standing)
        if permitted is None or action.resulting_standing not in permitted:
            return _reject(
                _StableReasonCodes.INVALID_TRUST_TRANSITION,
                (action.action_identity, current_standing, action.resulting_standing),
            )
        if (
            current_standing == "Experimental"
            and action.resulting_standing == "Trusted"
            and not certification_evidence_references
        ):
            return _reject(
                _StableReasonCodes.MISSING_MANDATORY_FACT,
                (action.action_identity,),
                (("fact", "certification_evidence"),),
            )
        return None

    @staticmethod
    def validate_context(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> _ValidationAcceptance | GovernanceRejection:
        """Validate one selected trust transition from immutable operation facts."""

        invalid = _invalid_context(snapshot, action, manifest, epoch, "trust")
        if invalid is not None:
            return invalid
        selected = _entry_for_subject(snapshot, action)
        if isinstance(selected, GovernanceRejection):
            return selected
        if action.prior_standing != selected.trust_standing:
            return _reject(
                _StableReasonCodes.INVALID_TRUST_TRANSITION,
                (action.action_identity, selected.trust_standing),
            )
        evidence = tuple(
            reference
            for record in manifest.certification_records
            for reference in record.evidence_references
        )
        rejection = _TrustValidator.validate(action, selected.trust_standing, evidence)
        if rejection is not None:
            return rejection
        return _accept("trust", snapshot, action, manifest, epoch)


class _RevocationValidator:
    """Validate scoped revocation facts without applying revocation."""

    @staticmethod
    def validate(
        action: GovernanceAction,
        existing_revocation_references: tuple[str, ...] = (),
        revoked_scope_references: tuple[str, ...] = (),
    ) -> GovernanceRejection | None:
        """Reject duplicate, already-effective, or unauthorized revocations."""

        if (
            not isinstance(action, GovernanceAction)
            or not isinstance(existing_revocation_references, tuple)
            or not isinstance(revoked_scope_references, tuple)
        ):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("revocation",))
        expected_roles = {
            "trust_revoked": "security_authority",
            "certification_revoked": "certification_authority",
            "compatibility_revoked": "compatibility_authority",
            "disabled": "registry_authority",
            "retired": "registry_authority",
        }
        expected = expected_roles.get(action.action_type)
        if expected is None or action.authority_role != expected:
            return _reject(
                _StableReasonCodes.INVALID_REVOCATION_AUTHORITY,
                (action.action_identity, action.authority_identity),
            )
        if action.action_identity in existing_revocation_references:
            return _reject(
                _StableReasonCodes.DUPLICATE_REVOCATION,
                (action.action_identity,),
            )
        overlap = tuple(
            reference
            for reference in action.subject_references
            if reference in revoked_scope_references
        )
        if overlap:
            return _reject(_StableReasonCodes.ALREADY_REVOKED_SCOPE, overlap)
        return None

    @staticmethod
    def validate_context(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> _ValidationAcceptance | GovernanceRejection:
        """Validate one selected revocation against immutable authoritative history."""

        invalid = _invalid_context(snapshot, action, manifest, epoch, "revocation")
        if invalid is not None:
            return invalid
        existing_revocations = tuple(
            reference
            for entry in snapshot.entries
            for reference in entry.governance_provenance
            if reference == action.action_identity
        )
        revoked_scope = tuple(
            reference
            for entry in snapshot.entries
            if entry.trust_standing == "Revoked" or entry.lifecycle_standing == "Retired"
            for reference in (entry.producer_identity,)
        )
        revoked_scope += tuple(
            record.record_identity
            for entry in snapshot.entries
            for record in entry.certification_records
            if record.verdict == "revoked"
        )
        revoked_scope += tuple(
            decision.decision_identity
            for entry in snapshot.entries
            for decision in entry.compatibility_decisions
            if decision.revocation_reference is not None
        )
        rejection = _RevocationValidator.validate(
            action,
            existing_revocations,
            revoked_scope,
        )
        if rejection is not None:
            return rejection
        return _accept("revocation", snapshot, action, manifest, epoch)
