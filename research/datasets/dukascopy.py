"""Dukascopy ``.bi5`` decoding (verified format, fail-closed).

Tick hour file ``{HH}h_ticks.bi5``: LZMA "alone" stream of 20-byte big-endian
records ``uint32 ms_offset, uint32 ask, uint32 bid, float32 ask_vol,
float32 bid_vol``. Offsets are milliseconds from the UTC hour start.

H1 candle month file ``{SIDE}_candles_hour_1.bi5``: 24-byte big-endian records
``uint32 sec_offset, uint32 open, uint32 close, uint32 low, uint32 high,
float32 volume``. Offsets are seconds from the UTC month start.

Prices are integer points; the scale is instrument-specific (see
``DUKASCOPY_INSTRUMENTS``). Volumes are quoted liquidity, never trade volume.
"""

from __future__ import annotations

import lzma
import struct
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal

from research.datasets.contracts import (
    MS_PER_HOUR,
    DatasetIntegrityError,
    HourStatus,
    InstrumentSpec,
    PriceSide,
    Provider,
    Tick,
    finite_non_negative,
    require,
)

TICK_RECORD = struct.Struct(">IIIff")
CANDLE_RECORD = struct.Struct(">IIIIIf")
DATAFEED_BASE_URL = "https://datafeed.dukascopy.com/datafeed"

# Explicit per-instrument scales. XAUUSD is NOT scaled like EURUSD.
DUKASCOPY_INSTRUMENTS: dict[str, InstrumentSpec] = {
    "EURUSD": InstrumentSpec("EURUSD", Provider.DUKASCOPY, "EURUSD", 5),
    "XAUUSD": InstrumentSpec("XAUUSD", Provider.DUKASCOPY, "XAUUSD", 3),
}


def instrument(symbol: str) -> InstrumentSpec:
    spec = DUKASCOPY_INSTRUMENTS.get(symbol)
    if spec is None:
        raise DatasetIntegrityError(f"instrument {symbol!r} has no configured Dukascopy scale")
    return spec


def volume_micro(value: float, name: str) -> int:
    """Quoted volume (provider unit) as an integer number of millionths."""
    finite_non_negative(value, name)
    return int((Decimal(value) * 1_000_000).to_integral_value(rounding=ROUND_HALF_EVEN))


def _decompress(payload: bytes, what: str) -> bytes:
    require(type(payload) is bytes, f"{what}: payload must be bytes")
    try:
        return lzma.decompress(payload, format=lzma.FORMAT_ALONE)
    except lzma.LZMAError as exc:
        raise DatasetIntegrityError(f"{what}: invalid LZMA payload ({exc})") from exc


def hour_start_ms(year: int, month: int, day: int, hour: int) -> int:
    return int(datetime(year, month, day, hour, tzinfo=UTC).timestamp() * 1000)


def decode_ticks(payload: bytes, hour_start: int) -> tuple[Tick, ...]:
    """Decode one non-empty tick hour file. Fails closed on any anomaly."""
    require(type(hour_start) is int and hour_start % MS_PER_HOUR == 0, "hour start not aligned")
    require(len(payload) > 0, "empty payload must be classified, not decoded")
    raw = _decompress(payload, "ticks")
    require(len(raw) > 0, "ticks: decompressed payload is empty")
    require(len(raw) % TICK_RECORD.size == 0, "ticks: record length is not a multiple of 20")
    ticks: list[Tick] = []
    previous = -1
    seen_last: tuple[int, int, int, float, float] | None = None
    for index, record in enumerate(TICK_RECORD.iter_unpack(raw)):
        offset, ask, bid, ask_vol, bid_vol = record
        where = f"record {index}"
        require(offset < MS_PER_HOUR, f"ticks: {where} offset outside its UTC hour")
        require(offset >= previous, f"ticks: {where} out of chronological order")
        require(record != seen_last, f"ticks: {where} duplicates the previous record")
        require(ask > 0 and bid > 0, f"ticks: {where} non-positive price")
        require(ask >= bid, f"ticks: {where} ask below bid")
        ticks.append(
            Tick(
                hour_start + offset,
                bid,
                ask,
                volume_micro(bid_vol, f"{where} bid volume"),
                volume_micro(ask_vol, f"{where} ask volume"),
            )
        )
        previous = offset
        seen_last = record
    return tuple(ticks)


