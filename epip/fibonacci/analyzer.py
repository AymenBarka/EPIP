from epip.fibonacci.config import FibonacciConfig
from epip.fibonacci.confluence import confluence_score
from epip.fibonacci.extensions import compute_extension
from epip.fibonacci.models import FibonacciDirection, FibonacciSnapshot
from epip.fibonacci.ote import ote_zones
from epip.fibonacci.premium_discount import premium_discount
from epip.fibonacci.retracements import compute_retracement
from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot, TrendDirection
from epip.swing.models import SwingSequence


class FibonacciAnalyzer:
    def __init__(self, c: FibonacciConfig) -> None:
        self.config = c

    def analyze(
        self,
        swings: SwingSequence,
        structure: MarketStructureSnapshot,
        liquidity: LiquiditySnapshot,
        version: int,
    ) -> FibonacciSnapshot:
        selected = tuple(x for x in swings.swings if x.point.confirmed)[-2:]
        start, end = selected[0].point.price, selected[1].point.price
        trend = structure.structure.trend.direction
        direction = (
            FibonacciDirection.BULLISH
            if trend == TrendDirection.UPTREND
            else (
                FibonacciDirection.BEARISH
                if trend == TrendDirection.DOWNTREND
                else FibonacciDirection.RANGE
            )
        )
        score = confluence_score(structure, liquidity, swings)
        retr = compute_retracement(start, end, self.config.levels, direction, score)
        ext = compute_extension(start, end, self.config.levels, direction, score)
        premium, discount = premium_discount(start, end, score)
        ote, golden = ote_zones(
            start,
            end,
            direction,
            self.config.ote_low,
            self.config.ote_high,
            self.config.golden_low,
            self.config.golden_high,
            score,
        )
        return FibonacciSnapshot(
            selected[-1].point.timestamp,
            swings.symbol,
            swings.timeframe,
            version,
            direction,
            retr,
            ext,
            (premium, discount, ote, golden),
            score,
            structure.version,
            liquidity.version,
            probability=score,
        )
