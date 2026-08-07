"""Liquidity zone derivation."""

from epip.liquidity.models import LiquidityPool, LiquidityZone


def zones_from_pools(
    pools: tuple[LiquidityPool, ...], threshold: float
) -> tuple[LiquidityZone, ...]:
    return tuple(
        LiquidityZone(x.symbol, x.timeframe, x.price - threshold, x.price + threshold, x.side)
        for x in pools
    )
