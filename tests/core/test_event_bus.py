from __future__ import annotations

from epip.core.event_bus import EventBus


def test_event_bus_orders_and_histories_listeners() -> None:
    bus = EventBus()
    calls: list[str] = []

    def handler_one(event: object) -> None:
        calls.append(f"one:{event}")

    def handler_two(event: object) -> None:
        calls.append(f"two:{event}")

    bus.subscribe(str, handler_one)
    bus.subscribe(str, handler_two)

    bus.publish("alpha")
    bus.publish_many(["beta", "gamma"])

    assert calls == ["one:alpha", "two:alpha", "one:beta", "two:beta", "one:gamma", "two:gamma"]
    assert bus.listener_count(str) == 2
    assert bus.listeners(str) == (handler_one, handler_two)
    assert bus.event_history() == ("alpha", "beta", "gamma")

    bus.unsubscribe(str, handler_two)
    bus.publish("delta")
    assert calls[-1] == "one:delta"

    bus.clear()
    assert bus.listener_count(str) == 0
    assert bus.listeners(str) == ()
