"""Plugin registry for the EPIP core kernel."""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from epip.core.plugin_protocol import PluginProtocol


class Registry:
    """Registry that tracks plugin registration state and ordering."""

    def __init__(self) -> None:
        self._plugins: dict[str, Any] = {}
        self._enabled: dict[str, bool] = {}
        self._priorities: dict[str, int] = {}
        self._order: list[str] = []
        self._lock = RLock()

    def register(self, plugin: PluginProtocol, priority: int | None = None) -> None:
        """Register a plugin with an optional priority override."""
        name = self._resolve_name(plugin)
        with self._lock:
            if name in self._order:
                self._order.remove(name)
            self._plugins[name] = plugin
            self._enabled[name] = True
            self._priorities[name] = (
                priority if priority is not None else self._priority_for(plugin)
            )
            self._order.append(name)

    def unregister(self, plugin_or_name: PluginProtocol | str) -> None:
        """Remove a plugin from the registry."""
        name = self._resolve_name(plugin_or_name)
        with self._lock:
            self._plugins.pop(name, None)
            self._enabled.pop(name, None)
            self._priorities.pop(name, None)
            if name in self._order:
                self._order.remove(name)

    def enable(self, plugin_or_name: PluginProtocol | str) -> None:
        """Enable a plugin."""
        name = self._resolve_name(plugin_or_name)
        with self._lock:
            self._enabled[name] = True

    def disable(self, plugin_or_name: PluginProtocol | str) -> None:
        """Disable a plugin."""
        name = self._resolve_name(plugin_or_name)
        with self._lock:
            self._enabled[name] = False

    def exists(self, plugin_or_name: PluginProtocol | str) -> bool:
        """Return True when the plugin is registered."""
        name = self._resolve_name(plugin_or_name)
        with self._lock:
            return name in self._plugins

    def ordered_plugins(self) -> tuple[Any, ...]:
        """Return enabled plugins sorted by priority and registration order."""
        with self._lock:
            active = [name for name in self._order if self._enabled.get(name, True)]
            ordered_names = sorted(
                active, key=lambda name: (self._priorities.get(name, 0), self._order.index(name))
            )
            return tuple(self._plugins[name] for name in ordered_names)

    def plugins_by_priority(self) -> dict[str, int]:
        """Return the current plugin priority map."""
        with self._lock:
            return {name: self._priorities[name] for name in self._order}

    def _isolated_copy(self) -> Registry:
        """Return a structural snapshot for one isolated plugin execution."""
        isolated = Registry()
        with self._lock:
            isolated._plugins = dict(self._plugins)
            isolated._enabled = dict(self._enabled)
            isolated._priorities = dict(self._priorities)
            isolated._order = list(self._order)
        return isolated

    def _resolve_name(self, plugin_or_name: PluginProtocol | str) -> str:
        if isinstance(plugin_or_name, str):
            return plugin_or_name
        return getattr(plugin_or_name, "name", plugin_or_name.__class__.__name__)

    def _priority_for(self, plugin: PluginProtocol) -> int:
        return getattr(plugin, "priority", 0)
