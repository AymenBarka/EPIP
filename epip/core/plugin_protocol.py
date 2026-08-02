"""Plugin protocol for the EPIP kernel."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from epip.core.plugin_context import PluginContext
from epip.core.plugin_result import PluginResult


@runtime_checkable
class PluginProtocol(Protocol):
    """Small execution contract for pluggable analysis components."""

    name: str
    priority: int

    def execute(self, context: PluginContext) -> PluginResult | object | None:
        """Execute the plugin against a plugin context."""
