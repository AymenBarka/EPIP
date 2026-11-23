"""Bounded, resumable Dukascopy acquisition (owner-run on Windows; A01 section 7).

Only governance-authorized windows can be acquired; there is no free date
range. Every limit is enforced before the corresponding action:

- byte budget: the transport receives the remaining budget and must refuse to
  read beyond it, so downloaded bytes never exceed the ceiling;
- request ceiling, minimum interval between requests, request timeout;
- bounded retries with deterministic exponential backoff on throttling,
  provider errors, partial bodies, corrupted payloads, and transport failures;
- abort after a bounded number of consecutive failed files.

Raw files are written atomically and never overwritten without explicit
permission. The volatile journal records every attempt and enables resume.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from research.datasets.canonical import sha256_hex
from research.datasets.contracts import (
    MS_PER_HOUR,
    DatasetIntegrityError,
    HourStatus,
    PriceSide,
    require,
)
from research.datasets.dukascopy import (
    candle_relative_path,
    candle_url,
    classify_empty_hour,
    decode_candles,
    decode_ticks,
    hour_start_ms,
    instrument,
    tick_relative_path,
    tick_url,
)
from research.datasets.storage import atomic_write_bytes, resolve_relative

JOURNAL_RELATIVE_PATH = "acquisition/journal.jsonl"
USER_AGENT = "EPIP-research-D00/1"


@dataclass(frozen=True, slots=True)
class AuthorizedWindow:
    window_id: str
    authority: str
    instruments: tuple[str, ...]
    tick_start_ms: int
    tick_end_ms: int
    candle_months: tuple[tuple[int, int], ...]
    max_bytes: int
    max_requests: int


AUTHORIZED_WINDOWS: dict[str, AuthorizedWindow] = {
    "A01-SAMPLE-2012-03": AuthorizedWindow(
        window_id="A01-SAMPLE-2012-03",
        authority="P04-R01-G00-A01 section 6",
        instruments=("EURUSD", "XAUUSD"),
        tick_start_ms=hour_start_ms(2012, 3, 12, 0),
        tick_end_ms=hour_start_ms(2012, 3, 17, 0),
        candle_months=((2012, 3),),
        max_bytes=20_000_000,
        max_requests=400,
    )
}


def authorized_window(window_id: str) -> AuthorizedWindow:
    window = AUTHORIZED_WINDOWS.get(window_id)
    if window is None:
        raise DatasetIntegrityError(f"window {window_id!r} is not governance-authorized")
    return window


class FetchKind(StrEnum):
    TICKS = "TICKS"
    CANDLES = "CANDLES"


@dataclass(frozen=True, slots=True)
class PlannedFetch:
    kind: FetchKind
    instrument: str
    url: str
    relative_path: str
    hour_start_ms: int | None
    year: int
    month: int
    side: PriceSide | None


def build_plan(window: AuthorizedWindow) -> tuple[PlannedFetch, ...]:
    """Deterministic plan: per instrument, every UTC hour of the tick window,
    then BID and ASK candles of each authorized month."""
    require(window.tick_end_ms > window.tick_start_ms, "window empty")
    require(window.tick_start_ms % MS_PER_HOUR == 0, "window start not on an hour")
    plan: list[PlannedFetch] = []
    for symbol in window.instruments:
        spec = instrument(symbol)
        for hour in range(window.tick_start_ms, window.tick_end_ms, MS_PER_HOUR):
            d = datetime.fromtimestamp(hour / 1000, tz=UTC)
            plan.append(
                PlannedFetch(
                    FetchKind.TICKS,
                    symbol,
                    tick_url(spec, hour),
                    tick_relative_path(spec, hour),
                    hour,
                    d.year,
                    d.month,
                    None,
                )
            )
        for year, month in window.candle_months:
            for side in (PriceSide.BID, PriceSide.ASK):
                plan.append(
                    PlannedFetch(
                        FetchKind.CANDLES,
                        symbol,
                        candle_url(spec, year, month, side),
                        candle_relative_path(spec, year, month, side),
                        None,
                        year,
                        month,
                        side,
                    )
                )
    require(len(plan) <= window.max_requests, "plan exceeds the request ceiling")
    return tuple(plan)


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    body: bytes
    declared_length: int | None


class TransportFailure(Exception):
    """Timeout or connection failure (transient)."""


class BudgetExceeded(Exception):
    """The response would exceed the remaining byte budget; nothing beyond it was read."""


class Transport(Protocol):
    def get(self, url: str, timeout_s: float, max_bytes: int) -> HttpResponse: ...


class UrllibTransport:
    """Real HTTP transport. Used only by an owner-run acquisition, never in tests' CI path."""

    def __init__(self, opener: Callable[..., Any] | None = None) -> None:
        self._open = opener or urllib.request.urlopen

    def get(self, url: str, timeout_s: float, max_bytes: int) -> HttpResponse:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            response = self._open(request, timeout=timeout_s)
        except urllib.error.HTTPError as exc:
            return HttpResponse(exc.code, b"", None)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise TransportFailure(str(exc)) from exc
        with response as handle:
            header = handle.headers.get("Content-Length")
            declared = int(header) if header is not None and header.isdigit() else None
            if declared is not None and declared > max_bytes:
                raise BudgetExceeded(f"declared {declared} > remaining {max_bytes}")
            try:
                body = handle.read(max_bytes)
                if len(body) == max_bytes and handle.read(1):
                    raise BudgetExceeded("body exceeds remaining budget")
            except (TimeoutError, OSError) as exc:
                raise TransportFailure(str(exc)) from exc
            return HttpResponse(int(handle.status), bytes(body), declared)


