"""Versioned session calendars (G00 section 7.3, Q00-G00 sections 6.5 and 6.6).

``ny-1700-close/1`` (D00, frozen) lives in ``dukascopy.py`` and is unchanged.

``ny-1700-close/2`` (D01) keeps every v1 rule and adds:

- an instrument-specific weekly reopening: XAUUSD reopens on Sunday at 18:00
  New York time (COMEX metals Globex session, Sunday 6:00 p.m. ET), so the
  Sunday 17:00–18:00 New York hour is a scheduled closure for XAUUSD only;
- a sourced **holiday reference** table. A holiday never classifies an hour by
  itself: an empty provider response on a holiday stays EMPTY_UNEXPLAINED and
  carries the reference, until an explicit owner decision (``batches.py``)
  declares it. An empty response never proves a closure.

Weekend hours wholly inside the common FX closure (Friday 17:00 to Sunday
17:00 New York) are scheduled closures for every instrument; D01 windows do
not request them and declare them from this calendar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from research.datasets.contracts import MS_PER_HOUR, HourStatus, InstrumentSpec, require
from research.datasets.dukascopy import (
    SESSION_CALENDAR_VERSION,
    classify_empty_hour,
    new_york_offset_ms,
)

CALENDAR_V1 = SESSION_CALENDAR_VERSION
CALENDAR_V2 = "ny-1700-close/2"
SUPPORTED_CALENDARS = (CALENDAR_V1, CALENDAR_V2)

_SUNDAY_REOPEN_18 = frozenset({"XAUUSD"})


@dataclass(frozen=True, slots=True)
class HolidayReference:
    """A sourced holiday that may explain provider gaps; never a closure by itself."""

    date_utc: str
    name: str
    instruments: tuple[str, ...]
    source: str


HOLIDAY_REFERENCES: tuple[HolidayReference, ...] = (
    HolidayReference(
        "2018-01-01",
        "New Year's Day",
        ("EURUSD", "XAUUSD"),
        "Dukascopy 'Holiday season market hours' notice of 2017-12-08 (dbl200910); "
        "warns of reduced liquidity and interruptions; hours not machine-readable",
    ),
    HolidayReference(
        "2018-03-30",
        "Good Friday",
        ("EURUSD", "XAUUSD"),
        "CME Globex Good Friday 2018 schedule: all markets closed on 2018-03-30 "
        "(exchange schedule, not Dukascopy spot hours)",
    ),
)


def _local(instant_ms: int) -> datetime:
    return datetime.fromtimestamp((instant_ms + new_york_offset_ms(instant_ms)) / 1000, tz=UTC)


def _in_common_weekend(instant_ms: int) -> bool:
    local = _local(instant_ms)
    weekday, hour = local.weekday(), local.hour
    return weekday == 5 or (weekday == 4 and hour >= 17) or (weekday == 6 and hour < 17)


def is_scheduled_weekend_hour(hour_start: int) -> bool:
    """Whole UTC hour inside the common FX weekend closure (all instruments)."""
    require(hour_start % MS_PER_HOUR == 0, "hour start not aligned")
    return _in_common_weekend(hour_start) and _in_common_weekend(hour_start + MS_PER_HOUR - 1)


def _v2_closed(symbol: str, instant_ms: int) -> bool:
    if _in_common_weekend(instant_ms):
        return True
    local = _local(instant_ms)
    weekday, hour = local.weekday(), local.hour
    if symbol in _SUNDAY_REOPEN_18 and weekday == 6 and hour == 17:
        return True
    return symbol in _SUNDAY_REOPEN_18 and weekday <= 3 and hour == 17


def classify_empty(spec: InstrumentSpec, hour_start: int, version: str) -> HourStatus:
    """Classify an HTTP 200 zero-byte tick hour under ``version``."""
    require(version in SUPPORTED_CALENDARS, f"unsupported calendar {version!r}")
    if version == CALENDAR_V1:
        return classify_empty_hour(spec, hour_start)
    closed = _v2_closed(spec.symbol, hour_start) and _v2_closed(
        spec.symbol, hour_start + MS_PER_HOUR - 1
    )
    return HourStatus.EXPECTED_CLOSURE if closed else HourStatus.EMPTY_UNEXPLAINED


def holiday_reference(symbol: str, hour_start: int, version: str) -> HolidayReference | None:
    """The sourced holiday covering this UTC hour's date, if any (v2 only)."""
    if version != CALENDAR_V2:
        return None
    day = datetime.fromtimestamp(hour_start / 1000, tz=UTC).strftime("%Y-%m-%d")
    for reference in HOLIDAY_REFERENCES:
        if reference.date_utc == day and symbol in reference.instruments:
            return reference
    return None
