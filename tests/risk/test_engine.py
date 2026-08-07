import pytest

from epip.core.event_bus import EventBus
from epip.decision.models import DecisionAction
from epip.risk import (
    Drawdown,
    DrawdownExceeded,
    ExposureExceeded,
    PositionPlanned,
    RiskAccepted,
    RiskConfig,
    RiskEngine,
    RiskRejected,
)
from epip.risk.config import PortfolioLimits
from epip.risk.exceptions import InvalidRiskInputError
from tests.risk.helpers import decision


def test_engine_accepts_and_maintains_state() -> None:
    bus = EventBus()
    engine = RiskEngine(config=RiskConfig(), event_bus=bus)
    first = engine.process(decision())
    second = engine.process(decision(version=2))
    assert first.plan.accepted and second.version == 2
    assert engine.snapshot("EURUSD", "H1") == second
    assert engine.history("EURUSD", "H1").latest() == second
    assert engine.graph("EURUSD", "H1").previous("EURUSD:H1:v2") is not None
    assert engine.metrics().plans == 2 and engine.metrics().accepted == 2
    assert isinstance(bus.event_history()[0], PositionPlanned)
    assert any(isinstance(event, RiskAccepted) for event in bus.event_history())


def test_engine_rejects_limits_and_publishes_events() -> None:
    bus = EventBus()
    config = RiskConfig(
        limits=PortfolioLimits(max_symbol_exposure=0.01, max_correlated_exposure=0.01)
    )
    engine = RiskEngine(config=config, event_bus=bus)
    snapshot = engine.process(
        decision(),
        current_symbol_exposure=0.5,
        correlated_exposure=0.5,
        drawdown=Drawdown(0.9, 0.9, 0.9),
    )
    assert not snapshot.plan.accepted and engine.metrics().rejected == 1
    assert any(isinstance(event, RiskRejected) for event in bus.event_history())
    assert any(isinstance(event, ExposureExceeded) for event in bus.event_history())
    assert any(isinstance(event, DrawdownExceeded) for event in bus.event_history())


@pytest.mark.parametrize("action", [DecisionAction.WAIT, DecisionAction.INVALID])
def test_invalid_decisions(action: DecisionAction) -> None:
    engine = RiskEngine(config=RiskConfig(), event_bus=EventBus())
    with pytest.raises(InvalidRiskInputError):
        engine.process(decision(action=action))


def test_invalid_config() -> None:
    with pytest.raises(InvalidRiskInputError):
        RiskEngine(config=RiskConfig(account_equity=0), event_bus=EventBus())
    assert RiskEngine(config=RiskConfig(), event_bus=EventBus()).snapshot("x", "y") is None
