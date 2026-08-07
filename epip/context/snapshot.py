"""Immutable EPIP-010 Market Context domain snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from epip.fibonacci.models import FibonacciSnapshot, FibonacciZone
from epip.liquidity.models import LiquidityPool, LiquiditySnapshot
from epip.market_structure.models import (
    BreakOfStructure,
    ChangeOfCharacter,
    MarketStructureSnapshot,
    TrendDirection,
)
from epip.swing.models import SwingSequence


class MarketPhase(StrEnum):
    UNKNOWN = "UNKNOWN"
    ACCUMULATION = "ACCUMULATION"
    MARKUP = "MARKUP"
    DISTRIBUTION = "DISTRIBUTION"
    MARKDOWN = "MARKDOWN"
    RANGE = "RANGE"


class InstitutionalBias(StrEnum):
    STRONGLY_BULLISH = "STRONGLY_BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    STRONGLY_BEARISH = "STRONGLY_BEARISH"


@dataclass(frozen=True, slots=True)
class MarketContextVersion:
    context: int
    structure: int
    liquidity: int
    fibonacci: int


@dataclass(frozen=True, slots=True)
class TrendContext:
    direction: TrendDirection
    confidence: float


@dataclass(frozen=True, slots=True)
class BiasContext:
    bias: InstitutionalBias
    score: float


@dataclass(frozen=True, slots=True)
class ConfluenceContext:
    score: float
    structure_score: float
    liquidity_score: float
    fibonacci_score: float


@dataclass(frozen=True, slots=True)
class MarketContext:
    symbol: str
    timeframe: str
    swing_snapshot: SwingSequence
    structure_snapshot: MarketStructureSnapshot
    liquidity_snapshot: LiquiditySnapshot
    fibonacci_snapshot: FibonacciSnapshot
    trend: TrendContext
    phase: MarketPhase
    bias: BiasContext
    confluence: ConfluenceContext
    premium: FibonacciZone | None
    discount: FibonacciZone | None
    ote: FibonacciZone | None
    golden_zone: FibonacciZone | None
    current_liquidity_pools: tuple[LiquidityPool, ...]
    current_bos: BreakOfStructure | None
    current_choch: ChangeOfCharacter | None

    @property
    def confluence_score(self) -> float:
        return self.confluence.score

    @property
    def institutional_bias(self) -> InstitutionalBias:
        return self.bias.bias


@dataclass(frozen=True, slots=True)
class MarketContextSnapshot:
    timestamp: str
    version: MarketContextVersion
    context: MarketContext
    engine_version: str = "EPIP-010"

    @property
    def symbol(self) -> str:
        return self.context.symbol

    @property
    def timeframe(self) -> str:
        return self.context.timeframe

    def to_dict(self) -> dict[str, Any]:
        from epip.context.serialization import to_dict

        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketContextSnapshot:
        from epip.context.serialization import from_dict

        return from_dict(data)

    def to_json(self) -> str:
        from epip.context.serialization import to_json

        return to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> MarketContextSnapshot:
        from epip.context.serialization import from_json

        return from_json(payload)
