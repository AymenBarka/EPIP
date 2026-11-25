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

import ctypes
import http.client
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from research.datasets.calendar import (
    CALENDAR_V1,
    SUPPORTED_CALENDARS,
    classify_empty,
    is_scheduled_weekend_hour,
)
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
    calendar_version: str = CALENDAR_V1
    skip_scheduled_weekend: bool = False
    max_planned_requests: int | None = None
    acquisition_open: bool = True

    def __post_init__(self) -> None:
        require(self.calendar_version in SUPPORTED_CALENDARS, "window calendar unsupported")
        require(
            self.max_planned_requests is None or 0 < self.max_planned_requests <= self.max_requests,
            "max_planned_requests invalid",
        )


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
            if window.skip_scheduled_weekend and is_scheduled_weekend_hour(hour):
                continue  # declared from the calendar, never requested
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
    require(
        window.max_planned_requests is None or len(plan) <= window.max_planned_requests,
        "plan exceeds the planned-request ceiling",
    )
    return tuple(plan)


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    body: bytes
    declared_length: int | None


def _describe(exc: BaseException) -> str:
    """Short ASCII description of a transport error, for the journal only."""
    text = f"{type(exc).__name__}: {exc}"
    return text.encode("ascii", "replace").decode("ascii")[:200]


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
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError) as exc:
            raise TransportFailure(_describe(exc)) from exc
        with response as handle:
            header = handle.headers.get("Content-Length")
            declared = int(header) if header is not None and header.isdigit() else None
            if declared is not None and declared > max_bytes:
                raise BudgetExceeded(f"declared {declared} > remaining {max_bytes}")
            try:
                body = handle.read(max_bytes)
                if len(body) == max_bytes and handle.read(1):
                    raise BudgetExceeded("body exceeds remaining budget")
            except (http.client.HTTPException, TimeoutError, OSError) as exc:
                raise TransportFailure(_describe(exc)) from exc
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
        require(1 <= self.timeout_s <= 120, "timeout_s must be between 1 and 120 seconds")
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
    detail: str = ""

    def to_line(self) -> bytes:
        fields: dict[str, object] = {
            "relative_path": self.relative_path,
            "url": self.url,
            "status": self.status.value,
            "attempts": self.attempts,
            "size_bytes": self.size_bytes,
            "raw_sha256": self.raw_sha256,
            "recorded_at_utc": self.recorded_at_utc,
        }
        if self.detail:
            fields["detail"] = self.detail
        return (
            json.dumps(
                fields,
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
                str(d.get("detail", "")),
            )
        except (ValueError, KeyError, TypeError) as exc:
            raise DatasetIntegrityError(f"journal line {number} is corrupted ({exc})") from exc
        latest[record.relative_path] = record
    return latest


DAILY_REQUESTS_RELATIVE_PATH = "acquisition/daily_requests.jsonl"
DAILY_REQUEST_CEILING = 5_000


class DailyRequestBudget:
    """Persistent per-UTC-day request counter shared by every run and window.

    One line is appended **before** each request, so a crash never hides a
    request; the count survives restarts (Q00-G00 section 6.5).
    """

    def __init__(self, data_root: Path, ceiling: int = DAILY_REQUEST_CEILING) -> None:
        require(type(ceiling) is int and ceiling > 0, "daily ceiling invalid")
        self._path = resolve_relative(data_root, DAILY_REQUESTS_RELATIVE_PATH)
        self.ceiling = ceiling
        self._cache: tuple[str, int] | None = None

    def used(self, utc_date: str) -> int:
        if self._cache is not None and self._cache[0] == utc_date:
            return self._cache[1]
        count = 0
        if self._path.is_file():
            for number, line in enumerate(self._path.read_bytes().splitlines(), 1):
                try:
                    record = json.loads(line)
                    day = record["utc_date"]
                    require(type(day) is str and len(day) == 10, "date invalid")
                except (ValueError, KeyError, TypeError) as exc:
                    raise DatasetIntegrityError(
                        f"daily request ledger line {number} is corrupted ({exc})"
                    ) from exc
                count += day == utc_date
        self._cache = (utc_date, count)
        return count

    def try_consume(self, utc_date: str, window_id: str) -> bool:
        used = self.used(utc_date)
        if used >= self.ceiling:
            return False
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(
            {"utc_date": utc_date, "window": window_id}, sort_keys=True, separators=(",", ":")
        )
        with open(self._path, "ab") as handle:
            handle.write((line + "\n").encode("ascii"))
        self._cache = (utc_date, used + 1)
        return True


def pending_items(window: AuthorizedWindow, data_root: Path) -> tuple[str, ...]:
    """Planned items whose latest journal record is not a stored outcome."""
    journal = read_journal(data_root)
    return tuple(
        item.relative_path
        for item in build_plan(window)
        if (record := journal.get(item.relative_path)) is None
        or record.status not in STORED_STATUSES
    )


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


def _classify(item: PlannedFetch, response: HttpResponse, calendar: str) -> FetchStatus:
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
        empty = classify_empty(instrument(item.instrument), item.hour_start_ms, calendar)
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


# --- acquisition locks ------------------------------------------------------------
LOCKS_RELATIVE_DIR = "acquisition/locks"
GLOBAL_LOCK_NAME = "global"
_STILL_ACTIVE = 259
_ERROR_INVALID_PARAMETER = 87
_ERROR_ACCESS_DENIED = 5
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class LockState(StrEnum):
    """Diagnostic state of a lock owner. Only NOT_RUNNING permits a release by
    someone other than the owner; UNKNOWN always fails closed."""

    ALIVE = "ALIVE"
    NOT_RUNNING = "NOT_RUNNING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class LockInfo:
    name: str
    path: Path
    owner: dict[str, object]
    state: LockState


def _lock_path(data_root: Path, name: str) -> Path:
    return resolve_relative(data_root, f"{LOCKS_RELATIVE_DIR}/{name}.lock")


def _posix_state(pid: int) -> LockState:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return LockState.NOT_RUNNING
    except PermissionError:
        return LockState.ALIVE
    except OSError:
        return LockState.UNKNOWN
    return LockState.ALIVE


def _windows_state(pid: int, kernel32: Any, last_error: Callable[[], int]) -> LockState:
    """Query a Windows process without signalling it (``os.kill`` would
    terminate it on Windows)."""
    handle = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        error = last_error()
        if error == _ERROR_INVALID_PARAMETER:
            return LockState.NOT_RUNNING
        if error == _ERROR_ACCESS_DENIED:
            return LockState.ALIVE
        return LockState.UNKNOWN
    try:
        code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return LockState.UNKNOWN
        return LockState.ALIVE if code.value == _STILL_ACTIVE else LockState.NOT_RUNNING
    finally:
        kernel32.CloseHandle(handle)


def process_state(
    pid: int,
    *,
    platform: str | None = None,
    kernel32: Any = None,
    last_error: Callable[[], int] | None = None,
) -> LockState:
    """Best-effort liveness of a local process id; never sends a signal on
    Windows. PID reuse after a restart reads as ALIVE, which fails closed."""
    if type(pid) is not int or pid <= 0:
        return LockState.UNKNOWN
    if (platform or sys.platform) == "win32":
        if kernel32 is None:  # pragma: no cover - exercised on Windows only
            kernel32 = vars(ctypes)["WinDLL"]("kernel32", use_last_error=True)
            last_error = vars(ctypes)["get_last_error"]
        assert last_error is not None
        return _windows_state(pid, kernel32, last_error)
    return _posix_state(pid)


def _owner_state(owner: dict[str, object]) -> LockState:
    pid = owner.get("pid")
    if owner.get("host") != socket.gethostname() or type(pid) is not int:
        return LockState.UNKNOWN
    return process_state(pid)


class AcquisitionLock:
    """Exclusive, fail-closed lock file created atomically with ``O_EXCL``.

    The file records its owner (pid, host, random token, window, time). Only
    the holder of the token releases it; nothing removes a lock because of its
    age. Works on Windows and POSIX with the standard library only.
    """

    def __init__(self, data_root: Path, name: str, window_id: str, acquired_utc: str) -> None:
        require(name.replace("-", "").isalnum(), f"invalid lock name {name!r}")
        self.path = _lock_path(data_root, name)
        self.name = name
        self.token = uuid.uuid4().hex
        self._owner = {
            "lock": name,
            "window": window_id,
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "token": self.token,
            "acquired_utc": acquired_utc,
            "executable": sys.executable,
        }
        self.held = False

    def acquire(self) -> AcquisitionLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
        try:
            fd = os.open(self.path, flags, 0o644)
        except FileExistsError:
            raise DatasetIntegrityError(
                f"acquisition lock {self.name} is held ({self.path}); another acquisition "
                "may be running. Follow the stale-lock recovery procedure; locks are "
                "never removed automatically"
            ) from None
        self.held = True
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(json.dumps(self._owner, sort_keys=True).encode("ascii") + b"\n")
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            self.path.unlink()
            self.held = False
            raise
        return self

    def release(self) -> None:
        if not self.held:
            return
        owner = _read_lock(self.path)
        require(
            owner.get("token") == self.token,
            f"acquisition lock {self.name} is no longer owned by this process; not removed",
        )
        self.path.unlink()
        self.held = False


def _read_lock(path: Path) -> dict[str, object]:
    try:
        loaded = json.loads(path.read_bytes())
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def inspect_locks(data_root: Path) -> tuple[LockInfo, ...]:
    """Diagnose existing locks without changing them."""
    directory = resolve_relative(data_root, LOCKS_RELATIVE_DIR)
    if not directory.is_dir():
        return ()
    infos = []
    for path in sorted(directory.glob("*.lock")):
        owner = _read_lock(path)
        infos.append(
            LockInfo(path.stem, path, owner, _owner_state(owner) if owner else LockState.UNKNOWN)
        )
    return tuple(infos)


def release_stale_lock(data_root: Path, name: str, token: str) -> None:
    """Owner-invoked recovery: remove lock ``name`` only if ``token`` matches its
    recorded token and its owner is verified NOT_RUNNING on this host."""
    path = _lock_path(data_root, name)
    require(path.is_file(), f"no acquisition lock {name}")
    owner = _read_lock(path)
    require(
        bool(owner) and owner.get("token") == token,
        f"lock {name}: token does not match the recorded owner; not removed",
    )
    state = _owner_state(owner)
    require(
        state is LockState.NOT_RUNNING,
        f"lock {name}: owner state {state.value}; ownership cannot be cleared safely. "
        "Manual owner intervention is required (see the D01-B1 recovery procedure)",
    )
    path.unlink()


def run_acquisition(
    window: AuthorizedWindow,
    data_root: Path,
    transport: Transport,
    clock: Clock,
    *,
    limits: AcquisitionLimits | None = None,
    allow_overwrite: bool = False,
    daily_budget: DailyRequestBudget | None = None,
) -> AcquisitionReport:
    """Run under an exclusive global lock (shared daily budget, one acquisition
    per data root) and an exclusive per-window lock, both taken before any
    network request and released on completion or exception."""
    require(
        window.acquisition_open,
        f"acquisition gate closed for {window.window_id}: a separate owner authorization "
        "must open it before any download",
    )
    now = clock.utc_now_text()
    held: list[AcquisitionLock] = []
    try:
        for name in (GLOBAL_LOCK_NAME, window.window_id):
            lock = AcquisitionLock(data_root, name, window.window_id, now)
            held.append(lock.acquire())
        return _run_acquisition(
            window,
            data_root,
            transport,
            clock,
            limits=limits,
            allow_overwrite=allow_overwrite,
            daily_budget=daily_budget,
        )
    finally:
        for lock in reversed(held):
            lock.release()


def _run_acquisition(
    window: AuthorizedWindow,
    data_root: Path,
    transport: Transport,
    clock: Clock,
    *,
    limits: AcquisitionLimits | None,
    allow_overwrite: bool,
    daily_budget: DailyRequestBudget | None,
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
        detail = ""
        while final is None:
            if requests_used >= limits.max_requests:
                aborted = "request ceiling reached"
                break
            if daily_budget is not None and not daily_budget.try_consume(
                clock.utc_now_text()[:10], window.window_id
            ):
                aborted = "daily request ceiling reached"
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
            except TransportFailure as exc:
                status = FetchStatus.TRANSPORT_FAILURE
                detail = str(exc)
            else:
                bytes_used += len(response.body)
                body = response.body
                status = _classify(item, response, window.calendar_version)
                detail = "" if response.status == 200 else f"HTTP {response.status}"
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
                "" if final in STORED_STATUSES else detail,
            ),
        )
        outcomes.append((item.relative_path, final))
        if consecutive_failures >= limits.max_consecutive_failures:
            aborted = "consecutive failure limit reached"
            break
    return AcquisitionReport(
        window.window_id, len(plan), tuple(outcomes), requests_used, bytes_used, aborted
    )
