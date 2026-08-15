"""A03 Increment 7 public GovernanceRegistry façade tests."""

from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

import pytest

from epip.governance.coordinator import _GovernanceCoordinator
from epip.governance.model import (
    GovernanceAction,
    GovernanceEpoch,
    GovernanceManifest,
    GovernanceRejection,
    RegistrySnapshot,
)
from epip.governance.registry import GovernanceRegistry
from tests.governance.test_model import _action, _entry, _manifest, _snapshot


def _operation() -> tuple[GovernanceAction, GovernanceManifest, GovernanceEpoch]:
    epoch = GovernanceEpoch(2)
    action = _action(
        action_identity="action-002",
        action_type="lifecycle_transitioned",
        authority_identity="registry-authority",
        authority_role="registry_authority",
        subject_references=("producer-001",),
        prior_standing="Declared",
        resulting_standing="Registered",
        policy_versions=(("registry", "1.0.0"),),
        effective_epoch=epoch,
        resulting_snapshot_reference="snapshot-reduction-002",
    )
    manifest = _manifest(
        manifest_identity="manifest-002",
        governance_epoch=epoch,
        actions=(action,),
        policy_versions=(("registry", "1.0.0"),),
        authority_facts=("registry-authority:registry_authority",),
    )
    return action, manifest, epoch


def _initial_snapshot() -> RegistrySnapshot:
    return _snapshot(
        entries=(_entry(lifecycle_standing="Declared", trust_standing="Untrusted"),),
    )


def _accepted(result: RegistrySnapshot | GovernanceRejection) -> RegistrySnapshot:
    assert isinstance(result, RegistrySnapshot)
    return result


def _rejection(result: RegistrySnapshot | GovernanceRejection) -> GovernanceRejection:
    assert isinstance(result, GovernanceRejection)
    return result


def test_registry_supports_empty_and_initial_immutable_state() -> None:
    assert GovernanceRegistry().current_snapshot is None
    snapshot = _initial_snapshot()
    registry = GovernanceRegistry(snapshot)
    assert registry.current_snapshot is snapshot
    assert not hasattr(registry, "__dict__")


def test_public_operation_delegates_success_and_updates_snapshot() -> None:
    previous = _initial_snapshot()
    registry = GovernanceRegistry(previous)
    action, manifest, epoch = _operation()
    result = _accepted(registry.apply(action, manifest, epoch))
    assert registry.current_snapshot is result
    assert result is not previous
    assert result.entries[0].lifecycle_standing == "Registered"
    assert result.manifest_reference == manifest.manifest_identity
    with pytest.raises(FrozenInstanceError):
        result.entries = ()  # type: ignore[misc]


def test_public_rejection_is_propagated_unchanged_without_partial_update() -> None:
    previous = _initial_snapshot()
    registry = GovernanceRegistry(previous)
    action, manifest, epoch = _operation()
    invalid = replace(action, authority_role="producer_owner")
    with patch.object(
        _GovernanceCoordinator,
        "coordinate",
        autospec=True,
        return_value=GovernanceRejection(
            "GOV_UNAUTHORIZED_AUTHORITY",
            (action.action_identity,),
        ),
    ) as delegation:
        result = registry.apply(invalid, manifest, epoch)
    rejection = _rejection(result)
    assert rejection.reason_code == "GOV_UNAUTHORIZED_AUTHORITY"
    assert result is delegation.return_value
    delegation.assert_called_once()
    assert registry.current_snapshot is previous


def test_exactly_one_coordinator_invocation_per_public_operation() -> None:
    registry = GovernanceRegistry(_initial_snapshot())
    action, manifest, epoch = _operation()
    original = _GovernanceCoordinator.coordinate

    def invoke(
        coordinator: _GovernanceCoordinator,
        delegated_action: GovernanceAction,
        delegated_manifest: GovernanceManifest,
        delegated_epoch: GovernanceEpoch,
    ) -> RegistrySnapshot | GovernanceRejection:
        return original(
            coordinator,
            delegated_action,
            delegated_manifest,
            delegated_epoch,
        )

    with patch.object(
        _GovernanceCoordinator, "coordinate", autospec=True, side_effect=invoke
    ) as delegation:
        result = registry.apply(action, manifest, epoch)
    assert isinstance(result, RegistrySnapshot)
    delegation.assert_called_once()


def test_identical_public_inputs_and_state_are_deterministic() -> None:
    action, manifest, epoch = _operation()
    first = _accepted(GovernanceRegistry(_initial_snapshot()).apply(action, manifest, epoch))
    second = _accepted(GovernanceRegistry(_initial_snapshot()).apply(action, manifest, epoch))
    assert first == second
    assert first.snapshot_identity == second.snapshot_identity


def test_registry_exposes_no_mutable_state_or_snapshot_setter() -> None:
    snapshot = _initial_snapshot()
    registry = GovernanceRegistry(snapshot)
    with pytest.raises(AttributeError):
        registry.current_snapshot = _snapshot()  # type: ignore[misc]
    assert registry.current_snapshot is snapshot
    assert not hasattr(registry, "store")
    assert not hasattr(registry, "coordinator")


def test_registry_is_a_facade_without_duplicated_component_logic() -> None:
    source = inspect.getsource(GovernanceRegistry)
    assert "Validator" not in source
    assert "_GovernanceReducer" not in source
    assert "_SnapshotBuilder" not in source
    assert "RegistrySnapshot(" not in source
    assert "replace_snapshot" not in source
    assert source.count("coordinate(") == 1
