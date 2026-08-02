"""Pure liquidity analysis orchestration."""

from epip.liquidity.config import LiquidityConfig
from epip.liquidity.equal_levels import EqualLevelDetector
from epip.liquidity.models import LiquidityLevel, LiquidityScope, LiquiditySide, LiquiditySnapshot
from epip.liquidity.pools import LiquidityPoolDetector
from epip.liquidity.sweeps import LiquiditySweepDetector
from epip.liquidity.zones import zones_from_pools
from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence
from epip.swing.types import PivotType, SwingScope


class LiquidityAnalyzer:
    def __init__(self, config: LiquidityConfig) -> None:
        self.config = config
        self.equal = EqualLevelDetector()
        self.pools = LiquidityPoolDetector()
        self.sweeps = LiquiditySweepDetector()

    def analyze(
        self, structure: MarketStructureSnapshot, sequence: SwingSequence, version: int
    ) -> LiquiditySnapshot:
        swings = tuple(
            x
            for x in sequence.swings
            if not self.config.internal_only or x.scope == SwingScope.INTERNAL
            if not self.config.external_only or x.scope == SwingScope.EXTERNAL
        )
        filtered = SwingSequence(sequence.symbol, sequence.timeframe, swings)
        highs, lows = self.equal.detect(filtered, self.config)
        pools = self.pools.detect(highs, lows, self.config)
        sweeps = self.sweeps.detect(filtered, pools, self.config)
        levels = tuple(
            LiquidityLevel(
                sequence.symbol,
                sequence.timeframe,
                x.point.timestamp,
                x.point.price,
                (
                    LiquiditySide.BUY_SIDE
                    if x.point.pivot_type == PivotType.HIGH
                    else LiquiditySide.SELL_SIDE
                ),
                (
                    LiquidityScope.INTERNAL
                    if x.scope == SwingScope.INTERNAL
                    else LiquidityScope.EXTERNAL
                ),
            )
            for x in swings
        )
        return LiquiditySnapshot(
            swings[-1].point.timestamp,
            sequence.symbol,
            sequence.timeframe,
            version,
            levels,
            pools,
            sweeps,
            highs,
            lows,
            zones_from_pools(pools, self.config.equal_threshold),
            structure.version,
        )
