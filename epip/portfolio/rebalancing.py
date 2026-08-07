"""Deterministic rebalancing recommendations."""

from dataclasses import dataclass

from epip.portfolio.models import PortfolioAllocation


@dataclass(frozen=True, slots=True)
class RebalanceInstruction:
    symbol: str
    current_fraction: float
    target_fraction: float


def recommend_rebalance(
    allocations: tuple[PortfolioAllocation, ...], maximum: float
) -> tuple[RebalanceInstruction, ...]:
    return tuple(
        RebalanceInstruction(item.symbol, item.fraction, maximum)
        for item in allocations
        if item.fraction > maximum
    )
