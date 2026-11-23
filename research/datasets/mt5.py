"""Research-only import of local MetaTrader 5 exports (no terminal, no broker).

Supported inputs (Symbols window export):

- bars: ``<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>``;
- ticks: ``<DATE> <TIME> <BID> <ASK> <LAST> <VOLUME> <FLAGS>``.

MT5 timestamps are broker server time. They are converted to UTC only through
an explicit ``ServerTimeConvention``; without one, the import is rejected
(quarantined). Ambiguous or non-existent local times at offset changes are
rejected. A missing BID or ASK stays missing; ASK is never reconstructed from
BID and spread. Bar price side must be declared by the caller.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from research.datasets.canonical import format_points, format_timestamp, parse_points
from research.datasets.contracts import (
    DatasetIntegrityError,
    InstrumentSpec,
    PriceSide,
    Provider,
    require,
    require_text,
)

BARS_HEADER = ("DATE", "TIME", "OPEN", "HIGH", "LOW", "CLOSE", "TICKVOL", "VOL", "SPREAD")
TICKS_HEADER = ("DATE", "TIME", "BID", "ASK", "LAST", "VOLUME", "FLAGS")
MT5_NORMALIZATION_VERSION = "epip-research-mt5-csv/1"


class TimezoneUnresolvedError(DatasetIntegrityError):
    """Server-time interpretation could not be established: quarantine."""


@dataclass(frozen=True, slots=True)
class OffsetSegment:
    """From the UTC instant ``effective_from_utc`` onward (until the next
    segment), server time equals UTC plus ``offset_minutes``."""

    effective_from_utc: datetime
    offset_minutes: int

    def __post_init__(self) -> None:
        require(type(self.effective_from_utc) is datetime, "effective_from_utc must be datetime")
        require(self.effective_from_utc.tzinfo is UTC, "effective_from_utc must be UTC-aware")
        require(type(self.offset_minutes) is int, "offset_minutes must be int")
        require(-14 * 60 <= self.offset_minutes <= 14 * 60, "offset_minutes out of range")


@dataclass(frozen=True, slots=True)
class ServerTimeConvention:
    broker: str
    source: str
    segments: tuple[OffsetSegment, ...]

    def __post_init__(self) -> None:
        require_text(self.broker, "broker")
        require_text(self.source, "convention source")
        require(len(self.segments) > 0, "at least one offset segment is required")
        starts = [s.effective_from_utc for s in self.segments]
        require(starts == sorted(starts) and len(set(starts)) == len(starts), "segments unsorted")

    def to_utc_ms(self, server_time: datetime) -> int:
        """Exactly one segment must map ``server_time`` into its own UTC range."""
        require(server_time.tzinfo is None, "server time must be naive")
        local_ms = int(server_time.replace(tzinfo=UTC).timestamp() * 1000)
        bounds = [int(s.effective_from_utc.timestamp() * 1000) for s in self.segments]
        candidates: list[int] = []
        for i, seg in enumerate(self.segments):
            utc_ms = local_ms - seg.offset_minutes * 60_000
            upper = bounds[i + 1] if i + 1 < len(bounds) else None
            if utc_ms >= bounds[i] and (upper is None or utc_ms < upper):
                candidates.append(utc_ms)
        if not candidates:
            raise TimezoneUnresolvedError(f"server time {server_time} is undefined or non-existent")
        if len(candidates) > 1:
            raise TimezoneUnresolvedError(f"server time {server_time} is ambiguous")
        return candidates[0]


@dataclass(frozen=True, slots=True)
class MT5Tick:
    timestamp_ms: int
    bid_points: int | None
    ask_points: int | None
    last_points: int | None
    volume: int
    flags: int


@dataclass(frozen=True, slots=True)
class MT5Bar:
    start_ms: int
    side: PriceSide
    open_points: int
    high_points: int
    low_points: int
    close_points: int
    tick_volume: int
    real_volume: int
    spread_points: int


@dataclass(frozen=True, slots=True)
class MT5Import:
    broker: str
    kind: str
    instrument: InstrumentSpec
    side: PriceSide | None
    convention_source: str
    ticks: tuple[MT5Tick, ...]
    bars: tuple[MT5Bar, ...]


def _decode(data: bytes) -> str:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8")
    return data.decode("utf-8")


def _rows(data: bytes, expected: tuple[str, ...]) -> list[list[str]]:
    try:
        text = _decode(data)
    except UnicodeDecodeError as exc:
        raise DatasetIntegrityError(f"MT5 export encoding unsupported ({exc})") from exc
    lines = [line for line in text.replace("\r\n", "\n").split("\n") if line != ""]
    require(len(lines) > 0, "MT5 export is empty")
    delimiter = "\t" if "\t" in lines[0] else ","
    header = tuple(cell.strip().strip("<>").upper() for cell in lines[0].split(delimiter))
    require(header == expected, f"MT5 header {header} does not match {expected}")
    rows = [line.split(delimiter) for line in lines[1:]]
    require(all(len(r) == len(expected) for r in rows), "MT5 row column count mismatch")
    return rows


def _server_time(date: str, time: str) -> datetime:
    fmt = "%Y.%m.%d %H:%M:%S.%f" if "." in time else "%Y.%m.%d %H:%M:%S"
    try:
        # Parsed with a placeholder +0000 offset, then made naive on purpose: this is
        # broker server time, converted to UTC only via ServerTimeConvention.
        parsed = datetime.strptime(f"{date} {time} +0000", f"{fmt} %z")
        return parsed.replace(tzinfo=None)
    except ValueError as exc:
        raise DatasetIntegrityError(f"MT5 timestamp {date} {time} invalid") from exc


def _price(text: str, decimals: int, name: str) -> int:
    whole, sep, frac = text.strip().partition(".")
    require(len(frac) <= decimals, f"{name} {text!r} has more than {decimals} decimals")
    value = parse_points(
        f"{whole}.{frac.ljust(decimals, '0')}" if sep else f"{whole}.{'0' * decimals}", decimals
    )
    require(value > 0, f"{name} must be positive")
    return value


def _optional_price(text: str, decimals: int, name: str) -> int | None:
    return None if text.strip() == "" else _price(text, decimals, name)


def _int(text: str, name: str) -> int:
    require(text.strip().isdigit(), f"{name} {text!r} must be a non-negative integer")
    return int(text.strip())


def _check_identity(
    broker: str, spec: InstrumentSpec, convention: ServerTimeConvention | None
) -> ServerTimeConvention:
    require_text(broker, "broker")
    require(spec.provider is Provider.MT5, "instrument spec must be an MT5 spec")
    if convention is None:
        raise TimezoneUnresolvedError("server-time convention not established: import quarantined")
    require(convention.broker == broker, "convention broker does not match import broker")
    return convention


def import_ticks(
    data: bytes, broker: str, spec: InstrumentSpec, convention: ServerTimeConvention | None
) -> MT5Import:
    conv = _check_identity(broker, spec, convention)
    d = spec.price_decimals
    ticks: list[MT5Tick] = []
    previous: MT5Tick | None = None
    for row in _rows(data, TICKS_HEADER):
        tick = MT5Tick(
            conv.to_utc_ms(_server_time(row[0], row[1])),
            _optional_price(row[2], d, "BID"),
            _optional_price(row[3], d, "ASK"),
            _optional_price(row[4], d, "LAST"),
            _int(row[5], "VOLUME"),
            _int(row[6], "FLAGS"),
        )
        require(tick.bid_points is not None or tick.ask_points is not None, "tick without BID/ASK")
        if tick.bid_points is not None and tick.ask_points is not None:
            require(tick.ask_points >= tick.bid_points, "MT5 tick ask below bid")
        if previous is not None:
            require(tick.timestamp_ms >= previous.timestamp_ms, "MT5 ticks out of order")
            require(tick != previous, "MT5 duplicate tick observation")
        ticks.append(tick)
        previous = tick
    return MT5Import(broker, "TICKS", spec, None, conv.source, tuple(ticks), ())


def import_bars(
    data: bytes,
    broker: str,
    spec: InstrumentSpec,
    side: PriceSide | None,
    convention: ServerTimeConvention | None,
) -> MT5Import:
    conv = _check_identity(broker, spec, convention)
    if side is None:
        raise DatasetIntegrityError("MT5 bar price side must be declared explicitly")
    d = spec.price_decimals
    bars: list[MT5Bar] = []
    for row in _rows(data, BARS_HEADER):
        o, h, lo, c = (_price(row[i], d, BARS_HEADER[i]) for i in (2, 3, 4, 5))
        require(lo <= min(o, c) and h >= max(o, c), "MT5 bar OHLC invalid")
        bar = MT5Bar(
            conv.to_utc_ms(_server_time(row[0], row[1])),
            side,
            o,
            h,
            lo,
            c,
            _int(row[6], "TICKVOL"),
            _int(row[7], "VOL"),
            _int(row[8], "SPREAD"),
        )
        if bars:
            require(bar.start_ms > bars[-1].start_ms, "MT5 bars duplicated or out of order")
        bars.append(bar)
    return MT5Import(broker, "BARS", spec, side, conv.source, (), tuple(bars))


def _opt(points: int | None, decimals: int) -> str:
    return "" if points is None else format_points(points, decimals)


def canonical_ticks_csv(result: MT5Import) -> bytes:
    require(result.kind == "TICKS", "not a tick import")
    d = result.instrument.price_decimals
    lines = ["timestamp_utc,bid,ask,last,volume,flags"]
    for t in result.ticks:
        lines.append(
            ",".join(
                (
                    format_timestamp(t.timestamp_ms),
                    _opt(t.bid_points, d),
                    _opt(t.ask_points, d),
                    _opt(t.last_points, d),
                    str(t.volume),
                    str(t.flags),
                )
            )
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def canonical_bars_csv(result: MT5Import) -> bytes:
    require(result.kind == "BARS", "not a bar import")
    d = result.instrument.price_decimals
    lines = ["start_utc,side,open,high,low,close,tick_volume,real_volume,spread_points"]
    for b in result.bars:
        lines.append(
            ",".join(
                (
                    format_timestamp(b.start_ms),
                    b.side.value,
                    format_points(b.open_points, d),
                    format_points(b.high_points, d),
                    format_points(b.low_points, d),
                    format_points(b.close_points, d),
                    str(b.tick_volume),
                    str(b.real_volume),
                    str(b.spread_points),
                )
            )
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def fixed_offset_convention(broker: str, offset_minutes: int, source: str) -> ServerTimeConvention:
    return ServerTimeConvention(
        broker, source, (OffsetSegment(datetime(1970, 1, 1, tzinfo=UTC), offset_minutes),)
    )


def segments_from(pairs: Sequence[tuple[datetime, int]]) -> tuple[OffsetSegment, ...]:
    return tuple(OffsetSegment(start, minutes) for start, minutes in pairs)
