"""Institutional property and boundary tests for portfolio accounting."""

import pytest

from epip.core.event_bus import EventBus
from epip.core.integrity import RelationshipIntegrityError
from epip.portfolio import PortfolioEngine
from epip.portfolio.allocation import calculate_allocations
from epip.portfolio.capital import used_margin
from epip.portfolio.equity import calculate_equity
from epip.portfolio.exposure import calculate_exposure
from epip.portfolio.models import (
    PortfolioEquity,
    PortfolioExposure,
    PortfolioPnL,
    PortfolioPosition,
    PositionDirection,
)
from epip.portfolio.pnl import calculate_pnl
from epip.portfolio.serialization import from_json, to_json
from tests.portfolio.helpers import execution


def position(symbol: str, direction: PositionDirection, value: float) -> PortfolioPosition:
    return PortfolioPosition(symbol, value / 100.0, direction, 100.0, 100.0)


def test_hedged_portfolio_preserves_exposure_identities() -> None:
    positions = (
        position("LONG", PositionDirection.LONG, 10_000.0),
        position("SHORT", PositionDirection.SHORT, 10_000.0),
    )
    exposure = calculate_exposure(positions, 10_000.0)
    assert exposure.gross_exposure == 2.0
    assert exposure.net_exposure == 0.0
    assert exposure.gross_exposure == exposure.long_exposure + exposure.short_exposure
    assert used_margin(positions, 0.2) == 4_000.0
    assert sum(item.fraction for item in calculate_allocations(positions, ())) == 1.0


def test_invalid_financial_identities_fail_fast() -> None:
    with pytest.raises(RelationshipIntegrityError):
        PortfolioExposure(1.0, 1.0, 1.0, 0.0, 0.5)
    with pytest.raises(RelationshipIntegrityError):
        PortfolioPnL(0.0, 0.0, 0.0, 1.0, 0.0, 2.0)
    with pytest.raises(RelationshipIntegrityError):
        PortfolioEquity(100.0, 50.0, 100.0, 0.5, 0.0, 60.0)


def test_equity_peak_drawdown_and_pnl_identities() -> None:
    equity = calculate_equity(
        initial=1_000.0,
        realized=100.0,
        unrealized=-50.0,
        commission=10.0,
        peak=1_100.0,
        cash=800.0,
        margin=200.0,
    )
    assert equity.current == 1_040.0
    assert equity.peak == 1_100.0
    assert equity.drawdown == pytest.approx(60.0 / 1_100.0)
    pnl = calculate_pnl(
        (PortfolioPosition("EURUSD", 1.0, PositionDirection.LONG, 100.0, 100.0, 0.0, -50.0),),
        100.0,
        10.0,
    )
    assert pnl.realized == 90.0
    assert pnl.unrealized == -50.0
    assert pnl.floating == pnl.unrealized


def test_periodic_pnl_is_explicitly_unavailable_and_round_trips() -> None:
    pnl = calculate_pnl((), 125.0, 5.0)
    assert (pnl.daily, pnl.weekly, pnl.monthly) == (None, None, None)
    assert pnl.realized == 120.0

    snapshot = PortfolioEngine(event_bus=EventBus()).process(execution())
    restored = from_json(to_json(snapshot))
    assert restored == snapshot
    assert restored.state.pnl.daily is None


def test_average_cost_increase_partial_close_and_complete_close() -> None:
    engine = PortfolioEngine(event_bus=EventBus())
    assert engine._apply_fill("EURUSD", 10.0, 100.0) == 0.0
    assert engine._apply_fill("EURUSD", 20.0, 115.0) == 0.0
    position = engine._positions["EURUSD"]
    assert position.quantity == 30.0
    assert position.average_price == 110.0

    assert engine._apply_fill("EURUSD", -5.0, 130.0) == 100.0
    position = engine._positions["EURUSD"]
    assert position.quantity == 25.0
    assert position.average_price == 110.0
    assert position.realized_pnl == 100.0

    assert engine._apply_fill("EURUSD", -25.0, 90.0) == -500.0
    assert "EURUSD" not in engine._positions


@pytest.mark.parametrize(
    ("opening", "closing", "direction", "expected_realized"),
    [
        (10.0, -15.0, PositionDirection.SHORT, 200.0),
        (-10.0, 15.0, PositionDirection.LONG, -200.0),
    ],
)
def test_average_cost_reversal_resets_basis_to_reversal_fill(
    opening: float,
    closing: float,
    direction: PositionDirection,
    expected_realized: float,
) -> None:
    engine = PortfolioEngine(event_bus=EventBus())
    engine._apply_fill("EURUSD", opening, 100.0)
    assert engine._apply_fill("EURUSD", closing, 120.0) == expected_realized
    position = engine._positions["EURUSD"]
    assert position.quantity == 5.0
    assert position.direction == direction
    assert position.average_price == 120.0
