"""TwelveData provider using an adapter port (no HTTP in EPIP-004)."""

from __future__ import annotations

from collections.abc import Iterator

from epip.core.candle import Candle
from epip.marketdata.adapters.twelvedata_adapter import NullTwelveDataAdapter, TwelveDataAdapter
from epip.marketdata.datasource_models import (
    ConnectionState,
    HealthCheck,
    HealthState,
    HistoryRequest,
    HistoryResponse,
)
from epip.marketdata.exceptions import ProviderError
from epip.marketdata.providers.base_provider import BaseProvider


class TwelveDataProvider(BaseProvider):
    """Adapter-backed provider prepared for future TwelveData integration."""

    def __init__(self, *, adapter: TwelveDataAdapter | None = None) -> None:
        super().__init__(name="twelvedata")
        self._adapter = adapter or NullTwelveDataAdapter()

    def _connect_impl(self) -> None:
        self._adapter.connect()

    def _disconnect_impl(self) -> None:
        self._adapter.disconnect()

    def available_symbols(self) -> tuple[str, ...]:
        return ()

    def available_timeframes(self) -> tuple[str, ...]:
        return ()

    def _history_impl(self, request: HistoryRequest) -> HistoryResponse:
        try:
            return self._adapter.history(request)
        except NotImplementedError as exc:
            raise ProviderError("TwelveData provider is interface-only in EPIP-004") from exc

    def latest(self, symbol: str, timeframe: str) -> Candle | None:
        self._ensure_connected()
        try:
            return self._adapter.latest(symbol, timeframe)
        except NotImplementedError as exc:
            raise ProviderError("TwelveData provider is interface-only in EPIP-004") from exc

    def stream(self, symbol: str, timeframe: str) -> Iterator[Candle]:
        self._ensure_connected()
        try:
            yield from self._adapter.stream(symbol, timeframe)
        except NotImplementedError as exc:
            raise ProviderError("TwelveData provider is interface-only in EPIP-004") from exc

    def health(self) -> HealthCheck:
        self._ensure_connected()
        try:
            return self._adapter.health()
        except NotImplementedError:
            return HealthCheck(
                status=HealthState.DEGRADED,
                connection=ConnectionState.CONNECTED,
                message="interface-only provider",
            )
