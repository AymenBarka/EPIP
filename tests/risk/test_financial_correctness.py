"""Institutional regression tests for risk and margin mathematics."""

import pytest

from epip.core.integrity import RelationshipIntegrityError
from epip.risk.margin import calculate_margin
from epip.risk.models import Margin
from epip.risk.position_sizer import kelly_criterion


def test_zero_notional_margin_is_finite_and_neutral() -> None:
    margin = calculate_margin(0.0, 5.0, 100_000.0)
    assert margin == Margin(0.0, 0.0, 100_000.0, 1.0)


@pytest.mark.parametrize(
    ("probability", "reward_risk", "expected"),
    [(0.0, 2.0, 0.0), (0.5, 1.0, 0.0), (0.6, 2.0, 0.4), (1.0, 2.0, 1.0)],
)
def test_kelly_formula_is_bounded(probability: float, reward_risk: float, expected: float) -> None:
    assert kelly_criterion(probability, reward_risk) == pytest.approx(expected)


def test_margin_rejects_used_value_below_required_margin() -> None:
    with pytest.raises(RelationshipIntegrityError):
        Margin(60.0, 50.0, 0.0, 0.0)
