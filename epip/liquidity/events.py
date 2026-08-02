"""Liquidity domain events."""

from dataclasses import dataclass

from epip.core.events import BaseEvent
from epip.liquidity.models import LiquiditySide


@dataclass(frozen=True, slots=True, kw_only=True)
class LiquidityEvent(BaseEvent):
    symbol: str
    timeframe: str


@dataclass(frozen=True, slots=True, kw_only=True)
class LiquidityDetected(LiquidityEvent):
    version: int


@dataclass(frozen=True, slots=True, kw_only=True)
class LiquidityPoolCreated(LiquidityEvent):
    pool_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class LiquiditySweepDetected(LiquidityEvent):
    side: LiquiditySide
    price: float


@dataclass(frozen=True, slots=True, kw_only=True)
class EqualHighDetected(LiquidityEvent):
    price: float


@dataclass(frozen=True, slots=True, kw_only=True)
class EqualLowDetected(LiquidityEvent):
    price: float


@dataclass(frozen=True, slots=True, kw_only=True)
class LiquidityConsumed(LiquidityEvent):
    pool_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class LiquidityInvalidated(LiquidityEvent):
    pool_id: str
