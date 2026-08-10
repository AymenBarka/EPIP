"""Memory-retention checks for cleared concurrency infrastructure."""

import gc
import tracemalloc

from epip.core.event_bus import EventBus
from epip.core.events import BaseEvent


def test_eventbus_clear_releases_repeated_history_batches() -> None:
    bus = EventBus()
    tracemalloc.start()
    baseline = tracemalloc.take_snapshot()
    for cycle in range(10):
        for sequence in range(1_000):
            bus.publish(
                BaseEvent(
                    id=f"memory:{cycle}:{sequence}",
                    timestamp="2026-01-01T00:00:00+00:00",
                )
            )
        bus.clear()
    gc.collect()
    final = tracemalloc.take_snapshot()
    tracemalloc.stop()
    growth = sum(stat.size_diff for stat in final.compare_to(baseline, "filename"))
    assert bus.event_history() == ()
    assert growth < 1_000_000
