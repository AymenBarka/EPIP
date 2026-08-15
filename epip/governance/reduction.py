"""Manifest-aware immutable A03 governance reduction.

Execution package: Programme A A03-V2-E02.
Governing contracts: ADR-EPIP017-03, ADR-EPIP017-09, and the frozen
A03 Architecture Amendment. This module owns validator dispatch,
acceptance completion, and immutable reduction only.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import NamedTuple, TypeAlias

from epip.governance.model import (
    GovernanceAction,
    GovernanceEpoch,
    GovernanceManifest,
    GovernanceRejection,
    RegistryEntry,
    RegistrySnapshot,
)
from epip.governance.validation import (
    _AdmissionValidator,
    _AuthorityValidator,
    _CertificationValidator,
    _CompatibilityValidator,
    _LifecycleValidator,
    _reject,
    _RevocationValidator,
    _StableReasonCodes,
    _TrustValidator,
    _ValidationAcceptance,
)

_ContextValidator: TypeAlias = Callable[
    [RegistrySnapshot, GovernanceAction, GovernanceManifest, GovernanceEpoch],
    _ValidationAcceptance | GovernanceRejection,
]

_LIFECYCLE_ACTIONS = frozenset({"activated", "lifecycle_transitioned", "disabled", "retired"})
_TRUST_ACTIONS = frozenset(
    {"trust_granted", "trust_reassessed", "trust_suspended", "trust_revoked"}
)
_AUDIT_ONLY_ACTIONS = frozenset(
    {
        "admission_requested",
        "architectural_conformity_confirmed",
        "capability_admitted",
        "structural_admission_rejected",
        "privilege_scope_changed",
        "emergency_suspended",
        "operational_suspension_requested",
    }
)
_ADMISSION_ACTIONS = frozenset({"structural_admission_approved"})
_CERTIFICATION_ACTIONS = frozenset(
    {
        "certification_issued",
        "certification_suspended",
        "certification_expired",
        "certification_revoked",
    }
)
_COMPATIBILITY_ACTIONS = frozenset({"compatibility_approved", "compatibility_revoked"})
_SUPPORTED_ACTIONS = frozenset().union(
    _LIFECYCLE_ACTIONS,
    _TRUST_ACTIONS,
    _AUDIT_ONLY_ACTIONS,
    _ADMISSION_ACTIONS,
    _CERTIFICATION_ACTIONS,
    _COMPATIBILITY_ACTIONS,
)


class _ReductionResult(NamedTuple):
    """Complete immutable E02 result bound to its exact validated inputs."""

    starting_snapshot: RegistrySnapshot
    action: GovernanceAction
    manifest: GovernanceManifest
    epoch: GovernanceEpoch
    validation_acceptances: tuple[_ValidationAcceptance, ...]
    entries: tuple[RegistryEntry, ...]
    governance_action_references: tuple[str, ...]
    policy_versions: tuple[tuple[str, str], ...]
    authority_facts: tuple[str, ...]


class _GovernanceReducer:
    """Validate and reduce one immutable governance operation without state ownership."""

    @staticmethod
    def reduce(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> _ReductionResult | GovernanceRejection:
        """Return one complete immutable reduction result or fail closed."""

        if (
            not isinstance(snapshot, RegistrySnapshot)
            or not isinstance(action, GovernanceAction)
            or not isinstance(manifest, GovernanceManifest)
            or not isinstance(epoch, GovernanceEpoch)
        ):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("governance_reduction",))
        if action.action_type not in _SUPPORTED_ACTIONS:
            return _reject(_StableReasonCodes.UNKNOWN_ACTION, (action.action_identity,))
        if manifest.actions != (action,) or manifest.governance_epoch != epoch:
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (action.action_identity, manifest.manifest_identity),
                (("fact", "complete_reducer_input_binding"),),
            )
        if action.action_identity in snapshot.governance_action_references:
            return _reject(
                _StableReasonCodes.DUPLICATE_OWNERSHIP,
                (action.action_identity,),
                (("fact", "governance_action_reference"),),
            )
        if epoch.sequence <= snapshot.governance_epoch.sequence:
            return _reject(
                _StableReasonCodes.ILLEGAL_LIFECYCLE_TRANSITION,
                (action.action_identity,),
                (("fact", "governance_epoch_order"),),
            )

        validators = _GovernanceReducer._applicable_validator_contracts(action.action_type)
        acceptances: list[_ValidationAcceptance] = []
        for expected_identity, validator in validators:
            outcome = validator(snapshot, action, manifest, epoch)
            if isinstance(outcome, GovernanceRejection):
                return outcome
            if not isinstance(outcome, _ValidationAcceptance):
                return _reject(
                    _StableReasonCodes.INCOMPLETE_DECLARATION,
                    (action.action_identity,),
                    (("fact", "validator_acceptance_completion"),),
                )
            if outcome.validator_identity != expected_identity or (
                outcome.snapshot,
                outcome.action,
                outcome.manifest,
                outcome.epoch,
            ) != (snapshot, action, manifest, epoch):
                return _reject(
                    _StableReasonCodes.INCOMPLETE_DECLARATION,
                    (action.action_identity, outcome.validator_identity),
                    (("fact", "validator_input_binding"),),
                )
            acceptances.append(outcome)
        reduced = _GovernanceReducer._reduce_entries(snapshot, action, manifest)
        if isinstance(reduced, GovernanceRejection):
            return reduced
        return _ReductionResult(
            starting_snapshot=snapshot,
            action=action,
            manifest=manifest,
            epoch=epoch,
            validation_acceptances=tuple(acceptances),
            entries=tuple(
                sorted(reduced, key=lambda entry: (entry.producer_identity, entry.producer_version))
            ),
            governance_action_references=(
                *snapshot.governance_action_references,
                action.action_identity,
            ),
            policy_versions=tuple(
                sorted(set(snapshot.policy_versions) | set(manifest.policy_versions))
            ),
            authority_facts=tuple(sorted(manifest.authority_facts)),
        )

    @staticmethod
    def _applicable_validators(action_type: str) -> tuple[_ContextValidator, ...]:
        """Select the complete validator set in one deterministic order."""

        return tuple(
            validator
            for _, validator in _GovernanceReducer._applicable_validator_contracts(action_type)
        )

    @staticmethod
    def _applicable_validator_contracts(
        action_type: str,
    ) -> tuple[tuple[str, _ContextValidator], ...]:
        """Bind each deterministically selected validator to its acceptance identity."""

        selected: list[tuple[str, _ContextValidator]] = [
            ("authority", _AuthorityValidator.validate_context)
        ]
        if action_type == "admission_requested" or action_type in _ADMISSION_ACTIONS:
            selected.append(("admission", _AdmissionValidator.validate_context))
        if action_type in _CERTIFICATION_ACTIONS:
            selected.append(("certification", _CertificationValidator.validate_context))
        if action_type in _COMPATIBILITY_ACTIONS:
            selected.append(("compatibility", _CompatibilityValidator.validate_context))
        if action_type in _LIFECYCLE_ACTIONS:
            selected.append(("lifecycle", _LifecycleValidator.validate_context))
        if action_type in _TRUST_ACTIONS:
            selected.append(("trust", _TrustValidator.validate_context))
        if action_type in {
            "certification_revoked",
            "compatibility_revoked",
            "disabled",
            "retired",
            "trust_revoked",
        }:
            selected.append(("revocation", _RevocationValidator.validate_context))
        return tuple(selected)

    @staticmethod
    def _reduce_entries(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        manifest: GovernanceManifest,
    ) -> tuple[RegistryEntry, ...] | GovernanceRejection:
        if action.action_type in _ADMISSION_ACTIONS:
            return _GovernanceReducer._reduce_admission(snapshot, action, manifest)
        if action.action_type in _CERTIFICATION_ACTIONS:
            return _GovernanceReducer._reduce_certification(snapshot, manifest)
        if action.action_type in _COMPATIBILITY_ACTIONS:
            return _GovernanceReducer._reduce_compatibility(snapshot, manifest)
        if action.action_type in _LIFECYCLE_ACTIONS:
            return _GovernanceReducer._reduce_standing(snapshot, action, lifecycle=True)
        if action.action_type in _TRUST_ACTIONS:
            return _GovernanceReducer._reduce_standing(snapshot, action, lifecycle=False)
        return snapshot.entries

    @staticmethod
    def _reduce_admission(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        manifest: GovernanceManifest,
    ) -> tuple[RegistryEntry, ...] | GovernanceRejection:
        if len(manifest.proposed_registry_entries) != 1:
            return _reject(
                _StableReasonCodes.MISSING_MANDATORY_FACT,
                (action.action_identity,),
                (("fact", "selected_proposed_registry_entry"),),
            )
        proposed = manifest.proposed_registry_entries[0]
        return (*snapshot.entries, proposed)

    @staticmethod
    def _reduce_certification(
        snapshot: RegistrySnapshot,
        manifest: GovernanceManifest,
    ) -> tuple[RegistryEntry, ...] | GovernanceRejection:
        if len(manifest.certification_records) != 1:
            return _reject(
                _StableReasonCodes.MISSING_MANDATORY_FACT,
                (manifest.manifest_identity,),
                (("fact", "selected_certification_record"),),
            )
        record = manifest.certification_records[0]
        matching = tuple(
            entry
            for entry in snapshot.entries
            if entry.producer_identity == record.producer_identity
        )
        if len(matching) != 1:
            return _reject(
                _StableReasonCodes.INVALID_CERTIFICATION_SCOPE,
                (record.record_identity, record.producer_identity),
            )
        prior = matching[0]
        if record in prior.certification_records:
            return _reject(
                _StableReasonCodes.INVALID_CERTIFICATION_STATE,
                (record.record_identity,),
                (("fact", "exactly_once_certification"),),
            )
        updated = replace(
            prior,
            certification_records=(*prior.certification_records, record),
            governance_provenance=(
                *prior.governance_provenance,
                manifest.actions[0].action_identity,
            ),
        )
        return _GovernanceReducer._replace_entry(snapshot, prior, updated)

    @staticmethod
    def _reduce_compatibility(
        snapshot: RegistrySnapshot,
        manifest: GovernanceManifest,
    ) -> tuple[RegistryEntry, ...] | GovernanceRejection:
        if len(manifest.compatibility_decisions) != 1:
            return _reject(
                _StableReasonCodes.MISSING_MANDATORY_FACT,
                (manifest.manifest_identity,),
                (("fact", "selected_compatibility_decision"),),
            )
        decision = manifest.compatibility_decisions[0]
        matching = tuple(
            entry
            for entry in snapshot.entries
            if decision.source_reference
            in {entry.producer_identity, f"{entry.producer_identity}@{entry.producer_version}"}
        )
        if len(matching) != 1:
            return _reject(
                _StableReasonCodes.UNKNOWN_COMPATIBILITY,
                (decision.decision_identity, decision.source_reference),
            )
        prior = matching[0]
        if decision in prior.compatibility_decisions:
            return _reject(
                _StableReasonCodes.REVOKED_COMPATIBILITY,
                (decision.decision_identity,),
                (("fact", "exactly_once_compatibility"),),
            )
        updated = replace(
            prior,
            compatibility_decisions=(*prior.compatibility_decisions, decision),
            governance_provenance=(
                *prior.governance_provenance,
                manifest.actions[0].action_identity,
            ),
        )
        return _GovernanceReducer._replace_entry(snapshot, prior, updated)

    @staticmethod
    def _reduce_standing(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
        *,
        lifecycle: bool,
    ) -> tuple[RegistryEntry, ...] | GovernanceRejection:
        matching = tuple(
            entry
            for entry in snapshot.entries
            if entry.producer_identity in action.subject_references
        )
        if len(matching) != 1:
            return _reject(
                _StableReasonCodes.INVALID_IDENTITY,
                (action.action_identity,),
                (("fact", "unique_subject_entry"),),
            )
        prior = matching[0]
        updated = replace(
            prior,
            lifecycle_standing=(
                action.resulting_standing if lifecycle else prior.lifecycle_standing
            ),
            trust_standing=(action.resulting_standing if not lifecycle else prior.trust_standing),
            governance_provenance=(*prior.governance_provenance, action.action_identity),
        )
        return _GovernanceReducer._replace_entry(snapshot, prior, updated)

    @staticmethod
    def _replace_entry(
        snapshot: RegistrySnapshot,
        prior: RegistryEntry,
        updated: RegistryEntry,
    ) -> tuple[RegistryEntry, ...]:
        return tuple(updated if entry is prior else entry for entry in snapshot.entries)
