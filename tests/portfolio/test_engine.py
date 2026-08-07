import pytest

from epip.core.event_bus import EventBus
from epip.execution.models import OrderSide
from epip.portfolio import (
    AllocationChanged,
    ExposureExceeded,
    PortfolioConfig,
    PortfolioEngine,
    PortfolioUpdated,
    PositionDirection,
    RiskLimitReached,
)
from epip.portfolio.exceptions import InvalidPortfolioInputError
from tests.portfolio.helpers import execution


def test_multiple_positions_and_metrics() -> None:
    bus = EventBus()
    engine = PortfolioEngine(event_bus=bus)
    first = engine.process(execution())
    second = engine.process(execution(symbol="GBPUSD", side=OrderSide.SHORT, version=2))
    assert first.version == 1 and second.version == 2 and len(second.state.positions) == 2
    assert second.state.exposure.long_exposure > 0 and second.state.exposure.short_exposure > 0
    assert engine.snapshot() == second and engine.history().latest() == second
    assert engine.graph().previous("portfolio:v2") is not None
    assert engine.metrics().snapshots == 2 and engine.metrics().positions == 2
    assert any(isinstance(event, PortfolioUpdated) for event in bus.event_history())
    assert any(isinstance(event, AllocationChanged) for event in bus.event_history())


def test_add_close_and_reverse_position() -> None:
    engine = PortfolioEngine(event_bus=EventBus())
    engine.process(execution(quantity=10, price=100))
    added = engine.process(execution(quantity=10, price=110, version=2))
    assert added.state.positions[0].average_price == 105
    reduced = engine.process(execution(side=OrderSide.SELL, quantity=5, price=120, version=3))
    assert reduced.state.positions[0].quantity == 15 and reduced.state.pnl.realized > 0
    reversed_state = engine.process(
        execution(side=OrderSide.SELL, quantity=20, price=90, version=4)
    )
    assert reversed_state.state.positions[0].direction == PositionDirection.SHORT
    closed = engine.process(execution(quantity=5, price=80, version=5))
    assert closed.state.positions == ()


def test_limits_correlations_and_rebalance_events() -> None:
    config = PortfolioConfig(
        max_gross_exposure=0.001,
        max_net_exposure=0.001,
        max_symbol_allocation=0.4,
        max_correlation_allocation=0.5,
        correlation_groups=(("FX", ("EURUSD", "GBPUSD")),),
    )
    bus = EventBus()
    engine = PortfolioEngine(event_bus=bus, config=config)
    snapshot = engine.process(execution())
    assert snapshot.state.limit_reasons
    assert engine.rebalance()[0].symbol == "EURUSD"
    assert any(isinstance(event, ExposureExceeded) for event in bus.event_history())
    assert any(isinstance(event, RiskLimitReached) for event in bus.event_history())


def test_validation() -> None:
    with pytest.raises(InvalidPortfolioInputError):
        PortfolioEngine(event_bus=EventBus(), config=PortfolioConfig(initial_capital=0))
    engine = PortfolioEngine(event_bus=EventBus())
    with pytest.raises(InvalidPortfolioInputError):
        engine.process(execution(completed=False))
    assert engine.snapshot() is None and engine.rebalance() == ()
