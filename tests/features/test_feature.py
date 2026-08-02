from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from epip.features.feature import Feature


def test_feature_is_immutable_and_serializable() -> None:
    feature = Feature(
        id="f-1",
        name="close",
        category="ohlc",
        value=1.23,
        timestamp="2024-01-01T00:00:00Z",
        metadata={"source": "ohlc"},
        quality_score=0.95,
        source="ohlc",
    )

    payload = feature.to_dict()
    assert payload["name"] == "close"
    assert json.loads(feature.to_json())["value"] == 1.23

    with pytest.raises(FrozenInstanceError):
        feature.name = "other"  # type: ignore[misc]

    assert feature.metadata["source"] == "ohlc"
