"""Immutable execution history."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from epip.execution.exceptions import ExecutionVersionError
from epip.execution.models import ExecutionSnapshot


@dataclass(frozen=True, slots=True)
class ExecutionHistory:
    snapshots: tuple[ExecutionSnapshot, ...] = ()

    def append(self, snapshot: ExecutionSnapshot) -> ExecutionHistory:
        expected = self.snapshots[-1].version + 1 if self.snapshots else 1
        if snapshot.version != expected:
            raise ExecutionVersionError("non-sequential execution version")
        return ExecutionHistory((*self.snapshots, snapshot))

    def latest(self) -> ExecutionSnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    def by_version(self, version: int) -> ExecutionSnapshot | None:
        return next((item for item in self.snapshots if item.version == version), None)

    def by_timestamp(self, timestamp: str) -> ExecutionSnapshot | None:
        return next((item for item in self.snapshots if item.timestamp == timestamp), None)

    def replay(self) -> Iterator[ExecutionSnapshot]:
        return iter(self.snapshots)
