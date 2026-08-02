"""TwelveData adapter port and null implementation for EPIP-004."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from epip.core.candle import Candle
from epip.marketdata.datasource_models import (
    ConnectionState,
    HealthCheck,
    HealthState,
    HistoryRequest,
    HistoryResponse,
)


class TwelveDataAdapter(Protocol):
    """Port for future TwelveData client implementations."""

    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def health(self) -> HealthCheck: ...

    def history(self, request: HistoryRequest) -> HistoryResponse: ...

    def latest(self, symbol: str, timeframe: str) -> Candle | None: ...

    def stream(self, symbol: str, timeframe: str) -> Iterator[Candle]: ...


class NullTwelveDataAdapter:
    """Non-network adapter placeholder used until HTTP integration is introduced."""

    def connect(self) -> None:
        return None

    def disconnect(self) -> None:
        return None

    def health(self) -> HealthCheck:
        return HealthCheck(
            status=HealthState.DEGRADED,
            connection=ConnectionState.CONNECTED,
            message="interface-only",
        )

    def history(self, request: HistoryRequest) -> HistoryResponse:
        raise NotImplementedError("TwelveData adapter is interface-only in EPIP-004")

    def latest(self, symbol: str, timeframe: str) -> Candle | None:
        raise NotImplementedError("TwelveData adapter is interface-only in EPIP-004")

    def stream(self, symbol: str, timeframe: str) -> Iterator[Candle]:
        raise NotImplementedError("TwelveData adapter is interface-only in EPIP-004")
