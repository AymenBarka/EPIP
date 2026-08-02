from __future__ import annotations

from epip.core.context import MarketContext
from epip.core.plugin_context import PluginContext


def test_plugin_context_is_immutable_and_contains_market_context() -> None:
    context = MarketContext(symbol="EURUSD", timeframe="M1", timestamp="2024-01-01T00:00:00Z")
    plugin_context = PluginContext(market_context=context, metadata={"source": "unit-test"})

    assert plugin_context.market_context.symbol == "EURUSD"
    assert plugin_context.metadata["source"] == "unit-test"
    assert plugin_context.event_bus is not None
    assert plugin_context.registry is not None
