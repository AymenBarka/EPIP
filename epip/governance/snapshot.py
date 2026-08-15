"""Reduction-result-aware deterministic A03 candidate construction.

Execution package: Programme A A03-V2-E03.
Governing contracts: ADR-EPIP017-03, ADR-EPIP017-08, ADR-EPIP017-09,
and the frozen A03 Architecture Amendment.
This module constructs immutable snapshots only; it performs no governance
validation, reduction, persistence, publication, coordination, or projection.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from hashlib import sha256
from typing import TypeAlias

from epip.governance.model import (
    GovernanceAction,
    GovernanceEpoch,
    GovernanceManifest,
    GovernanceRejection,
    RegistryEntry,
    RegistrySnapshot,
)
from epip.governance.reduction import _ReductionResult
from epip.governance.validation import _reject, _StableReasonCodes, _ValidationAcceptance

_CanonicalScalar: TypeAlias = str | int | bool | None
_CanonicalValue: TypeAlias = _CanonicalScalar | list["_CanonicalValue"]
_SNAPSHOT_IDENTITY_DOMAIN = "registry-snapshot"
_SNAPSHOT_DOMAIN_VERSION = "1"
_SNAPSHOT_SCHEMA_VERSION = "1"
_CANONICALIZATION_PROFILE = "epip-json-v1"
_DIGEST_PROFILE = "sha256-v1"
_MANIFEST_SCHEMA_VERSION = "1.0.0"
_IDENTITY_DOMAIN_VERSION = "1.0.0"
_MANIFEST_CANONICALIZATION_PROFILE = ("governance-manifest", "1.0.0")
_MANIFEST_DIGEST_PROFILE = ("governance-manifest", "1.0.0")


def _canonical_value(value: object) -> _CanonicalValue:
    """Project frozen model content into deterministic primitive content."""

    if value is None or isinstance(value, str | int | bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return [
            [field.name, _canonical_value(getattr(value, field.name))] for field in fields(value)
        ]
    raise TypeError("unsupported canonical snapshot value")


def _snapshot_identity(
    entries: tuple[RegistryEntry, ...],
    manifest: GovernanceManifest,
    epoch: GovernanceEpoch,
    action_references: tuple[str, ...],
    policies: tuple[tuple[str, str], ...],
    authority_facts: tuple[str, ...],
) -> str:
    """Derive one domain-qualified identity from canonical immutable facts."""

    content: _CanonicalValue = [
        _SNAPSHOT_IDENTITY_DOMAIN,
        _SNAPSHOT_DOMAIN_VERSION,
        _SNAPSHOT_SCHEMA_VERSION,
        _CANONICALIZATION_PROFILE,
        _DIGEST_PROFILE,
        manifest.manifest_identity,
        epoch.sequence,
        _canonical_value(entries),
        _canonical_value(action_references),
        _canonical_value(policies),
        _canonical_value(authority_facts),
    ]
    encoded = json.dumps(content, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    digest = sha256(encoded).hexdigest()
    return (
        f"{_SNAPSHOT_IDENTITY_DOMAIN}:{_SNAPSHOT_DOMAIN_VERSION}:"
        f"{_SNAPSHOT_SCHEMA_VERSION}:{_CANONICALIZATION_PROFILE}:"
        f"{_DIGEST_PROFILE}:{digest}"
    )


class _SnapshotBuilder:
    """Build one canonical immutable registry snapshot without publishing it."""

    @staticmethod
    def build(
        reduction: _ReductionResult,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> RegistrySnapshot | GovernanceRejection:
        """Return one reproducible snapshot or deterministic fail-closed rejection."""

        if (
            not isinstance(reduction, _ReductionResult)
            or not isinstance(manifest, GovernanceManifest)
            or not isinstance(epoch, GovernanceEpoch)
        ):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("snapshot_construction",))

        if (
            reduction.manifest != manifest
            or reduction.epoch != epoch
            or reduction.action != manifest.actions[0]
            or manifest.governance_epoch != epoch
        ):
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (manifest.manifest_identity,),
                (("fact", "reduction_manifest_epoch_binding"),),
            )

        if (
            not isinstance(reduction.starting_snapshot, RegistrySnapshot)
            or not isinstance(reduction.action, GovernanceAction)
            or not isinstance(reduction.manifest, GovernanceManifest)
            or not isinstance(reduction.epoch, GovernanceEpoch)
            or not isinstance(reduction.validation_acceptances, tuple)
            or any(
                not isinstance(acceptance, _ValidationAcceptance)
                for acceptance in reduction.validation_acceptances
            )
            or not isinstance(reduction.entries, tuple)
            or any(not isinstance(entry, RegistryEntry) for entry in reduction.entries)
            or not isinstance(reduction.governance_action_references, tuple)
            or any(
                not isinstance(reference, str) or not reference
                for reference in reduction.governance_action_references
            )
            or not isinstance(reduction.policy_versions, tuple)
            or any(
                not isinstance(policy, tuple)
                or len(policy) != 2
                or any(not isinstance(value, str) or not value for value in policy)
                for policy in reduction.policy_versions
            )
            or not isinstance(reduction.authority_facts, tuple)
            or any(not isinstance(fact, str) or not fact for fact in reduction.authority_facts)
        ):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("snapshot_construction",))

        entry_keys = tuple(
            (entry.producer_identity, entry.producer_version) for entry in reduction.entries
        )
        if len(entry_keys) != len(set(entry_keys)):
            return _reject(
                _StableReasonCodes.DUPLICATE_OWNERSHIP,
                (manifest.manifest_identity,),
                (("fact", "duplicate_registry_entry_identity"),),
            )

        if len(reduction.governance_action_references) != len(
            set(reduction.governance_action_references)
        ):
            return _reject(
                _StableReasonCodes.INVALID_IDENTITY,
                (manifest.manifest_identity,),
                (("fact", "duplicate_governance_action_identity"),),
            )

        if (
            reduction.starting_snapshot.governance_epoch.sequence >= epoch.sequence
            or reduction.governance_action_references
            != (
                *reduction.starting_snapshot.governance_action_references,
                reduction.action.action_identity,
            )
        ):
            return _reject(
                _StableReasonCodes.ILLEGAL_LIFECYCLE_TRANSITION,
                (manifest.manifest_identity,),
                (("fact", "governance_epoch_mismatch"),),
            )

        if (
            manifest.manifest_schema_version != _MANIFEST_SCHEMA_VERSION
            or manifest.identity_domain_version != _IDENTITY_DOMAIN_VERSION
            or (
                manifest.canonicalization_profile_identity,
                manifest.canonicalization_profile_version,
            )
            != _MANIFEST_CANONICALIZATION_PROFILE
            or (manifest.digest_profile_identity, manifest.digest_profile_version)
            != _MANIFEST_DIGEST_PROFILE
        ):
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (manifest.manifest_identity,),
                (("fact", "inconsistent_governance_manifest"),),
            )

        canonical_entries = tuple(
            sorted(
                reduction.entries,
                key=lambda item: (item.producer_identity, item.producer_version),
            )
        )
        action_references = reduction.governance_action_references
        policies = tuple(sorted(reduction.policy_versions))
        authority_facts = tuple(sorted(reduction.authority_facts))
        return RegistrySnapshot(
            snapshot_identity=_snapshot_identity(
                canonical_entries,
                manifest,
                epoch,
                action_references,
                policies,
                authority_facts,
            ),
            manifest_reference=manifest.manifest_identity,
            governance_epoch=epoch,
            entries=canonical_entries,
            governance_action_references=action_references,
            policy_versions=policies,
        )
