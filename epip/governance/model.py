"""Immutable A03 governance facts without registry or authority behaviour.

Implementation architecture: Programme A A03, Increment 1 and A03-MP-01.
Governing contracts: ADR-EPIP017-01, ADR-EPIP017-02, ADR-EPIP017-03,
ADR-EPIP017-08, ADR-EPIP017-09, ADR-EPIP017-11, and ADR-EPIP017-17.
Responsibility: intrinsic structural integrity of immutable governance facts.
"""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text
from epip.producer import ProducerContract


def _require_identifier(value: object, field: str) -> str:
    """Require an explicit non-empty identifier without interpreting its domain."""

    return require_text(value, field)


def _require_version(value: object, field: str) -> str:
    """Require an explicit non-empty version without imposing a version scheme."""

    return require_text(value, field)


def _require_epoch(value: object, field: str) -> int:
    """Require a non-negative logical epoch and reject booleans."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DataIntegrityError(f"{field} must be a non-negative integer")
    return value


def _require_text_tuple(
    value: object,
    field: str,
    *,
    required: bool = False,
    unique: bool = True,
) -> tuple[str, ...]:
    """Require a tuple of immutable non-empty strings."""

    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field} must be an immutable tuple")
    if required and not value:
        raise MissingFieldError(f"{field} must not be empty")
    for item in value:
        require_text(item, field)
    if unique and len(set(value)) != len(value):
        raise DataIntegrityError(f"{field} must not contain duplicates")
    return value


def _require_pairs(
    value: object,
    field: str,
    *,
    required: bool = False,
) -> tuple[tuple[str, str], ...]:
    """Require an immutable tuple of unique non-empty string pairs."""

    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field} must be an immutable tuple")
    if required and not value:
        raise MissingFieldError(f"{field} must not be empty")
    result: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise DataIntegrityError(f"{field} must contain immutable pairs")
        left, right = item
        require_text(left, field)
        require_text(right, field)
        result.append((left, right))
    if len(set(result)) != len(result):
        raise DataIntegrityError(f"{field} must not contain duplicates")
    return value


def _require_optional_text(value: object, field: str) -> str | None:
    """Validate an optional string without treating an empty string as absence."""

    if value is None:
        return None
    return require_text(value, field)


def _require_model_tuple(
    value: object,
    expected: type[object],
    field: str,
) -> tuple[object, ...]:
    """Require an immutable tuple containing only the expected immutable model."""

    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field} must be an immutable tuple")
    if any(not isinstance(item, expected) for item in value):
        raise DataIntegrityError(f"{field} contains an unsupported value")
    return value


def _require_unique_models(value: tuple[object, ...], field: str) -> None:
    """Reject duplicate immutable model values."""

    if len(set(value)) != len(value):
        raise DataIntegrityError(f"{field} must not contain duplicates")


@dataclass(frozen=True, slots=True)
class GovernanceEpoch:
    """A03 logical governance boundary governed by ADR-EPIP017-03."""

    sequence: int

    def __post_init__(self) -> None:
        """Validate only the intrinsic logical-epoch representation."""

        _require_epoch(self.sequence, "governance_epoch.sequence")


@dataclass(frozen=True, slots=True)
class GovernanceAction:
    """A03 immutable governance fact governed by ADR-EPIP017-03 and ADR-09."""

    action_identity: str
    action_type: str
    authority_identity: str
    authority_role: str
    subject_references: tuple[str, ...]
    prior_standing: str | None
    resulting_standing: str
    policy_versions: tuple[tuple[str, str], ...]
    contract_versions: tuple[tuple[str, str], ...]
    effective_epoch: GovernanceEpoch
    reason_code: str
    evidence_references: tuple[str, ...]
    approval_references: tuple[str, ...]
    separation_attestations: tuple[str, ...]
    relationship_references: tuple[str, ...] = ()
    resulting_snapshot_reference: str | None = None

    def __post_init__(self) -> None:
        """Reject malformed or mutable action facts without authorizing them."""

        for name in (
            "action_identity",
            "action_type",
            "authority_identity",
            "authority_role",
            "resulting_standing",
            "reason_code",
        ):
            _require_identifier(getattr(self, name), f"governance_action.{name}")
        _require_optional_text(self.prior_standing, "governance_action.prior_standing")
        _require_optional_text(
            self.resulting_snapshot_reference,
            "governance_action.resulting_snapshot_reference",
        )
        if not isinstance(self.effective_epoch, GovernanceEpoch):
            raise DataIntegrityError("governance_action.effective_epoch must be GovernanceEpoch")
        _require_text_tuple(
            self.subject_references,
            "governance_action.subject_references",
            required=True,
        )
        _require_pairs(self.policy_versions, "governance_action.policy_versions", required=True)
        _require_pairs(self.contract_versions, "governance_action.contract_versions")
        _require_text_tuple(self.evidence_references, "governance_action.evidence_references")
        _require_text_tuple(self.approval_references, "governance_action.approval_references")
        _require_text_tuple(
            self.separation_attestations,
            "governance_action.separation_attestations",
        )
        _require_text_tuple(
            self.relationship_references,
            "governance_action.relationship_references",
        )


@dataclass(frozen=True, slots=True)
class GovernanceFactReference:
    """A03-MP-01 local fact reference governed by ADR-03 and ADR-09."""

    identity_domain: str
    artifact_identity: str
    artifact_version: str
    fact_type: str
    relationship_role: str

    def __post_init__(self) -> None:
        """Validate the complete canonical reference representation."""

        _require_identifier(self.identity_domain, "governance_fact_reference.identity_domain")
        _require_identifier(
            self.artifact_identity,
            "governance_fact_reference.artifact_identity",
        )
        _require_version(self.artifact_version, "governance_fact_reference.artifact_version")
        _require_identifier(self.fact_type, "governance_fact_reference.fact_type")
        _require_identifier(
            self.relationship_role,
            "governance_fact_reference.relationship_role",
        )


@dataclass(frozen=True, slots=True)
class AdmissionRequest:
    """A03 immutable admission declaration governed by ADR-EPIP017-03."""

    request_identity: str
    producer_identity: str
    producer_version: str
    owner_identity: str
    maintainer_identities: tuple[str, ...]
    producer_contract_version: str
    implementation_identity: str
    capability_references: tuple[tuple[str, str], ...]
    schema_versions: tuple[tuple[str, str], ...]
    profile_references: tuple[tuple[str, str], ...]
    security_classification: str
    requested_privileges: tuple[str, ...]
    external_boundaries: tuple[str, ...]
    certification_profile_reference: str
    evidence_references: tuple[str, ...]
    predecessor_references: tuple[str, ...] = ()
    successor_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate admission declaration structure without deciding admission."""

        for name in (
            "request_identity",
            "producer_identity",
            "owner_identity",
            "implementation_identity",
            "security_classification",
            "certification_profile_reference",
        ):
            _require_identifier(getattr(self, name), f"admission_request.{name}")
        _require_version(self.producer_version, "admission_request.producer_version")
        _require_version(
            self.producer_contract_version,
            "admission_request.producer_contract_version",
        )
        _require_text_tuple(
            self.maintainer_identities,
            "admission_request.maintainer_identities",
        )
        _require_pairs(
            self.capability_references,
            "admission_request.capability_references",
            required=True,
        )
        _require_pairs(
            self.schema_versions,
            "admission_request.schema_versions",
            required=True,
        )
        _require_pairs(
            self.profile_references,
            "admission_request.profile_references",
            required=True,
        )
        _require_text_tuple(
            self.requested_privileges,
            "admission_request.requested_privileges",
        )
        _require_text_tuple(
            self.external_boundaries,
            "admission_request.external_boundaries",
        )
        _require_text_tuple(
            self.evidence_references,
            "admission_request.evidence_references",
            required=True,
        )
        _require_text_tuple(
            self.predecessor_references,
            "admission_request.predecessor_references",
        )
        _require_text_tuple(
            self.successor_references,
            "admission_request.successor_references",
        )


