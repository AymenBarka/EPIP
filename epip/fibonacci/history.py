from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

from epip.fibonacci.exceptions import FibonacciVersionError
from epip.fibonacci.models import FibonacciSnapshot


@dataclass(frozen=True, slots=True)
class FibonacciHistory:
    snapshots: tuple[FibonacciSnapshot, ...] = ()

    def append(self, s: FibonacciSnapshot) -> FibonacciHistory:
        expected = self.snapshots[-1].version + 1 if self.snapshots else 1
        if s.version != expected:
            raise FibonacciVersionError("non-sequential version")
        return FibonacciHistory((*self.snapshots, s))

    def latest(self) -> FibonacciSnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    def by_version(self, v: int) -> FibonacciSnapshot | None:
        return next((x for x in self.snapshots if x.version == v), None)

    def by_timestamp(self, t: str) -> FibonacciSnapshot | None:
        return next((x for x in self.snapshots if x.timestamp == t), None)

    def replay(self) -> Iterator[FibonacciSnapshot]:
        return iter(self.snapshots)

    def to_json(self) -> str:
        return json.dumps({"snapshots": [x.to_dict() for x in self.snapshots]}, sort_keys=True)

    @classmethod
    def from_json(cls, p: str) -> FibonacciHistory:
        return cls(tuple(FibonacciSnapshot.from_dict(x) for x in json.loads(p)["snapshots"]))
