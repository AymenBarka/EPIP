"""Deterministic A03 registry snapshot construction.

Implementation architecture: Programme A A03, Increment 4.
Governing contracts: ADR-EPIP017-03 and ADR-EPIP017-09.
This module constructs immutable snapshots only; it performs no governance
validation, reduction, persistence, publication, coordination, or projection.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from hashlib import sha256
from typing import TypeAlias

from epip.governance.model import (
    GovernanceEpoch,
    GovernanceManifest,
    GovernanceRejection,
    RegistryEntry,
    RegistrySnapshot,
)
from epip.governance.validation import _reject, _StableReasonCodes

_CanonicalScalar: TypeAlias = str | int | bool | None
_CanonicalValue: TypeAlias = _CanonicalScalar | list["_CanonicalValue"]
_SNAPSHOT_IDENTITY_DOMAIN = "registry-snapshot"
_SNAPSHOT_DOMAIN_VERSION = "1"
_SNAPSHOT_SCHEMA_VERSION = "1"
_CANONICALIZATION_PROFILE = "epip-json-v1"
_DIGEST_PROFILE = "sha256-v1"


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
        _canonical_value(tuple(sorted(manifest.authority_facts))),
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
        entries: tuple[RegistryEntry, ...],
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> RegistrySnapshot | GovernanceRejection:
        """Return one reproducible snapshot or deterministic fail-closed rejection."""

        if (
            not isinstance(entries, tuple)
            or any(not isinstance(entry, RegistryEntry) for entry in entries)
            or not isinstance(manifest, GovernanceManifest)
            or not isinstance(epoch, GovernanceEpoch)
        ):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("snapshot_construction",))

        entry_keys = tuple((entry.producer_identity, entry.producer_version) for entry in entries)
        if len(entry_keys) != len(set(entry_keys)):
            return _reject(
                _StableReasonCodes.DUPLICATE_OWNERSHIP,
                (manifest.manifest_identity,),
                (("fact", "duplicate_registry_entry_identity"),),
            )

        action_keys = tuple(action.action_identity for action in manifest.actions)
        if len(action_keys) != len(set(action_keys)):
            return _reject(
                _StableReasonCodes.INVALID_IDENTITY,
                (manifest.manifest_identity,),
                (("fact", "duplicate_governance_action_identity"),),
            )

        if manifest.governance_epoch != epoch or any(
            action.effective_epoch.sequence > epoch.sequence for action in manifest.actions
        ):
            return _reject(
                _StableReasonCodes.ILLEGAL_LIFECYCLE_TRANSITION,
                (manifest.manifest_identity,),
                (("fact", "governance_epoch_mismatch"),),
            )

        manifest_policies = frozenset(manifest.policy_versions)
        authority_facts = frozenset(manifest.authority_facts)
        if any(
            not set(action.policy_versions) <= manifest_policies
            or f"{action.authority_identity}:{action.authority_role}" not in authority_facts
            for action in manifest.actions
        ):
            return _reject(
                _StableReasonCodes.INCOMPLETE_DECLARATION,
                (manifest.manifest_identity,),
                (("fact", "inconsistent_governance_manifest"),),
            )

        canonical_entries = tuple(
            sorted(entries, key=lambda item: (item.producer_identity, item.producer_version))
        )
        canonical_actions = tuple(
            sorted(
                manifest.actions,
                key=lambda item: (item.effective_epoch.sequence, item.action_identity),
            )
        )
        action_references = tuple(action.action_identity for action in canonical_actions)
        policies = tuple(sorted(manifest.policy_versions))
        return RegistrySnapshot(
            snapshot_identity=_snapshot_identity(
                canonical_entries,
                manifest,
                epoch,
                action_references,
                policies,
            ),
            manifest_reference=manifest.manifest_identity,
            governance_epoch=epoch,
            entries=canonical_entries,
            governance_action_references=action_references,
            policy_versions=policies,
        )
