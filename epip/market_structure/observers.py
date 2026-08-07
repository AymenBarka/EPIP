"""Optional observer support independent from the domain EventBus."""

from __future__ import annotations

from threading import RLock
from typing import Protocol, runtime_checkable

from epip.market_structure.models import MarketStructureSnapshot


@runtime_checkable
class StructureObserver(Protocol):
    """Consumer notified after an immutable snapshot is committed."""

    def on_structure(self, snapshot: MarketStructureSnapshot) -> None:
        """Receive the latest immutable structure snapshot."""


class ObserverRegistry:
    """Thread-safe observer registry with deterministic notification order."""

    def __init__(self) -> None:
        self._observers: list[StructureObserver] = []
        self._lock = RLock()

    def register(self, observer: StructureObserver) -> None:
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def unregister(self, observer: StructureObserver) -> None:
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)

    def observers(self) -> tuple[StructureObserver, ...]:
        with self._lock:
            return tuple(self._observers)

    def notify(self, snapshot: MarketStructureSnapshot) -> None:
        for observer in self.observers():
            observer.on_structure(snapshot)
