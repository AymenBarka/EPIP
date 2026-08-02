from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from epip.features.feature_store import FeatureStore
from epip.features.providers.ohlc_provider import OHLCProvider
from epip.features.providers.session_provider import SessionProvider


def test_feature_store_builds_caches_and_supports_history() -> None:
    store = FeatureStore()
    store.register_provider(OHLCProvider())
    store.register_provider(SessionProvider())

    candle: dict[str, Any] = {
        "symbol": "EURUSD",
        "timeframe": "M1",
        "timestamp": "2024-01-01T00:00:00Z",
        "open": 1.1000,
        "high": 1.1100,
        "low": 1.0950,
        "close": 1.1050,
    }

    first = store.build_feature_set("EURUSD", "M1", "2024-01-01T00:00:00Z", payload=candle)
    assert first.get("close") is not None
    assert first.get("session") is not None

    cached = store.build_feature_set("EURUSD", "M1", "2024-01-01T00:00:00Z", payload=candle)
    assert cached is first
    assert len(store.history()) == 1
    assert store.cache_size() == 1

    other = store.build_feature_set("GBPUSD", "M1", "2024-01-01T00:00:00Z", payload=candle)
    assert other.get("close") is not None
    assert store.cache_size() == 2

    store.invalidate_cache("EURUSD")
    assert store.cache_size() == 1


def test_feature_store_is_thread_safe() -> None:
    store = FeatureStore()
    store.register_provider(OHLCProvider())

    candle: dict[str, Any] = {
        "symbol": "EURUSD",
        "timeframe": "M1",
        "timestamp": "2024-01-01T00:00:00Z",
        "open": 1.1000,
        "high": 1.1100,
        "low": 1.0950,
        "close": 1.1050,
    }

    def runner(index: int) -> None:
        store.build_feature_set("EURUSD", "M1", f"2024-01-01T00:00:00Z-{index}", payload=candle)

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(runner, range(4)))

    assert store.cache_size() == 4
