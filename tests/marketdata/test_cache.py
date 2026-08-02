from __future__ import annotations

from time import sleep

import pytest

from epip.core.candle import Candle
from epip.marketdata.datasource_cache import DataSourceCache
from epip.marketdata.datasource_models import (
    HistoryChunk,
    HistoryMetadata,
    HistoryRequest,
    HistoryResponse,
)


def _candle(index: int = 0) -> Candle:
    return Candle(
        timestamp=f"2024-01-01T00:00:{index:02d}+00:00",
        symbol="EURUSD",
        timeframe="M1",
        open=1.1000,
        high=1.1010,
        low=1.0990,
        close=1.1005,
        volume=1000.0,
    )


def _response() -> HistoryResponse:
    metadata = HistoryMetadata(
        total_count=1,
        returned_count=1,
        page=1,
        page_size=1,
        has_next=False,
        source="test",
        from_cache=False,
    )
    return HistoryResponse(
        symbol="EURUSD",
        timeframe="M1",
        chunk=HistoryChunk(candles=(_candle(),), metadata=metadata),
    )


def test_cache_history_latest_and_stats() -> None:
    cache = DataSourceCache(expiration_seconds=60.0, max_entries=4)
    req = HistoryRequest(symbol="EURUSD", timeframe="M1", limit=1, page=1, page_size=1)

    cache.set_history(req, _response())
    cached = cache.get_history(req)
    assert cached is not None
    assert cached.chunk.metadata.from_cache is True

    cache.set_latest(symbol="EURUSD", timeframe="M1", candle=_candle(1))
    latest = cache.get_latest(symbol="EURUSD", timeframe="M1")
    assert latest is not None

    stats = cache.stats()
    assert stats.history_hits == 1
    assert stats.latest_hits == 1


def test_cache_expiration_invalidation_and_lru() -> None:
    cache = DataSourceCache(expiration_seconds=0.01, max_entries=1)
    req_a = HistoryRequest(symbol="EURUSD", timeframe="M1", limit=1, page=1, page_size=1)
    req_b = HistoryRequest(symbol="GBPUSD", timeframe="M1", limit=1, page=1, page_size=1)

    cache.set_history(req_a, _response())
    cache.set_history(req_b, _response())

    assert cache.get_history(req_a) is None
    assert cache.get_history(req_b) is not None

    sleep(0.02)
    assert cache.prune_expired() >= 1

    cache.set_latest(symbol="EURUSD", timeframe="M1", candle=_candle())
    cache.invalidate(symbol="EURUSD", timeframe="M1")
    assert cache.get_latest(symbol="EURUSD", timeframe="M1") is None

    cache.set_history(req_b, _response())
    cache.invalidate()
    assert cache.get_history(req_b) is None


def test_cache_validates_constructor() -> None:
    with pytest.raises(ValueError):
        DataSourceCache(expiration_seconds=0.0, max_entries=1)

    with pytest.raises(ValueError):
        DataSourceCache(expiration_seconds=1.0, max_entries=0)
