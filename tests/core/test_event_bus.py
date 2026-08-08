from __future__ import annotations

import pytest

from epip.core.event_bus import EventBus
from epip.core.events import BaseEvent
from epip.core.integrity import EventIntegrityError


def test_event_bus_orders_and_histories_listeners() -> None:
    bus = EventBus()
    calls: list[str] = []

    def handler_one(event: object) -> None:
        calls.append(f"one:{event.id}")  # type: ignore[attr-defined]

    def handler_two(event: object) -> None:
        calls.append(f"two:{event.id}")  # type: ignore[attr-defined]

    bus.subscribe(BaseEvent, handler_one)
    bus.subscribe(BaseEvent, handler_two)

    events = tuple(BaseEvent(id=value, timestamp="t") for value in ("alpha", "beta", "gamma"))
    bus.publish(events[0])
    bus.publish_many(events[1:])

    assert calls == ["one:alpha", "two:alpha", "one:beta", "two:beta", "one:gamma", "two:gamma"]
    assert bus.listener_count(BaseEvent) == 2
    assert bus.listeners(BaseEvent) == (handler_one, handler_two)
    assert bus.event_history() == events

    bus.unsubscribe(BaseEvent, handler_two)
    bus.publish(BaseEvent(id="delta", timestamp="t"))
    assert calls[-1] == "one:delta"

    bus.clear()
    assert bus.listener_count(BaseEvent) == 0
    assert bus.listeners(BaseEvent) == ()


def test_event_bus_rejects_objects_without_integrity_contract() -> None:
    bus = EventBus()
    with pytest.raises(EventIntegrityError, match="IntegrityValidatable"):
        bus.publish("arbitrary")
    assert bus.event_history() == ()
