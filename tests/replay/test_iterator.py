from __future__ import annotations

from epip.core.candle import Candle
from epip.marketdata.datasource_models import HistoryRequest
from epip.marketdata.providers.fake_provider import FakeProvider
from epip.replay.replay_iterator import ReplayIterator


def test_iterator_is_lazy_and_resettable() -> None:
    provider = FakeProvider(symbols=("EURUSD",), timeframes=("M1",), candles_per_series=7)
    provider.connect()

    iterator: ReplayIterator[Candle] = ReplayIterator(
        market_data=provider,
        request=HistoryRequest(symbol="EURUSD", timeframe="M1", limit=3, page=1, page_size=3),
    )

    first_peek = iterator.peek()
    assert first_peek is not None
    first = iterator.next()
    assert first is not None
    assert iterator.current() == first
    assert iterator.previous() is None

    second = iterator.next()
    assert second is not None
    assert iterator.previous() == first
    assert iterator.peek() is not None

    consumed = [first, second]
    while True:
        candle = iterator.next()
        if candle is None:
            break
        consumed.append(candle)

    assert len(consumed) == 7
    assert iterator.finished() is True

    iterator.reset()
    assert iterator.finished() is False
    restarted = iterator.next()
    assert restarted is not None
    assert restarted.timestamp == first.timestamp

    provider.disconnect()
