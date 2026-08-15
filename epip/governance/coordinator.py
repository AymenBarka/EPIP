"""Single-operation orchestration for existing immutable A03 components.

Implementation architecture: Programme A A03, Increment 6.
Governing contracts: ADR-EPIP017-03 and ADR-EPIP017-09.
This module contains no governance, validation, reduction, construction,
persistence, publication, scheduling, or producer-execution rules.
"""

from __future__ import annotations

from threading import RLock

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


class _GovernanceCoordinator:
    """Orchestrate one atomic governance operation at a time."""

    __slots__ = ("__lock", "__store")

    def __init__(self, store: GovernanceStore) -> None:
        """Bind the coordinator to one in-memory immutable snapshot store."""

        if not isinstance(store, GovernanceStore):
            raise TypeError("store must be GovernanceStore")
        self.__store = store
        self.__lock = RLock()

    def coordinate(
        self,
        action: GovernanceAction,
        manifest: GovernanceManifest,
        epoch: GovernanceEpoch,
    ) -> RegistrySnapshot | GovernanceRejection:
        """Run the existing reduction and construction components atomically."""

        with self.__lock:
            current = self.__store.current_snapshot
            reduced = _GovernanceReducer.reduce(current, action, manifest, epoch)
            if isinstance(reduced, GovernanceRejection):
                return reduced

            constructed = _SnapshotBuilder.build(reduced, manifest, epoch)
            if isinstance(constructed, GovernanceRejection):
                return constructed

            return self.__store.replace_snapshot(constructed)
