from __future__ import annotations

from epip.marketdata.providers.fake_provider import FakeProvider
from epip.replay.replay_config import ReplayConfig
from epip.replay.replay_scheduler import ReplayScheduler


def test_scheduler_orders_multiple_streams_chronologically() -> None:
    provider = FakeProvider(
        symbols=("EURUSD", "GBPUSD"),
        timeframes=("M1",),
        candles_per_series=4,
    )
    provider.connect()

    scheduler = ReplayScheduler(
        market_data=provider,
        config=ReplayConfig(symbols=("EURUSD", "GBPUSD"), timeframes=("M1",), page_size=2),
    )

    timestamps: list[str] = []
    symbols: list[str] = []
    while True:
        item = scheduler.next()
        if item is None:
            break
        timestamps.append(item.candle.timestamp)
        symbols.append(item.symbol)

    assert timestamps == sorted(timestamps)
    assert set(symbols) == {"EURUSD", "GBPUSD"}
    assert scheduler.finished() is True

    scheduler.reset()
    assert scheduler.finished() is False
    provider.disconnect()
