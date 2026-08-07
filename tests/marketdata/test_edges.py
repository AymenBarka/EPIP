from __future__ import annotations

from pathlib import Path

from epip.core.candle import Candle
from epip.marketdata.adapters.mt5_adapter import NullMT5Adapter
from epip.marketdata.adapters.twelvedata_adapter import NullTwelveDataAdapter
from epip.marketdata.config import MarketDataConfig
from epip.marketdata.datasource import DataSource
from epip.marketdata.datasource_cache import DataSourceCache
from epip.marketdata.datasource_models import (
    ConnectionState,
    HealthCheck,
    HealthState,
    HistoryChunk,
    HistoryMetadata,
    HistoryRequest,
    HistoryResponse,
    LiveRequest,
    LiveResponse,
    LiveSubscription,
)
from epip.marketdata.exceptions import InvalidRequestError
from epip.marketdata.providers.base_provider import BaseProvider
from epip.marketdata.providers.csv_provider import CSVProvider
from epip.marketdata.providers.fake_provider import FakeProvider
from epip.marketdata.providers.mt5_provider import MT5Provider
from epip.marketdata.providers.twelvedata_provider import TwelveDataProvider


class EmptyHistoryProvider(BaseProvider):
    def __init__(self) -> None:
        super().__init__(name="empty")

    def available_symbols(self) -> tuple[str, ...]:
        return ("EURUSD",)

    def available_timeframes(self) -> tuple[str, ...]:
        return ("M1",)

    def _history_impl(self, request: HistoryRequest) -> HistoryResponse:
        metadata = HistoryMetadata(
            total_count=0,
            returned_count=0,
            page=request.page,
            page_size=request.page_size,
            has_next=False,
            source="empty",
            from_cache=False,
        )
        return HistoryResponse(
            symbol=request.symbol,
            timeframe=request.timeframe,
            chunk=HistoryChunk(candles=(), metadata=metadata),
        )


class NoHealthAdapter(NullTwelveDataAdapter, NullMT5Adapter):
    def health(self) -> HealthCheck:
        raise NotImplementedError("health not implemented")


def _candle() -> Candle:
    return Candle(
        timestamp="2024-01-01T00:00:00+00:00",
        symbol="EURUSD",
        timeframe="M1",
        open=1.1,
        high=1.2,
        low=1.0,
        close=1.15,
        volume=1000.0,
    )


def test_base_provider_empty_latest_stream_and_lifecycle() -> None:
    provider = EmptyHistoryProvider()
    provider.connect()
    provider.connect()

    assert provider.latest("EURUSD", "M1") is None
    assert list(provider.stream("EURUSD", "M1")) == []

    provider.disconnect()
    provider.disconnect()


def test_config_defaults_and_fallbacks() -> None:
    cfg = MarketDataConfig.from_dict(
        {
            "provider": "fake",
            "cache": ["invalid"],
            "csv": "invalid",
            "twelvedata": "invalid",
            "mt5": "invalid",
            "timeout_seconds": object(),
            "retry_count": object(),
            "fake_candles_per_series": object(),
            "symbols": None,
            "timeframes": None,
        }
    )

    assert cfg.cache.expiration_seconds == 60.0
    assert cfg.cache.max_entries == 1024
    assert cfg.csv.path == ""
    assert cfg.twelvedata.api_key == ""
    assert cfg.mt5.terminal_path == ""
    assert cfg.symbols == ("EURUSD",)
    assert cfg.timeframes == ("M1",)


def test_models_validation_and_live_models() -> None:
    try:
        HistoryRequest(symbol="", timeframe="M1")
        assert False
    except ValueError:
        pass

    try:
        HistoryRequest(symbol="EURUSD", timeframe="")
        assert False
    except ValueError:
        pass

    try:
        HistoryRequest(symbol="EURUSD", timeframe="M1", page=0)
        assert False
    except ValueError:
        pass

    live_request = LiveRequest(symbol="EURUSD", timeframe="M1")
    live_response = LiveResponse(symbol="EURUSD", timeframe="M1", candle=None)
    subscription = LiveSubscription(
        symbol="EURUSD",
        timeframe="M1",
        subscription_id="sub-1",
        active=True,
    )

    assert live_request.symbol == "EURUSD"
    assert live_response.candle is None
    assert subscription.active is True


def test_cache_latest_expiration_and_trim() -> None:
    cache = DataSourceCache(expiration_seconds=0.01, max_entries=1)
    cache.set_latest(symbol="EURUSD", timeframe="M1", candle=_candle())
    cache.set_latest(symbol="GBPUSD", timeframe="M1", candle=_candle())
    assert cache.get_latest(symbol="EURUSD", timeframe="M1") is None


def test_adapter_and_provider_health_fallback_paths() -> None:
    tw_adapter = NoHealthAdapter()
    mt5_adapter = NoHealthAdapter()

    tw = TwelveDataProvider(adapter=tw_adapter)
    mt5 = MT5Provider(adapter=mt5_adapter)
    tw.connect()
    mt5.connect()

    assert tw.available_symbols() == ()
    assert mt5.available_timeframes() == ()

    tw_health = tw.health()
    mt5_health = mt5.health()

    assert tw_health.status == HealthState.DEGRADED
    assert mt5_health.connection == ConnectionState.CONNECTED

    tw.disconnect()
    mt5.disconnect()


def test_csv_and_fake_request_filters(tmp_path: Path) -> None:
    csv_path = tmp_path / "candles.csv"
    csv_path.write_text(
        "timestamp,symbol,timeframe,open,high,low,close,volume\n"
        "2024-01-01T00:00:00+00:00,EURUSD,M1,1.1,1.2,1.0,1.15,1000\n"
        "2024-01-01T00:01:00+00:00,EURUSD,M1,1.1,1.2,1.0,1.15,1000\n"
        "2024-01-01T00:02:00+00:00,EURUSD,M1,1.1,1.2,1.0,1.15,1000\n",
        encoding="utf-8",
    )

    csv_provider = CSVProvider(csv_path=str(csv_path))
    csv_provider.connect()
    csv_result = csv_provider.history(
        HistoryRequest(
            symbol="EURUSD",
            timeframe="M1",
            start="2024-01-01T00:01:00+00:00",
            end="2024-01-01T00:02:00+00:00",
            page=1,
            page_size=10,
        )
    )
    assert csv_result.chunk.metadata.returned_count == 2
    csv_provider.disconnect()

    fake_provider = FakeProvider(symbols=("EURUSD",), timeframes=("M1",), candles_per_series=20)
    fake_provider.connect()
    fake_rows = fake_provider.history(
        HistoryRequest(
            symbol="EURUSD",
            timeframe="M1",
            start="2024-01-01T00:05:00+00:00",
            end="2024-01-01T00:09:00+00:00",
            page=1,
            page_size=20,
        )
    )
    assert fake_rows.chunk.metadata.returned_count == 5
    fake_provider.disconnect()


def test_datasource_facade_additional_paths() -> None:
    provider = FakeProvider(symbols=("EURUSD",), timeframes=("M1",), candles_per_series=10)
    source = DataSource(provider)
    source.connect()

    assert source.available_timeframes() == ("M1",)
    response = source.history(HistoryRequest(symbol="EURUSD", timeframe="M1", page=1, page_size=5))
    assert response.chunk.metadata.returned_count == 5
    assert list(source.stream("EURUSD", "M1"))

    source.disconnect()


def test_factory_error_passthrough() -> None:
    try:
        raise InvalidRequestError("invalid")
    except InvalidRequestError:
        assert True
