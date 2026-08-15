"""Pure A03 governance reduction over immutable snapshot facts.

Implementation architecture: Programme A A03, Increment 3.
Governing contracts: ADR-EPIP017-01, ADR-EPIP017-02, ADR-EPIP017-03,
and ADR-EPIP017-09. This module owns no registry, storage, publication,
coordination, eligibility projection, or identifier-generation behaviour.
"""

from __future__ import annotations

from dataclasses import replace

from epip.governance.model import (
    GovernanceAction,
    GovernanceRejection,
    RegistryEntry,
    RegistrySnapshot,
)
from epip.governance.validation import (
    _AuthorityValidator,
    _LifecycleValidator,
    _reject,
    _RevocationValidator,
    _StableReasonCodes,
    _TrustValidator,
)

_LIFECYCLE_ACTIONS = frozenset({"activated", "lifecycle_transitioned", "disabled", "retired"})
_TRUST_ACTIONS = frozenset(
    {"trust_granted", "trust_reassessed", "trust_suspended", "trust_revoked"}
)
_AUDIT_ONLY_ACTIONS = frozenset(
    {
        "admission_requested",
        "architectural_conformity_confirmed",
        "capability_admitted",
        "structural_admission_approved",
        "structural_admission_rejected",
        "privilege_scope_changed",
        "emergency_suspended",
        "operational_suspension_requested",
    }
)
_FACT_BEARING_ACTIONS = frozenset(
    {
        "certification_issued",
        "certification_suspended",
        "certification_expired",
        "certification_revoked",
        "compatibility_approved",
        "compatibility_revoked",
    }
)


