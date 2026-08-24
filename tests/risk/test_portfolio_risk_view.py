from dataclasses import FrozenInstanceError

import pytest

from epip.core.integrity import DataIntegrityError
from epip.risk import PortfolioRiskView
from epip.strategy_runtime._base import digest


def view(**changes: object) -> PortfolioRiskView:
    values: dict[str, object] = {
        "contract_version": "p01-v1",
        "portfolio_version": 3,
        "as_of_timestamp": "2026-08-24T12:30:15.000000Z",
        "base_currency": "USD",
        "equity": 100_000.0,
        "available_capital": 90_000.0,
        "used_margin": 10_000.0,
        "gross_exposure": 0.4,
        "net_exposure": -0.1,
        "instrument_exposure": 0.2,
        "open_risk_amount": None,
        "current_leverage": None,
        "drawdown_fraction": 0.05,
        "open_position_count": 2,
        "correlation_exposure": (("fx", 0.2),),
        "limit_facts": ("within-limits",),
        "source_execution_version": 5,
        "source_digest": "d" * 64,
    }
    values.update(changes)
    return PortfolioRiskView(view_id=digest(values), **values)  # type: ignore[arg-type]


def test_portfolio_risk_view_is_immutable_and_allows_explicit_unknowns() -> None:
    value = view()
    assert value.open_risk_amount is None and value.current_leverage is None
    assert hash(value)
    with pytest.raises(FrozenInstanceError):
        value.equity = 1.0  # type: ignore[misc]


@pytest.mark.parametrize(
    "change", [{"equity": float("nan")}, {"drawdown_fraction": 1.1}, {"open_position_count": -1}]
)
def test_portfolio_risk_view_fails_closed(change: dict[str, object]) -> None:
    with pytest.raises(DataIntegrityError):
        view(**change)
