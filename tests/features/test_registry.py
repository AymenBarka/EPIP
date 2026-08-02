from __future__ import annotations

from epip.features.feature_registry import FeatureRegistry


def test_registry_tracks_feature_metadata() -> None:
    registry = FeatureRegistry()
    registry.register("close", provider="ohlc", category="ohlc", priority=10)
    registry.register("body", provider="ohlc", category="ohlc", priority=5)

    entry = registry.get("close")
    assert entry is not None
    assert entry.provider == "ohlc"
    assert entry.category == "ohlc"
    assert entry.priority == 10
    assert registry.names() == ("close", "body")
