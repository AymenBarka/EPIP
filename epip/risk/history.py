"""Immutable risk history."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from epip.risk.exceptions import RiskVersionError
from epip.risk.models import RiskSnapshot


@dataclass(frozen=True, slots=True)
class RiskHistory:
    snapshots: tuple[RiskSnapshot, ...] = ()

    def append(self, snapshot: RiskSnapshot) -> RiskHistory:
        expected = self.snapshots[-1].version + 1 if self.snapshots else 1
        if snapshot.version != expected:
            raise RiskVersionError("non-sequential risk version")
        return RiskHistory((*self.snapshots, snapshot))

    def latest(self) -> RiskSnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    def by_version(self, version: int) -> RiskSnapshot | None:
        return next((item for item in self.snapshots if item.version == version), None)

    def by_timestamp(self, timestamp: str) -> RiskSnapshot | None:
        return next((item for item in self.snapshots if item.timestamp == timestamp), None)

    def replay(self) -> Iterator[RiskSnapshot]:
        return iter(self.snapshots)
