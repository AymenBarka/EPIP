"""Deterministic structure/liquidity/swing confluence."""

from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot, TrendDirection
from epip.swing.models import SwingSequence


def confluence_score(
    structure: MarketStructureSnapshot, liquidity: LiquiditySnapshot, swings: SwingSequence
) -> float:
    trend = (
        0.3
        if structure.structure.trend.direction not in (TrendDirection.UNKNOWN, TrendDirection.RANGE)
        else 0.1
    )
    pools = min(0.25, 0.05 * len(liquidity.pools))
    sweeps = min(0.2, 0.1 * len(liquidity.sweeps))
    quality = min(0.25, 0.05 * len(swings.swings))
    return max(0.0, min(1.0, trend + pools + sweeps + quality))
