"""Immutable Elliott snapshot history."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from epip.elliott.exceptions import WaveVersionError
from epip.elliott.models import WaveSnapshot


@dataclass(frozen=True, slots=True)
class WaveHistory:
    snapshots: tuple[WaveSnapshot, ...] = ()

    def append(self, snapshot: WaveSnapshot) -> WaveHistory:
        expected = self.snapshots[-1].version + 1 if self.snapshots else 1
        if snapshot.version != expected:
            raise WaveVersionError("non-sequential Elliott version")
        return WaveHistory((*self.snapshots, snapshot))

    def latest(self) -> WaveSnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    def by_version(self, version: int) -> WaveSnapshot | None:
        return next((snapshot for snapshot in self.snapshots if snapshot.version == version), None)

    def by_timestamp(self, timestamp: str) -> WaveSnapshot | None:
        return next(
            (snapshot for snapshot in self.snapshots if snapshot.timestamp == timestamp), None
        )

    def replay(self) -> Iterator[WaveSnapshot]:
        return iter(self.snapshots)
