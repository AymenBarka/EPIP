"""Lazy paginated iterator for replay candle streams."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from threading import RLock
from typing import TypeVar, cast

from epip.core.candle import Candle
from epip.marketdata.datasource_models import HistoryRequest, HistoryResponse
from epip.marketdata.datasource_protocol import DataSourceProtocol

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ReplayIteratorCheckpoint[T]:
    page: int
    buffer: tuple[T, ...]
    index: int
    current: T | None
    previous: T | None
    finished: bool
    has_next_page: bool


class ReplayIterator[T]:
    """Lazy iterator over paginated history responses."""

    def __init__(
        self,
        *,
        market_data: DataSourceProtocol,
        request: HistoryRequest,
        extractor: Callable[[HistoryResponse], tuple[T, ...]] | None = None,
    ) -> None:
        self._market_data = market_data
        self._base_request = request
        self._extractor = extractor or cast(
            Callable[[HistoryResponse], tuple[T, ...]], _default_extractor
        )
        self._lock = RLock()
        self._page = 1
        self._buffer: tuple[T, ...] = ()
        self._index = 0
        self._current: T | None = None
        self._previous: T | None = None
        self._finished = False
        self._has_next_page = True

    def next(self) -> T | None:
        with self._lock:
            if not self._ensure_buffer_locked():
                self._finished = True
                return None
            self._previous = self._current
            self._current = self._buffer[self._index]
            self._index += 1
            if self._index >= len(self._buffer) and not self._has_next_page:
                self._finished = True
            return self._current

    def previous(self) -> T | None:
        with self._lock:
            return self._previous

    def peek(self) -> T | None:
        with self._lock:
            if not self._ensure_buffer_locked():
                return None
            return self._buffer[self._index]

    def current(self) -> T | None:
        with self._lock:
            return self._current

    def reset(self) -> None:
        with self._lock:
            self._page = 1
            self._buffer = ()
            self._index = 0
            self._current = None
            self._previous = None
            self._finished = False
            self._has_next_page = True

    def finished(self) -> bool:
        with self._lock:
            return self._finished

    def _ensure_buffer_locked(self) -> bool:
        if self._index < len(self._buffer):
            return True
        if not self._has_next_page:
            return False

        request = replace(self._base_request, page=self._page)
        response = self._market_data.history(request)
        self._buffer = tuple(self._extractor(response))
        self._index = 0
        self._page += 1
        self._has_next_page = response.chunk.metadata.has_next
        return bool(self._buffer)

    def __iter__(self) -> ReplayIterator[T]:
        return self

    def __next__(self) -> T:
        item = self.next()
        if item is None:
            raise StopIteration
        return item

    def _checkpoint(self) -> ReplayIteratorCheckpoint[T]:
        return ReplayIteratorCheckpoint(
            self._page,
            self._buffer,
            self._index,
            self._current,
            self._previous,
            self._finished,
            self._has_next_page,
        )

    def _restore(self, checkpoint: ReplayIteratorCheckpoint[T]) -> None:
        self._page = checkpoint.page
        self._buffer = checkpoint.buffer
        self._index = checkpoint.index
        self._current = checkpoint.current
        self._previous = checkpoint.previous
        self._finished = checkpoint.finished
        self._has_next_page = checkpoint.has_next_page


def _default_extractor(response: HistoryResponse) -> tuple[Candle, ...]:
    return response.chunk.candles
