"""Atomic in-memory ownership of one immutable A03 registry snapshot.

Implementation architecture: Programme A A03, Increment 5.
Governing contracts: ADR-EPIP017-03 and ADR-EPIP017-09.
This state holder contains no registry, governance, validation, reduction,
snapshot-construction, persistence, publication, or orchestration logic.
"""

from __future__ import annotations

from threading import RLock

from epip.governance.model import RegistrySnapshot


def _require_snapshot(snapshot: object) -> RegistrySnapshot:
    """Require an already constructed immutable registry snapshot."""

    if not isinstance(snapshot, RegistrySnapshot):
        raise TypeError("snapshot must be an immutable RegistrySnapshot")
    return snapshot


class GovernanceStore:
    """Own exactly one optional current snapshot and replace it atomically.

    Implementation owner: Programme A A03, Increment 5.
    Governing ADRs: ADR-EPIP017-03 and ADR-EPIP017-09.
    Responsibility: in-memory snapshot state ownership only.
    """

    __slots__ = ("__current_snapshot", "__lock")

    def __init__(self, initial_snapshot: RegistrySnapshot | None = None) -> None:
        """Create an empty store or retain one immutable initial snapshot."""

        if initial_snapshot is not None:
            _require_snapshot(initial_snapshot)
        self.__lock = RLock()
        self.__current_snapshot = initial_snapshot

    @property
    def current_snapshot(self) -> RegistrySnapshot | None:
        """Return the immutable snapshot held at one atomic read boundary."""

        with self.__lock:
            return self.__current_snapshot

    def replace_snapshot(self, snapshot: RegistrySnapshot) -> RegistrySnapshot | None:
        """Atomically replace the current snapshot and return its prior value."""

        replacement = _require_snapshot(snapshot)
        with self.__lock:
            previous = self.__current_snapshot
            self.__current_snapshot = replacement
            return previous
