"""D00 acceptance 26-32: offline dry-run, budget, rate, retries, empty responses,
resume safety, atomic writes. All transports are fakes; no network is used."""

from __future__ import annotations

import io
import urllib.error
from dataclasses import replace
from pathlib import Path
from typing import Self

import pytest

from research.datasets.acquisition import (
    AUTHORIZED_WINDOWS,
    AcquisitionLimits,
    AuthorizedWindow,
    BudgetExceeded,
    FetchKind,
    FetchStatus,
    HttpResponse,
    TransportFailure,
    UrllibTransport,
    authorized_window,
    build_plan,
    read_journal,
    run_acquisition,
)
from research.datasets.contracts import DatasetIntegrityError, PriceSide
from research.datasets.storage import atomic_write_bytes, resolve_relative
from research.tests.fixtures import (
    FakeClock,
    FakeTransport,
    failing,
    hour_ms,
    month_candles,
    ok,
    status,
    tick_payload,
    tick_records,
    url_hour,
)

WINDOW = authorized_window("A01-SAMPLE-2012-03")


def sample_responder(url: str, _max: int) -> HttpResponse:
    symbol = url.split("/datafeed/", maxsplit=1)[1].split("/", maxsplit=1)[0]
    if url.endswith("_candles_hour_1.bi5"):
        side = PriceSide.BID if "/BID_" in url else PriceSide.ASK
        return ok(
            month_candles(
                symbol, 2012, 3, side, lambda h: WINDOW.tick_start_ms <= h < WINDOW.tick_end_ms
            )
        )
    return ok(tick_payload(tick_records(symbol, url_hour(url))))


def small_window(hours: int = 3) -> AuthorizedWindow:
    return replace(
        WINDOW,
        instruments=("EURUSD",),
        tick_end_ms=WINDOW.tick_start_ms + hours * 3_600_000,
        candle_months=(),
    )


def test_authorized_window_is_exactly_the_a01_sample() -> None:
    assert set(AUTHORIZED_WINDOWS) == {"A01-SAMPLE-2012-03"}
    assert WINDOW.instruments == ("EURUSD", "XAUUSD")
    assert WINDOW.tick_start_ms == hour_ms(2012, 3, 12, 0)
    assert WINDOW.tick_end_ms == hour_ms(2012, 3, 17, 0)
    assert WINDOW.candle_months == ((2012, 3),)
    assert WINDOW.max_bytes == 20_000_000 and WINDOW.max_requests == 400
    with pytest.raises(DatasetIntegrityError, match="not governance-authorized"):
        authorized_window("FULL-HISTORY")


def test_plan_is_deterministic_and_bounded() -> None:
    plan = build_plan(WINDOW)
    assert plan == build_plan(WINDOW)
    assert len(plan) == 2 * (5 * 24 + 2) == 244
    ticks = [p for p in plan if p.kind is FetchKind.TICKS]
    assert ticks[0].url.endswith("/EURUSD/2012/02/12/00h_ticks.bi5")
    assert ticks[-1].url.endswith("/XAUUSD/2012/02/16/23h_ticks.bi5")
    assert all(p.hour_start_ms is not None for p in ticks)
    with pytest.raises(DatasetIntegrityError, match="request ceiling"):
        build_plan(replace(WINDOW, max_requests=10))


def test_full_sample_run_stays_within_limits(tmp_path: Path) -> None:
    clock = FakeClock()
    transport = FakeTransport(sample_responder, clock=clock)
    report = run_acquisition(WINDOW, tmp_path, transport, clock)
    assert report.aborted is None and report.requests_used == 244
    assert report.bytes_used <= WINDOW.max_bytes
    assert {s for _, s in report.outcomes} == {FetchStatus.POPULATED}
    assert not list(tmp_path.rglob("*.partial"))
    gaps = [b - a for a, b in zip(transport.call_times, transport.call_times[1:], strict=False)]
    assert min(gaps) >= 1.0


def test_download_budget_is_never_exceeded(tmp_path: Path) -> None:
    clock = FakeClock()
    transport = FakeTransport(sample_responder, clock=clock)
    payload = len(tick_payload(tick_records("EURUSD", WINDOW.tick_start_ms)))
    limits = AcquisitionLimits(max_bytes=payload + 10, max_requests=400)
    report = run_acquisition(small_window(), tmp_path, transport, clock, limits=limits)
    assert report.aborted == "byte budget would be exceeded"
    assert report.bytes_used <= limits.max_bytes
    assert [s for _, s in report.outcomes] == [FetchStatus.POPULATED]
    assert transport.calls[1][1] == limits.max_bytes - payload


def test_request_ceiling_and_rate_are_enforced(tmp_path: Path) -> None:
    clock = FakeClock()
    transport = FakeTransport(lambda u, m: status(503), clock=clock)
    limits = AcquisitionLimits(max_bytes=10**6, max_requests=3, max_retries=8)
    report = run_acquisition(small_window(), tmp_path, transport, clock, limits=limits)
    assert report.aborted == "request ceiling reached" and report.requests_used == 3
    assert len(transport.calls) == 3
    assert clock.sleeps[:2] == [2.0, 4.0]


