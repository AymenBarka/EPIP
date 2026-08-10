"""Fake provider for deterministic tests and benchmarks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from epip.core.candle import Candle
from epip.core.identity import ClockProtocol, IdGeneratorProtocol
from epip.marketdata.datasource_models import (
    HistoryChunk,
    HistoryMetadata,
    HistoryRequest,
    HistoryResponse,
)
from epip.marketdata.providers.base_provider import BaseProvider


class FakeProvider(BaseProvider):
    """In-memory deterministic provider used for tests."""

    def __init__(
        self,
        *,
        symbols: tuple[str, ...] = ("EURUSD",),
        timeframes: tuple[str, ...] = ("M1",),
        candles_per_series: int = 2_000,
        cache_expiration_seconds: float = 60.0,
        cache_max_entries: int = 1024,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        super().__init__(
            name="fake",
            cache_expiration_seconds=cache_expiration_seconds,
            cache_max_entries=cache_max_entries,
            clock=clock,
            id_generator=id_generator,
        )
        self._symbols = symbols
        self._timeframes = timeframes
        self._candles_per_series = candles_per_series
        self._series: dict[tuple[str, str], tuple[Candle, ...]] = {}

    def _connect_impl(self) -> None:
        self._series.clear()
        for symbol in self._symbols:
            for timeframe in self._timeframes:
                self._series[(symbol, timeframe)] = self._generate(symbol, timeframe)

    def _disconnect_impl(self) -> None:
        self._series.clear()

    def available_symbols(self) -> tuple[str, ...]:
        return self._symbols

    def available_timeframes(self) -> tuple[str, ...]:
        return self._timeframes

    def _history_impl(self, request: HistoryRequest) -> HistoryResponse:
        rows = list(self._series.get((request.symbol, request.timeframe), ()))
        if request.start is not None:
            rows = [item for item in rows if item.timestamp >= request.start]
        if request.end is not None:
            rows = [item for item in rows if item.timestamp <= request.end]

        total_count = len(rows)
        page_size = min(request.page_size, request.limit)
        offset = (request.page - 1) * page_size
        end_index = offset + page_size
        paged = tuple(rows[offset:end_index])

        chunk = HistoryChunk(
            candles=paged,
            metadata=HistoryMetadata(
                total_count=total_count,
                returned_count=len(paged),
                page=request.page,
                page_size=page_size,
                has_next=end_index < total_count,
                source=self.name,
                from_cache=False,
            ),
        )
        return HistoryResponse(symbol=request.symbol, timeframe=request.timeframe, chunk=chunk)

    def _generate(self, symbol: str, timeframe: str) -> tuple[Candle, ...]:
        base = datetime(2024, 1, 1, tzinfo=UTC)
        candles: list[Candle] = []
        price = 1.1000
        for index in range(self._candles_per_series):
            open_price = price
            close_price = open_price + (0.0001 if index % 2 == 0 else -0.00008)
            high_price = max(open_price, close_price) + 0.00004
            low_price = min(open_price, close_price) - 0.00004
            candles.append(
                Candle(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    timestamp=(base + timedelta(minutes=index)).isoformat(),
                    symbol=symbol,
                    timeframe=timeframe,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=500.0 + float(index),
                )
            )
            price = close_price
        return tuple(candles)
