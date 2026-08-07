"""Immutable liquidity history."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from epip.liquidity.exceptions import LiquidityHistoryError, LiquidityVersionError
from epip.liquidity.models import LiquiditySnapshot


@dataclass(frozen=True, slots=True)
class LiquidityHistory:
    snapshots: tuple[LiquiditySnapshot, ...] = ()

    def append(self, snapshot: LiquiditySnapshot) -> LiquidityHistory:
        expected = self.snapshots[-1].version + 1 if self.snapshots else 1
        if snapshot.version != expected:
            raise LiquidityVersionError("non-sequential version")
        if self.snapshots and snapshot.timestamp < self.snapshots[-1].timestamp:
            raise LiquidityHistoryError("non-chronological snapshot")
        return LiquidityHistory((*self.snapshots, snapshot))

    def latest(self) -> LiquiditySnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    def by_version(self, version: int) -> LiquiditySnapshot | None:
        return next((x for x in self.snapshots if x.version == version), None)

    def by_timestamp(self, timestamp: str) -> LiquiditySnapshot | None:
        return next((x for x in self.snapshots if x.timestamp == timestamp), None)

    def replay(self) -> Iterator[LiquiditySnapshot]:
        return iter(self.snapshots)

    def to_dict(self) -> dict[str, Any]:
        return {"snapshots": [x.to_dict() for x in self.snapshots]}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LiquidityHistory:
        return cls(tuple(LiquiditySnapshot.from_dict(x) for x in data.get("snapshots", ())))

    @classmethod
    def from_json(cls, payload: str) -> LiquidityHistory:
        return cls.from_dict(json.loads(payload))