@dataclass(frozen=True, slots=True)
class ProviderCandle:
    """One Dukascopy H1 candle as published (no alteration)."""

    start_ms: int
    side: PriceSide
    open_points: int
    high_points: int
    low_points: int
    close_points: int
    volume_micro: int


def month_start_ms(year: int, month: int) -> int:
    return int(datetime(year, month, 1, tzinfo=UTC).timestamp() * 1000)


def decode_candles(
    payload: bytes, year: int, month: int, side: PriceSide
) -> tuple[ProviderCandle, ...]:
    require(type(side) is PriceSide, "candles: side invalid")
    require(len(payload) > 0, "empty payload must be classified, not decoded")
    raw = _decompress(payload, "candles")
    require(len(raw) % CANDLE_RECORD.size == 0, "candles: record length is not a multiple of 24")
    start = month_start_ms(year, month)
    end = month_start_ms(year + (month == 12), month % 12 + 1)
    candles: list[ProviderCandle] = []
    previous = -1
    for index, (offset, o, c, lo, hi, vol) in enumerate(CANDLE_RECORD.iter_unpack(raw)):
        where = f"candle {index}"
        require(offset % 3600 == 0, f"candles: {where} not on an hour boundary")
        require(offset > previous, f"candles: {where} out of order or duplicated")
        t = start + offset * 1000
        require(t < end, f"candles: {where} outside its month")
        require(min(o, c, lo, hi) > 0, f"candles: {where} non-positive price")
        require(lo <= min(o, c) and hi >= max(o, c), f"candles: {where} OHLC invalid")
        candles.append(ProviderCandle(t, side, o, hi, lo, c, volume_micro(vol, where)))
        previous = offset
    return tuple(candles)


def tick_url(spec: InstrumentSpec, hour_start: int) -> str:
    d = datetime.fromtimestamp(hour_start / 1000, tz=UTC)
    return (
        f"{DATAFEED_BASE_URL}/{spec.provider_symbol}/{d.year:04d}/{d.month - 1:02d}/"
        f"{d.day:02d}/{d.hour:02d}h_ticks.bi5"
    )


def candle_url(spec: InstrumentSpec, year: int, month: int, side: PriceSide) -> str:
    return (
        f"{DATAFEED_BASE_URL}/{spec.provider_symbol}/{year:04d}/{month - 1:02d}/"
        f"{side.value}_candles_hour_1.bi5"
    )


def tick_relative_path(spec: InstrumentSpec, hour_start: int) -> str:
    d = datetime.fromtimestamp(hour_start / 1000, tz=UTC)
    return (
        f"raw/dukascopy/{spec.symbol}/ticks/{d.year:04d}/{d.month:02d}/{d.day:02d}/"
        f"{d.hour:02d}h_ticks.bi5"
    )


def candle_relative_path(spec: InstrumentSpec, year: int, month: int, side: PriceSide) -> str:
    return f"raw/dukascopy/{spec.symbol}/candles_h1/{side.value}/{year:04d}-{month:02d}.bi5"


SESSION_CALENDAR_VERSION = "saturday-only/1"


def classify_empty_hour(hour_start: int) -> HourStatus:
    """Classify an HTTP 200 zero-byte hour.

    Calendar ``saturday-only/1``: only hours inside Saturday UTC are treated as
    an expected closure. Every other empty hour is EMPTY_UNEXPLAINED; an empty
    response never proves a closure by itself.
    """
    d = datetime.fromtimestamp(hour_start / 1000, tz=UTC)
    return HourStatus.EXPECTED_CLOSURE if d.weekday() == 5 else HourStatus.EMPTY_UNEXPLAINED
