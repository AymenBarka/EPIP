from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from epip.features.feature import Feature
from epip.features.feature_pipeline import FeaturePipeline
from epip.features.feature_set import FeatureSet
from epip.features.providers.base_provider import BaseFeatureProvider


class IncrementProvider(BaseFeatureProvider):
    name = "increment"
    priority = 10

    def provide(
        self,
        *,
        symbol: str,
        timeframe: str,
        timestamp: str,
        payload: Mapping[str, Any] | None = None,
        feature_set: FeatureSet | None = None,
    ) -> FeatureSet:
        base_value = int((payload or {}).get("value", 0))
        return FeatureSet(
            (
                Feature(
                    id=f"{self.name}-{timestamp}",
                    name="incremented",
                    category="test",
                    value=float(base_value + 1),
                    timestamp=timestamp,
                    metadata={"symbol": symbol},
                    quality_score=0.9,
                    source=self.name,
                ),
            )
        )


class ScaleProvider(BaseFeatureProvider):
    name = "scale"
    priority = 20

    def provide(
        self,
        *,
        symbol: str,
        timeframe: str,
        timestamp: str,
        payload: Mapping[str, Any] | None = None,
        feature_set: FeatureSet | None = None,
    ) -> FeatureSet:
        value = float((payload or {}).get("value", 0))
        return FeatureSet(
            (
                Feature(
                    id=f"{self.name}-{timestamp}",
                    name="scaled",
                    category="test",
                    value=value * 2.0,
                    timestamp=timestamp,
                    metadata={"timeframe": timeframe},
                    quality_score=0.8,
                    source=self.name,
                ),
            )
        )


def test_pipeline_executes_providers_in_order() -> None:
    pipeline = FeaturePipeline((IncrementProvider(), ScaleProvider()))
    feature_set = pipeline.run(
        symbol="EURUSD",
        timeframe="M1",
        timestamp="2024-01-01T00:00:00Z",
        payload={"value": 3},
    )

    assert feature_set.get("incremented") is not None
    assert feature_set.get("scaled") is not None
    incremented = feature_set.get("incremented")
    scaled = feature_set.get("scaled")
    assert incremented is not None
    assert scaled is not None
    assert incremented.value == 4.0
    assert scaled.value == 6.0
