"""Immutable portfolio history."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from epip.portfolio.exceptions import PortfolioVersionError
from epip.portfolio.models import PortfolioSnapshot


@dataclass(frozen=True, slots=True)
class PortfolioHistory:
    snapshots: tuple[PortfolioSnapshot, ...] = ()

    def append(self, snapshot: PortfolioSnapshot) -> PortfolioHistory:
        expected = self.snapshots[-1].version + 1 if self.snapshots else 1
        if snapshot.version != expected:
            raise PortfolioVersionError("non-sequential portfolio version")
        return PortfolioHistory((*self.snapshots, snapshot))

    def latest(self) -> PortfolioSnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    def by_version(self, version: int) -> PortfolioSnapshot | None:
        return next((item for item in self.snapshots if item.version == version), None)

    def by_timestamp(self, timestamp: str) -> PortfolioSnapshot | None:
        return next((item for item in self.snapshots if item.timestamp == timestamp), None)

    def replay(self) -> Iterator[PortfolioSnapshot]:
        return iter(self.snapshots)
