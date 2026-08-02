"""Base interfaces for feature providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from epip.features.feature_set import FeatureSet


class BaseFeatureProvider(ABC):
    """Base class for providers that enrich a feature set."""

    name: str = ""
    priority: int = 0

    @abstractmethod
    def provide(
        self,
        *,
        symbol: str,
        timeframe: str,
        timestamp: str,
        payload: Mapping[str, Any] | None = None,
        feature_set: FeatureSet | None = None,
    ) -> FeatureSet:
        """Return the features produced by this provider."""
