"""Portfolio-wide risk-limit validation."""

from epip.portfolio.config import PortfolioConfig
from epip.portfolio.models import PortfolioAllocation, PortfolioEquity, PortfolioExposure


def evaluate_limits(
    exposure: PortfolioExposure,
    allocations: tuple[PortfolioAllocation, ...],
    correlations: tuple[tuple[str, float], ...],
    equity: PortfolioEquity,
    config: PortfolioConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if exposure.gross_exposure > config.max_gross_exposure:
        reasons.append("GROSS_EXPOSURE")
    if abs(exposure.net_exposure) > config.max_net_exposure:
        reasons.append("NET_EXPOSURE")
    if any(item.fraction > config.max_symbol_allocation for item in allocations):
        reasons.append("SYMBOL_ALLOCATION")
    if any(value > config.max_correlation_allocation for _, value in correlations):
        reasons.append("CORRELATION_CONCENTRATION")
    if equity.drawdown > config.max_drawdown:
        reasons.append("DRAWDOWN")
    return tuple(reasons)
