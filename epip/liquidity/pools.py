"""Liquidity pool construction."""

from epip.liquidity.config import LiquidityConfig
from epip.liquidity.models import EqualHigh, EqualLow, LiquidityPool, LiquidityScope, LiquiditySide


class LiquidityPoolDetector:
    def detect(
        self, highs: tuple[EqualHigh, ...], lows: tuple[EqualLow, ...], config: LiquidityConfig
    ) -> tuple[LiquidityPool, ...]:
        pools = [
            LiquidityPool(
                f"BSL:{x.symbol}:{x.timeframe}:{x.indices[0]}",
                x.symbol,
                x.timeframe,
                x.price,
                LiquiditySide.BUY_SIDE,
                LiquidityScope.EXTERNAL,
                len(x.indices),
                x.indices,
            )
            for x in highs
            if len(x.indices) >= config.minimum_pool_size
        ]
        pools += [
            LiquidityPool(
                f"SSL:{x.symbol}:{x.timeframe}:{x.indices[0]}",
                x.symbol,
                x.timeframe,
                x.price,
                LiquiditySide.SELL_SIDE,
                LiquidityScope.EXTERNAL,
                len(x.indices),
                x.indices,
            )
            for x in lows
            if len(x.indices) >= config.minimum_pool_size
        ]
        return tuple(pools)
