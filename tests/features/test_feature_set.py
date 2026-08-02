from __future__ import annotations

from epip.features.feature import Feature
from epip.features.feature_set import FeatureSet


def test_feature_set_supports_lookup_merge_and_serialization() -> None:
    close = Feature(
        id="f-close",
        name="close",
        category="ohlc",
        value=1.25,
        timestamp="2024-01-01T00:00:00Z",
        metadata={},
        quality_score=1.0,
        source="ohlc",
    )
    volume = Feature(
        id="f-volume",
        name="volume",
        category="volume",
        value=120.5,
        timestamp="2024-01-01T00:00:00Z",
        metadata={},
        quality_score=0.9,
        source="ohlc",
    )

    feature_set = FeatureSet((close, volume))

    assert feature_set.get("close") is close
    assert feature_set.exists("volume") is True
    assert feature_set.filter(category="ohlc").get("close") is close

    merged = feature_set.merge(
        FeatureSet(
            (Feature("f-body", "body", "ohlc", 0.25, "2024-01-01T00:00:00Z", {}, 0.8, "ohlc"),)
        )
    )

    assert merged.get("body") is not None
    assert merged.to_dict()["close"]["value"] == 1.25
    assert "body" in merged.to_json()
