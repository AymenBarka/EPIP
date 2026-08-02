"""Configuration models for Market Data Layer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CacheConfig:
    expiration_seconds: float = 60.0
    max_entries: int = 1024


@dataclass(frozen=True, slots=True)
class CSVConfig:
    path: str = ""
    default_symbol: str | None = None
    default_timeframe: str | None = None


@dataclass(frozen=True, slots=True)
class TwelveDataConfig:
    api_key: str = ""


@dataclass(frozen=True, slots=True)
class MT5Config:
    terminal_path: str = ""


@dataclass(frozen=True, slots=True)
class MarketDataConfig:
    provider: str = "fake"
    timeout_seconds: float = 10.0
    retry_count: int = 1
    cache: CacheConfig = field(default_factory=CacheConfig)
    csv: CSVConfig = field(default_factory=CSVConfig)
    twelvedata: TwelveDataConfig = field(default_factory=TwelveDataConfig)
    mt5: MT5Config = field(default_factory=MT5Config)
    symbols: tuple[str, ...] = ("EURUSD",)
    timeframes: tuple[str, ...] = ("M1",)
    fake_candles_per_series: int = 2_000

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> MarketDataConfig:
        cache_payload = payload.get("cache", {})
        csv_payload = payload.get("csv", {})
        twelvedata_payload = payload.get("twelvedata", {})
        mt5_payload = payload.get("mt5", {})

        cache = CacheConfig(
            expiration_seconds=_to_float(
                _safe_dict(cache_payload).get("expiration_seconds"),
                default=60.0,
            ),
            max_entries=_to_int(_safe_dict(cache_payload).get("max_entries"), default=1024),
        )
        csv = CSVConfig(
            path=str(_safe_dict(csv_payload).get("path", "")),
            default_symbol=_optional_str(_safe_dict(csv_payload).get("default_symbol")),
            default_timeframe=_optional_str(_safe_dict(csv_payload).get("default_timeframe")),
        )
        twelvedata = TwelveDataConfig(
            api_key=str(_safe_dict(twelvedata_payload).get("api_key", ""))
        )
        mt5 = MT5Config(terminal_path=str(_safe_dict(mt5_payload).get("terminal_path", "")))

        symbols = _to_tuple(payload.get("symbols"), fallback=("EURUSD",))
        timeframes = _to_tuple(payload.get("timeframes"), fallback=("M1",))

        return cls(
            provider=str(payload.get("provider", "fake")),
            timeout_seconds=_to_float(payload.get("timeout_seconds"), default=10.0),
            retry_count=_to_int(payload.get("retry_count"), default=1),
            cache=cache,
            csv=csv,
            twelvedata=twelvedata,
            mt5=mt5,
            symbols=symbols,
            timeframes=timeframes,
            fake_candles_per_series=_to_int(payload.get("fake_candles_per_series"), default=2_000),
        )


def _safe_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def _to_tuple(value: object, *, fallback: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return fallback
    if isinstance(value, str):
        cleaned = value.strip()
        return (cleaned,) if cleaned else fallback
    if isinstance(value, (list, tuple, set)):
        normalized = tuple(str(item).strip() for item in value if str(item).strip())
        return normalized or fallback
    return fallback


def _to_float(value: object, *, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value)
    return default


def _to_int(value: object, *, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    return default
