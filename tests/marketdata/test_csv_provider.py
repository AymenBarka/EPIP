from __future__ import annotations

import csv
from pathlib import Path

import pytest

from epip.marketdata.datasource_models import ConnectionState, HealthState, HistoryRequest
from epip.marketdata.exceptions import ConnectionError, ProviderError
from epip.marketdata.providers.csv_provider import CSVProvider


def _write_csv(path: Path) -> None:
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
        for index in range(12):
            writer.writerow(
                {
                    "timestamp": f"2024-01-01T00:{index:02d}:00+00:00",
                    "symbol": "EURUSD",
                    "timeframe": "M1",
                    "open": 1.1 + (index * 0.0001),
                    "high": 1.2 + (index * 0.0001),
                    "low": 1.0 + (index * 0.0001),
                    "close": 1.15 + (index * 0.0001),
                    "volume": 1000 + index,
                }
            )


def test_csv_provider_full_flow(tmp_path: Path) -> None:
    path = tmp_path / "candles.csv"
    _write_csv(path)

    provider = CSVProvider(csv_path=str(path))
    degraded = provider.health()
    assert degraded.connection == ConnectionState.DISCONNECTED

    provider.connect()
    health = provider.health()
    assert health.status == HealthState.HEALTHY
    assert provider.available_symbols() == ("EURUSD",)
    assert provider.available_timeframes() == ("M1",)

    response = provider.history(
        HistoryRequest(symbol="EURUSD", timeframe="M1", page=1, page_size=5)
    )
    assert response.chunk.metadata.returned_count == 5
    assert response.chunk.metadata.has_next is True

    page2 = provider.history(HistoryRequest(symbol="EURUSD", timeframe="M1", page=2, page_size=5))
    assert page2.chunk.metadata.returned_count == 5

    latest = provider.latest("EURUSD", "M1")
    assert latest is not None

    streamed = list(provider.stream("EURUSD", "M1"))
    assert len(streamed) == 12

    provider.disconnect()

    with pytest.raises(ConnectionError):
        provider.history(HistoryRequest(symbol="EURUSD", timeframe="M1"))


def test_csv_provider_errors(tmp_path: Path) -> None:
    missing = CSVProvider(csv_path=str(tmp_path / "missing.csv"))
    with pytest.raises(ProviderError):
        missing.connect()

    invalid = tmp_path / "invalid.csv"
    with invalid.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open"])
        writer.writeheader()
        writer.writerow({"timestamp": "2024-01-01T00:00:00+00:00", "open": 1.1})

    provider = CSVProvider(csv_path=str(invalid))
    with pytest.raises(ProviderError):
        provider.connect()
