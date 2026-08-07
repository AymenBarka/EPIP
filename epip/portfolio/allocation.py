"""Capital allocation calculations."""

from epip.portfolio.models import PortfolioAllocation, PortfolioPosition


def calculate_allocations(
    positions: tuple[PortfolioPosition, ...], groups: tuple[tuple[str, tuple[str, ...]], ...]
) -> tuple[PortfolioAllocation, ...]:
    total = sum(position.market_value for position in positions)
    symbol_groups = {symbol: name for name, symbols in groups for symbol in symbols}
    return tuple(
        PortfolioAllocation(
            position.symbol,
            position.market_value,
            position.market_value / total if total else 0.0,
            symbol_groups.get(position.symbol),
        )
        for position in sorted(positions, key=lambda item: item.symbol)
    )
