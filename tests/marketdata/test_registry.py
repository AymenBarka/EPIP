from __future__ import annotations

from epip.marketdata.datasource_registry import DataSourceRegistry
from epip.marketdata.providers.fake_provider import FakeProvider


def test_registry_register_default_and_unregiser() -> None:
    registry = DataSourceRegistry()
    a = FakeProvider(symbols=("EURUSD",), timeframes=("M1",), candles_per_series=5)
    b = FakeProvider(symbols=("GBPUSD",), timeframes=("M5",), candles_per_series=5)

    registry.register("a", a)
    registry.register("b", b, as_default=True)

    assert registry.exists("a") is True
    assert registry.providers() == ("a", "b")
    assert registry.default() is b

    registry.unregister("b")
    assert registry.default() is a

    registry.unregister("a")
    assert registry.default() is None
