"""Container for features collected for a single candle."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from epip.features.feature import Feature


@dataclass(frozen=True, slots=True)
class FeatureSet:
    """Immutable set of features available for a candle."""

    features: tuple[Feature, ...] = ()
    _feature_map: Mapping[str, Feature] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        features = tuple(self.features)
        object.__setattr__(self, "features", features)
        object.__setattr__(
            self, "_feature_map", MappingProxyType({item.name: item for item in features})
        )

    def get(self, name: str, default: Feature | None = None) -> Feature | None:
        return self._feature_map.get(name, default)

    def exists(self, name: str) -> bool:
        return name in self._feature_map

    def filter(
        self,
        *,
        category: str | None = None,
        source: str | None = None,
        names: Iterable[str] | None = None,
    ) -> FeatureSet:
        selected: list[Feature] = []
        allowed_names = None if names is None else set(names)
        for feature in self.features:
            if category is not None and feature.category != category:
                continue
            if source is not None and feature.source != source:
                continue
            if allowed_names is not None and feature.name not in allowed_names:
                continue
            selected.append(feature)
        return FeatureSet(tuple(selected))

    def merge(self, other: FeatureSet) -> FeatureSet:
        combined = {feature.name: feature for feature in self.features}
        for feature in other.features:
            combined[feature.name] = feature
        return FeatureSet(tuple(combined.values()))

    def to_dict(self) -> dict[str, dict[str, Any]]:
        return {name: feature.to_dict() for name, feature in self._feature_map.items()}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)
