"""Thread-safe LRU cache for market data history and latest requests."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock

from epip.core.candle import Candle
from epip.marketdata.datasource_models import HistoryRequest, HistoryResponse


@dataclass(frozen=True, slots=True)
class CacheStats:
    history_hits: int
    history_misses: int
    latest_hits: int
    latest_misses: int
    history_size: int
    latest_size: int


@dataclass(frozen=True, slots=True)
class _HistoryKey:
    symbol: str
    timeframe: str
    start: str | None
    end: str | None
    limit: int
    page: int
    page_size: int


@dataclass(frozen=True, slots=True)
class _LatestKey:
    symbol: str
    timeframe: str


@dataclass(frozen=True, slots=True)
class _Entry[T]:
    value: T
    expires_at: datetime


class DataSourceCache:
    """Stores cached history and latest responses using LRU eviction."""

    def __init__(self, *, expiration_seconds: float = 60.0, max_entries: int = 1024) -> None:
        if expiration_seconds <= 0:
            raise ValueError("expiration_seconds must be greater than zero")
        if max_entries <= 0:
            raise ValueError("max_entries must be greater than zero")

        self._lock = RLock()
        self._expiration = timedelta(seconds=expiration_seconds)
        self._max_entries = max_entries
        self._history: OrderedDict[_HistoryKey, _Entry[HistoryResponse]] = OrderedDict()
        self._latest: OrderedDict[_LatestKey, _Entry[Candle]] = OrderedDict()
        self._history_hits = 0
        self._history_misses = 0
        self._latest_hits = 0
        self._latest_misses = 0

    def get_history(self, request: HistoryRequest) -> HistoryResponse | None:
        key = _HistoryKey(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
            limit=request.limit,
            page=request.page,
            page_size=request.page_size,
        )
        now = datetime.now(UTC)
        with self._lock:
            entry = self._history.get(key)
            if entry is None:
                self._history_misses += 1
                return None
            if entry.expires_at <= now:
                self._history.pop(key, None)
                self._history_misses += 1
                return None
            self._history.move_to_end(key)
            self._history_hits += 1
            metadata = entry.value.chunk.metadata
            return HistoryResponse(
                symbol=entry.value.symbol,
                timeframe=entry.value.timeframe,
                chunk=type(entry.value.chunk)(
                    candles=entry.value.chunk.candles,
                    metadata=type(metadata)(
                        total_count=metadata.total_count,
                        returned_count=metadata.returned_count,
                        page=metadata.page,
                        page_size=metadata.page_size,
                        has_next=metadata.has_next,
                        source=metadata.source,
                        from_cache=True,
                    ),
                ),
            )

    def set_history(self, request: HistoryRequest, response: HistoryResponse) -> None:
        key = _HistoryKey(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
            limit=request.limit,
            page=request.page,
            page_size=request.page_size,
        )
        with self._lock:
            self._history[key] = _Entry(
                value=response, expires_at=datetime.now(UTC) + self._expiration
            )
            self._history.move_to_end(key)
            self._trim_history()

    def get_latest(self, *, symbol: str, timeframe: str) -> Candle | None:
        key = _LatestKey(symbol=symbol, timeframe=timeframe)
        now = datetime.now(UTC)
        with self._lock:
            entry = self._latest.get(key)
            if entry is None:
                self._latest_misses += 1
                return None
            if entry.expires_at <= now:
                self._latest.pop(key, None)
                self._latest_misses += 1
                return None
            self._latest.move_to_end(key)
            self._latest_hits += 1
            return entry.value

    def set_latest(self, *, symbol: str, timeframe: str, candle: Candle) -> None:
        key = _LatestKey(symbol=symbol, timeframe=timeframe)
        with self._lock:
            self._latest[key] = _Entry(
                value=candle, expires_at=datetime.now(UTC) + self._expiration
            )
            self._latest.move_to_end(key)
            self._trim_latest()

    def invalidate(self, *, symbol: str | None = None, timeframe: str | None = None) -> None:
        with self._lock:
            if symbol is None and timeframe is None:
                self._history.clear()
                self._latest.clear()
                return
            self._history = OrderedDict(
                (
                    key,
                    value,
                )
                for key, value in self._history.items()
                if not (
                    (symbol is None or key.symbol == symbol)
                    and (timeframe is None or key.timeframe == timeframe)
                )
            )
            self._latest = OrderedDict(
                (
                    key,
                    value,
                )
                for key, value in self._latest.items()
                if not (
                    (symbol is None or key.symbol == symbol)
                    and (timeframe is None or key.timeframe == timeframe)
                )
            )

    def prune_expired(self) -> int:
        now = datetime.now(UTC)
        removed = 0
        with self._lock:
            history_keys = [key for key, value in self._history.items() if value.expires_at <= now]
            latest_keys = [key for key, value in self._latest.items() if value.expires_at <= now]
            for history_key in history_keys:
                self._history.pop(history_key, None)
                removed += 1
            for latest_key in latest_keys:
                self._latest.pop(latest_key, None)
                removed += 1
        return removed

    def stats(self) -> CacheStats:
        with self._lock:
            return CacheStats(
                history_hits=self._history_hits,
                history_misses=self._history_misses,
                latest_hits=self._latest_hits,
                latest_misses=self._latest_misses,
                history_size=len(self._history),
                latest_size=len(self._latest),
            )

    def _trim_history(self) -> None:
        while len(self._history) > self._max_entries:
            self._history.popitem(last=False)

    def _trim_latest(self) -> None:
        while len(self._latest) > self._max_entries:
            self._latest.popitem(last=False)
