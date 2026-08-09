"""Scheduler-independent EventBus progress and fairness checks."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from epip.core.event_bus import EventBus
from epip.core.events import BaseEvent


def test_every_contending_publisher_makes_complete_progress() -> None:
    publishers = 64
    publications = 100
    bus = EventBus()
    barrier = Barrier(publishers)
    completed = [0] * publishers

    def publish(index: int) -> None:
        barrier.wait()
        for sequence in range(publications):
            bus.publish(
                BaseEvent(
                    id=f"fair:{index}:{sequence}",
                    timestamp="2026-01-01T00:00:00+00:00",
                )
            )
            completed[index] += 1

    with ThreadPoolExecutor(max_workers=publishers) as executor:
        futures = [executor.submit(publish, index) for index in range(publishers)]
        for future in futures:
            future.result(timeout=30)

    assert completed == [publications] * publishers
    assert len(bus.event_history()) == publishers * publications
