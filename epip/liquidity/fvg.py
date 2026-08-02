"""Fair Value Gap domain models and future detector contract."""

from dataclasses import dataclass

from epip.liquidity.models import LiquidityScope


@dataclass(frozen=True, slots=True)
class FairValueGap:
    symbol: str
    timeframe: str
    timestamp: str
    low: float
    high: float
    scope: LiquidityScope
    filled_ratio: float = 0.0
    confluence_score: float = 0.0


@dataclass(frozen=True, slots=True)
class BullishFVG(FairValueGap):
    pass


@dataclass(frozen=True, slots=True)
class BearishFVG(FairValueGap):
    pass


class FairValueGapDetector:
    def detect(self, *_args: object, **_kwargs: object) -> tuple[FairValueGap, ...]:
        return ()
