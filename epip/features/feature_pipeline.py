"""Pipeline for progressively enriching a feature set."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from epip.features.feature_set import FeatureSet
from epip.features.providers.base_provider import BaseFeatureProvider


class FeaturePipeline:
    """Runs providers in order to build a richer feature set."""

    def __init__(self, providers: Iterable[BaseFeatureProvider] | None = None) -> None:
        self._providers = tuple(providers or ())

    def run(
        self,
        *,
        symbol: str,
        timeframe: str,
        timestamp: str,
        payload: Mapping[str, Any] | None = None,
        feature_set: FeatureSet | None = None,
    ) -> FeatureSet:
        current = feature_set or FeatureSet()
        for provider in self._providers:
            current = current.merge(
                provider.provide(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    payload=payload,
                    feature_set=current,
                )
            )
        return current
