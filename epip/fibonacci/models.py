"""Immutable Fibonacci domain models."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class FibonacciDirection(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGE = "RANGE"


@dataclass(frozen=True, slots=True)
class FibonacciLevel:
    ratio: float
    price: float
    label: str = ""
    confluence_score: float = 0.0


@dataclass(frozen=True, slots=True)
class FibonacciRetracement:
    start_price: float
    end_price: float
    direction: FibonacciDirection
    levels: tuple[FibonacciLevel, ...]
    confluence_score: float = 0.0


@dataclass(frozen=True, slots=True)
class FibonacciExtension:
    start_price: float
    end_price: float
    levels: tuple[FibonacciLevel, ...]
    confluence_score: float = 0.0


@dataclass(frozen=True, slots=True)
class FibonacciZone:
    low: float
    high: float
    name: str
    confluence_score: float = 0.0


@dataclass(frozen=True, slots=True)
class GoldenZone(FibonacciZone):
    pass


@dataclass(frozen=True, slots=True)
class PremiumZone(FibonacciZone):
    pass


@dataclass(frozen=True, slots=True)
class DiscountZone(FibonacciZone):
    pass


@dataclass(frozen=True, slots=True)
class OTEZone(FibonacciZone):
    pass


@dataclass(frozen=True, slots=True)
class ConfluenceZone(FibonacciZone):
    sources: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FibonacciSnapshot:
    timestamp: str
    symbol: str
    timeframe: str
    version: int
    direction: FibonacciDirection
    retracement: FibonacciRetracement
    extension: FibonacciExtension
    zones: tuple[FibonacciZone, ...]
    confluence_score: float = 0.0
    structure_version: int = 1
    liquidity_version: int = 1
    engine_version: str = "EPIP-009"
    probability: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "probability", max(0.0, min(1.0, self.probability)))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FibonacciSnapshot:
        level: Callable[[dict[str, Any]], FibonacciLevel] = lambda x: FibonacciLevel(**x)
        ret = d["retracement"]
        ext = d["extension"]
        retr = FibonacciRetracement(
            ret["start_price"],
            ret["end_price"],
            FibonacciDirection(ret["direction"]),
            tuple(level(x) for x in ret["levels"]),
            ret.get("confluence_score", 0.0),
        )
        extension = FibonacciExtension(
            ext["start_price"],
            ext["end_price"],
            tuple(level(x) for x in ext["levels"]),
            ext.get("confluence_score", 0.0),
        )
        zones = tuple(FibonacciZone(**x) for x in d["zones"])
        return cls(
            d["timestamp"],
            d["symbol"],
            d["timeframe"],
            int(d["version"]),
            FibonacciDirection(d["direction"]),
            retr,
            extension,
            zones,
            float(d.get("confluence_score", 0)),
            int(d.get("structure_version", 1)),
            int(d.get("liquidity_version", 1)),
            str(d.get("engine_version", "EPIP-009")),
            float(d.get("probability", 0.0)),
        )

    @classmethod
    def from_json(cls, payload: str) -> FibonacciSnapshot:
        return cls.from_dict(json.loads(payload))
