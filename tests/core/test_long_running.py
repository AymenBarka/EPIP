"""Long-running EventBus integrity test suitable for continuous integration."""

from epip.core.event_bus import EventBus
from epip.core.events import BaseEvent


def test_one_hundred_thousand_sequential_events_remain_lossless() -> None:
    total = 100_000
    bus = EventBus()
    for sequence in range(total):
        bus.publish(BaseEvent(id=f"long:{sequence}", timestamp="2026-01-01T00:00:00+00:00"))
    history = bus.event_history()
    assert len(history) == total
    first = history[0]
    last = history[-1]
    assert isinstance(first, BaseEvent)
    assert isinstance(last, BaseEvent)
    assert first.id == "long:0"
    assert last.id == f"long:{total - 1}"
