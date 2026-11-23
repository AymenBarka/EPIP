"""Deterministic offline fixtures for D00 tests (no network, no real market data)."""

from __future__ import annotations

import lzma
import struct
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from research.datasets.acquisition import BudgetExceeded, HttpResponse, TransportFailure
from research.datasets.contracts import MS_PER_HOUR, PriceSide
from research.datasets.dukascopy import CANDLE_RECORD, TICK_RECORD, month_start_ms

BASE_POINTS = {"EURUSD": 130_000, "XAUUSD": 1_700_000}


def encode(raw: bytes) -> bytes:
    return lzma.compress(raw, format=lzma.FORMAT_ALONE)


def tick_records(symbol: str, hour_start: int) -> list[tuple[int, int, int, float, float]]:
    """Synthetic but deterministic quotes for one hour: (offset, ask, bid, askv, bidv)."""
    hour_index = hour_start // MS_PER_HOUR
    count = 5 + hour_index % 7
    base = BASE_POINTS[symbol] + (hour_index % 50) * 3
    records = []
    for i in range(count):
        bid = base + ((i * 7 + hour_index) % 11) - 5
        spread = 2 + i % 3
        records.append((i * 600_000 // count + 17, bid + spread, bid, 1.5 + i / 4, 0.75 + i / 8))
    return records


def tick_payload(records: list[tuple[int, int, int, float, float]]) -> bytes:
    return encode(b"".join(TICK_RECORD.pack(*r) for r in records))


def candle_payload(rows: list[tuple[int, int, int, int, int, float]]) -> bytes:
    return encode(b"".join(CANDLE_RECORD.pack(*r) for r in rows))


def month_candles(
    symbol: str,
    year: int,
    month: int,
    side: PriceSide,
    populated: Callable[[int], bool],
) -> bytes:
    """Provider-style month file consistent with ``tick_records`` for populated hours."""
    start = month_start_ms(year, month)
    end = month_start_ms(year + (month == 12), month % 12 + 1)
    rows = []
    last = BASE_POINTS[symbol]
    for hour in range(start, end, MS_PER_HOUR):
        offset = (hour - start) // 1000
        if populated(hour):
            prices = [r[2] if side is PriceSide.BID else r[1] for r in tick_records(symbol, hour)]
            rows.append((offset, prices[0], prices[-1], min(prices), max(prices), 12.5))
            last = prices[-1]
        else:
            rows.append((offset, last, last, last, last, 0.0))
    return candle_payload(rows)


def hour_ms(year: int, month: int, day: int, hour: int) -> int:
    return int(datetime(year, month, day, hour, tzinfo=UTC).timestamp() * 1000)


@dataclass
class FakeClock:
    now: float = 1000.0
    sleeps: list[float] = field(default_factory=list)

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    def utc_now_text(self) -> str:
        return "2026-11-22T00:00:00Z"


Responder = Callable[[str, int], HttpResponse]


@dataclass
class FakeTransport:
    """Serves scripted responses; honours the byte-budget contract like the real one."""

    responder: Responder
    calls: list[tuple[str, int]] = field(default_factory=list)
    clock: FakeClock | None = None
    call_times: list[float] = field(default_factory=list)

    def get(self, url: str, timeout_s: float, max_bytes: int) -> HttpResponse:
        assert timeout_s > 0
        self.calls.append((url, max_bytes))
        if self.clock is not None:
            self.call_times.append(self.clock.now)
        response = self.responder(url, max_bytes)
        if len(response.body) > max_bytes:
            raise BudgetExceeded("fake: body larger than remaining budget")
        return response


def ok(body: bytes) -> HttpResponse:
    return HttpResponse(200, body, len(body))


def status(code: int) -> HttpResponse:
    return HttpResponse(code, b"", 0)


def failing(_url: str, _max: int) -> HttpResponse:
    raise TransportFailure("fake timeout")


def url_hour(url: str) -> int:
    """Inverse of ``tick_url`` for fixtures (month in URL is zero-based)."""
    parts = url.rsplit("/", 4)
    year, month0, day, hour = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4][:2])
    return hour_ms(year, month0 + 1, day, hour)


def pack_tick(offset: int, ask: int, bid: int, askv: float, bidv: float) -> bytes:
    return struct.pack(">IIIff", offset, ask, bid, askv, bidv)
