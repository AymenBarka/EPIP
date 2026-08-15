"""A03-V2-E05 ordered governance transition orchestration tests."""

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
from epip.governance.reduction import _GovernanceReducer, _ReductionResult
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
        policy_versions=(("admission", "1.0.0"),),
        effective_epoch=epoch,
        resulting_snapshot_reference="snapshot-reduction-002",
    )
    manifest = _manifest(
        manifest_identity="manifest-002",
        governance_epoch=epoch,
        actions=(action,),
        policy_versions=action.policy_versions,
        authority_facts=("registry-authority:registry_authority",),
    )
    return action, manifest, epoch


def _initial_snapshot() -> RegistrySnapshot:
    return _snapshot(
        entries=(_entry(lifecycle_standing="Declared", trust_standing="Untrusted"),),
    )


def _store() -> GovernanceStore:
    return GovernanceStore(_initial_snapshot())


def _accepted(result: RegistrySnapshot | GovernanceRejection) -> RegistrySnapshot:
    assert isinstance(result, RegistrySnapshot)
    return result


def _rejection(label: str) -> GovernanceRejection:
    return GovernanceRejection(f"TEST_{label.upper()}", (label,), ())


def _successful_intermediates() -> tuple[
    RegistrySnapshot,
    GovernanceAction,
    GovernanceManifest,
    GovernanceEpoch,
    _ReductionResult,
    RegistrySnapshot,
]:
    current = _initial_snapshot()
    action, manifest, epoch = _operation()
    reduction = _GovernanceReducer.reduce(current, action, manifest, epoch)
    assert isinstance(reduction, _ReductionResult)
    candidate = _SnapshotBuilder.build(reduction, manifest, epoch)
    assert isinstance(candidate, RegistrySnapshot)
    return current, action, manifest, epoch, reduction, candidate


def test_coordinator_rejects_invalid_store_dependency() -> None:
    with pytest.raises(TypeError, match="store must be GovernanceStore"):
        _GovernanceCoordinator(cast(GovernanceStore, object()))


def test_successful_orchestration_transfers_exact_objects_once_in_order() -> None:
    current, action, manifest, epoch, reduction, candidate = _successful_intermediates()
    store = GovernanceStore(current)
    coordinator = _GovernanceCoordinator(store)
    trace: list[str] = []

    def reduce_once(
        actual_snapshot: RegistrySnapshot,
        actual_action: GovernanceAction,
        actual_manifest: GovernanceManifest,
        actual_epoch: GovernanceEpoch,
    ) -> _ReductionResult:
        trace.append("reduce")
        assert actual_snapshot is current
        assert actual_action is action
        assert actual_manifest is manifest
        assert actual_epoch is epoch
        return reduction

    def build_once(
        actual_reduction: _ReductionResult,
        actual_manifest: GovernanceManifest,
        actual_epoch: GovernanceEpoch,
    ) -> RegistrySnapshot:
        trace.append("build")
        assert actual_reduction is reduction
        assert actual_manifest is manifest
        assert actual_epoch is epoch
        return candidate

    original_replace = GovernanceStore.replace_snapshot

    def publish_once(
        actual_store: GovernanceStore,
        actual_candidate: RegistrySnapshot,
    ) -> RegistrySnapshot | GovernanceRejection:
        trace.append("publish")
        assert actual_store is store
        assert actual_candidate is candidate
        return original_replace(actual_store, actual_candidate)

    with (
        patch.object(_GovernanceReducer, "reduce", side_effect=reduce_once) as reducer,
        patch.object(_SnapshotBuilder, "build", side_effect=build_once) as builder,
        patch.object(
            GovernanceStore, "replace_snapshot", autospec=True, side_effect=publish_once
        ) as publication,
    ):
        result = coordinator.coordinate(action, manifest, epoch)

    assert result is candidate
    assert store.current_snapshot is candidate
    assert trace == ["reduce", "build", "publish"]
    reducer.assert_called_once_with(current, action, manifest, epoch)
    builder.assert_called_once_with(reduction, manifest, epoch)
    publication.assert_called_once_with(store, candidate)


