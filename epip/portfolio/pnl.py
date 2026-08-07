"""Portfolio PnL calculations."""

from epip.portfolio.models import PortfolioPnL, PortfolioPosition


def calculate_pnl(
    positions: tuple[PortfolioPosition, ...], realized: float, commission: float
) -> PortfolioPnL:
    unrealized = sum(position.unrealized_pnl for position in positions)
    net_realized = realized - commission
    return PortfolioPnL(
        net_realized, net_realized, net_realized, unrealized, net_realized, unrealized
    )