class Clock(Protocol):
    def monotonic(self) -> float: ...

    def sleep(self, seconds: float) -> None: ...

    def utc_now_text(self) -> str: ...


class SystemClock:
    def monotonic(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def utc_now_text(self) -> str:
        return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class AcquisitionLimits:
    max_bytes: int
    max_requests: int
    min_interval_s: float = 1.0
    timeout_s: float = 30.0
    max_retries: int = 4
    backoff_base_s: float = 2.0
    backoff_cap_s: float = 60.0
    max_consecutive_failures: int = 5

    def __post_init__(self) -> None:
        require(type(self.max_bytes) is int and self.max_bytes > 0, "max_bytes invalid")
        require(type(self.max_requests) is int and self.max_requests > 0, "max_requests invalid")
        require(self.min_interval_s >= 1.0, "min_interval_s must be >= 1 second")
        require(0 < self.timeout_s <= 120, "timeout_s out of range")
        require(type(self.max_retries) is int and 0 <= self.max_retries <= 8, "max_retries")
        require(0 < self.backoff_base_s <= self.backoff_cap_s <= 300, "backoff invalid")
        require(
            type(self.max_consecutive_failures) is int and self.max_consecutive_failures > 0,
            "max_consecutive_failures invalid",
        )

    def backoff(self, attempt: int) -> float:
        return float(min(self.backoff_cap_s, self.backoff_base_s * (2**attempt)))


def limits_for(window: AuthorizedWindow) -> AcquisitionLimits:
    return AcquisitionLimits(max_bytes=window.max_bytes, max_requests=window.max_requests)


class FetchStatus(StrEnum):
    POPULATED = "POPULATED"
    EXPECTED_CLOSURE = "EXPECTED_CLOSURE"
    EMPTY_UNEXPLAINED = "EMPTY_UNEXPLAINED"
    MISSING = "MISSING"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    THROTTLED = "THROTTLED"
    CORRUPTED = "CORRUPTED"
    PARTIAL = "PARTIAL"
    TRANSPORT_FAILURE = "TRANSPORT_FAILURE"
    SKIPPED_VERIFIED = "SKIPPED_VERIFIED"


STORED_STATUSES = frozenset(
    {FetchStatus.POPULATED, FetchStatus.EXPECTED_CLOSURE, FetchStatus.EMPTY_UNEXPLAINED}
)
RETRYABLE = frozenset(
    {
        FetchStatus.THROTTLED,
        FetchStatus.PROVIDER_ERROR,
        FetchStatus.PARTIAL,
        FetchStatus.CORRUPTED,
        FetchStatus.TRANSPORT_FAILURE,
    }
)


@dataclass(frozen=True, slots=True)
class JournalRecord:
    relative_path: str
    url: str
    status: FetchStatus
    attempts: int
    size_bytes: int
    raw_sha256: str
    recorded_at_utc: str

    def to_line(self) -> bytes:
        return (
            json.dumps(
                {
                    "relative_path": self.relative_path,
                    "url": self.url,
                    "status": self.status.value,
                    "attempts": self.attempts,
                    "size_bytes": self.size_bytes,
                    "raw_sha256": self.raw_sha256,
                    "recorded_at_utc": self.recorded_at_utc,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("ascii")


def read_journal(data_root: Path) -> dict[str, JournalRecord]:
    """Latest record per relative path."""
    path = resolve_relative(data_root, JOURNAL_RELATIVE_PATH)
    latest: dict[str, JournalRecord] = {}
    if not path.is_file():
        return latest
    for number, line in enumerate(path.read_bytes().splitlines(), 1):
        try:
            d = json.loads(line)
            record = JournalRecord(
                d["relative_path"],
                d["url"],
                FetchStatus(d["status"]),
                int(d["attempts"]),
                int(d["size_bytes"]),
                d["raw_sha256"],
                d["recorded_at_utc"],
            )
        except (ValueError, KeyError, TypeError) as exc:
            raise DatasetIntegrityError(f"journal line {number} is corrupted ({exc})") from exc
        latest[record.relative_path] = record
    return latest


def _append_journal(data_root: Path, record: JournalRecord) -> None:
    path = resolve_relative(data_root, JOURNAL_RELATIVE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "ab") as handle:
        handle.write(record.to_line())


@dataclass(frozen=True, slots=True)
class AcquisitionReport:
    window_id: str
    planned: int
    outcomes: tuple[tuple[str, FetchStatus], ...]
    requests_used: int
    bytes_used: int
    aborted: str | None


def _classify(item: PlannedFetch, response: HttpResponse) -> FetchStatus:
    if response.status == 404:
        return FetchStatus.MISSING
    if response.status in (429, 503):
        return FetchStatus.THROTTLED
    if response.status != 200:
        return FetchStatus.PROVIDER_ERROR
    if response.declared_length is not None and response.declared_length != len(response.body):
        return FetchStatus.PARTIAL
    if len(response.body) == 0:
        if item.kind is FetchKind.CANDLES or item.hour_start_ms is None:
            return FetchStatus.EMPTY_UNEXPLAINED
        empty = classify_empty_hour(item.hour_start_ms)
        return (
            FetchStatus.EXPECTED_CLOSURE
            if empty is HourStatus.EXPECTED_CLOSURE
            else FetchStatus.EMPTY_UNEXPLAINED
        )
    try:
        if item.kind is FetchKind.TICKS:
            assert item.hour_start_ms is not None
            decode_ticks(response.body, item.hour_start_ms)
        else:
            assert item.side is not None
            decode_candles(response.body, item.year, item.month, item.side)
    except DatasetIntegrityError:
        return FetchStatus.CORRUPTED
    return FetchStatus.POPULATED


def run_acquisition(
    window: AuthorizedWindow,
    data_root: Path,
    transport: Transport,
    clock: Clock,
    *,
    limits: AcquisitionLimits | None = None,
    allow_overwrite: bool = False,
) -> AcquisitionReport:
    limits = limits or limits_for(window)
    require(limits.max_bytes <= window.max_bytes, "limits exceed the window byte ceiling")
    require(limits.max_requests <= window.max_requests, "limits exceed the window request ceiling")
    plan = build_plan(window)
    journal = read_journal(data_root)
    outcomes: list[tuple[str, FetchStatus]] = []
    requests_used = 0
    bytes_used = 0
    consecutive_failures = 0
    last_request: float | None = None
    aborted: str | None = None

    for item in plan:
        target = resolve_relative(data_root, item.relative_path)
        known = journal.get(item.relative_path)
        if target.exists():
            verified = (
                known is not None
                and known.status in STORED_STATUSES
                and sha256_hex(target.read_bytes()) == known.raw_sha256
            )
            if verified:
                outcomes.append((item.relative_path, FetchStatus.SKIPPED_VERIFIED))
                continue
            if not allow_overwrite:
                aborted = f"unverified existing file {item.relative_path}; refusing to overwrite"
                break
        final: FetchStatus | None = None
        attempts = 0
        body = b""
        while final is None:
            if requests_used >= limits.max_requests:
                aborted = "request ceiling reached"
                break
            remaining = limits.max_bytes - bytes_used
            if remaining <= 0:
                aborted = "byte budget exhausted"
                break
            if last_request is not None:
                wait = limits.min_interval_s - (clock.monotonic() - last_request)
                if wait > 0:
                    clock.sleep(wait)
            last_request = clock.monotonic()
            requests_used += 1
            attempts += 1
            try:
                response = transport.get(item.url, limits.timeout_s, remaining)
            except BudgetExceeded:
                aborted = "byte budget would be exceeded"
                break
            except TransportFailure:
                status = FetchStatus.TRANSPORT_FAILURE
            else:
                bytes_used += len(response.body)
                body = response.body
                status = _classify(item, response)
            if status in RETRYABLE and attempts <= limits.max_retries:
                clock.sleep(limits.backoff(attempts - 1))
                continue
            final = status
        if aborted is not None:
            break
        assert final is not None
        if final in STORED_STATUSES:
            atomic_write_bytes(target, body, overwrite=allow_overwrite)
            consecutive_failures = 0
        elif final is FetchStatus.MISSING:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
        _append_journal(
            data_root,
            JournalRecord(
                item.relative_path,
                item.url,
                final,
                attempts,
                len(body) if final in STORED_STATUSES else 0,
                sha256_hex(body if final in STORED_STATUSES else b""),
                clock.utc_now_text(),
            ),
        )
        outcomes.append((item.relative_path, final))
        if consecutive_failures >= limits.max_consecutive_failures:
            aborted = "consecutive failure limit reached"
            break
    return AcquisitionReport(
        window.window_id, len(plan), tuple(outcomes), requests_used, bytes_used, aborted
    )