def test_reduction_rejection_stops_before_construction_and_publication() -> None:
    store = _store()
    previous = store.current_snapshot
    action, manifest, epoch = _operation()
    rejection = _rejection("reduction")

    with (
        patch.object(_GovernanceReducer, "reduce", return_value=rejection) as reducer,
        patch.object(_SnapshotBuilder, "build") as builder,
        patch.object(GovernanceStore, "replace_snapshot", autospec=True) as publication,
    ):
        result = _GovernanceCoordinator(store).coordinate(action, manifest, epoch)

    assert result is rejection
    assert store.current_snapshot is previous
    reducer.assert_called_once_with(previous, action, manifest, epoch)
    builder.assert_not_called()
    publication.assert_not_called()


def test_validation_rejection_from_reducer_stops_the_lifecycle() -> None:
    store = _store()
    previous = store.current_snapshot
    action, manifest, epoch = _operation()
    invalid = _action(
        **{
            **{field: getattr(action, field) for field in action.__dataclass_fields__},
            "authority_role": "producer_owner",
        }
    )
    invalid_manifest = _manifest(
        manifest_identity=manifest.manifest_identity,
        governance_epoch=epoch,
        actions=(invalid,),
        policy_versions=invalid.policy_versions,
        authority_facts=("registry-authority:producer_owner",),
    )

    with (
        patch.object(_SnapshotBuilder, "build") as builder,
        patch.object(GovernanceStore, "replace_snapshot", autospec=True) as publication,
    ):
        result = _GovernanceCoordinator(store).coordinate(invalid, invalid_manifest, epoch)

    assert isinstance(result, GovernanceRejection)
    assert result.reason_code == "GOV_UNAUTHORIZED_AUTHORITY"
    assert store.current_snapshot is previous
    builder.assert_not_called()
    publication.assert_not_called()


def test_snapshot_failure_stops_before_publication() -> None:
    current, action, manifest, epoch, reduction, _ = _successful_intermediates()
    store = GovernanceStore(current)
    rejection = _rejection("construction")

    with (
        patch.object(_GovernanceReducer, "reduce", return_value=reduction) as reducer,
        patch.object(_SnapshotBuilder, "build", return_value=rejection) as builder,
        patch.object(GovernanceStore, "replace_snapshot", autospec=True) as publication,
    ):
        result = _GovernanceCoordinator(store).coordinate(action, manifest, epoch)

    assert result is rejection
    assert store.current_snapshot is current
    reducer.assert_called_once()
    builder.assert_called_once_with(reduction, manifest, epoch)
    publication.assert_not_called()


def test_publication_failure_is_propagated_and_preserves_authoritative_state() -> None:
    current, action, manifest, epoch, reduction, candidate = _successful_intermediates()
    store = GovernanceStore(current)
    rejection = _rejection("publication")

    with (
        patch.object(_GovernanceReducer, "reduce", return_value=reduction) as reducer,
        patch.object(_SnapshotBuilder, "build", return_value=candidate) as builder,
        patch.object(
            GovernanceStore,
            "replace_snapshot",
            autospec=True,
            return_value=rejection,
        ) as publication,
    ):
        result = _GovernanceCoordinator(store).coordinate(action, manifest, epoch)

    assert result is rejection
    assert store.current_snapshot is current
    reducer.assert_called_once()
    builder.assert_called_once()
    publication.assert_called_once_with(store, candidate)


def test_identical_inputs_and_starting_state_produce_identical_transition() -> None:
    action, manifest, epoch = _operation()
    first = _accepted(_GovernanceCoordinator(_store()).coordinate(action, manifest, epoch))
    second = _accepted(_GovernanceCoordinator(_store()).coordinate(action, manifest, epoch))

    assert first == second
    assert first.snapshot_identity == second.snapshot_identity


def test_coordinator_contains_only_the_single_orchestration_path() -> None:
    source = inspect.getsource(_GovernanceCoordinator.coordinate)

    assert source.count("_GovernanceReducer.reduce") == 1
    assert source.count("_SnapshotBuilder.build") == 1
    assert source.count("replace_snapshot") == 1
    assert "RegistrySnapshot(" not in source
    assert "_Validator" not in source
    assert "for " not in source
    assert "while " not in source
    assert "retry" not in source.lower()
    assert "recover" not in source.lower()
