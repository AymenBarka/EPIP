from __future__ import annotations

import ast
import gc
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event, Thread
from time import sleep
from weakref import ref

import pytest

from epip.core.event_bus import EventBus, EventReentrancyError
from epip.core.events import BaseEvent


def _event(identifier: str) -> BaseEvent:
    return BaseEvent(id=identifier, timestamp="2026-01-01T00:00:00+00:00")


def _event_id(event: object) -> str:
    assert isinstance(event, BaseEvent)
    return event.id


def test_concurrent_publication_delivers_every_event_once() -> None:
    bus = EventBus()
    calls: list[str] = []
    bus.subscribe(BaseEvent, lambda event: calls.append(_event_id(event)))
    barrier = Barrier(9)

    def publish(index: int) -> None:
        barrier.wait()
        bus.publish(_event(str(index)))

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(publish, index) for index in range(8)]
        barrier.wait()
        for future in futures:
            future.result(timeout=5)

    history = tuple(_event_id(event) for event in bus.event_history())
    assert tuple(calls) == history
    assert sorted(calls) == [str(index) for index in range(8)]


def test_listener_snapshot_is_stable_during_subscription_changes() -> None:
    bus = EventBus()
    calls: list[str] = []

    def added(event: object) -> None:
        calls.append(f"added:{event.id}")  # type: ignore[attr-defined]

    def first(event: object) -> None:
        calls.append(f"first:{event.id}")  # type: ignore[attr-defined]
        bus.subscribe(BaseEvent, added)
        bus.unsubscribe(BaseEvent, first)
        bus.clear()

    def second(event: object) -> None:
        calls.append(f"second:{event.id}")  # type: ignore[attr-defined]

    bus.subscribe(BaseEvent, first)
    bus.subscribe(BaseEvent, second)
    bus.publish(_event("one"))

    assert calls == ["first:one", "second:one"]
    assert bus.listeners(BaseEvent) == ()


def test_recursive_publication_is_fifo_and_listener_ordered() -> None:
    bus = EventBus()
    calls: list[str] = []

    def first(event: object) -> None:
        calls.append(f"first:{event.id}")  # type: ignore[attr-defined]
        if event.id == "outer":  # type: ignore[attr-defined]
            bus.publish(_event("inner"))

    def second(event: object) -> None:
        calls.append(f"second:{event.id}")  # type: ignore[attr-defined]

    bus.subscribe(BaseEvent, first)
    bus.subscribe(BaseEvent, second)
    bus.publish(_event("outer"))

    assert calls == ["first:outer", "second:outer", "first:inner", "second:inner"]
    assert tuple(_event_id(event) for event in bus.event_history()) == ("outer", "inner")


def test_listener_exception_does_not_strand_queued_publications() -> None:
    bus = EventBus()
    calls: list[str] = []

    def listener(event: object) -> None:
        identifier = event.id  # type: ignore[attr-defined]
        calls.append(identifier)
        if identifier == "bad":
            bus.publish(_event("queued"))
            raise ValueError("listener failed")

    bus.subscribe(BaseEvent, listener)
    with pytest.raises(ValueError, match="listener failed"):
        bus.publish(_event("bad"))

    assert calls == ["bad", "queued"]
    bus.publish(_event("after"))
    assert calls[-1] == "after"


def test_slow_listener_never_duplicates_or_loses_events() -> None:
    bus = EventBus()
    entered = Event()
    release = Event()
    calls: list[str] = []

    def listener(event: object) -> None:
        calls.append(event.id)  # type: ignore[attr-defined]
        if event.id == "slow":  # type: ignore[attr-defined]
            entered.set()
            assert release.wait(timeout=5)

    bus.subscribe(BaseEvent, listener)
    slow = Thread(target=bus.publish, args=(_event("slow"),))
    slow.start()
    assert entered.wait(timeout=5)
    fast = Thread(target=bus.publish, args=(_event("fast"),))
    fast.start()
    sleep(0.02)
    assert not fast.is_alive()
    assert calls == ["slow"]
    release.set()
    slow.join(timeout=5)
    fast.join(timeout=5)

    assert not slow.is_alive()
    assert not fast.is_alive()
    assert calls == ["slow", "fast"]


def test_recursive_publication_limit_prevents_infinite_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("epip.core.event_bus.MAX_REENTRANT_EVENTS", 8)
    bus = EventBus()

    def loop(_: object) -> None:
        bus.publish(_event("loop"))

    bus.subscribe(BaseEvent, loop)
    with pytest.raises(EventReentrancyError, match="recursive publication limit"):
        bus.publish(_event("loop"))

    assert len(bus.event_history()) == 10


def test_engines_never_publish_inside_their_state_lock() -> None:
    engine_paths = tuple(Path("epip").glob("*/engine.py")) + tuple(
        Path("epip/replay").glob("replay_engine.py")
    )
    violations: list[str] = []
    for path in engine_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.With, ast.AsyncWith)):
                continue
            for nested in ast.walk(node):
                if not isinstance(nested, ast.Call):
                    continue
                function = nested.func
                if isinstance(function, ast.Attribute) and (
                    function.attr == "publish" or function.attr.startswith("_publish")
                ):
                    violations.append(f"{path}:{nested.lineno}:{function.attr}")
    assert violations == []


class _CustomBaseException(BaseException):
    pass


class _FailingListener:
    def __init__(self, error: BaseException) -> None:
        self.error = error

    def __call__(self, _: object) -> None:
        raise self.error


@pytest.mark.parametrize(
    "error",
    (KeyboardInterrupt(), SystemExit(), GeneratorExit(), _CustomBaseException()),
)
def test_dispatcher_recovers_from_every_base_exception(error: BaseException) -> None:
    bus = EventBus()
    listener = _FailingListener(error)
    listener_reference = ref(listener)
    bus.subscribe(BaseEvent, listener)

    with pytest.raises(type(error)):
        bus.publish(_event("failing"))

    bus.unsubscribe(BaseEvent, listener)
    error.__traceback__ = None
    del listener
    gc.collect()
    assert listener_reference() is None
    assert not bus._dispatching
    assert bus._dispatcher_thread is None
    assert not bus._callback_active
    assert not bus._queue

    delivered: list[str] = []
    bus.subscribe(BaseEvent, lambda event: delivered.append(_event_id(event)))
    bus.publish(_event("recovered"))
    assert delivered == ["recovered"]


def test_listener_can_join_thread_that_publishes_without_deadlock() -> None:
    bus = EventBus()
    delivered: list[str] = []
    child_threads: list[Thread] = []

    def listener(event: object) -> None:
        identifier = _event_id(event)
        delivered.append(identifier)
        if identifier != "root":
            return
        child = Thread(target=bus.publish, args=(_event("child"),))
        child_threads.append(child)
        child.start()
        child.join(timeout=2)
        assert not child.is_alive()

    bus.subscribe(BaseEvent, listener)
    bus.publish(_event("root"))

    assert delivered == ["root", "child"]
    assert [_event_id(event) for event in bus.event_history()] == ["root", "child"]
    assert all(not thread.is_alive() for thread in child_threads)
    assert not bus._dispatching
    assert bus._dispatcher_thread is None
    assert not bus._callback_active
    assert not bus._queue
