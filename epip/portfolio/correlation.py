"""Deterministic correlation-group aggregation."""

from epip.portfolio.models import PortfolioAllocation


def correlation_exposure(
    allocations: tuple[PortfolioAllocation, ...],
) -> tuple[tuple[str, float], ...]:
    totals: dict[str, float] = {}
    for allocation in allocations:
        if allocation.correlation_group is not None:
            totals[allocation.correlation_group] = (
                totals.get(allocation.correlation_group, 0.0) + allocation.fraction
            )
    return tuple(sorted(totals.items()))
