"""Portfolio equity and drawdown calculations."""

from epip.portfolio.models import PortfolioEquity


def calculate_equity(
    initial: float,
    realized: float,
    unrealized: float,
    commission: float,
    peak: float,
    cash: float,
    margin: float,
) -> PortfolioEquity:
    current = initial + realized + unrealized - commission
    current_peak = max(peak, current)
    drawdown = (current_peak - current) / current_peak if current_peak else 0.0
    return PortfolioEquity(initial, current, current_peak, drawdown, cash, margin)
