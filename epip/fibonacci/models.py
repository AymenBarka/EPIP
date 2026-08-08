"""Immutable Fibonacci domain models."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from epip.core.integrity import (
    RelationshipIntegrityError,
    integrity_deserializer,
    require_finite,
    require_non_negative,
    require_text,
    require_unit_interval,
    require_version,
)


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

    def __post_init__(self) -> None:
        require_non_negative(self.ratio, "fibonacci_level.ratio")
        require_finite(self.price, "fibonacci_level.price")
        require_unit_interval(self.confluence_score, "fibonacci_level.confluence_score")


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

    def __post_init__(self) -> None:
        require_non_negative(self.low, "fibonacci_zone.low")
        require_non_negative(self.high, "fibonacci_zone.high")
        require_text(self.name, "fibonacci_zone.name")
        require_unit_interval(self.confluence_score, "fibonacci_zone.confluence_score")
        if self.low > self.high:
            raise RelationshipIntegrityError("fibonacci zone low exceeds high")


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
        self.validate_integrity()

    def validate_integrity(self) -> None:
        require_text(self.timestamp, "fibonacci_snapshot.timestamp")
        require_text(self.symbol, "fibonacci_snapshot.symbol")
        require_text(self.timeframe, "fibonacci_snapshot.timeframe")
        require_version(self.version, "fibonacci_snapshot.version")
        require_version(self.structure_version, "fibonacci_snapshot.structure_version")
        require_version(self.liquidity_version, "fibonacci_snapshot.liquidity_version")
        require_text(self.engine_version, "fibonacci_snapshot.engine_version")
        require_unit_interval(self.confluence_score, "fibonacci_snapshot.confluence_score")
        require_unit_interval(self.probability, "fibonacci_snapshot.probability")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    @integrity_deserializer
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
    @integrity_deserializer
    def from_json(cls, payload: str) -> FibonacciSnapshot:
        return cls.from_dict(json.loads(payload))
