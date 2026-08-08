"""Portfolio PnL calculations."""

from epip.portfolio.models import PortfolioPnL, PortfolioPosition


def calculate_pnl(
    positions: tuple[PortfolioPosition, ...], realized: float, commission: float
) -> PortfolioPnL:
    unrealized = sum(position.unrealized_pnl for position in positions)
    net_realized = realized - commission
    # EPIP has no trading calendar or period ledger.  Reporting cumulative
    # realized PnL as daily, weekly, or monthly would therefore be misleading.
    return PortfolioPnL(None, None, None, unrealized, net_realized, unrealized)
