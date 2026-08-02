"""Port definition for all market data providers."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from epip.core.candle import Candle
from epip.marketdata.datasource_models import HealthCheck, HistoryRequest, HistoryResponse


class DataSourceProtocol(Protocol):
    """Unified provider contract for market data ingress."""

    def connect(self) -> None:
        """Connect provider resources."""

    def disconnect(self) -> None:
        """Disconnect provider resources."""

    def health(self) -> HealthCheck:
        """Return provider health snapshot."""

    def available_symbols(self) -> tuple[str, ...]:
        """Return available symbols."""

    def available_timeframes(self) -> tuple[str, ...]:
        """Return available timeframes."""

    def history(self, request: HistoryRequest) -> HistoryResponse:
        """Return historical candles."""

    def latest(self, symbol: str, timeframe: str) -> Candle | None:
        """Return latest candle for symbol/timeframe."""

    def stream(self, symbol: str, timeframe: str) -> Iterator[Candle]:
        """Return candle stream iterator."""
