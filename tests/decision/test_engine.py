import pytest

from epip.core.event_bus import EventBus
from epip.decision import DecisionAction, DecisionConfig, DecisionEngine
from epip.decision.exceptions import InvalidDecisionInputError
from tests.decision.helpers import snapshots


def test_engine_long_multi_stream_and_versions() -> None:
    engine = DecisionEngine(config=DecisionConfig(), event_bus=EventBus())
    context, elliott = snapshots()
    first = engine.process(context, elliott)
    second = engine.process(context, elliott)
    other = engine.process(*snapshots(symbol="GBPUSD", timeframe="H1"))
    assert first.decision.action == DecisionAction.LONG
    assert second.decision.action == DecisionAction.ADD
    assert (first.version, second.version, other.version) == (1, 2, 1)
    assert engine.snapshot("EURUSD", "M15") == second
    assert engine.metrics().decisions == 3


def test_engine_rejects_misaligned_elliott() -> None:
    context, _ = snapshots()
    _, other = snapshots(symbol="GBPUSD")
    with pytest.raises(InvalidDecisionInputError):
        DecisionEngine(config=DecisionConfig(), event_bus=EventBus()).process(context, other)
