"""CSV provider implementation for Market Data Layer."""

from __future__ import annotations

import csv
from pathlib import Path

from epip.core.candle import Candle
from epip.core.identity import ClockProtocol, IdGeneratorProtocol
from epip.marketdata.datasource_models import (
    HistoryChunk,
    HistoryMetadata,
    HistoryRequest,
    HistoryResponse,
)
from epip.marketdata.exceptions import InvalidRequestError, ProviderError
from epip.marketdata.providers.base_provider import BaseProvider


class CSVProvider(BaseProvider):
    """Provider that loads and serves candles from a CSV file."""

    def __init__(
        self,
        *,
        csv_path: str,
        default_symbol: str | None = None,
        default_timeframe: str | None = None,
        cache_expiration_seconds: float = 60.0,
        cache_max_entries: int = 1024,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        super().__init__(
            name="csv",
            cache_expiration_seconds=cache_expiration_seconds,
            cache_max_entries=cache_max_entries,
            clock=clock,
            id_generator=id_generator,
        )
        self._path = Path(csv_path)
        self._default_symbol = default_symbol
        self._default_timeframe = default_timeframe
        self._candles: tuple[Candle, ...] = ()

    def _connect_impl(self) -> None:
        if not self._path.exists():
            raise ProviderError(f"CSV file not found: {self._path}")

        candles: list[Candle] = []
        with self._path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required_columns = {"timestamp", "open", "high", "low", "close", "volume"}
            if reader.fieldnames is None or not required_columns.issubset(set(reader.fieldnames)):
                raise ProviderError("CSV file is missing required candle columns")

            for row in reader:
                symbol = str(row.get("symbol") or self._default_symbol or "UNKNOWN")
                timeframe = str(row.get("timeframe") or self._default_timeframe or "M1")
                candles.append(
                    Candle(
                        clock=self._clock,
                        id_generator=self._id_generator,
                        timestamp=str(row["timestamp"]),
                        symbol=symbol,
                        timeframe=timeframe,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row["volume"]),
                    )
                )

        self._candles = tuple(sorted(candles, key=lambda item: item.timestamp))

    def _disconnect_impl(self) -> None:
        self._candles = ()

    def available_symbols(self) -> tuple[str, ...]:
        return tuple(sorted({item.symbol for item in self._candles}))

    def available_timeframes(self) -> tuple[str, ...]:
        return tuple(sorted({item.timeframe for item in self._candles}))

    def _history_impl(self, request: HistoryRequest) -> HistoryResponse:
        if request.limit <= 0:
            raise InvalidRequestError("limit must be greater than zero")

        filtered = [
            item
            for item in self._candles
            if item.symbol == request.symbol and item.timeframe == request.timeframe
        ]
        if request.start is not None:
            filtered = [item for item in filtered if item.timestamp >= request.start]
        if request.end is not None:
            filtered = [item for item in filtered if item.timestamp <= request.end]

        total_count = len(filtered)
        page_size = min(request.page_size, request.limit)
        offset = (request.page - 1) * page_size
        end_index = offset + page_size
        paged = tuple(filtered[offset:end_index])

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
