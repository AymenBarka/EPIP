from dataclasses import replace

from epip.decision.models import DecisionAction
from epip.risk.config import PortfolioLimits, RiskConfig
from epip.risk.drawdown import within_drawdown_limits
from epip.risk.exposure import calculate_exposure
from epip.risk.leverage import calculate_leverage
from epip.risk.margin import calculate_margin
from epip.risk.models import Drawdown
from epip.risk.stop_manager import StopManager
from epip.risk.take_profit import TakeProfitManager
from epip.risk.validators import validate_config
from tests.risk.helpers import decision


def test_exposure_drawdown_margin_leverage() -> None:
    exposure = calculate_exposure("X", 10_000, 100_000, 0.1, 0.2)
    assert exposure.symbol_exposure == 0.2 and exposure.total_exposure == 0.4
    assert within_drawdown_limits(Drawdown(), PortfolioLimits())
    assert not within_drawdown_limits(Drawdown(daily=1), PortfolioLimits())
    leverage = calculate_leverage(50_000, 100_000, 5)
    assert leverage.required == 0.5
    margin = calculate_margin(50_000, 2, 100_000, 10_000)
    assert margin.required == 25_000 and margin.remaining == 65_000


def test_stop_and_targets_long_short_and_fallbacks() -> None:
    config = RiskConfig(trailing_stop=True, break_even_trigger=1.0)
    long = decision().decision
    stop = StopManager().build(long, 100, config, structure_price=97)
    assert stop.kind == "STRUCTURE" and stop.trailing
    targets = TakeProfitManager().build(long, 100, stop)
    assert len(targets) == 3 and sum(item.fraction for item in targets) == 1
    short = decision(action=DecisionAction.SHORT).decision
    short = replace(
        short,
        exit_zone=replace(short.exit_zone, stop_loss=None),
        invalidation=replace(short.invalidation, price=None),
    )
    atr_stop = StopManager().build(short, 100, config, atr=2)
    assert atr_stop.price == 104 and atr_stop.kind == "ATR"


def test_config_validation() -> None:
    validate_config(RiskConfig())
