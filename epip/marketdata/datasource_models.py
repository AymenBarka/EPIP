"""Immutable models for Market Data Layer contracts."""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from enum import Enum

from epip.core.candle import Candle
from epip.core.identity import ClockProtocol, resolve_clock


class ConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    DEGRADED = "degraded"


class HealthState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True, slots=True)
class HealthCheck:
    status: HealthState
    connection: ConnectionState
    message: str
    checked_at: str = ""
    clock: InitVar[ClockProtocol | None] = None

    def __post_init__(self, clock: ClockProtocol | None) -> None:
        object.__setattr__(self, "checked_at", self.checked_at or resolve_clock(clock).now())


@dataclass(frozen=True, slots=True)
class HistoryRequest:
    symbol: str
    timeframe: str
    start: str | None = None
    end: str | None = None
    limit: int = 500
    page: int = 1
    page_size: int = 500

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol must be provided")
        if not self.timeframe:
            raise ValueError("timeframe must be provided")
        if self.limit <= 0:
            raise ValueError("limit must be greater than zero")
        if self.page <= 0:
            raise ValueError("page must be greater than zero")
        if self.page_size <= 0:
            raise ValueError("page_size must be greater than zero")


@dataclass(frozen=True, slots=True)
class HistoryMetadata:
    total_count: int
    returned_count: int
    page: int
    page_size: int
    has_next: bool
    source: str
    from_cache: bool


@dataclass(frozen=True, slots=True)
class HistoryChunk:
    candles: tuple[Candle, ...]
    metadata: HistoryMetadata


@dataclass(frozen=True, slots=True)
class HistoryResponse:
    symbol: str
    timeframe: str
    chunk: HistoryChunk


@dataclass(frozen=True, slots=True)
class LiveRequest:
    symbol: str
    timeframe: str


@dataclass(frozen=True, slots=True)
class LiveResponse:
    symbol: str
    timeframe: str
    candle: Candle | None


@dataclass(frozen=True, slots=True)
class LiveSubscription:
    symbol: str
    timeframe: str
    subscription_id: str
    active: bool
