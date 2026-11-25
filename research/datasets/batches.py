"""Governed acquisition batches beyond the D00 technical sample (Q00-G00 section 6).

D01-B1: EURUSD and XAUUSD, 2018-01-01 to 2018-07-01 (end excluded), one
window per instrument-month, calendar ``ny-1700-close/2``. Every window is
independently resumable and verifiable.

**Acquisition gate.** Only the windows in ``OPEN_WINDOWS`` accept owner-run
downloads (with ``--confirm-provider-terms``); every other D01-B1 window has
``acquisition_open=False``: planning and dry runs work, real downloads are
refused. Only a separately authorized commit may open a gate.

**Owner decisions.** An unexplained or failed hour blocks its month unless an
explicit owner decision, committed here, covers it. Decisions are recorded in
the dataset manifest diagnostics and therefore in its identity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from research.datasets.acquisition import AUTHORIZED_WINDOWS, AuthorizedWindow
from research.datasets.calendar import CALENDAR_V2
from research.datasets.contracts import DatasetIntegrityError, require
from research.datasets.dukascopy import hour_start_ms, month_start_ms

D01_B1 = "D01-B1"
D01_B1_AUTHORITY = "P04-R01-Q00-G00 section 6.3; P04-R01-D01-B1 implementation authorization"
D01_B1_INSTRUMENTS = ("EURUSD", "XAUUSD")
D01_B1_MONTHS = ((2018, 1), (2018, 2), (2018, 3), (2018, 4), (2018, 5), (2018, 6))
MAX_PLANNED_PER_MONTH = 600
MAX_REQUESTS_PER_RUN = 1_500
MAX_BYTES_PER_RUN = 100_000_000


# Owner authorization of 2026-11-25 (first acquisition window): one window only.
OPEN_WINDOWS: frozenset[str] = frozenset({"D01-B1-EURUSD-2018-01"})


def _month_window(symbol: str, year: int, month: int) -> AuthorizedWindow:
    end_year, end_month = (year + 1, 1) if month == 12 else (year, month + 1)
    window_id = f"{D01_B1}-{symbol}-{year:04d}-{month:02d}"
    return AuthorizedWindow(
        window_id=window_id,
        authority=D01_B1_AUTHORITY,
        instruments=(symbol,),
        tick_start_ms=month_start_ms(year, month),
        tick_end_ms=month_start_ms(end_year, end_month),
        candle_months=((year, month),),
        max_bytes=MAX_BYTES_PER_RUN,
        max_requests=MAX_REQUESTS_PER_RUN,
        calendar_version=CALENDAR_V2,
        skip_scheduled_weekend=True,
        max_planned_requests=MAX_PLANNED_PER_MONTH,
        acquisition_open=window_id in OPEN_WINDOWS,
    )


BATCH_WINDOWS: dict[str, tuple[AuthorizedWindow, ...]] = {
    D01_B1: tuple(
        _month_window(symbol, year, month)
        for symbol in D01_B1_INSTRUMENTS
        for year, month in D01_B1_MONTHS
    )
}
_BY_ID = {w.window_id: w for windows in BATCH_WINDOWS.values() for w in windows}
require(not set(_BY_ID) & set(AUTHORIZED_WINDOWS), "batch window ids collide with D00")


def governed_window(window_id: str) -> AuthorizedWindow:
    """The D00 window or a governed batch window; anything else is refused."""
    window = AUTHORIZED_WINDOWS.get(window_id) or _BY_ID.get(window_id)
    if window is None:
        raise DatasetIntegrityError(f"window {window_id!r} is not governance-authorized")
    return window


def batch_windows(batch_id: str) -> tuple[AuthorizedWindow, ...]:
    windows = BATCH_WINDOWS.get(batch_id)
    if windows is None:
        raise DatasetIntegrityError(f"batch {batch_id!r} is not governance-authorized")
    return windows


_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_HOUR = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:00:00Z")


class DecisionKind(StrEnum):
    DECLARE_EXPECTED_CLOSURE = "DECLARE_EXPECTED_CLOSURE"  # an observed empty hour only
    DECLARE_MISSING = "DECLARE_MISSING"  # a failed hour after three separate runs
    EXCLUDE_MONTH = "EXCLUDE_MONTH"


@dataclass(frozen=True, slots=True)
class OwnerDecision:
    window_id: str
    hour_utc: str  # "YYYY-MM-DDTHH:00:00Z"; empty for EXCLUDE_MONTH
    kind: DecisionKind
    source: str
    rationale: str
    decided_on: str

    def __post_init__(self) -> None:
        require(self.window_id in _BY_ID, "decision window is not a governed batch window")
        require(type(self.kind) is DecisionKind, "decision kind invalid")
        require(bool(self.source) and bool(self.rationale), "decision needs source and rationale")
        require(
            type(self.decided_on) is str and bool(_DATE.fullmatch(self.decided_on)),
            "decided_on must be YYYY-MM-DD",
        )
        if self.kind is DecisionKind.EXCLUDE_MONTH:
            require(self.hour_utc == "", "EXCLUDE_MONTH applies to the whole window")
        else:
            require(
                type(self.hour_utc) is str and bool(_HOUR.fullmatch(self.hour_utc)),
                "hour_utc must be YYYY-MM-DDTHH:00:00Z",
            )

    @property
    def hour_ms(self) -> int:
        y, m, d, h = (
            int(self.hour_utc[0:4]),
            int(self.hour_utc[5:7]),
            int(self.hour_utc[8:10]),
            int(self.hour_utc[11:13]),
        )
        return hour_start_ms(y, m, d, h)


# Committed owner decisions. Empty until real D01-B1 data is acquired and reviewed.
OWNER_DECISIONS: tuple[OwnerDecision, ...] = ()


def decisions_for(
    window_id: str, decisions: tuple[OwnerDecision, ...] = OWNER_DECISIONS
) -> tuple[OwnerDecision, ...]:
    return tuple(d for d in decisions if d.window_id == window_id)
