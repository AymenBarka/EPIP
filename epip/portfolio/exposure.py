"""Official global portfolio exposure calculations."""

from epip.portfolio.models import PortfolioExposure, PortfolioPosition, PositionDirection


def calculate_exposure(
    positions: tuple[PortfolioPosition, ...], equity: float
) -> PortfolioExposure:
    long_value = sum(p.market_value for p in positions if p.direction == PositionDirection.LONG)
    short_value = sum(p.market_value for p in positions if p.direction == PositionDirection.SHORT)
    gross = long_value + short_value
    net = long_value - short_value
    concentration = max((p.market_value for p in positions), default=0.0) / max(gross, 1.0)
    scale = max(equity, 1.0)
    return PortfolioExposure(
        long_value / scale, short_value / scale, gross / scale, net / scale, concentration
    )
