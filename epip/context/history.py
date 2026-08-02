"""Immutable Market Context history."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from epip.context.exceptions import MarketContextVersionError
from epip.context.snapshot import MarketContextSnapshot


@dataclass(frozen=True, slots=True)
class MarketContextHistory:
    snapshots: tuple[MarketContextSnapshot, ...] = ()

    def append(self, snapshot: MarketContextSnapshot) -> MarketContextHistory:
        expected = self.snapshots[-1].version.context + 1 if self.snapshots else 1
        if snapshot.version.context != expected:
            raise MarketContextVersionError("non-sequential context version")
        return MarketContextHistory((*self.snapshots, snapshot))

    def latest(self) -> MarketContextSnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    def by_version(self, version: int) -> MarketContextSnapshot | None:
        return next((item for item in self.snapshots if item.version.context == version), None)

    def by_timestamp(self, timestamp: str) -> MarketContextSnapshot | None:
        return next((item for item in self.snapshots if item.timestamp == timestamp), None)

    def replay(self) -> Iterator[MarketContextSnapshot]:
        return iter(self.snapshots)
