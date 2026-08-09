"""Cross-component production-stress acceptance checks."""

from concurrent.futures import ThreadPoolExecutor

from epip.core.event_bus import EventBus
from epip.core.events import BaseEvent


def test_independent_eventbus_instances_are_isolated_under_parallel_load() -> None:
    bus_count = 16
    events_per_bus = 1_000

    def exercise(index: int) -> tuple[str, ...]:
        bus = EventBus()
        for sequence in range(events_per_bus):
            bus.publish(
                BaseEvent(
                    id=f"isolated:{index}:{sequence}",
                    timestamp="2026-01-01T00:00:00+00:00",
                )
            )
        identifiers: list[str] = []
        for event in bus.event_history():
            assert isinstance(event, BaseEvent)
            identifiers.append(event.id)
        return tuple(identifiers)

    with ThreadPoolExecutor(max_workers=bus_count) as executor:
        histories = list(executor.map(exercise, range(bus_count)))

    assert all(len(history) == events_per_bus for history in histories)
    assert len({identifier for history in histories for identifier in history}) == (
        bus_count * events_per_bus
    )
