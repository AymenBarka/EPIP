import pytest

from epip.core.event_bus import EventBus
from epip.fibonacci import FibonacciConfig, FibonacciEngine
from epip.fibonacci.exceptions import InvalidFibonacciInputError
from tests.fibonacci.helpers import inputs


def test_engine_bull_bear_range_multi_stream() -> None:
    engine = FibonacciEngine(config=FibonacciConfig(), event_bus=EventBus())
    s, m, l = inputs()
    a = engine.process(s, m, l)
    b = engine.process(s, m, l)
    assert (a.version, b.version) == (1, 2)
    assert engine.history("EURUSD", "M1").latest() == b
    assert engine.graph("EURUSD", "M1").nodes
    assert engine.metrics().computations == 2
    s2, m2, l2 = inputs("GBPUSD", "M5")
    assert engine.process(s2, m2, l2).symbol == "GBPUSD"
    with pytest.raises(InvalidFibonacciInputError):
        engine.process(s, m, l2)
