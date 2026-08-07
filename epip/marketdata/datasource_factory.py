"""Factory for constructing market data providers from config."""

from __future__ import annotations

from collections.abc import Callable

from epip.marketdata.config import MarketDataConfig
from epip.marketdata.datasource_protocol import DataSourceProtocol
from epip.marketdata.exceptions import InvalidRequestError
from epip.marketdata.providers.csv_provider import CSVProvider
from epip.marketdata.providers.fake_provider import FakeProvider
from epip.marketdata.providers.mt5_provider import MT5Provider
from epip.marketdata.providers.twelvedata_provider import TwelveDataProvider


class DataSourceFactory:
    """Builds providers based on normalized MarketDataConfig."""

    @classmethod
    def build(cls, config: MarketDataConfig) -> DataSourceProtocol:
        provider_name = config.provider.strip().lower()
        builders: dict[str, Callable[[MarketDataConfig], DataSourceProtocol]] = {
            "csv": cls._build_csv,
            "fake": cls._build_fake,
            "twelvedata": cls._build_twelvedata,
            "mt5": cls._build_mt5,
        }
        builder = builders.get(provider_name)
        if builder is None:
            allowed = ", ".join(sorted(builders))
            raise InvalidRequestError(
                f"unknown provider '{provider_name}', expected one of: {allowed}"
            )
        return builder(config)

    @staticmethod
    def _build_csv(config: MarketDataConfig) -> DataSourceProtocol:
        if not config.csv.path:
            raise InvalidRequestError("csv.path is required when provider=csv")
        return CSVProvider(
            csv_path=config.csv.path,
            default_symbol=config.csv.default_symbol,
            default_timeframe=config.csv.default_timeframe,
            cache_expiration_seconds=config.cache.expiration_seconds,
            cache_max_entries=config.cache.max_entries,
        )

    @staticmethod
    def _build_fake(config: MarketDataConfig) -> DataSourceProtocol:
        return FakeProvider(
            symbols=config.symbols,
            timeframes=config.timeframes,
            candles_per_series=config.fake_candles_per_series,
            cache_expiration_seconds=config.cache.expiration_seconds,
            cache_max_entries=config.cache.max_entries,
        )

    @staticmethod
    def _build_twelvedata(config: MarketDataConfig) -> DataSourceProtocol:
        return TwelveDataProvider()

    @staticmethod
    def _build_mt5(config: MarketDataConfig) -> DataSourceProtocol:
        return MT5Provider()