class _GovernanceReducer:
    """Reduce one immutable governance action without owning registry state."""

    @staticmethod
    def reduce(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
    ) -> RegistrySnapshot | GovernanceRejection:
        """Return a new snapshot or one deterministic fail-closed rejection."""

        if not isinstance(snapshot, RegistrySnapshot) or not isinstance(action, GovernanceAction):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("governance_reduction",))

        authority_rejection = _AuthorityValidator.validate(action)
        if authority_rejection is not None:
            return authority_rejection
        precondition_rejection = _GovernanceReducer._validate_reduction_preconditions(
            snapshot, action
        )
        if precondition_rejection is not None:
            return precondition_rejection

        entries = snapshot.entries
        if action.action_type in _LIFECYCLE_ACTIONS:
            reduced = _GovernanceReducer._reduce_lifecycle(snapshot, action)
            if isinstance(reduced, GovernanceRejection):
                return reduced
            entries = reduced
        elif action.action_type in _TRUST_ACTIONS:
            reduced = _GovernanceReducer._reduce_trust(snapshot, action)
            if isinstance(reduced, GovernanceRejection):
                return reduced
            entries = reduced
        elif action.action_type in _FACT_BEARING_ACTIONS:
            return _GovernanceReducer._reject_unavailable_fact(snapshot, action)
        elif action.action_type in _AUDIT_ONLY_ACTIONS:
            ownership_rejection = _GovernanceReducer._validate_ownership(snapshot, action)
            if ownership_rejection is not None:
                return ownership_rejection
        else:
            return _reject(_StableReasonCodes.UNKNOWN_ACTION, (action.action_identity,))

        assert action.resulting_snapshot_reference is not None
        return RegistrySnapshot(
            snapshot_identity=action.resulting_snapshot_reference,
            manifest_reference=snapshot.manifest_reference,
            governance_epoch=action.effective_epoch,
            entries=tuple(
                sorted(entries, key=lambda item: (item.producer_identity, item.producer_version))
            ),
            governance_action_references=(
                *snapshot.governance_action_references,
                action.action_identity,
            ),
            policy_versions=tuple(
                sorted(set(snapshot.policy_versions) | set(action.policy_versions))
            ),
        )

    @staticmethod
    def _validate_reduction_preconditions(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
    ) -> GovernanceRejection | None:
        if action.resulting_snapshot_reference is None:
            return _reject(
                _StableReasonCodes.MISSING_MANDATORY_FACT,
                (action.action_identity,),
                (("fact", "resulting_snapshot_reference"),),
            )
        if action.action_identity in snapshot.governance_action_references:
            return _reject(
                _StableReasonCodes.DUPLICATE_OWNERSHIP,
                (action.action_identity,),
                (("fact", "governance_action_reference"),),
            )
        if action.effective_epoch.sequence <= snapshot.governance_epoch.sequence:
            return _reject(
                _StableReasonCodes.ILLEGAL_LIFECYCLE_TRANSITION,
                (action.action_identity,),
                (("fact", "governance_epoch_order"),),
            )
        return None

    @staticmethod
    def _subject_entry(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
    ) -> RegistryEntry | GovernanceRejection:
        matches = tuple(
            entry
            for entry in snapshot.entries
            if entry.producer_identity in action.subject_references
        )
        if len(matches) != 1:
            return _reject(
                _StableReasonCodes.INVALID_IDENTITY,
                (action.action_identity,),
                (("fact", "unique_subject_entry"),),
            )
        return matches[0]

    @staticmethod
    def _replace_entry(
        snapshot: RegistrySnapshot,
        prior: RegistryEntry,
        updated: RegistryEntry,
    ) -> tuple[RegistryEntry, ...]:
        return tuple(updated if entry is prior else entry for entry in snapshot.entries)

    @staticmethod
    def _reduce_lifecycle(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
    ) -> tuple[RegistryEntry, ...] | GovernanceRejection:
        entry = _GovernanceReducer._subject_entry(snapshot, action)
        if isinstance(entry, GovernanceRejection):
            return entry
        if action.prior_standing != entry.lifecycle_standing:
            return _reject(
                _StableReasonCodes.ILLEGAL_LIFECYCLE_TRANSITION,
                (action.action_identity, entry.producer_identity),
            )
        if action.action_type in {"disabled", "retired"}:
            revocation_rejection = _RevocationValidator.validate(action)
            assert revocation_rejection is None
        lifecycle_rejection = _LifecycleValidator.validate(
            entry,
            action.resulting_standing,
            certification_valid=any(
                record.verdict == "passed" for record in entry.certification_records
            ),
            trusted=entry.trust_standing == "Trusted",
            compatibility_valid=any(
                decision.revocation_reference is None for decision in entry.compatibility_decisions
            ),
            remediation_approved=bool(action.approval_references),
            recertification_approved=bool(action.approval_references),
        )
        if lifecycle_rejection is not None:
            return lifecycle_rejection
        updated = replace(
            entry,
            lifecycle_standing=action.resulting_standing,
            governance_provenance=(*entry.governance_provenance, action.action_identity),
        )
        return _GovernanceReducer._replace_entry(snapshot, entry, updated)

    @staticmethod
    def _reduce_trust(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
    ) -> tuple[RegistryEntry, ...] | GovernanceRejection:
        entry = _GovernanceReducer._subject_entry(snapshot, action)
        if isinstance(entry, GovernanceRejection):
            return entry
        if action.prior_standing != entry.trust_standing:
            return _reject(
                _StableReasonCodes.INVALID_TRUST_TRANSITION,
                (action.action_identity, entry.producer_identity),
            )
        if action.action_type == "trust_revoked":
            revocation_rejection = _RevocationValidator.validate(action)
            assert revocation_rejection is None
        trust_rejection = _TrustValidator.validate(
            action,
            entry.trust_standing,
            action.evidence_references,
        )
        if trust_rejection is not None:
            return trust_rejection
        updated = replace(
            entry,
            trust_standing=action.resulting_standing,
            governance_provenance=(*entry.governance_provenance, action.action_identity),
        )
        return _GovernanceReducer._replace_entry(snapshot, entry, updated)

    @staticmethod
    def _validate_ownership(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
    ) -> GovernanceRejection | None:
        if action.action_type != "admission_requested":
            return None
        matching = tuple(
            entry
            for entry in snapshot.entries
            if entry.producer_identity in action.subject_references
        )
        if any(entry.owner_identity != action.authority_identity for entry in matching):
            return _reject(
                _StableReasonCodes.DUPLICATE_OWNERSHIP,
                (action.action_identity, *tuple(entry.producer_identity for entry in matching)),
            )
        return None

    @staticmethod
    def _reject_unavailable_fact(
        snapshot: RegistrySnapshot,
        action: GovernanceAction,
    ) -> GovernanceRejection:
        if action.action_type.startswith("certification_"):
            known = {
                record.record_identity
                for entry in snapshot.entries
                for record in entry.certification_records
            }
            if known.intersection(action.subject_references):
                return _reject(
                    _StableReasonCodes.INVALID_CERTIFICATION_STATE,
                    (action.action_identity,),
                    (("fact", "duplicate_certification"),),
                )
            fact = "certification_record"
        else:
            fact = "compatibility_decision"
        return _reject(
            _StableReasonCodes.MISSING_MANDATORY_FACT,
            (action.action_identity,),
            (("fact", fact),),
        )
