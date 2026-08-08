from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import cast

import pytest

from epip.core import DeterministicClock, DeterministicIdGenerator, Price
from epip.marketdata.datasource import DataSource
from epip.marketdata.datasource_models import ConnectionState, HistoryRequest
from epip.marketdata.exceptions import ConnectionError, ProviderError
from epip.marketdata.providers.fake_provider import FakeProvider
from epip.marketdata.providers.mt5_provider import MT5Provider
from epip.marketdata.providers.twelvedata_provider import TwelveDataProvider


def test_fake_provider_and_datasource_facade() -> None:
    provider = FakeProvider(symbols=("EURUSD",), timeframes=("M1",), candles_per_series=50)
    facade = DataSource(provider)

    facade.connect()
    assert facade.available_symbols() == ("EURUSD",)

    response = facade.history(
        HistoryRequest(symbol="EURUSD", timeframe="M1", limit=20, page_size=20)
    )
    assert response.chunk.metadata.returned_count == 20

    cached = facade.history(HistoryRequest(symbol="EURUSD", timeframe="M1", limit=20, page_size=20))
    assert cached.chunk.metadata.from_cache is True

    latest = facade.latest("EURUSD", "M1")
    assert latest is not None

    stats = provider.cache_stats()
    assert stats.history_hits >= 1

    facade.disconnect()
    health = facade.health()
    assert health.connection == ConnectionState.DISCONNECTED


def test_fake_provider_thread_safety() -> None:
    provider = FakeProvider(symbols=("EURUSD",), timeframes=("M1",), candles_per_series=300)
    provider.connect()

    def run_once(_: int) -> int:
        response = provider.history(
            HistoryRequest(symbol="EURUSD", timeframe="M1", limit=100, page_size=100)
        )
        return response.chunk.metadata.returned_count

    with ThreadPoolExecutor(max_workers=8) as pool:
        values = list(pool.map(run_once, range(24)))

    assert all(value == 100 for value in values)

    provider.disconnect()
    with pytest.raises(ConnectionError):
        provider.latest("EURUSD", "M1")


def test_interface_only_providers_raise() -> None:
    tw = TwelveDataProvider()
    mt5 = MT5Provider()
    tw.connect()
    mt5.connect()

    with pytest.raises(ProviderError):
        tw.history(HistoryRequest(symbol="EURUSD", timeframe="M1"))
    with pytest.raises(ProviderError):
        mt5.history(HistoryRequest(symbol="EURUSD", timeframe="M1"))

    with pytest.raises(ProviderError):
        tw.latest("EURUSD", "M1")
    with pytest.raises(ProviderError):
        mt5.latest("EURUSD", "M1")

    with pytest.raises(ProviderError):
        list(tw.stream("EURUSD", "M1"))
    with pytest.raises(ProviderError):
        list(mt5.stream("EURUSD", "M1"))

    tw.disconnect()
    mt5.disconnect()


def test_fake_provider_propagates_deterministic_identity_to_candles_and_prices() -> None:
    def identities() -> tuple[str, ...]:
        provider = FakeProvider(
            candles_per_series=2,
            clock=DeterministicClock(),
            id_generator=DeterministicIdGenerator("market-data"),
        )
        provider.connect()
        candle = provider.latest("EURUSD", "M1")
        assert candle is not None
        prices = tuple(
            cast(Price, item) for item in (candle.open, candle.high, candle.low, candle.close)
        )
        return (
            candle.uuid,
            *(item.uuid for item in prices),
        )

    assert identities() == identities()
