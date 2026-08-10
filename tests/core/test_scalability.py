"""Reproducible scalability validation for the synchronous EventBus."""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from epip.core.event_bus import EventBus
from epip.core.events import BaseEvent


@pytest.mark.parametrize("thread_count", [1, 2, 8, 32, 64, 128, 256])
def test_eventbus_scalability_matrix_is_lossless_and_locally_fifo(
    thread_count: int,
) -> None:
    events_per_thread = 32
    bus = EventBus()
    barrier = Barrier(thread_count)

    def publish(thread_index: int) -> None:
        barrier.wait()
        for sequence in range(events_per_thread):
            bus.publish(
                BaseEvent(
                    id=f"{thread_index}:{sequence}",
                    timestamp="2026-01-01T00:00:00+00:00",
                )
            )

    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [executor.submit(publish, index) for index in range(thread_count)]
        for future in futures:
            future.result(timeout=30)

    history = []
    for event in bus.event_history():
        assert isinstance(event, BaseEvent)
        history.append(event.id)
    assert len(history) == thread_count * events_per_thread
    assert len(set(history)) == len(history)
    per_thread: dict[int, list[int]] = defaultdict(list)
    for identifier in history:
        thread_text, sequence_text = identifier.split(":")
        per_thread[int(thread_text)].append(int(sequence_text))
    assert all(values == list(range(events_per_thread)) for values in per_thread.values())
