"""Pure aggregation of official upstream scores and states."""

from epip.context.snapshot import (
    BiasContext,
    ConfluenceContext,
    InstitutionalBias,
    MarketPhase,
)
from epip.fibonacci.models import FibonacciSnapshot
from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot, StructureState, TrendDirection


class MarketContextAggregator:
    def confluence(
        self,
        structure: MarketStructureSnapshot,
        liquidity: LiquiditySnapshot,
        fibonacci: FibonacciSnapshot,
    ) -> ConfluenceContext:
        resting = tuple(pool for pool in liquidity.pools if pool.resting)
        liquidity_score = (
            sum(pool.confluence_score for pool in resting) / len(resting) if resting else 0.0
        )
        score = max(
            0.0,
            min(
                1.0,
                (structure.confidence + liquidity_score + fibonacci.confluence_score) / 3.0,
            ),
        )
        return ConfluenceContext(
            score, structure.confidence, liquidity_score, fibonacci.confluence_score
        )

    def phase(self, structure: MarketStructureSnapshot) -> MarketPhase:
        state = structure.structure.state
        if state == StructureState.ACCUMULATION:
            return MarketPhase.ACCUMULATION
        if state == StructureState.DISTRIBUTION:
            return MarketPhase.DISTRIBUTION
        if state == StructureState.UPTREND:
            return MarketPhase.MARKUP
        if state == StructureState.DOWNTREND:
            return MarketPhase.MARKDOWN
        if state == StructureState.RANGE:
            return MarketPhase.RANGE
        return MarketPhase.UNKNOWN

    def bias(self, direction: TrendDirection, confluence: float) -> BiasContext:
        if direction == TrendDirection.UPTREND:
            bias = (
                InstitutionalBias.STRONGLY_BULLISH
                if confluence >= 0.75
                else InstitutionalBias.BULLISH
            )
            score = confluence
        elif direction == TrendDirection.DOWNTREND:
            bias = (
                InstitutionalBias.STRONGLY_BEARISH
                if confluence >= 0.75
                else InstitutionalBias.BEARISH
            )
            score = -confluence
        else:
            bias = InstitutionalBias.NEUTRAL
            score = 0.0
        return BiasContext(bias, score)
