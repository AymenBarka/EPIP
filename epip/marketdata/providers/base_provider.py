"""Base provider implementation for Market Data Layer providers."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from threading import RLock

from epip.core.candle import Candle
from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.marketdata.datasource_cache import CacheStats, DataSourceCache
from epip.marketdata.datasource_models import (
    ConnectionState,
    HealthCheck,
    HealthState,
    HistoryRequest,
    HistoryResponse,
)
from epip.marketdata.exceptions import ConnectionError


class BaseProvider(ABC):
    """Base class implementing lifecycle and cache orchestration."""

    def __init__(
        self,
        *,
        name: str,
        cache_expiration_seconds: float = 60.0,
        cache_max_entries: int = 1024,
        logger: logging.Logger | None = None,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        self.name = name
        self._lock = RLock()
        self._connected = False
        self._clock = resolve_clock(clock)
        self._id_generator = resolve_id_generator(id_generator)
        self._cache = DataSourceCache(
            expiration_seconds=cache_expiration_seconds,
            max_entries=cache_max_entries,
            clock=self._clock,
        )
        self._logger = logger or logging.getLogger(f"epip.marketdata.{name}")

    def connect(self) -> None:
        with self._lock:
            if self._connected:
                return
            self._connect_impl()
            self._connected = True

    def disconnect(self) -> None:
        with self._lock:
            if not self._connected:
                return
            self._disconnect_impl()
            self._connected = False

    def health(self) -> HealthCheck:
        with self._lock:
            if not self._connected:
                return HealthCheck(
                    status=HealthState.DEGRADED,
                    connection=ConnectionState.DISCONNECTED,
                    message="provider disconnected",
                    clock=self._clock,
                )
            return HealthCheck(
                status=HealthState.HEALTHY,
                connection=ConnectionState.CONNECTED,
                message="provider connected",
                clock=self._clock,
            )

    def history(self, request: HistoryRequest) -> HistoryResponse:
        self._ensure_connected()
        cached = self._cache.get_history(request)
        if cached is not None:
            return cached

        response = self._history_impl(request)
        self._cache.set_history(request, response)
        if response.chunk.candles:
            self._cache.set_latest(
                symbol=request.symbol,
                timeframe=request.timeframe,
                candle=response.chunk.candles[-1],
            )
        return response

    def latest(self, symbol: str, timeframe: str) -> Candle | None:
        self._ensure_connected()
        cached = self._cache.get_latest(symbol=symbol, timeframe=timeframe)
        if cached is not None:
            return cached

        response = self.history(HistoryRequest(symbol=symbol, timeframe=timeframe, limit=1))
        if not response.chunk.candles:
            return None
        latest = response.chunk.candles[-1]
        self._cache.set_latest(symbol=symbol, timeframe=timeframe, candle=latest)
        return latest

    def stream(self, symbol: str, timeframe: str) -> Iterator[Candle]:
        self._ensure_connected()
        response = self.history(
            HistoryRequest(
                symbol=symbol, timeframe=timeframe, limit=10_000, page=1, page_size=10_000
            )
        )
        yield from response.chunk.candles

    def cache_stats(self) -> CacheStats:
        return self._cache.stats()

    def _ensure_connected(self) -> None:
        with self._lock:
            if not self._connected:
                raise ConnectionError(f"{self.name} provider is not connected")

    def _connect_impl(self) -> None:
        """Optional provider-specific connection hook."""

    def _disconnect_impl(self) -> None:
        """Optional provider-specific disconnection hook."""

    @abstractmethod
    def available_symbols(self) -> tuple[str, ...]:
        """Return available symbols."""

    @abstractmethod
    def available_timeframes(self) -> tuple[str, ...]:
        """Return available timeframes."""

    @abstractmethod
    def _history_impl(self, request: HistoryRequest) -> HistoryResponse:
        """Provider-specific history retrieval implementation."""
