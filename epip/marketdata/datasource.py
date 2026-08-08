"""Datasource façade exposing the DataSourceProtocol entry point."""

from __future__ import annotations

from collections.abc import Iterator

from epip.core.candle import Candle
from epip.core.integrity import integrity_boundary
from epip.marketdata.datasource_models import HealthCheck, HistoryRequest, HistoryResponse
from epip.marketdata.datasource_protocol import DataSourceProtocol


class DataSource:
    """Thin façade around a DataSourceProtocol implementation."""

    def __init__(self, provider: DataSourceProtocol) -> None:
        self._provider = provider

    def connect(self) -> None:
        self._provider.connect()

    def disconnect(self) -> None:
        self._provider.disconnect()

    def health(self) -> HealthCheck:
        return self._provider.health()

    def available_symbols(self) -> tuple[str, ...]:
        return self._provider.available_symbols()

    def available_timeframes(self) -> tuple[str, ...]:
        return self._provider.available_timeframes()

    @integrity_boundary
    def history(self, request: HistoryRequest) -> HistoryResponse:
        return self._provider.history(request)

    @integrity_boundary
    def latest(self, symbol: str, timeframe: str) -> Candle | None:
        return self._provider.latest(symbol, timeframe)

    def stream(self, symbol: str, timeframe: str) -> Iterator[Candle]:
        return self._provider.stream(symbol, timeframe)
