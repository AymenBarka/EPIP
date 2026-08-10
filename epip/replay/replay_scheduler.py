"""Chronological replay scheduler across symbols and timeframes."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from threading import RLock

from epip.core.candle import Candle
from epip.marketdata.datasource_models import HistoryRequest
from epip.marketdata.datasource_protocol import DataSourceProtocol
from epip.replay.replay_config import ReplayConfig
from epip.replay.replay_iterator import ReplayIterator, ReplayIteratorCheckpoint


@dataclass(frozen=True, slots=True)
class ScheduledCandle:
    """Candle scheduled for replay processing."""

    symbol: str
    timeframe: str
    candle: Candle


@dataclass(frozen=True, slots=True)
class ReplaySchedulerCheckpoint:
    heap: tuple[tuple[str, int, str, str, ReplayIterator[Candle], Candle], ...]
    counter: int
    initialized: bool
    iterators: tuple[tuple[ReplayIterator[Candle], ReplayIteratorCheckpoint[Candle]], ...]


class ReplayScheduler:
    """Merges multiple paginated candle streams in chronological order."""

    def __init__(self, *, market_data: DataSourceProtocol, config: ReplayConfig) -> None:
        self._market_data = market_data
        self._config = config
        self._lock = RLock()
        self._heap: list[tuple[str, int, str, str, ReplayIterator[Candle], Candle]] = []
        self._counter = 0
        self._initialized = False

    def reset(self) -> None:
        with self._lock:
            self._heap.clear()
            self._counter = 0
            self._initialized = False

    def finished(self) -> bool:
        with self._lock:
            self._initialize_locked()
            return not self._heap

    def next(self) -> ScheduledCandle | None:
        with self._lock:
            self._initialize_locked()
            if not self._heap:
                return None
            _, _, symbol, timeframe, iterator, candle = heappop(self._heap)
            next_candle = iterator.next()
            if next_candle is not None:
                self._push_locked(symbol, timeframe, iterator, next_candle)
            return ScheduledCandle(symbol=symbol, timeframe=timeframe, candle=candle)

    def _initialize_locked(self) -> None:
        if self._initialized:
            return
        for symbol in self._config.symbols:
            for timeframe in self._config.timeframes:
                iterator = ReplayIterator[Candle](
                    market_data=self._market_data,
                    request=HistoryRequest(
                        symbol=symbol,
                        timeframe=timeframe,
                        start=self._config.start_date,
                        end=self._config.end_date,
                        limit=self._config.page_size,
                        page=1,
                        page_size=self._config.page_size,
                    ),
                )
                first = iterator.next()
                if first is not None:
                    self._push_locked(symbol, timeframe, iterator, first)
        self._initialized = True

    def _push_locked(
        self,
        symbol: str,
        timeframe: str,
        iterator: ReplayIterator[Candle],
        candle: Candle,
    ) -> None:
        heappush(self._heap, (candle.timestamp, self._counter, symbol, timeframe, iterator, candle))
        self._counter += 1

    def _checkpoint(self) -> ReplaySchedulerCheckpoint:
        iterators: dict[int, ReplayIterator[Candle]] = {}
        for _, _, _, _, iterator, _ in self._heap:
            iterators[id(iterator)] = iterator
        return ReplaySchedulerCheckpoint(
            tuple(self._heap),
            self._counter,
            self._initialized,
            tuple((iterator, iterator._checkpoint()) for iterator in iterators.values()),
        )

    def _restore(self, checkpoint: ReplaySchedulerCheckpoint) -> None:
        for iterator, state in checkpoint.iterators:
            iterator._restore(state)
        self._heap = list(checkpoint.heap)
        self._counter = checkpoint.counter
        self._initialized = checkpoint.initialized
