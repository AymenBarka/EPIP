"""Immutable EPIP-008 liquidity domain models."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from epip.core.integrity import (
    RelationshipIntegrityError,
    integrity_deserializer,
    require_positive,
    require_text,
    require_unit_interval,
    require_version,
)


class LiquiditySide(StrEnum):
    BUY_SIDE = "BUY_SIDE"
    SELL_SIDE = "SELL_SIDE"


class LiquidityScope(StrEnum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class LiquidityStatus(StrEnum):
    RESTING = "RESTING"
    SWEPT = "SWEPT"
    CONSUMED = "CONSUMED"
    INVALIDATED = "INVALIDATED"


@dataclass(frozen=True, slots=True)
class LiquidityLevel:
    symbol: str
    timeframe: str
    timestamp: str
    price: float
    side: LiquiditySide
    scope: LiquidityScope
    touches: int = 1
    status: LiquidityStatus = LiquidityStatus.RESTING
    confluence_score: float = 0.0

    def __post_init__(self) -> None:
        require_text(self.symbol, "liquidity_level.symbol")
        require_text(self.timeframe, "liquidity_level.timeframe")
        require_text(self.timestamp, "liquidity_level.timestamp")
        require_positive(self.price, "liquidity_level.price")
        require_positive(self.touches, "liquidity_level.touches")
        require_unit_interval(self.confluence_score, "liquidity_level.confluence_score")


@dataclass(frozen=True, slots=True)
class EqualHigh:
    symbol: str
    timeframe: str
    price: float
    indices: tuple[int, ...]
    timestamps: tuple[str, ...]
    confluence_score: float = 0.0


@dataclass(frozen=True, slots=True)
class EqualLow:
    symbol: str
    timeframe: str
    price: float
    indices: tuple[int, ...]
    timestamps: tuple[str, ...]
    confluence_score: float = 0.0


@dataclass(frozen=True, slots=True)
class InternalLiquidity:
    levels: tuple[LiquidityLevel, ...] = ()


@dataclass(frozen=True, slots=True)
class ExternalLiquidity:
    levels: tuple[LiquidityLevel, ...] = ()


@dataclass(frozen=True, slots=True)
class LiquidityZone:
    symbol: str
    timeframe: str
    low: float
    high: float
    side: LiquiditySide
    active: bool = True
    confluence_score: float = 0.0


@dataclass(frozen=True, slots=True)
class LiquidityPool:
    pool_id: str
    symbol: str
    timeframe: str
    price: float
    side: LiquiditySide
    scope: LiquidityScope
    touches: int
    level_indices: tuple[int, ...]
    resting: bool = True
    confluence_score: float = 0.0

    def __post_init__(self) -> None:
        require_text(self.pool_id, "liquidity_pool.id")
        require_text(self.symbol, "liquidity_pool.symbol")
        require_text(self.timeframe, "liquidity_pool.timeframe")
        require_positive(self.price, "liquidity_pool.price")
        require_positive(self.touches, "liquidity_pool.touches")
        require_unit_interval(self.confluence_score, "liquidity_pool.confluence_score")
        if len(self.level_indices) != len(set(self.level_indices)):
            raise RelationshipIntegrityError("liquidity pool contains duplicated indices")


@dataclass(frozen=True, slots=True)
class LiquiditySweep:
    symbol: str
    timeframe: str
    timestamp: str
    side: LiquiditySide
    level_price: float
    sweep_price: float
    confirmed: bool
    stop_hunt: bool = False
    confluence_score: float = 0.0


@dataclass(frozen=True, slots=True)
class LiquiditySnapshot:
    timestamp: str
    symbol: str
    timeframe: str
    version: int
    levels: tuple[LiquidityLevel, ...] = ()
    pools: tuple[LiquidityPool, ...] = ()
    sweeps: tuple[LiquiditySweep, ...] = ()
    equal_highs: tuple[EqualHigh, ...] = ()
    equal_lows: tuple[EqualLow, ...] = ()
    zones: tuple[LiquidityZone, ...] = ()
    structure_version: int = 1
    engine_version: str = "EPIP-008"

    def __post_init__(self) -> None:
        self.validate_integrity()

    def validate_integrity(self) -> None:
        require_text(self.timestamp, "liquidity_snapshot.timestamp")
        require_text(self.symbol, "liquidity_snapshot.symbol")
        require_text(self.timeframe, "liquidity_snapshot.timeframe")
        require_version(self.version, "liquidity_snapshot.version")
        require_version(self.structure_version, "liquidity_snapshot.structure_version")
        require_text(self.engine_version, "liquidity_snapshot.engine_version")
        pool_ids = tuple(pool.pool_id for pool in self.pools)
        if len(pool_ids) != len(set(pool_ids)):
            raise RelationshipIntegrityError("liquidity snapshot contains duplicated pool IDs")
        if any(level.symbol != self.symbol for level in self.levels):
            raise RelationshipIntegrityError("liquidity snapshot contains a different symbol")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    @integrity_deserializer
    def from_dict(cls, data: dict[str, Any]) -> LiquiditySnapshot:
        level: Callable[[dict[str, Any]], LiquidityLevel] = lambda x: LiquidityLevel(
            **{
                **x,
                "side": LiquiditySide(x["side"]),
                "scope": LiquidityScope(x["scope"]),
                "status": LiquidityStatus(x["status"]),
            }
        )
        pool: Callable[[dict[str, Any]], LiquidityPool] = lambda x: LiquidityPool(
            **{
                **x,
                "side": LiquiditySide(x["side"]),
                "scope": LiquidityScope(x["scope"]),
                "level_indices": tuple(x["level_indices"]),
            }
        )
        sweep: Callable[[dict[str, Any]], LiquiditySweep] = lambda x: LiquiditySweep(
            **{**x, "side": LiquiditySide(x["side"])}
        )
        zone: Callable[[dict[str, Any]], LiquidityZone] = lambda x: LiquidityZone(
            **{**x, "side": LiquiditySide(x["side"])}
        )
        return cls(
            timestamp=data["timestamp"],
            symbol=data["symbol"],
            timeframe=data["timeframe"],
            version=int(data["version"]),
            levels=tuple(level(x) for x in data.get("levels", ())),
            pools=tuple(pool(x) for x in data.get("pools", ())),
            sweeps=tuple(sweep(x) for x in data.get("sweeps", ())),
            equal_highs=tuple(
                EqualHigh(
                    **{**x, "indices": tuple(x["indices"]), "timestamps": tuple(x["timestamps"])}
                )
                for x in data.get("equal_highs", ())
            ),
            equal_lows=tuple(
                EqualLow(
                    **{**x, "indices": tuple(x["indices"]), "timestamps": tuple(x["timestamps"])}
                )
                for x in data.get("equal_lows", ())
            ),
            zones=tuple(zone(x) for x in data.get("zones", ())),
            structure_version=int(data.get("structure_version", 1)),
            engine_version=str(data.get("engine_version", "EPIP-008")),
        )

    @classmethod
    @integrity_deserializer
    def from_json(cls, payload: str) -> LiquiditySnapshot:
        return cls.from_dict(json.loads(payload))
