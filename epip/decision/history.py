"""Immutable Decision history."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from epip.decision.exceptions import DecisionVersionError
from epip.decision.models import DecisionSnapshot


@dataclass(frozen=True, slots=True)
class DecisionHistory:
    snapshots: tuple[DecisionSnapshot, ...] = ()

    def append(self, snapshot: DecisionSnapshot) -> DecisionHistory:
        expected = self.snapshots[-1].version + 1 if self.snapshots else 1
        if snapshot.version != expected:
            raise DecisionVersionError("non-sequential decision version")
        return DecisionHistory((*self.snapshots, snapshot))

    def latest(self) -> DecisionSnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    def by_version(self, version: int) -> DecisionSnapshot | None:
        return next((snapshot for snapshot in self.snapshots if snapshot.version == version), None)

    def by_timestamp(self, timestamp: str) -> DecisionSnapshot | None:
        return next(
            (snapshot for snapshot in self.snapshots if snapshot.timestamp == timestamp), None
        )

    def replay(self) -> Iterator[DecisionSnapshot]:
        return iter(self.snapshots)
