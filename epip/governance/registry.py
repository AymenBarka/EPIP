"""Public A03 governance façade over the frozen orchestration components.

Implementation architecture: Programme A A03, Increment 7.
Governing contracts: ADR-EPIP017-03 and ADR-EPIP017-09.
This module exposes no persistence, publication, scheduling, recovery,
producer execution, validation, reduction, or snapshot-construction logic.
"""

from __future__ import annotations

from epip.governance.coordinator import _GovernanceCoordinator
from epip.governance.model import (
    GovernanceAction,
    GovernanceEpoch,
    GovernanceManifest,
    GovernanceRejection,
    RegistrySnapshot,
)
from epip.governance.store import GovernanceStore

__all__ = ["GovernanceRegistry"]


class GovernanceRegistry:
    """Public deterministic façade for one-at-a-time governance operations.

    Implementation owner: Programme A A03, Increment 7.
    Governing ADRs: ADR-EPIP017-03 and ADR-EPIP017-09.
    Responsibility: public delegation and immutable state access only.
    """

    __slots__ = ("__coordinator", "__store")

    def __init__(self, initial_snapshot: RegistrySnapshot | None = None) -> None:
        """Own one private store initialized with one authoritative snapshot."""

        if initial_snapshot is None:
            raise TypeError("initial_snapshot must be an immutable RegistrySnapshot")
        self.__store = GovernanceStore(initial_snapshot)
        self.__coordinator = _GovernanceCoordinator(self.__store)

    @property
    def current_snapshot(self) -> RegistrySnapshot:
        """Return read-only access to the current immutable registry snapshot."""

        return self.__store.current_snapshot

    def apply(
        self,
        action: GovernanceAction,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> RegistrySnapshot | GovernanceRejection:
        """Delegate exactly one immutable governance operation to the coordinator."""

        return self.__coordinator.coordinate(action, manifest, epoch)
