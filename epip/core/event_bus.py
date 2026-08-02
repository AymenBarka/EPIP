"""Thread-safe event bus for core domain communication."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock
from typing import Any

Listener = Callable[[object], None]


class EventBus:
    """Deterministic, thread-safe pub/sub bus for the EPIP kernel."""

    def __init__(self) -> None:
        self._listeners: dict[type[Any], list[Listener]] = {}
        self._lock = RLock()
        self._history: list[object] = []

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
        with self._lock:
            self._history.append(event)
            snapshot = list(self._listeners.get(type(event), ()))
            object_listeners = list(self._listeners.get(object, ()))
            listeners = tuple(snapshot + object_listeners)

        for listener in listeners:
            listener(event)

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