@dataclass(frozen=True, slots=True)
class CertificationProfile:
    """A03 immutable certification requirements governed by ADR-EPIP017-03."""

    profile_identity: str
    profile_version: str
    required_evidence: tuple[str, ...]
    test_classes: tuple[str, ...]
    repeat_count: int | None
    environmental_constraints: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    failure_criteria: tuple[str, ...]
    expiry_rules: tuple[str, ...]
    recertification_triggers: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate certification-profile structure without executing certification."""

        _require_identifier(self.profile_identity, "certification_profile.profile_identity")
        _require_version(self.profile_version, "certification_profile.profile_version")
        if self.repeat_count is not None and (
            isinstance(self.repeat_count, bool)
            or not isinstance(self.repeat_count, int)
            or self.repeat_count < 1
        ):
            raise DataIntegrityError(
                "certification_profile.repeat_count must be a positive integer or None"
            )
        for name in (
            "required_evidence",
            "test_classes",
            "environmental_constraints",
            "acceptance_criteria",
            "failure_criteria",
            "expiry_rules",
            "recertification_triggers",
        ):
            _require_text_tuple(
                getattr(self, name),
                f"certification_profile.{name}",
                required=True,
            )


@dataclass(frozen=True, slots=True)
class CertificationRecord:
    """A03 immutable certification verdict governed by ADR-EPIP017-03."""

    record_identity: str
    certification_authority_identity: str
    producer_identity: str
    producer_version: str
    implementation_identity: str
    producer_contract_version: str
    capability_references: tuple[tuple[str, str], ...]
    configuration_profile: str
    schema_versions: tuple[tuple[str, str], ...]
    temporal_profile: str
    determinism_profile: str
    replay_profile: str
    execution_profile: str
    isolation_profile: str
    resource_profile: str
    privilege_scope: tuple[str, ...]
    certification_profile_reference: str
    certification_suite_version: str
    evidence_references: tuple[str, ...]
    verdict: str
    effective_epoch: GovernanceEpoch
    expiration_or_review_condition: str
    status_relationship_reference: str | None = None

    def __post_init__(self) -> None:
        """Validate record structure without issuing or interpreting a verdict."""

        for name in (
            "record_identity",
            "certification_authority_identity",
            "producer_identity",
            "implementation_identity",
            "configuration_profile",
            "temporal_profile",
            "determinism_profile",
            "replay_profile",
            "execution_profile",
            "isolation_profile",
            "resource_profile",
            "certification_profile_reference",
            "verdict",
            "expiration_or_review_condition",
        ):
            _require_identifier(getattr(self, name), f"certification_record.{name}")
        for name in (
            "producer_version",
            "producer_contract_version",
            "certification_suite_version",
        ):
            _require_version(getattr(self, name), f"certification_record.{name}")
        _require_optional_text(
            self.status_relationship_reference,
            "certification_record.status_relationship_reference",
        )
        if not isinstance(self.effective_epoch, GovernanceEpoch):
            raise DataIntegrityError("certification_record.effective_epoch must be GovernanceEpoch")
        _require_pairs(
            self.capability_references,
            "certification_record.capability_references",
            required=True,
        )
        _require_pairs(
            self.schema_versions,
            "certification_record.schema_versions",
            required=True,
        )
        _require_text_tuple(
            self.privilege_scope,
            "certification_record.privilege_scope",
        )
        _require_text_tuple(
            self.evidence_references,
            "certification_record.evidence_references",
            required=True,
        )


@dataclass(frozen=True, slots=True)
class CompatibilityDecision:
    """A03 immutable directional compatibility fact governed by ADR-EPIP017-03."""

    decision_identity: str
    compatibility_authority_identity: str
    source_reference: str
    target_reference: str
    compatibility_dimension: str
    direction: str
    intended_use: str
    version_scope: tuple[tuple[str, str], ...]
    profile_scope: tuple[tuple[str, str], ...]
    evidence_references: tuple[str, ...]
    policy_version: str
    effective_epoch: GovernanceEpoch
    review_or_expiry_condition: str
    revocation_reference: str | None = None
    supersession_reference: str | None = None

    def __post_init__(self) -> None:
        """Validate compatibility fact structure without inferring compatibility."""

        for name in (
            "decision_identity",
            "compatibility_authority_identity",
            "source_reference",
            "target_reference",
            "compatibility_dimension",
            "direction",
            "intended_use",
            "review_or_expiry_condition",
        ):
            _require_identifier(getattr(self, name), f"compatibility_decision.{name}")
        _require_version(self.policy_version, "compatibility_decision.policy_version")
        _require_optional_text(
            self.revocation_reference,
            "compatibility_decision.revocation_reference",
        )
        _require_optional_text(
            self.supersession_reference,
            "compatibility_decision.supersession_reference",
        )
        if not isinstance(self.effective_epoch, GovernanceEpoch):
            raise DataIntegrityError(
                "compatibility_decision.effective_epoch must be GovernanceEpoch"
            )
        _require_pairs(
            self.version_scope,
            "compatibility_decision.version_scope",
            required=True,
        )
        _require_pairs(
            self.profile_scope,
            "compatibility_decision.profile_scope",
            required=True,
        )
        _require_text_tuple(
            self.evidence_references,
            "compatibility_decision.evidence_references",
            required=True,
        )


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    """A03 immutable producer governance view governed by ADR-EPIP017-03."""

    producer_identity: str
    producer_version: str
    descriptor_reference: str
    owner_identity: str
    producer_contract_version: str
    implementation_identity: str
    capability_references: tuple[tuple[str, str], ...]
    trust_standing: str
    certification_records: tuple[CertificationRecord, ...]
    compatibility_decisions: tuple[CompatibilityDecision, ...]
    lifecycle_standing: str
    governance_provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate entry structure without deriving eligibility or lifecycle."""

        for name in (
            "producer_identity",
            "descriptor_reference",
            "owner_identity",
            "implementation_identity",
            "trust_standing",
            "lifecycle_standing",
        ):
            _require_identifier(getattr(self, name), f"registry_entry.{name}")
        _require_version(self.producer_version, "registry_entry.producer_version")
        _require_version(
            self.producer_contract_version,
            "registry_entry.producer_contract_version",
        )
        _require_pairs(
            self.capability_references,
            "registry_entry.capability_references",
            required=True,
        )
        _require_model_tuple(
            self.certification_records,
            CertificationRecord,
            "registry_entry.certification_records",
        )
        _require_model_tuple(
            self.compatibility_decisions,
            CompatibilityDecision,
            "registry_entry.compatibility_decisions",
        )
        _require_text_tuple(
            self.governance_provenance,
            "registry_entry.governance_provenance",
            required=True,
        )


