from __future__ import annotations

import logging
import tracemalloc
from collections.abc import Iterator
from dataclasses import dataclass
from time import perf_counter

from epip.core.candle import Candle
from epip.core.event_bus import EventBus
from epip.features.feature_store import FeatureStore
from epip.marketdata.datasource_models import (
    ConnectionState,
    HealthCheck,
    HealthState,
    HistoryChunk,
    HistoryMetadata,
    HistoryRequest,
    HistoryResponse,
)
from epip.marketdata.datasource_protocol import DataSourceProtocol
from epip.replay.replay_config import ReplayConfig
from epip.replay.replay_engine import ReplayEngine

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _SeriesSpec:
    symbol: str
    timeframe: str
    count: int


class SyntheticReplayProvider(DataSourceProtocol):
    def __init__(self, *, spec: _SeriesSpec) -> None:
        self._spec = spec
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def health(self) -> HealthCheck:
        return HealthCheck(
            status=HealthState.HEALTHY,
            connection=(
                ConnectionState.CONNECTED if self._connected else ConnectionState.DISCONNECTED
            ),
            message="synthetic replay provider",
        )

    def available_symbols(self) -> tuple[str, ...]:
        return (self._spec.symbol,)

    def available_timeframes(self) -> tuple[str, ...]:
        return (self._spec.timeframe,)

    def history(self, request: HistoryRequest) -> HistoryResponse:
        page_size = min(request.page_size, request.limit)
        offset = (request.page - 1) * page_size
        end_index = min(offset + page_size, self._spec.count)
        candles = tuple(self._candle_at(index) for index in range(offset, end_index))
        metadata = HistoryMetadata(
            total_count=self._spec.count,
            returned_count=len(candles),
            page=request.page,
            page_size=page_size,
            has_next=end_index < self._spec.count,
            source="synthetic",
            from_cache=False,
        )
        return HistoryResponse(
            symbol=self._spec.symbol,
            timeframe=self._spec.timeframe,
            chunk=HistoryChunk(candles=candles, metadata=metadata),
        )

    def latest(self, symbol: str, timeframe: str) -> Candle | None:
        if symbol != self._spec.symbol or timeframe != self._spec.timeframe:
            return None
        return self._candle_at(self._spec.count - 1)

    def stream(self, symbol: str, timeframe: str) -> Iterator[Candle]:
        for index in range(self._spec.count):
            yield self._candle_at(index)

    def _candle_at(self, index: int) -> Candle:
        base_open = 1.1000 + (index * 0.00001)
        close = base_open + (0.00005 if index % 2 == 0 else -0.00004)
        return Candle(
            timestamp=f"2024-01-01T00:{index // 60:02d}:{index % 60:02d}+00:00",
            symbol=self._spec.symbol,
            timeframe=self._spec.timeframe,
            open=base_open,
            high=max(base_open, close) + 0.00002,
            low=min(base_open, close) - 0.00002,
            close=close,
            volume=1000.0 + float(index),
        )


def _run_case(candle_count: int) -> None:
    provider = SyntheticReplayProvider(
        spec=_SeriesSpec(symbol="EURUSD", timeframe="M1", count=candle_count)
    )
    engine = ReplayEngine(
        market_data=provider,
        feature_store=FeatureStore(),
        event_bus=EventBus(),
        kernel=None,
    )
    session = engine.create_session(
        ReplayConfig(symbols=("EURUSD",), timeframes=("M1",), page_size=5_000)
    )

    tracemalloc.start()
    started = perf_counter()
    metrics = engine.run(session)
    elapsed = perf_counter() - started
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    LOGGER.info("candles=%d", candle_count)
    LOGGER.info("elapsed_seconds=%.6f", elapsed)
    LOGGER.info("candles_per_second=%.2f", metrics.candles_per_second)
    LOGGER.info("processed_candles=%d", metrics.processed_candles)
    LOGGER.info("processed_events=%d", metrics.processed_events)
    LOGGER.info("processed_features=%d", metrics.processed_features)
    LOGGER.info("peak_memory_bytes=%d", peak)
    LOGGER.info("current_memory_bytes=%d", current)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for candle_count in (1_000_000, 5_000_000, 10_000_000):
        _run_case(candle_count)


if __name__ == "__main__":
    main()
