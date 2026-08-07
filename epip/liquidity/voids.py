"""Liquidity void model and future detector."""

from dataclasses import dataclass

from epip.liquidity.models import LiquidityScope


@dataclass(frozen=True, slots=True)
class LiquidityVoid:
    symbol: str
    timeframe: str
    timestamp: str
    low: float
    high: float
    scope: LiquidityScope
    filled_ratio: float = 0.0
    confluence_score: float = 0.0


class LiquidityVoidDetector:
    def detect(self, *_args: object, **_kwargs: object) -> tuple[LiquidityVoid, ...]:
        return ()
