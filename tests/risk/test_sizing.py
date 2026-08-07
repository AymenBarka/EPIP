import pytest

from epip.risk.config import RiskConfig
from epip.risk.models import RiskProfile, SizingMethod
from epip.risk.position_sizer import PositionSizer, kelly_criterion


@pytest.mark.parametrize(
    "method,kwargs",
    [
        (SizingMethod.FIXED_RISK, {}),
        (SizingMethod.FIXED_AMOUNT, {}),
        (SizingMethod.KELLY, {}),
        (SizingMethod.FRACTIONAL_KELLY, {}),
        (SizingMethod.ATR, {"atr": 2.0}),
        (SizingMethod.VOLATILITY_ADJUSTED, {"volatility": 0.02}),
    ],
)
def test_sizing_methods(method: SizingMethod, kwargs: dict[str, float]) -> None:
    profile = RiskProfile(method, 0.01, fixed_amount=500, kelly_fraction=0.25)
    size = PositionSizer().size(100, 98, 0.6, RiskConfig(profile=profile), **kwargs)
    assert size.quantity >= 0 and size.notional <= 100_000 and size.method == method


def test_kelly_and_sizing_edges() -> None:
    assert kelly_criterion(0.6, 2) == pytest.approx(0.4)
    assert kelly_criterion(0.5, 0) == 0 and kelly_criterion(0, 1) == 0
    assert PositionSizer().size(100, 100, 0.5, RiskConfig()).quantity == 0
    config = RiskConfig(min_position_size=999999)
    assert PositionSizer().size(100, 99, 0.5, config).risk_amount == 0
