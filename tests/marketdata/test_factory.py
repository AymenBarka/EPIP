from __future__ import annotations

import csv
from pathlib import Path

import pytest

from epip.marketdata.config import MarketDataConfig
from epip.marketdata.datasource_factory import DataSourceFactory
from epip.marketdata.exceptions import InvalidRequestError
from epip.marketdata.providers.csv_provider import CSVProvider
from epip.marketdata.providers.fake_provider import FakeProvider
from epip.marketdata.providers.mt5_provider import MT5Provider
from epip.marketdata.providers.twelvedata_provider import TwelveDataProvider


def _csv_file(tmp_path: Path) -> Path:
    path = tmp_path / "candles.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp",
                "symbol",
                "timeframe",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "timestamp": "2024-01-01T00:00:00+00:00",
                "symbol": "EURUSD",
                "timeframe": "M1",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
                "volume": 1000.0,
            }
        )
    return path


def test_factory_builds_providers(tmp_path: Path) -> None:
    csv_path = _csv_file(tmp_path)

    csv_cfg = MarketDataConfig.from_dict({"provider": "csv", "csv": {"path": str(csv_path)}})
    fake_cfg = MarketDataConfig.from_dict({"provider": "fake"})
    tw_cfg = MarketDataConfig.from_dict({"provider": "twelvedata"})
    mt5_cfg = MarketDataConfig.from_dict({"provider": "mt5"})

    assert isinstance(DataSourceFactory.build(csv_cfg), CSVProvider)
    assert isinstance(DataSourceFactory.build(fake_cfg), FakeProvider)
    assert isinstance(DataSourceFactory.build(tw_cfg), TwelveDataProvider)
    assert isinstance(DataSourceFactory.build(mt5_cfg), MT5Provider)


def test_factory_validates_provider_and_csv_path() -> None:
    with pytest.raises(InvalidRequestError):
        DataSourceFactory.build(MarketDataConfig.from_dict({"provider": "unknown"}))

    with pytest.raises(InvalidRequestError):
        DataSourceFactory.build(
            MarketDataConfig.from_dict({"provider": "csv", "csv": {"path": ""}})
        )


def test_config_from_dict_normalizes_fields() -> None:
    cfg = MarketDataConfig.from_dict(
        {
            "provider": "fake",
            "symbols": "EURUSD",
            "timeframes": ["M1", "M5"],
            "cache": {"expiration_seconds": 30, "max_entries": 256},
            "timeout_seconds": 5,
            "retry_count": 3,
            "fake_candles_per_series": 128,
        }
    )

    assert cfg.symbols == ("EURUSD",)
    assert cfg.timeframes == ("M1", "M5")
    assert cfg.cache.expiration_seconds == 30.0
    assert cfg.cache.max_entries == 256
    assert cfg.timeout_seconds == 5.0
    assert cfg.retry_count == 3
    assert cfg.fake_candles_per_series == 128
