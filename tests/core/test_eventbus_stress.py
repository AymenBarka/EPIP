from __future__ import annotations

import gc
import tracemalloc
from collections import Counter, defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, Thread
from time import perf_counter, sleep

import pytest

from epip.core.event_bus import (
    MAX_REENTRANT_EVENTS,
    EventBus,
    EventReentrancyError,
)
from epip.core.events import BaseEvent

THREADS = 64
EVENTS_PER_THREAD = 10_000
TOTAL_EVENTS = THREADS * EVENTS_PER_THREAD
SLOW_LISTENER_SECONDS = 0.2
SIMULTANEOUS_PUBLISHERS = 200
CONTENTION_THREADS = 16
CONTENTION_EVENTS_PER_THREAD = 200
PERFORMANCE_THREADS = 8
PERFORMANCE_EVENTS_PER_THREAD = 1_000
SNAPSHOT_EVENTS = 20_000
SNAPSHOT_LISTENERS = 8


def _event(identifier: str) -> BaseEvent:
    return BaseEvent(id=identifier, timestamp="2026-01-01T00:00:00+00:00")


def _event_id(event: object) -> str:
    assert isinstance(event, BaseEvent)
    return event.id


def test_640000_publications_are_lossless_unique_and_fifo(
    record_property: Callable[[str, object], None],
) -> None:
    bus = EventBus()
    delivered: list[str] = []
    batch_durations: dict[int, float] = {}
    bus.subscribe(BaseEvent, lambda event: delivered.append(_event_id(event)))
    start = Barrier(THREADS)

    def publish_batch(thread_index: int) -> None:
        start.wait()
        batch_started = perf_counter()
        for event_index in range(EVENTS_PER_THREAD):
            bus.publish(_event(f"{thread_index}:{event_index}"))
        batch_durations[thread_index] = perf_counter() - batch_started

    started = perf_counter()
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(publish_batch, index) for index in range(THREADS)]
        for future in futures:
            future.result(timeout=300)
    duration = perf_counter() - started

    history = [_event_id(event) for event in bus.event_history()]
    record_property("events_per_second", TOTAL_EVENTS / duration)
    record_property("fastest_publisher_seconds", min(batch_durations.values()))
    record_property("slowest_publisher_seconds", max(batch_durations.values()))
    print(
        "stress_metrics "
        f"throughput={TOTAL_EVENTS / duration:.2f}events/s "
        f"fastest_publisher={min(batch_durations.values()):.4f}s "
        f"slowest_publisher={max(batch_durations.values()):.4f}s"
    )
    assert len(history) == TOTAL_EVENTS
    assert len(delivered) == TOTAL_EVENTS
    assert delivered == history
    assert len(set(delivered)) == TOTAL_EVENTS
    per_thread: dict[int, list[int]] = defaultdict(list)
    for identifier in history:
        thread_text, event_text = identifier.split(":")
        per_thread[int(thread_text)].append(int(event_text))
    for thread_index in range(THREADS):
        assert per_thread[thread_index] == list(range(EVENTS_PER_THREAD))


def test_slow_listener_with_200_publishers_has_no_deadlock_or_loss() -> None:
    bus = EventBus()
    entered = Event()
    delivered: list[str] = []

    def listener(event: object) -> None:
        identifier = _event_id(event)
        delivered.append(identifier)
        if identifier == "slow":
            entered.set()
            sleep(SLOW_LISTENER_SECONDS)

    bus.subscribe(BaseEvent, listener)
    blocker = Thread(target=bus.publish, args=(_event("slow"),))
    blocker.start()
    assert entered.wait(timeout=2)

    with ThreadPoolExecutor(max_workers=SIMULTANEOUS_PUBLISHERS) as executor:
        futures = [
            executor.submit(bus.publish, _event(f"publisher:{index}"))
            for index in range(SIMULTANEOUS_PUBLISHERS)
        ]
        for future in futures:
            future.result(timeout=10)
    blocker.join(timeout=10)

    history = [_event_id(event) for event in bus.event_history()]
    assert not blocker.is_alive()
    assert delivered == history
    assert len(delivered) == SIMULTANEOUS_PUBLISHERS + 1
    assert len(set(delivered)) == len(delivered)


def test_deep_recursive_publication_is_bounded_and_queue_recovers() -> None:
    bus = EventBus()
    tracemalloc.start()

    def recursive(_: object) -> None:
        bus.publish(_event("recursive"))

    bus.subscribe(BaseEvent, recursive)
    with pytest.raises(EventReentrancyError, match="recursive publication limit"):
        bus.publish(_event("root"))

    assert len(bus.event_history()) == MAX_REENTRANT_EVENTS + 2
    assert not bus._queue
    bus.clear()
    bus.subscribe(BaseEvent, lambda _: None)
    bus.publish(_event("recovered"))
    assert [_event_id(event) for event in bus.event_history()] == ["recovered"]
    bus.clear()
    gc.collect()
    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(
        "reentrancy_memory " f"current_after_clear_bytes={current_memory} peak_bytes={peak_memory}"
    )
    assert current_memory < peak_memory


