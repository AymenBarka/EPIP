"""Atomic publication of one authoritative immutable A03 registry snapshot.

Execution package: Programme A A03-V2-E04.
Governing contracts: ADR-EPIP017-03 and ADR-EPIP017-09.
This state holder owns publication only; it contains no governance validation,
reduction, snapshot construction, persistence, or orchestration logic.
"""

from __future__ import annotations

from threading import RLock

from epip.governance.model import GovernanceRejection, RegistrySnapshot
from epip.governance.validation import _reject, _StableReasonCodes


def _require_snapshot(snapshot: object) -> RegistrySnapshot:
    """Require an already constructed immutable registry snapshot."""

    if not isinstance(snapshot, RegistrySnapshot):
        raise TypeError("snapshot must be an immutable RegistrySnapshot")
    return snapshot


class GovernanceStore:
    """Own and atomically publish exactly one authoritative snapshot.

    Implementation owner: Programme A A03-V2-E04.
    Governing ADRs: ADR-EPIP017-03 and ADR-EPIP017-09.
    Responsibility: in-memory snapshot state ownership only.
    """

    __slots__ = ("__current_snapshot", "__lock")

    def __init__(self, initial_snapshot: RegistrySnapshot) -> None:
        """Initialize with exactly one immutable authoritative snapshot."""

        initial = _require_snapshot(initial_snapshot)
        self.__lock = RLock()
        self.__current_snapshot = initial

    @property
    def current_snapshot(self) -> RegistrySnapshot:
        """Return the immutable snapshot held at one atomic read boundary."""

        with self.__lock:
            return self.__current_snapshot

    def replace_snapshot(
        self,
        snapshot: RegistrySnapshot,
    ) -> RegistrySnapshot | GovernanceRejection:
        """Atomically publish one complete candidate or fail closed."""

        if not isinstance(snapshot, RegistrySnapshot):
            return _reject(_StableReasonCodes.INVALID_MODEL, ("snapshot_publication",))
        with self.__lock:
            current = self.__current_snapshot
            if snapshot.snapshot_identity == current.snapshot_identity:
                return _reject(
                    _StableReasonCodes.INVALID_IDENTITY,
                    (snapshot.snapshot_identity,),
                    (("fact", "duplicate_snapshot_publication"),),
                )
            if snapshot.governance_epoch.sequence <= current.governance_epoch.sequence:
                return _reject(
                    _StableReasonCodes.ILLEGAL_LIFECYCLE_TRANSITION,
                    (snapshot.snapshot_identity, current.snapshot_identity),
                    (("fact", "stale_snapshot_publication"),),
                )
            if len(snapshot.governance_action_references) != len(
                current.governance_action_references
            ) + 1 or snapshot.governance_action_references[:-1] != (
                current.governance_action_references
            ):
                return _reject(
                    _StableReasonCodes.INCOMPLETE_DECLARATION,
                    (snapshot.snapshot_identity, current.snapshot_identity),
                    (("fact", "append_only_publication_history"),),
                )
            self.__current_snapshot = snapshot
            return snapshot
