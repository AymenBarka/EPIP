"""Deterministic canonical serialization and hashing.

Frozen rules (``epip-research-ticks-csv/1`` and ``epip-research-bars-csv/1``):

- UTF-8, ``\\n`` line endings, one header row, no trailing spaces, final newline;
- timestamps ``YYYY-MM-DDTHH:MM:SS.mmmZ`` (UTC, milliseconds);
- prices rendered from integer points with exactly ``price_decimals`` decimals;
- quoted volumes rendered from integer millionths with exactly six decimals;
- ticks keep source order (already validated non-decreasing, no duplicates);
- bars ordered by (start, side);
- gzip: level 9, ``mtime=0``, empty file name. Identity uses uncompressed bytes.
"""

from __future__ import annotations

import gzip
import hashlib
import io
from collections.abc import Iterable
from datetime import UTC, datetime

from research.datasets.contracts import (
    Bar,
    BarCoverage,
    DatasetIntegrityError,
    InstrumentSpec,
    PriceSide,
    Tick,
    require,
)

TICK_HEADER = "timestamp_utc,bid,ask,bid_volume,ask_volume"
BAR_HEADER = "start_utc,end_utc,side,open,high,low,close,tick_count,coverage"
GZIP_LEVEL = 9


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def format_timestamp(ms: int) -> str:
    require(type(ms) is int and ms >= 0, "timestamp must be a non-negative int")
    seconds, millis = divmod(ms, 1000)
    d = datetime.fromtimestamp(seconds, tz=UTC)
    return f"{d:%Y-%m-%dT%H:%M:%S}.{millis:03d}Z"


def parse_timestamp(text: str) -> int:
    require(len(text) == 24 and text.endswith("Z") and text[19] == ".", f"bad timestamp {text!r}")
    try:
        d = datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
    except ValueError as exc:
        raise DatasetIntegrityError(f"bad timestamp {text!r}") from exc
    require(text[20:23].isdigit(), f"bad milliseconds {text!r}")
    return int(d.timestamp()) * 1000 + int(text[20:23])


def format_points(points: int, decimals: int) -> str:
    require(type(points) is int and points >= 0, "points must be a non-negative int")
    whole, frac = divmod(points, 10**decimals)
    return f"{whole}.{frac:0{decimals}d}"


def parse_points(text: str, decimals: int) -> int:
    whole, sep, frac = text.partition(".")
    require(sep == "." and whole.isdigit() and frac.isdigit(), f"bad decimal {text!r}")
    require(len(frac) == decimals, f"decimal {text!r} must have {decimals} decimals")
    return int(whole) * int(10**decimals) + int(frac)


def ticks_to_csv(ticks: Iterable[Tick], spec: InstrumentSpec) -> bytes:
    lines = [TICK_HEADER]
    for t in ticks:
        lines.append(
            ",".join(
                (
                    format_timestamp(t.timestamp_ms),
                    format_points(t.bid_points, spec.price_decimals),
                    format_points(t.ask_points, spec.price_decimals),
                    format_points(t.bid_volume_micro, 6),
                    format_points(t.ask_volume_micro, 6),
                )
            )
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def csv_to_ticks(data: bytes, spec: InstrumentSpec) -> tuple[Tick, ...]:
    text = data.decode("utf-8")
    require(text.endswith("\n") and "\r" not in text, "canonical CSV line endings invalid")
    rows = text[:-1].split("\n")
    require(rows[0] == TICK_HEADER, "tick CSV header mismatch")
    out: list[Tick] = []
    for row in rows[1:]:
        cells = row.split(",")
        require(len(cells) == 5, f"tick row has {len(cells)} columns")
        out.append(
            Tick(
                parse_timestamp(cells[0]),
                parse_points(cells[1], spec.price_decimals),
                parse_points(cells[2], spec.price_decimals),
                parse_points(cells[3], 6),
                parse_points(cells[4], 6),
            )
        )
    return tuple(out)


def bars_to_csv(bars: Iterable[Bar], spec: InstrumentSpec) -> bytes:
    ordered = sorted(bars, key=lambda b: (b.start_ms, b.side.value))
    lines = [BAR_HEADER]
    for b in ordered:
        d = spec.price_decimals
        lines.append(
            ",".join(
                (
                    format_timestamp(b.start_ms),
                    format_timestamp(b.end_ms),
                    b.side.value,
                    format_points(b.open_points, d),
                    format_points(b.high_points, d),
                    format_points(b.low_points, d),
                    format_points(b.close_points, d),
                    str(b.tick_count),
                    b.coverage.value,
                )
            )
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def csv_to_bars(data: bytes, spec: InstrumentSpec) -> tuple[Bar, ...]:
    text = data.decode("utf-8")
    require(text.endswith("\n") and "\r" not in text, "canonical CSV line endings invalid")
    rows = text[:-1].split("\n")
    require(rows[0] == BAR_HEADER, "bar CSV header mismatch")
    d = spec.price_decimals
    out: list[Bar] = []
    for row in rows[1:]:
        c = row.split(",")
        require(len(c) == 9 and c[7].isdigit(), "bar row malformed")
        require(
            c[2] in PriceSide.__members__ and c[8] in BarCoverage.__members__,
            "bar side or coverage invalid",
        )
        out.append(
            Bar(
                parse_timestamp(c[0]),
                parse_timestamp(c[1]),
                PriceSide(c[2]),
                parse_points(c[3], d),
                parse_points(c[4], d),
                parse_points(c[5], d),
                parse_points(c[6], d),
                int(c[7]),
                BarCoverage(c[8]),
            )
        )
    return tuple(out)


def deterministic_gzip(data: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(
        filename="", mode="wb", compresslevel=GZIP_LEVEL, fileobj=buffer, mtime=0
    ) as handle:
        handle.write(data)
    return buffer.getvalue()


def gunzip(data: bytes) -> bytes:
    return gzip.decompress(data)
