from __future__ import annotations

from epip.core.plugin_context import PluginContext
from epip.core.registry import Registry


class DummyPlugin:
    name = "dummy"
    priority = 5

    def execute(self, context: PluginContext) -> None:
        return None


class HighPriorityPlugin:
    name = "high"
    priority = 1

    def execute(self, context: PluginContext) -> None:
        return None


def test_registry_registers_enables_disables_and_orders_plugins() -> None:
    registry = Registry()
    dummy = DummyPlugin()
    high = HighPriorityPlugin()

    registry.register(dummy)
    registry.register(high)

    assert registry.exists(dummy)
    assert registry.ordered_plugins() == (high, dummy)
    assert registry.plugins_by_priority()["high"] == 1

    registry.disable(dummy)
    assert registry.ordered_plugins() == (high,)

    registry.enable(dummy)
    assert registry.ordered_plugins() == (high, dummy)

    registry.unregister(dummy)
    assert not registry.exists(dummy)
