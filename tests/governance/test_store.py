"""A03-V2-E04 authoritative atomic publication tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from inspect import getsource
from typing import cast

import pytest

from epip.governance.model import GovernanceEpoch, GovernanceRejection, RegistrySnapshot
from epip.governance.store import GovernanceStore
from tests.governance.test_model import _entry, _snapshot


def _initial_snapshot() -> RegistrySnapshot:
    return _snapshot(
        snapshot_identity="snapshot-001",
        manifest_reference="manifest-001",
        governance_epoch=GovernanceEpoch(1),
        governance_action_references=("action-001",),
    )


def _candidate_snapshot(**overrides: object) -> RegistrySnapshot:
    values: dict[str, object] = {
        "snapshot_identity": "snapshot-002",
        "manifest_reference": "manifest-002",
        "governance_epoch": GovernanceEpoch(2),
        "governance_action_references": ("action-001", "action-002"),
    }
    values.update(overrides)
    return _snapshot(**values)


def _rejection(result: RegistrySnapshot | GovernanceRejection) -> GovernanceRejection:
    assert isinstance(result, GovernanceRejection)
    return result


def test_store_initializes_with_exactly_one_immutable_authoritative_snapshot() -> None:
    initial = _initial_snapshot()
    store = GovernanceStore(initial)

    assert store.current_snapshot is initial
    assert not hasattr(store, "__dict__")
    with pytest.raises(FrozenInstanceError):
        initial.manifest_reference = "changed"  # type: ignore[misc]
    assert store.current_snapshot is initial


@pytest.mark.parametrize("invalid", [None, [], {}, object(), "snapshot", 1])
def test_store_rejects_invalid_initial_authoritative_state(invalid: object) -> None:
    with pytest.raises(TypeError, match="immutable RegistrySnapshot"):
        GovernanceStore(cast(RegistrySnapshot, invalid))


def test_publication_is_atomic_deterministic_and_exposes_exact_candidate() -> None:
    initial = _initial_snapshot()
    candidate = _candidate_snapshot()
    first_store = GovernanceStore(initial)
    second_store = GovernanceStore(initial)

    first = first_store.replace_snapshot(candidate)
    second = second_store.replace_snapshot(candidate)

    assert first is candidate
    assert second is candidate
    assert first == second
    assert first_store.current_snapshot is candidate
    assert second_store.current_snapshot is candidate
    assert first_store.current_snapshot.entries is candidate.entries


def test_failed_publication_preserves_previous_authoritative_snapshot() -> None:
    initial = _initial_snapshot()
    store = GovernanceStore(initial)

    invalid = store.replace_snapshot(cast(RegistrySnapshot, object()))

    assert _rejection(invalid).reason_code == "GOV_INVALID_MODEL"
    assert store.current_snapshot is initial


def test_duplicate_and_stale_publications_fail_closed_deterministically() -> None:
    initial = _initial_snapshot()
    store = GovernanceStore(initial)
    duplicate = replace(
        _candidate_snapshot(),
        snapshot_identity=initial.snapshot_identity,
    )
    first_duplicate = store.replace_snapshot(duplicate)
    second_duplicate = store.replace_snapshot(duplicate)
    assert first_duplicate == second_duplicate
    assert _rejection(first_duplicate).diagnostic_details == (
        ("fact", "duplicate_snapshot_publication"),
    )
    assert store.current_snapshot is initial

    stale = _candidate_snapshot(governance_epoch=GovernanceEpoch(1))
    first_stale = store.replace_snapshot(stale)
    second_stale = store.replace_snapshot(stale)
    assert first_stale == second_stale
    assert _rejection(first_stale).diagnostic_details == (("fact", "stale_snapshot_publication"),)
    assert store.current_snapshot is initial


@pytest.mark.parametrize(
    "history",
    [
        (),
        ("action-002",),
        ("action-001", "action-002", "action-003"),
        ("action-other", "action-002"),
    ],
)
def test_unsupported_publication_history_is_rejected_without_state_change(
    history: tuple[str, ...],
) -> None:
    initial = _initial_snapshot()
    store = GovernanceStore(initial)
    candidate = _candidate_snapshot(governance_action_references=history)

    first = store.replace_snapshot(candidate)
    second = store.replace_snapshot(candidate)

    assert first == second
    assert _rejection(first).diagnostic_details == (("fact", "append_only_publication_history"),)
    assert store.current_snapshot is initial


def test_publication_preserves_append_only_history_and_snapshot_immutability() -> None:
    initial = _initial_snapshot()
    candidate = _candidate_snapshot()
    store = GovernanceStore(initial)

    published = store.replace_snapshot(candidate)

    assert published is candidate
    assert store.current_snapshot.governance_action_references == (
        "action-001",
        "action-002",
    )
    assert initial.governance_action_references == ("action-001",)
    with pytest.raises(FrozenInstanceError):
        store.current_snapshot.snapshot_identity = "changed"  # type: ignore[misc]


def test_concurrent_reads_observe_only_complete_authoritative_snapshots() -> None:
    initial = _initial_snapshot()
    candidate = _candidate_snapshot()
    store = GovernanceStore(initial)

    def publish() -> RegistrySnapshot | GovernanceRejection:
        return store.replace_snapshot(candidate)

    def read_many() -> tuple[RegistrySnapshot, ...]:
        return tuple(store.current_snapshot for _ in range(300))

    with ThreadPoolExecutor(max_workers=5) as executor:
        publication = executor.submit(publish)
        readers = tuple(executor.submit(read_many) for _ in range(4))
        observed = tuple(snapshot for reader in readers for snapshot in reader.result())
        result = publication.result()

    assert result is candidate
    assert observed
    assert all(snapshot is initial or snapshot is candidate for snapshot in observed)
    assert store.current_snapshot is candidate


def test_store_does_not_repeat_semantics_construct_or_orchestrate() -> None:
    initial = _initial_snapshot()
    semantically_opaque_candidate = _candidate_snapshot(
        entries=(
            _entry(
                producer_identity="opaque-producer",
                trust_standing="opaque-standing",
                lifecycle_standing="opaque-lifecycle",
            ),
        ),
        policy_versions=(("opaque-policy", "99"),),
    )
    store = GovernanceStore(initial)

    assert store.replace_snapshot(semantically_opaque_candidate) is semantically_opaque_candidate
    source = getsource(GovernanceStore)
    assert "_GovernanceReducer" not in source
    assert "_SnapshotBuilder" not in source
    assert "_GovernanceCoordinator" not in source
    assert "validate_context" not in source