def test_minimum_interval_between_requests(tmp_path: Path) -> None:
    clock = FakeClock()
    transport = FakeTransport(sample_responder, clock=clock)
    run_acquisition(small_window(4), tmp_path, transport, clock)
    assert all(
        b - a >= 1.0 for a, b in zip(transport.call_times, transport.call_times[1:], strict=False)
    )
    with pytest.raises(DatasetIntegrityError, match="min_interval_s"):
        AcquisitionLimits(max_bytes=1, max_requests=1, min_interval_s=0.5)


@pytest.mark.parametrize(
    ("responder", "final"),
    [
        (lambda u, m: status(503), FetchStatus.THROTTLED),
        (lambda u, m: status(429), FetchStatus.THROTTLED),
        (lambda u, m: status(500), FetchStatus.PROVIDER_ERROR),
        (lambda u, m: HttpResponse(200, b"abc", 10), FetchStatus.PARTIAL),
        (lambda u, m: ok(b"garbage-not-lzma"), FetchStatus.CORRUPTED),
        (failing, FetchStatus.TRANSPORT_FAILURE),
    ],
)
def test_bounded_retries_then_final_status(
    tmp_path: Path, responder: object, final: FetchStatus
) -> None:
    clock = FakeClock()
    transport = FakeTransport(responder, clock=clock)  # type: ignore[arg-type]
    limits = AcquisitionLimits(
        max_bytes=10**6, max_requests=400, max_retries=2, max_consecutive_failures=2
    )
    report = run_acquisition(small_window(), tmp_path, transport, clock, limits=limits)
    assert [s for _, s in report.outcomes] == [final, final]
    assert report.aborted == "consecutive failure limit reached"
    assert report.requests_used == 6
    assert clock.sleeps.count(2.0) == 2 and clock.sleeps.count(4.0) == 2
    assert not list((tmp_path / "raw").rglob("*.bi5")) if (tmp_path / "raw").exists() else True
    journal = read_journal(tmp_path)
    assert all(
        r.status is final and r.attempts == 3 and r.size_bytes == 0 for r in journal.values()
    )


def test_not_found_is_missing_without_retry(tmp_path: Path) -> None:
    clock = FakeClock()
    transport = FakeTransport(lambda u, m: status(404), clock=clock)
    report = run_acquisition(small_window(), tmp_path, transport, clock)
    assert [s for _, s in report.outcomes] == [FetchStatus.MISSING] * 3
    assert report.requests_used == 3 and report.aborted is None


def test_empty_http_200_is_not_automatically_a_closure(tmp_path: Path) -> None:
    saturday = replace(
        WINDOW,
        instruments=("EURUSD",),
        tick_start_ms=hour_ms(2012, 3, 16, 23),
        tick_end_ms=hour_ms(2012, 3, 17, 1),
        candle_months=((2012, 3),),
    )
    clock = FakeClock()
    transport = FakeTransport(lambda u, m: ok(b""), clock=clock)
    report = run_acquisition(saturday, tmp_path, transport, clock)
    assert [s for _, s in report.outcomes] == [
        FetchStatus.EMPTY_UNEXPLAINED,
        FetchStatus.EXPECTED_CLOSURE,
        FetchStatus.EMPTY_UNEXPLAINED,
        FetchStatus.EMPTY_UNEXPLAINED,
    ]
    assert (tmp_path / "raw/dukascopy/EURUSD/ticks/2012/03/17/00h_ticks.bi5").read_bytes() == b""


def test_resume_skips_verified_files_and_refuses_unverified(tmp_path: Path) -> None:
    clock = FakeClock()
    run_acquisition(small_window(), tmp_path, FakeTransport(sample_responder, clock=clock), clock)
    second = FakeTransport(sample_responder, clock=clock)
    report = run_acquisition(small_window(), tmp_path, second, clock)
    assert [s for _, s in report.outcomes] == [FetchStatus.SKIPPED_VERIFIED] * 3
    assert second.calls == []
    target = tmp_path / "raw/dukascopy/EURUSD/ticks/2012/03/12/01h_ticks.bi5"
    target.write_bytes(b"tampered")
    third = FakeTransport(sample_responder, clock=clock)
    report = run_acquisition(small_window(), tmp_path, third, clock)
    assert report.aborted is not None and "refusing to overwrite" in report.aborted
    assert target.read_bytes() == b"tampered"
    report = run_acquisition(small_window(), tmp_path, third, clock, allow_overwrite=True)
    assert report.aborted is None and target.read_bytes() != b"tampered"


