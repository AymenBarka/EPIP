"""Immutable feature object for the EPIP feature store."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from epip.core.integrity import deep_freeze, deep_thaw, require_text, require_unit_interval


@dataclass(frozen=True, slots=True)
class Feature:
    """Represents a single feature emitted by a provider for a candle."""

    id: str
    name: str
    category: str
    value: Any
    timestamp: str
    metadata: Mapping[str, Any]
    quality_score: float
    source: str

    def __post_init__(self) -> None:
        require_text(self.id, "feature.id")
        require_text(self.name, "feature.name")
        require_text(self.category, "feature.category")
        require_text(self.timestamp, "feature.timestamp")
        require_text(self.source, "feature.source")
        require_unit_interval(self.quality_score, "feature.quality_score")
        object.__setattr__(self, "metadata", deep_freeze(self.metadata))
        object.__setattr__(self, "value", deep_freeze(self.value))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "value": deep_thaw(self.value),
            "timestamp": self.timestamp,
            "metadata": deep_thaw(self.metadata),
            "quality_score": self.quality_score,
            "source": self.source,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)
