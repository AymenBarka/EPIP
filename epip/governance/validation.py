"""Pure stateless A03 governance validators.

Implementation architecture: Programme A A03, Increment 2.
Governing contracts: ADR-EPIP017-01, ADR-EPIP017-02, ADR-EPIP017-03.
This module performs validation only; it owns no authority or state.
"""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType

from epip.governance.model import (
    AdmissionRequest,
    CertificationProfile,
    CertificationRecord,
    CompatibilityDecision,
    GovernanceAction,
    GovernanceRejection,
    RegistryEntry,
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
        return None


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
