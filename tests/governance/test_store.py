"""A03 Increment 5 GovernanceStore tests governed by ADR-03 and ADR-09."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from typing import cast

import pytest

from epip.governance import RegistrySnapshot
from epip.governance.store import GovernanceStore
from tests.governance.test_model import _snapshot


def test_store_has_initial_empty_state() -> None:
    store = GovernanceStore()
    assert store.current_snapshot is None
    assert not hasattr(store, "__dict__")


def test_store_retains_initial_immutable_snapshot() -> None:
    snapshot = _snapshot()
    store = GovernanceStore(snapshot)
    assert store.current_snapshot is snapshot
    with pytest.raises(FrozenInstanceError):
        snapshot.manifest_reference = "changed"  # type: ignore[misc]
    assert store.current_snapshot is snapshot


def test_store_replaces_snapshot_atomically_and_returns_previous() -> None:
    first = _snapshot(snapshot_identity="snapshot-001")
    second = _snapshot(snapshot_identity="snapshot-002")
    store = GovernanceStore()
    assert store.replace_snapshot(first) is None
    assert store.current_snapshot is first
    assert store.replace_snapshot(second) is first
    assert store.current_snapshot is second


def test_store_supports_repeated_deterministic_replacement() -> None:
    snapshots = tuple(_snapshot(snapshot_identity=f"snapshot-{index:03d}") for index in range(1, 5))
    store = GovernanceStore()
    observed = tuple(store.replace_snapshot(snapshot) for snapshot in snapshots)
    assert observed == (None, *snapshots[:-1])
    assert store.current_snapshot is snapshots[-1]


@pytest.mark.parametrize("invalid", [[], {}, object(), "snapshot", 1])
def test_store_rejects_mutable_and_invalid_initial_snapshots(invalid: object) -> None:
    with pytest.raises(TypeError, match="immutable RegistrySnapshot"):
        GovernanceStore(cast(RegistrySnapshot, invalid))


@pytest.mark.parametrize("invalid", [None, [], {}, object(), "snapshot", 1])
def test_store_rejects_invalid_replacements_without_state_change(invalid: object) -> None:
    snapshot = _snapshot()
    store = GovernanceStore(snapshot)
    with pytest.raises(TypeError, match="immutable RegistrySnapshot"):
        store.replace_snapshot(cast(RegistrySnapshot, invalid))
    assert store.current_snapshot is snapshot


def test_store_exposes_no_property_setter_or_mutable_copy() -> None:
    snapshot = _snapshot()
    store = GovernanceStore(snapshot)
    with pytest.raises(AttributeError):
        store.current_snapshot = replace(snapshot)  # type: ignore[misc]
    exposed = store.current_snapshot
    assert exposed is snapshot
    assert exposed is not None
    with pytest.raises(FrozenInstanceError):
        exposed.snapshot_identity = "changed"  # type: ignore[misc]


def test_concurrent_reads_observe_only_complete_snapshot_references() -> None:
    snapshots = tuple(_snapshot(snapshot_identity=f"snapshot-{index:03d}") for index in range(20))
    store = GovernanceStore(snapshots[0])
    allowed = frozenset(snapshot.snapshot_identity for snapshot in snapshots)

    def write_all() -> None:
        for snapshot in snapshots[1:]:
            store.replace_snapshot(snapshot)

    def read_many() -> tuple[str, ...]:
        observed: list[str] = []
        for _ in range(200):
            current = store.current_snapshot
            assert current is not None
            observed.append(current.snapshot_identity)
        return tuple(observed)

    with ThreadPoolExecutor(max_workers=5) as executor:
        writer = executor.submit(write_all)
        readers = tuple(executor.submit(read_many) for _ in range(4))
        writer.result()
        observations = tuple(result for reader in readers for result in reader.result())

    assert observations
    assert set(observations) <= allowed
    assert store.current_snapshot is snapshots[-1]
