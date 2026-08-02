"""Builder for immutable Market Context aggregates."""

from epip.context.aggregator import MarketContextAggregator
from epip.context.snapshot import MarketContext, TrendContext
from epip.fibonacci.models import FibonacciSnapshot
from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence


class MarketContextBuilder:
    def __init__(self, aggregator: MarketContextAggregator | None = None) -> None:
        self._aggregator = aggregator or MarketContextAggregator()

    def build(
        self,
        swings: SwingSequence,
        structure: MarketStructureSnapshot,
        liquidity: LiquiditySnapshot,
        fibonacci: FibonacciSnapshot,
    ) -> MarketContext:
        confluence = self._aggregator.confluence(structure, liquidity, fibonacci)
        zones = {zone.name: zone for zone in fibonacci.zones}
        return MarketContext(
            symbol=swings.symbol,
            timeframe=swings.timeframe,
            swing_snapshot=swings,
            structure_snapshot=structure,
            liquidity_snapshot=liquidity,
            fibonacci_snapshot=fibonacci,
            trend=self._trend(structure),
            phase=self._aggregator.phase(structure),
            bias=self._aggregator.bias(structure.structure.trend.direction, confluence.score),
            confluence=confluence,
            premium=zones.get("PREMIUM"),
            discount=zones.get("DISCOUNT"),
            ote=zones.get("OTE"),
            golden_zone=zones.get("GOLDEN"),
            current_liquidity_pools=tuple(pool for pool in liquidity.pools if pool.resting),
            current_bos=structure.current_bos,
            current_choch=structure.current_choch,
        )

    @staticmethod
    def _trend(structure: MarketStructureSnapshot) -> TrendContext:
        return TrendContext(structure.structure.trend.direction, structure.confidence)
