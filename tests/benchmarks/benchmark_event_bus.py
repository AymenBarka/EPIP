from __future__ import annotations

from time import perf_counter

from epip.core.event_bus import EventBus


def main() -> None:
    bus = EventBus()
    for _ in range(100):
        bus.subscribe(str, lambda event: None)

    start = perf_counter()
    for index in range(100_000):
        bus.publish(f"event-{index}")
    duration = perf_counter() - start
    print(f"event_bus_publish_100000={duration:.6f}s")


if __name__ == "__main__":
    main()
