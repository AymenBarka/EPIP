"""Immutable chronological history for market-structure snapshots."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from epip.core.integrity import integrity_deserializer
from epip.market_structure.exceptions import HistoryError, StructureVersionError
from epip.market_structure.models import MarketStructureSnapshot
from epip.market_structure.serialization import deterministic_json, load_json


@dataclass(frozen=True, slots=True)
class StructureHistory:
    """Persistent-style immutable collection suitable for replay and backtesting."""

    snapshots: tuple[MarketStructureSnapshot, ...] = ()

    def __post_init__(self) -> None:
        versions = tuple(snapshot.version for snapshot in self.snapshots)
        if len(set(versions)) != len(versions):
            raise StructureVersionError(
                "duplicate structure version", metadata={"versions": versions}
            )
        timestamps = tuple(snapshot.timestamp for snapshot in self.snapshots)
        if timestamps != tuple(sorted(timestamps)):
            raise HistoryError(
                "snapshots must be chronological", metadata={"timestamps": timestamps}
            )

    def append(self, snapshot: MarketStructureSnapshot) -> StructureHistory:
        expected = self.snapshots[-1].version + 1 if self.snapshots else 1
        if snapshot.version != expected:
            raise StructureVersionError(
                "non-sequential structure version",
                metadata={"expected": expected, "actual": snapshot.version},
            )
        if self.snapshots and snapshot.timestamp < self.snapshots[-1].timestamp:
            raise HistoryError(
                "snapshot timestamp precedes latest history entry",
                metadata={"latest": self.snapshots[-1].timestamp, "actual": snapshot.timestamp},
            )
        return StructureHistory((*self.snapshots, snapshot))

    def latest(self) -> MarketStructureSnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    def by_timestamp(self, timestamp: str) -> MarketStructureSnapshot | None:
        return next((item for item in self.snapshots if item.timestamp == timestamp), None)

    def by_version(self, version: int) -> MarketStructureSnapshot | None:
        return next((item for item in self.snapshots if item.version == version), None)

    def replay(self) -> Iterator[MarketStructureSnapshot]:
        return iter(self.snapshots)

    def to_dict(self) -> dict[str, Any]:
        return {"snapshots": [snapshot.to_dict() for snapshot in self.snapshots]}

    @classmethod
    @integrity_deserializer
    def from_dict(cls, payload: Mapping[str, Any]) -> StructureHistory:
        values = payload.get("snapshots", [])
        if not isinstance(values, list):
            raise HistoryError("serialized snapshots must be a list")
        snapshots: list[MarketStructureSnapshot] = []
        for value in values:
            if not isinstance(value, Mapping):
                raise HistoryError("serialized snapshot must be a mapping")
            snapshots.append(MarketStructureSnapshot.from_dict(value))
        return cls(tuple(snapshots))

    def to_json(self) -> str:
        return deterministic_json(self.to_dict())

    @classmethod
    def from_json(cls, payload: str) -> StructureHistory:
        return cls.from_dict(load_json(payload))