def test_limits_cannot_exceed_window(tmp_path: Path) -> None:
    clock = FakeClock()
    with pytest.raises(DatasetIntegrityError, match="byte ceiling"):
        run_acquisition(
            WINDOW,
            tmp_path,
            FakeTransport(sample_responder),
            clock,
            limits=AcquisitionLimits(max_bytes=WINDOW.max_bytes + 1, max_requests=1),
        )
    with pytest.raises(DatasetIntegrityError, match="request ceiling"):
        run_acquisition(
            WINDOW,
            tmp_path,
            FakeTransport(sample_responder),
            clock,
            limits=AcquisitionLimits(max_bytes=1, max_requests=WINDOW.max_requests + 1),
        )


def test_exhausted_budget_aborts_before_request(tmp_path: Path) -> None:
    clock = FakeClock()
    body = tick_payload(tick_records("EURUSD", WINDOW.tick_start_ms))
    transport = FakeTransport(lambda u, m: ok(body), clock=clock)
    limits = AcquisitionLimits(max_bytes=len(body), max_requests=10)
    report = run_acquisition(small_window(), tmp_path, transport, clock, limits=limits)
    assert report.aborted == "byte budget exhausted" and len(transport.calls) == 1


def test_atomic_write_never_overwrites_and_leaves_no_partial(tmp_path: Path) -> None:
    path = tmp_path / "a" / "b.bin"
    atomic_write_bytes(path, b"one")
    with pytest.raises(DatasetIntegrityError, match="refusing to overwrite"):
        atomic_write_bytes(path, b"two")
    atomic_write_bytes(path, b"two", overwrite=True)
    assert path.read_bytes() == b"two" and not list(tmp_path.rglob("*.partial"))
    for bad in ("../x", "/abs", "a\\b"):
        with pytest.raises(DatasetIntegrityError, match="unsafe"):
            resolve_relative(tmp_path, bad)


def test_corrupted_journal_is_rejected(tmp_path: Path) -> None:
    journal = tmp_path / "acquisition" / "journal.jsonl"
    journal.parent.mkdir(parents=True)
    journal.write_bytes(b'{"relative_path":"x"}\n')
    with pytest.raises(DatasetIntegrityError, match="journal line 1"):
        read_journal(tmp_path)


def test_limits_validation_and_backoff_cap() -> None:
    limits = AcquisitionLimits(max_bytes=1, max_requests=1)
    assert [limits.backoff(n) for n in range(7)] == [2.0, 4.0, 8.0, 16.0, 32.0, 60.0, 60.0]
    for bad in (
        {"max_bytes": 0},
        {"max_requests": 0},
        {"timeout_s": 0},
        {"max_retries": 9},
        {"backoff_base_s": 0},
        {"max_consecutive_failures": 0},
    ):
        with pytest.raises(DatasetIntegrityError):
            AcquisitionLimits(**{"max_bytes": 1, "max_requests": 1, **bad})


class _FakeHandle:
    def __init__(self, body: bytes, length: str | None, status_code: int = 200) -> None:
        self._stream = io.BytesIO(body)
        self.headers = {} if length is None else {"Content-Length": length}
        self.status = status_code

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def read(self, size: int) -> bytes:
        return self._stream.read(size)


def test_urllib_transport_contract_without_network() -> None:
    seen: list[object] = []

    def opener(request: object, timeout: float) -> _FakeHandle:
        seen.append((request, timeout))
        return _FakeHandle(b"abcdef", "6")

    response = UrllibTransport(opener).get("https://example.invalid/x", 5.0, 100)
    assert (response.status, response.body, response.declared_length) == (200, b"abcdef", 6)
    assert seen[0][0].get_header("User-agent") == "EPIP-research-D00/1"  # type: ignore[index]
    with pytest.raises(BudgetExceeded):
        UrllibTransport(lambda r, timeout: _FakeHandle(b"abcdef", "6")).get(
            "https://example.invalid/u", 5.0, 5
        )
    with pytest.raises(BudgetExceeded):
        UrllibTransport(lambda r, timeout: _FakeHandle(b"abcdef", None)).get(
            "https://example.invalid/u", 5.0, 5
        )
    unknown = UrllibTransport(lambda r, timeout: _FakeHandle(b"abc", None)).get(
        "https://example.invalid/u", 5.0, 5
    )
    assert unknown.declared_length is None and unknown.body == b"abc"


def test_urllib_transport_error_mapping() -> None:
    def http_error(request: object, timeout: float) -> object:
        raise urllib.error.HTTPError("u", 503, "busy", {}, None)  # type: ignore[arg-type]

    assert UrllibTransport(http_error).get("https://example.invalid/u", 1.0, 1).status == 503

    def url_error(request: object, timeout: float) -> object:
        raise urllib.error.URLError("down")

    with pytest.raises(TransportFailure):
        UrllibTransport(url_error).get("https://example.invalid/u", 1.0, 1)

    class _Broken(_FakeHandle):
        def read(self, size: int) -> bytes:
            raise TimeoutError("slow")

    with pytest.raises(TransportFailure):
        UrllibTransport(lambda r, timeout: _Broken(b"", "1")).get(
            "https://example.invalid/u", 1.0, 10
        )
