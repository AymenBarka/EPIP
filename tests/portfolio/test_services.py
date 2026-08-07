from epip.portfolio.allocation import calculate_allocations
from epip.portfolio.capital import available_cash, used_margin
from epip.portfolio.correlation import correlation_exposure
from epip.portfolio.equity import calculate_equity
from epip.portfolio.exposure import calculate_exposure
from epip.portfolio.models import PortfolioPosition, PositionDirection
from epip.portfolio.pnl import calculate_pnl
from epip.portfolio.rebalancing import recommend_rebalance


def positions() -> tuple[PortfolioPosition, ...]:
    return (
        PortfolioPosition("A", 10, PositionDirection.LONG, 100, 110, 0, 100),
        PortfolioPosition("B", 5, PositionDirection.SHORT, 100, 90, 0, 50),
    )


def test_exposure_allocations_and_correlation() -> None:
    values = positions()
    exposure = calculate_exposure(values, 1000)
    assert exposure.long_exposure == 1.1 and exposure.short_exposure == 0.45
    assert exposure.gross_exposure == 1.55 and exposure.net_exposure == 0.65
    allocations = calculate_allocations(values, (("GROUP", ("A", "B")),))
    assert sum(item.fraction for item in allocations) == 1
    assert correlation_exposure(allocations) == (("GROUP", 1.0),)
    assert recommend_rebalance(allocations, 0.5)


def test_capital_pnl_equity() -> None:
    values = positions()
    margin = used_margin(values, 0.2)
    assert margin == 310 and available_cash(1000, 20, 5, margin) == 705
    pnl = calculate_pnl(values, 20, 5)
    assert pnl.realized == 15 and pnl.unrealized == 150
    equity = calculate_equity(1000, 20, 150, 5, 1200, 705, margin)
    assert equity.current == 1165 and equity.drawdown > 0
