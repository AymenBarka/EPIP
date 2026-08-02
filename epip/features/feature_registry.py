"""Registry for feature metadata and provider ownership."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeatureRegistryEntry:
    """Metadata describing how a feature is produced."""

    name: str
    provider: str
    category: str
    priority: int


class FeatureRegistry:
    """Stores feature metadata independent from execution logic."""

    def __init__(self) -> None:
        self._entries: dict[str, FeatureRegistryEntry] = {}
        self._order: list[str] = []

    def register(self, name: str, *, provider: str, category: str, priority: int) -> None:
        entry = FeatureRegistryEntry(
            name=name, provider=provider, category=category, priority=priority
        )
        self._entries[name] = entry
        if name not in self._order:
            self._order.append(name)

    def unregister(self, name: str) -> None:
        self._entries.pop(name, None)
        if name in self._order:
            self._order.remove(name)

    def get(self, name: str) -> FeatureRegistryEntry | None:
        return self._entries.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(self._order)

    def entries(self) -> tuple[FeatureRegistryEntry, ...]:
        return tuple(self._entries[name] for name in self._order)
