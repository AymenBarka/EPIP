"""Immutable feature object for the EPIP feature store."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


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
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "value": self.value,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
            "quality_score": self.quality_score,
            "source": self.source,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)
