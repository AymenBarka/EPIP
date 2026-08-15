"""A03 Increment 6 coordinator tests governed by ADR-03 and ADR-09."""

from __future__ import annotations

import inspect
from typing import cast
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
from epip.governance.reduction import _GovernanceReducer
from epip.governance.snapshot import _SnapshotBuilder
from epip.governance.store import GovernanceStore
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


def _store() -> GovernanceStore:
    return GovernanceStore(
        _snapshot(
            entries=(_entry(lifecycle_standing="Declared", trust_standing="Untrusted"),),
        )
    )


def _accepted(result: RegistrySnapshot | GovernanceRejection) -> RegistrySnapshot:
    assert isinstance(result, RegistrySnapshot)
    return result


def _rejection(result: RegistrySnapshot | GovernanceRejection) -> GovernanceRejection:
    assert isinstance(result, GovernanceRejection)
    return result


def test_coordinator_rejects_invalid_store_dependency() -> None:
    with pytest.raises(TypeError, match="store must be GovernanceStore"):
        _GovernanceCoordinator(cast(GovernanceStore, object()))


def test_coordinator_fails_closed_when_store_is_empty() -> None:
    coordinator = _GovernanceCoordinator(GovernanceStore())
    action, manifest, epoch = _operation()
    result = _rejection(coordinator.coordinate(action, manifest, epoch))
    assert result.reason_code == "GOV_MISSING_MANDATORY_FACT"
    assert result.diagnostic_details == (("fact", "current_registry_snapshot"),)


def test_successful_orchestration_replaces_store_with_immutable_snapshot() -> None:
    store = _store()
    previous = store.current_snapshot
    coordinator = _GovernanceCoordinator(store)
    action, manifest, epoch = _operation()
    result = _accepted(coordinator.coordinate(action, manifest, epoch))
    assert store.current_snapshot is result
    assert result is not previous
    assert result.manifest_reference == "manifest-002"
    assert result.governance_epoch == epoch
    assert result.entries[0].lifecycle_standing == "Registered"
    assert result.governance_action_references == ("action-002",)
    with pytest.raises(AttributeError):
        result.entries = ()  # type: ignore[misc]


def test_validator_rejection_propagates_without_partial_update() -> None:
    store = _store()
    previous = store.current_snapshot
    coordinator = _GovernanceCoordinator(store)
    action, manifest, epoch = _operation()
    invalid = _action(
        **{
            **{field: getattr(action, field) for field in action.__dataclass_fields__},
            "authority_role": "producer_owner",
        }
    )
    result = _rejection(coordinator.coordinate(invalid, manifest, epoch))
    assert result.reason_code == "GOV_UNAUTHORIZED_AUTHORITY"
    assert store.current_snapshot is previous


def test_reducer_rejection_propagates_without_builder_or_store_update() -> None:
    store = _store()
    previous = store.current_snapshot
    coordinator = _GovernanceCoordinator(store)
    action, manifest, epoch = _operation()
    illegal = _action(
        **{
            **{field: getattr(action, field) for field in action.__dataclass_fields__},
            "prior_standing": "Enabled",
        }
    )
    with patch.object(_SnapshotBuilder, "build", wraps=_SnapshotBuilder.build) as builder:
        result = _rejection(coordinator.coordinate(illegal, manifest, epoch))
    assert result.reason_code == "GOV_ILLEGAL_LIFECYCLE_TRANSITION"
    builder.assert_not_called()
    assert store.current_snapshot is previous


def test_builder_rejection_propagates_without_store_update() -> None:
    store = _store()
    previous = store.current_snapshot
    coordinator = _GovernanceCoordinator(store)
    action, manifest, _ = _operation()
    mismatched_epoch = GovernanceEpoch(3)
    result = _rejection(coordinator.coordinate(action, manifest, mismatched_epoch))
    assert result.diagnostic_details == (("fact", "governance_epoch_mismatch"),)
    assert store.current_snapshot is previous


def test_each_component_is_invoked_once_per_successful_operation() -> None:
    store = _store()
    coordinator = _GovernanceCoordinator(store)
    action, manifest, epoch = _operation()
    with (
        patch.object(_GovernanceReducer, "reduce", wraps=_GovernanceReducer.reduce) as reducer,
        patch.object(_SnapshotBuilder, "build", wraps=_SnapshotBuilder.build) as builder,
        patch.object(
            GovernanceStore,
            "replace_snapshot",
            autospec=True,
            wraps=GovernanceStore.replace_snapshot,
        ) as replacement,
    ):
        result = coordinator.coordinate(action, manifest, epoch)
    assert isinstance(result, RegistrySnapshot)
    reducer.assert_called_once()
    builder.assert_called_once()
    replacement.assert_called_once()


def test_identical_inputs_and_initial_state_produce_identical_results() -> None:
    action, manifest, epoch = _operation()
    first = _accepted(_GovernanceCoordinator(_store()).coordinate(action, manifest, epoch))
    second = _accepted(_GovernanceCoordinator(_store()).coordinate(action, manifest, epoch))
    assert first == second
    assert first.snapshot_identity == second.snapshot_identity


def test_coordinator_contains_no_duplicated_component_logic() -> None:
    source = inspect.getsource(_GovernanceCoordinator)
    assert "_AuthorityValidator" not in source
    assert "_LifecycleValidator" not in source
    assert "RegistrySnapshot(" not in source
    assert "replace(" not in source
    assert source.count("_GovernanceReducer.reduce") == 1
    assert source.count("_SnapshotBuilder.build") == 1
    assert source.count("replace_snapshot") == 1
