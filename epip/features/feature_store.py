"""Thread-safe feature store for EPIP."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from threading import RLock
from typing import Any

from epip.features.feature_pipeline import FeaturePipeline
from epip.features.feature_set import FeatureSet
from epip.features.providers.base_provider import BaseFeatureProvider
from epip.features.providers.ohlc_provider import OHLCProvider
from epip.features.providers.session_provider import SessionProvider


@dataclass(frozen=True, slots=True)
class FeatureStoreCheckpoint:
    cache: dict[tuple[str, str, str], FeatureSet]
    history: tuple[FeatureSet, ...]


class FeatureStore:
    """Centralized provider-driven feature repository for enriched market data."""

    def __init__(
        self,
        *,
        providers: tuple[BaseFeatureProvider, ...] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._providers: dict[str, BaseFeatureProvider] = {}
        self._priorities: dict[str, int] = {}
        self._order: list[str] = []
        self._pipeline = FeaturePipeline()
        self._cache: dict[tuple[str, str, str], FeatureSet] = {}
        self._history: list[FeatureSet] = []
        self._lock = RLock()
        self.logger = logger or logging.getLogger("epip.features")

        for provider in providers or (OHLCProvider(), SessionProvider()):
            self.register_provider(provider)

    def register_provider(self, provider: BaseFeatureProvider, priority: int | None = None) -> None:
        name = self._resolve_name(provider)
        with self._lock:
            self._providers[name] = provider
            self._priorities[name] = provider.priority if priority is None else priority
            if name not in self._order:
                self._order.append(name)
            self._pipeline = FeaturePipeline(self._ordered_providers())

    def unregister_provider(self, provider_or_name: BaseFeatureProvider | str) -> None:
        name = self._resolve_name(provider_or_name)
        with self._lock:
            self._providers.pop(name, None)
            self._priorities.pop(name, None)
            if name in self._order:
                self._order.remove(name)
            self._pipeline = FeaturePipeline(self._ordered_providers())

    def build_feature_set(
        self,
        symbol: str,
        timeframe: str,
        timestamp: str,
        *,
        payload: Mapping[str, Any] | None = None,
    ) -> FeatureSet:
        cache_key = (symbol, timeframe, timestamp)
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self.logger.debug("cache hit for %s", cache_key)
                return cached

            feature_set = self._cache.get(cache_key)
            if feature_set is None:
                feature_set = self._pipeline.run(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    payload=payload,
                )
                self._cache[cache_key] = feature_set
                self._history.append(feature_set)

            return feature_set

    def invalidate_cache(
        self,
        symbol: str | None = None,
        timeframe: str | None = None,
        timestamp: str | None = None,
    ) -> None:
        with self._lock:
            if symbol is None and timeframe is None and timestamp is None:
                self._cache.clear()
                return
            keys_to_remove = [
                key
                for key in self._cache
                if (symbol is None or key[0] == symbol)
                and (timeframe is None or key[1] == timeframe)
                and (timestamp is None or key[2] == timestamp)
            ]
            for key in keys_to_remove:
                self._cache.pop(key, None)

    def history(self) -> tuple[FeatureSet, ...]:
        with self._lock:
            return tuple(self._history)

    def cache_size(self) -> int:
        with self._lock:
            return len(self._cache)

    def cache_keys(self) -> tuple[tuple[str, str, str], ...]:
        with self._lock:
            return tuple(self._cache.keys())

    def _ordered_providers(self) -> tuple[BaseFeatureProvider, ...]:
        with self._lock:
            ordered_names = sorted(
                self._order,
                key=lambda name: (self._priorities.get(name, 0), self._order.index(name)),
            )
            return tuple(self._providers[name] for name in ordered_names)

    def _resolve_name(self, provider_or_name: BaseFeatureProvider | str) -> str:
        if isinstance(provider_or_name, str):
            return provider_or_name
        return getattr(provider_or_name, "name", provider_or_name.__class__.__name__)

    def _checkpoint(self) -> FeatureStoreCheckpoint:
        return FeatureStoreCheckpoint(dict(self._cache), tuple(self._history))

    def _restore(self, checkpoint: FeatureStoreCheckpoint) -> None:
        self._cache = dict(checkpoint.cache)
        self._history = list(checkpoint.history)
