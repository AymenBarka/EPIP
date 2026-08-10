"""MT5 provider using an adapter port (no MetaTrader dependency in EPIP-004)."""

from __future__ import annotations

from collections.abc import Iterator

from epip.core.candle import Candle
from epip.core.identity import ClockProtocol, IdGeneratorProtocol
from epip.marketdata.adapters.mt5_adapter import MT5Adapter, NullMT5Adapter
from epip.marketdata.datasource_models import (
    ConnectionState,
    HealthCheck,
    HealthState,
    HistoryRequest,
    HistoryResponse,
)
from epip.marketdata.exceptions import ProviderError
from epip.marketdata.providers.base_provider import BaseProvider


class MT5Provider(BaseProvider):
    """Adapter-backed provider prepared for future MT5 integration."""

    def __init__(
        self,
        *,
        adapter: MT5Adapter | None = None,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        super().__init__(name="mt5", clock=clock, id_generator=id_generator)
        self._adapter = adapter or NullMT5Adapter()

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
            raise ProviderError("MT5 provider is architecture-only in EPIP-004") from exc

    def latest(self, symbol: str, timeframe: str) -> Candle | None:
        self._ensure_connected()
        try:
            return self._adapter.latest(symbol, timeframe)
        except NotImplementedError as exc:
            raise ProviderError("MT5 provider is architecture-only in EPIP-004") from exc

    def stream(self, symbol: str, timeframe: str) -> Iterator[Candle]:
        self._ensure_connected()
        try:
            yield from self._adapter.stream(symbol, timeframe)
        except NotImplementedError as exc:
            raise ProviderError("MT5 provider is architecture-only in EPIP-004") from exc

    def health(self) -> HealthCheck:
        self._ensure_connected()
        try:
            return self._adapter.health()
        except NotImplementedError:
            return HealthCheck(
                status=HealthState.DEGRADED,
                connection=ConnectionState.CONNECTED,
                message="architecture-only provider",
                clock=self._clock,
            )
