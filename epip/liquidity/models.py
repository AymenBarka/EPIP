"""Immutable EPIP-008 liquidity domain models."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
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
    def from_json(cls, payload: str) -> LiquiditySnapshot:
        return cls.from_dict(json.loads(payload))
