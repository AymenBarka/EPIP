"""Failure-injection tests for engine in-memory transaction boundaries."""

from __future__ import annotations

import pytest

from epip.context import MarketContextConfig, MarketContextEngine
from epip.context.history import MarketContextHistory
from epip.core.atomicity import EngineTransaction
from epip.core.event_bus import EventBus
from epip.portfolio import PortfolioEngine
from tests.context.helpers import official_inputs
from tests.portfolio.helpers import execution


class _FailingOwner:
    def __init__(self) -> None:
        self.first = "old-first"
        self._second = "old-second"

    @property
    def second(self) -> str:
        return self._second

    @second.setter
    def second(self, value: str) -> None:
        if value == "fail":
            raise RuntimeError("commit failure")
        self._second = value


def test_commit_rollback_restores_every_reference() -> None:
    owner = _FailingOwner()
    transaction = EngineTransaction(owner)
    transaction.stage("first", "new-first")
    transaction.stage("second", "fail")

    with pytest.raises(RuntimeError, match="commit failure"):
        transaction.commit()

    assert owner.first == "old-first"
    assert owner.second == "old-second"


def test_context_history_failure_leaves_previous_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bus = EventBus()
    engine = MarketContextEngine(config=MarketContextConfig(), event_bus=bus)
    inputs = official_inputs()
    previous = engine.process(*inputs)
    history = engine.history(previous.symbol, previous.timeframe)
    graph = engine.graph(previous.symbol, previous.timeframe)
    events = bus.event_history()

    def fail_append(self: MarketContextHistory, snapshot: object) -> MarketContextHistory:
        raise RuntimeError("history failure")

    monkeypatch.setattr(MarketContextHistory, "append", fail_append)
    with pytest.raises(RuntimeError, match="history failure"):
        engine.process(*inputs)

    assert engine.snapshot(previous.symbol, previous.timeframe) is previous
    assert engine.history(previous.symbol, previous.timeframe) == history
    assert engine.graph(previous.symbol, previous.timeframe) == graph
    assert bus.event_history() == events


def test_portfolio_calculation_failure_does_not_apply_fill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bus = EventBus()
    engine = PortfolioEngine(event_bus=bus)
    previous = engine.process(execution())
    history = engine.history()
    graph = engine.graph()
    metrics = engine.metrics()
    events = bus.event_history()

    def fail_exposure(*args: object, **kwargs: object) -> object:
        raise RuntimeError("calculation failure")

    monkeypatch.setattr("epip.portfolio.engine.calculate_exposure", fail_exposure)
    with pytest.raises(RuntimeError, match="calculation failure"):
        engine.process(execution(version=2, price=110))

    assert engine.snapshot() is previous
    assert engine.history() == history
    assert engine.graph() == graph
    assert engine.metrics() == metrics
    assert bus.event_history() == events
