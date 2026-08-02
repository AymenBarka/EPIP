"""Liquidity sweep and stop-hunt detection."""

from epip.liquidity.config import LiquidityConfig
from epip.liquidity.models import LiquidityPool, LiquiditySide, LiquiditySweep
from epip.swing.models import SwingSequence


class LiquiditySweepDetector:
    def detect(
        self, sequence: SwingSequence, pools: tuple[LiquidityPool, ...], config: LiquidityConfig
    ) -> tuple[LiquiditySweep, ...]:
        last = sequence.last()
        if last is None:
            return ()
        result = []
        for pool in pools:
            crossed = (
                last.point.price > pool.price + config.minimum_distance
                if pool.side == LiquiditySide.BUY_SIDE
                else last.point.price < pool.price - config.minimum_distance
            )
            if crossed:
                confirmed = last.point.confirmed if config.sweep_confirmation else True
                result.append(
                    LiquiditySweep(
                        sequence.symbol,
                        sequence.timeframe,
                        last.point.timestamp,
                        pool.side,
                        pool.price,
                        last.point.price,
                        confirmed,
                        confirmed,
                    )
                )
        return tuple(result)
