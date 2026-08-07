"""Portfolio capital accounting."""

from epip.portfolio.models import PortfolioPosition


def used_margin(positions: tuple[PortfolioPosition, ...], margin_rate: float) -> float:
    return sum(position.market_value for position in positions) * margin_rate


def available_cash(initial: float, realized: float, commission: float, margin: float) -> float:
    return max(0.0, initial + realized - commission - margin)
