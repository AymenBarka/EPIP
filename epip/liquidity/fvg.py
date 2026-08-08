"""Fair Value Gap domain models and future detector contract."""

from dataclasses import dataclass

from epip.core.integrity import (
    RelationshipIntegrityError,
    require_finite,
    require_text,
    require_unit_interval,
)
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

    def __post_init__(self) -> None:
        require_text(self.symbol, "fvg.symbol")
        require_text(self.timeframe, "fvg.timeframe")
        require_text(self.timestamp, "fvg.timestamp")
        low = require_finite(self.low, "fvg.low")
        high = require_finite(self.high, "fvg.high")
        if low > high:
            raise RelationshipIntegrityError("fvg.low must not exceed fvg.high")
        require_unit_interval(self.filled_ratio, "fvg.filled_ratio")
        require_unit_interval(self.confluence_score, "fvg.confluence_score")


@dataclass(frozen=True, slots=True)
class BullishFVG(FairValueGap):
    pass


@dataclass(frozen=True, slots=True)
class BearishFVG(FairValueGap):
    pass


class FairValueGapDetector:
    def detect(self, *_args: object, **_kwargs: object) -> tuple[FairValueGap, ...]:
        return ()
