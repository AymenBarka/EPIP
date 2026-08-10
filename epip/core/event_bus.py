"""Thread-safe event bus for core domain communication."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from threading import Event, RLock, get_ident
from typing import Any

from epip.core.integrity import DataIntegrityError, EventIntegrityError, validate_object

Listener = Callable[[object], None]

# Maximum number of events one dispatcher may process without returning control.
# This bounds recursive listener publication and prevents an infinite dispatch cycle.
MAX_REENTRANT_EVENTS = 10_000


class EventReentrancyError(RuntimeError):
    """Raised when one dispatch cycle exceeds the recursive publication limit."""


@dataclass(slots=True)
class _QueuedPublication:
    event: object
    listeners: tuple[Listener, ...]
    publisher_thread: int
    reentrant: bool
    completed: Event = field(default_factory=Event)
    error: BaseException | None = None


class EventBus:
    """Deterministic, thread-safe pub/sub bus for the EPIP kernel."""

    def __init__(self) -> None:
        self._listeners: dict[type[Any], list[Listener]] = {}
        self._lock = RLock()
        self._history: list[object] = []
        self._queue: deque[_QueuedPublication] = deque()
        self._dispatching = False
        self._dispatcher_thread: int | None = None
        self._callback_active = False

    def subscribe(self, event_type: type[Any], listener: Listener) -> None:
        """Register a listener for a specific event type."""
        with self._lock:
            listeners = self._listeners.setdefault(event_type, [])
            if listener not in listeners:
                listeners.append(listener)

    def unsubscribe(self, event_type: type[Any], listener: Listener) -> None:
        """Remove a listener for a specific event type."""
        with self._lock:
            listeners = self._listeners.get(event_type)
            if listeners is None:
                return
            try:
                listeners.remove(listener)
            except ValueError:
                return
            if not listeners:
                self._listeners.pop(event_type, None)

    def publish(self, event: object) -> None:
        """Dispatch an event to all matching listeners."""
        try:
            validate_object(event, "event", explicit=True)
        except DataIntegrityError as exc:
            raise EventIntegrityError(f"invalid event: {exc}") from exc
        with self._lock:
            self._history.append(event)
            listeners = (
                *self._listeners.get(type(event), ()),
                *self._listeners.get(object, ()),
            )
            current_thread = get_ident()
            recursive = self._dispatching and self._dispatcher_thread == current_thread
            publication = _QueuedPublication(event, listeners, current_thread, recursive)
            self._queue.append(publication)
            if not self._dispatching:
                self._dispatching = True
                self._dispatcher_thread = current_thread
                dispatch = True
            else:
                dispatch = False
            defer_until_dispatch = self._callback_active

        if dispatch:
            try:
                error = self._drain_queue()
            except BaseException as exc:
                self._abort_dispatch(exc)
                raise
            if error is not None:
                raise error
            return
        if recursive or defer_until_dispatch:
            return
        publication.completed.wait()
        if publication.error is not None:
            raise publication.error

    def _drain_queue(self) -> BaseException | None:
        first_error: BaseException | None = None
        reentrant_events = 0
        dispatcher_thread = get_ident()
        while True:
            with self._lock:
                if not self._queue:
                    self._dispatching = False
                    self._dispatcher_thread = None
                    return first_error
                publication = self._queue.popleft()
                if publication.reentrant and reentrant_events >= MAX_REENTRANT_EVENTS:
                    error = EventReentrancyError(
                        "recursive publication limit exceeded in one dispatch cycle"
                    )
                    publication.error = error
                    publication.completed.set()
                    if first_error is None:
                        first_error = error
                    continue
                if publication.reentrant:
                    reentrant_events += 1
                self._callback_active = True

            try:
                for listener in publication.listeners:
                    listener(publication.event)
            except BaseException as exc:  # noqa: BLE001 - listener boundary isolation
                publication.error = exc
                if publication.publisher_thread == dispatcher_thread and first_error is None:
                    first_error = exc
            finally:
                with self._lock:
                    self._callback_active = False
                publication.completed.set()

    def _abort_dispatch(self, error: BaseException) -> None:
        """Restore dispatcher invariants after an unexpected internal failure."""
        with self._lock:
            pending = tuple(self._queue)
            self._queue.clear()
            self._dispatching = False
            self._dispatcher_thread = None
            self._callback_active = False
        for publication in pending:
            publication.error = error
            publication.completed.set()

    def publish_many(self, events: Iterable[object]) -> None:
        """Publish each event in deterministic order."""
        for event in events:
            self.publish(event)

    def clear(self) -> None:
        """Remove all listeners and reset history."""
        with self._lock:
            self._listeners.clear()
            self._history.clear()

    def listeners(self, event_type: type[Any]) -> tuple[Listener, ...]:
        """Return the registered listeners for an event type."""
        with self._lock:
            return tuple(self._listeners.get(event_type, ()))

    def listener_count(self, event_type: type[Any]) -> int:
        """Return the number of listeners for an event type."""
        with self._lock:
            return len(self._listeners.get(event_type, ()))

    def event_history(self) -> tuple[object, ...]:
        """Return the ordered history of published events."""
        with self._lock:
            return tuple(self._history)
