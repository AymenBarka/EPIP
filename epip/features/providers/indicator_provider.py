"""Indicator provider placeholder for future technical indicators."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from epip.features.feature_set import FeatureSet
from epip.features.providers.base_provider import BaseFeatureProvider


class IndicatorProvider(BaseFeatureProvider):
    """Reserved provider interface for future indicator features."""

    name = "indicator"
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
        return FeatureSet()