def test_aba_listener_mutation_preserves_current_and_next_snapshots() -> None:
    bus = EventBus()
    calls: list[str] = []

    def replacement(event: object) -> None:
        calls.append(f"replacement:{_event_id(event)}")

    def stable(event: object) -> None:
        calls.append(f"stable:{_event_id(event)}")

    def mutating(event: object) -> None:
        calls.append(f"mutating:{_event_id(event)}")
        bus.subscribe(BaseEvent, replacement)
        bus.unsubscribe(BaseEvent, replacement)
        bus.subscribe(BaseEvent, replacement)
        bus.clear()
        bus.subscribe(BaseEvent, replacement)

    bus.subscribe(BaseEvent, mutating)
    bus.subscribe(BaseEvent, stable)
    bus.publish(_event("current"))
    bus.publish(_event("next"))

    assert calls == ["mutating:current", "stable:current", "replacement:next"]


def test_extreme_contention_preserves_history_and_listener_order() -> None:
    bus = EventBus()
    calls: dict[str, list[str]] = defaultdict(list)
    publisher_counts: Counter[int] = Counter()
    start = Barrier(CONTENTION_THREADS + 1)

    def first(event: object) -> None:
        calls[_event_id(event)].append("first")

    def unstable(event: object) -> None:
        identifier = _event_id(event)
        calls[identifier].append("unstable")
        if identifier.endswith(":0"):
            raise ValueError("expected listener failure")

    def slow(event: object) -> None:
        calls[_event_id(event)].append("slow")
        sleep(0.0001)

    bus.subscribe(BaseEvent, first)
    bus.subscribe(BaseEvent, unstable)
    bus.subscribe(BaseEvent, slow)

    def publish_batch(thread_index: int) -> None:
        start.wait()
        for event_index in range(CONTENTION_EVENTS_PER_THREAD):
            try:
                bus.publish(_event(f"{thread_index}:{event_index}"))
            except ValueError:
                assert event_index == 0
            publisher_counts[thread_index] += 1

    with ThreadPoolExecutor(max_workers=CONTENTION_THREADS) as executor:
        futures = [executor.submit(publish_batch, index) for index in range(CONTENTION_THREADS)]
        start.wait()
        for future in futures:
            future.result(timeout=30)

    history = [_event_id(event) for event in bus.event_history()]
    assert len(history) == CONTENTION_THREADS * CONTENTION_EVENTS_PER_THREAD
    assert len(set(history)) == len(history)
    assert publisher_counts == Counter(
        {index: CONTENTION_EVENTS_PER_THREAD for index in range(CONTENTION_THREADS)}
    )
    for identifier in history:
        expected = ["first", "unstable"]
        if not identifier.endswith(":0"):
            expected.append("slow")
        assert calls[identifier] == expected


def test_latency_and_listener_snapshot_cost_are_measured() -> None:
    latencies: list[float] = []
    bus = EventBus()
    listeners = [lambda _: None for _ in range(SNAPSHOT_LISTENERS)]
    for listener in listeners:
        bus.subscribe(BaseEvent, listener)
    start = Barrier(PERFORMANCE_THREADS)

    def timed_batch(thread_index: int) -> None:
        start.wait()
        for event_index in range(PERFORMANCE_EVENTS_PER_THREAD):
            started = perf_counter()
            bus.publish(_event(f"latency:{thread_index}:{event_index}"))
            latencies.append(perf_counter() - started)

    with ThreadPoolExecutor(max_workers=PERFORMANCE_THREADS) as executor:
        futures = [executor.submit(timed_batch, index) for index in range(PERFORMANCE_THREADS)]
        for future in futures:
            future.result(timeout=30)

    def snapshot_duration(listener_count: int) -> float:
        measured_bus = EventBus()
        measured_listeners = [lambda _: None for _ in range(listener_count)]
        for listener in measured_listeners:
            measured_bus.subscribe(BaseEvent, listener)
        started = perf_counter()
        for index in range(SNAPSHOT_EVENTS):
            measured_bus.publish(_event(f"snapshot:{listener_count}:{index}"))
        return perf_counter() - started

    no_listener_duration = snapshot_duration(0)
    listener_duration = snapshot_duration(SNAPSHOT_LISTENERS)
    average_latency = sum(latencies) / len(latencies)
    maximum_latency = max(latencies)
    snapshot_overhead = listener_duration - no_listener_duration
    print(
        "performance_metrics "
        f"average_latency_ms={average_latency * 1_000:.4f} "
        f"maximum_latency_ms={maximum_latency * 1_000:.4f} "
        f"no_listener_throughput={SNAPSHOT_EVENTS / no_listener_duration:.2f}events/s "
        f"{SNAPSHOT_LISTENERS}_listener_throughput="
        f"{SNAPSHOT_EVENTS / listener_duration:.2f}events/s "
        f"snapshot_{SNAPSHOT_LISTENERS}_listeners_overhead_ms="
        f"{snapshot_overhead * 1_000:.4f}"
    )
    assert len(latencies) == PERFORMANCE_THREADS * PERFORMANCE_EVENTS_PER_THREAD