@dataclass(frozen=True, slots=True)
class GovernanceManifest:
    """A03-MP-01 operation input governed by ADR-03 and ADR-09."""

    manifest_schema_version: str
    identity_domain_version: str
    canonicalization_profile_identity: str
    canonicalization_profile_version: str
    digest_profile_identity: str
    digest_profile_version: str
    manifest_identity: str
    governance_epoch: GovernanceEpoch
    actions: tuple[GovernanceAction, ...]
    admission_requests: tuple[AdmissionRequest, ...]
    producer_contracts: tuple[ProducerContract, ...]
    proposed_registry_entries: tuple[RegistryEntry, ...]
    certification_profiles: tuple[CertificationProfile, ...]
    certification_records: tuple[CertificationRecord, ...]
    compatibility_decisions: tuple[CompatibilityDecision, ...]
    fact_references: tuple[GovernanceFactReference, ...]
    policy_versions: tuple[tuple[str, str], ...]
    authority_facts: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate only the frozen manifest schema and intrinsic structure."""

        for name in (
            "manifest_schema_version",
            "identity_domain_version",
            "canonicalization_profile_version",
            "digest_profile_version",
        ):
            _require_version(getattr(self, name), f"governance_manifest.{name}")
        for name in (
            "canonicalization_profile_identity",
            "digest_profile_identity",
            "manifest_identity",
        ):
            _require_identifier(getattr(self, name), f"governance_manifest.{name}")
        if not isinstance(self.governance_epoch, GovernanceEpoch):
            raise DataIntegrityError("governance_manifest.governance_epoch must be GovernanceEpoch")

        sections: tuple[tuple[str, object, type[object]], ...] = (
            ("actions", self.actions, GovernanceAction),
            ("admission_requests", self.admission_requests, AdmissionRequest),
            ("producer_contracts", self.producer_contracts, ProducerContract),
            ("proposed_registry_entries", self.proposed_registry_entries, RegistryEntry),
            ("certification_profiles", self.certification_profiles, CertificationProfile),
            ("certification_records", self.certification_records, CertificationRecord),
            ("compatibility_decisions", self.compatibility_decisions, CompatibilityDecision),
            ("fact_references", self.fact_references, GovernanceFactReference),
        )
        for name, values, expected in sections:
            models = _require_model_tuple(values, expected, f"governance_manifest.{name}")
            _require_unique_models(models, f"governance_manifest.{name}")

        if len(self.actions) != 1:
            raise DataIntegrityError("governance_manifest.actions must contain exactly one action")
        if self.actions[0].effective_epoch != self.governance_epoch:
            raise DataIntegrityError("governance_manifest action epoch must match manifest epoch")
        for record in self.certification_records:
            if record.effective_epoch != self.governance_epoch:
                raise DataIntegrityError(
                    "governance_manifest certification epoch must match manifest epoch"
                )
        for decision in self.compatibility_decisions:
            if decision.effective_epoch != self.governance_epoch:
                raise DataIntegrityError(
                    "governance_manifest compatibility epoch must match manifest epoch"
                )

        _require_pairs(self.policy_versions, "governance_manifest.policy_versions", required=True)
        _require_text_tuple(
            self.authority_facts,
            "governance_manifest.authority_facts",
            required=True,
        )
        self._validate_local_fact_references()

    def _validate_local_fact_references(self) -> None:
        """Require one exact local reference for every contained typed fact."""

        facts = (
            *(_fact_coordinates(value) for value in self.admission_requests),
            *(_fact_coordinates(value) for value in self.producer_contracts),
            *(_fact_coordinates(value) for value in self.proposed_registry_entries),
            *(_fact_coordinates(value) for value in self.certification_profiles),
            *(_fact_coordinates(value) for value in self.certification_records),
            *(_fact_coordinates(value) for value in self.compatibility_decisions),
        )
        reference_coordinates = tuple(
            (
                reference.identity_domain,
                reference.artifact_identity,
                reference.artifact_version,
                reference.fact_type,
                reference.relationship_role,
            )
            for reference in self.fact_references
        )
        if len(set(reference_coordinates)) != len(reference_coordinates):
            raise DataIntegrityError("governance_manifest.fact_references must resolve uniquely")
        reference_targets = {
            (identity_domain, artifact_identity, artifact_version, fact_type)
            for (
                identity_domain,
                artifact_identity,
                artifact_version,
                fact_type,
                _,
            ) in reference_coordinates
        }
        if set(facts) != reference_targets:
            raise DataIntegrityError(
                "governance_manifest.fact_references must resolve every contained fact exactly"
            )


def _fact_coordinates(value: object) -> tuple[str, str, str, str]:
    """Return the complete local domain, identity, version, and fact-type key."""

    if isinstance(value, AdmissionRequest):
        return "producer", value.request_identity, value.producer_version, "admission_request"
    if isinstance(value, ProducerContract):
        return "producer", value.producer_identity, value.producer_version, "producer_contract"
    if isinstance(value, RegistryEntry):
        return "producer", value.producer_identity, value.producer_version, "registry_entry"
    if isinstance(value, CertificationProfile):
        return (
            "certification",
            value.profile_identity,
            value.profile_version,
            "certification_profile",
        )
    if isinstance(value, CertificationRecord):
        return (
            "certification",
            value.record_identity,
            value.certification_suite_version,
            "certification_record",
        )
    if isinstance(value, CompatibilityDecision):
        return (
            "validation",
            value.decision_identity,
            value.policy_version,
            "compatibility_decision",
        )
    raise DataIntegrityError("governance_manifest contains an unsupported fact")


@dataclass(frozen=True, slots=True)
class RegistrySnapshot:
    """A03 immutable registry view governed by ADR-EPIP017-03 and ADR-09."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    entries: tuple[RegistryEntry, ...]
    governance_action_references: tuple[str, ...]
    policy_versions: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        """Validate snapshot structure without deriving or publishing it."""

        _require_identifier(self.snapshot_identity, "registry_snapshot.snapshot_identity")
        _require_identifier(self.manifest_reference, "registry_snapshot.manifest_reference")
        if not isinstance(self.governance_epoch, GovernanceEpoch):
            raise DataIntegrityError("registry_snapshot.governance_epoch must be GovernanceEpoch")
        _require_model_tuple(self.entries, RegistryEntry, "registry_snapshot.entries")
        _require_text_tuple(
            self.governance_action_references,
            "registry_snapshot.governance_action_references",
        )
        _require_pairs(
            self.policy_versions,
            "registry_snapshot.policy_versions",
            required=True,
        )


@dataclass(frozen=True, slots=True)
class GovernanceRejection:
    """A03 immutable fail-closed rejection fact governed by ADR-EPIP017-03."""

    reason_code: str
    affected_references: tuple[str, ...]
    diagnostic_details: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate deterministic rejection data without remediation behaviour."""

        _require_identifier(self.reason_code, "governance_rejection.reason_code")
        _require_text_tuple(
            self.affected_references,
            "governance_rejection.affected_references",
            required=True,
        )
        _require_pairs(
            self.diagnostic_details,
            "governance_rejection.diagnostic_details",
        )
