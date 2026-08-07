"""Immutable heterogeneous liquidity clusters."""

from dataclasses import dataclass

from epip.liquidity.fvg import FairValueGap
from epip.liquidity.models import EqualHigh, EqualLow, LiquidityPool
from epip.liquidity.voids import LiquidityVoid


@dataclass(frozen=True, slots=True)
class LiquidityCluster:
    cluster_id: str
    equal_highs: tuple[EqualHigh, ...] = ()
    equal_lows: tuple[EqualLow, ...] = ()
    pools: tuple[LiquidityPool, ...] = ()
    fair_value_gaps: tuple[FairValueGap, ...] = ()
    voids: tuple[LiquidityVoid, ...] = ()
    confluence_score: float = 0.0
