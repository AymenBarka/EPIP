"""P04-R01-D01-B1 offline tests: monthly windows, calendar v2, limits, budget,
quality gates, reproducibility, and isolation. Synthetic fixtures only."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from research.datasets import cli
from research.datasets.acquisition import (
    AUTHORIZED_WINDOWS,
    AuthorizedWindow,
    DailyRequestBudget,
    FetchKind,
    FetchStatus,
    HttpResponse,
    authorized_window,
    build_plan,
    read_journal,
    run_acquisition,
)
from research.datasets.batch_ops import (
    MonthStatus,
    batch_plan,
    batch_quality,
    export_manifests,
    reproduce,
    window_quality,
)
from research.datasets.batches import (
    BATCH_WINDOWS,
    D01_B1,
    OWNER_DECISIONS,
    DecisionKind,
    OwnerDecision,
    _month_window,
    batch_windows,
    governed_window,
)
from research.datasets.build import build_instrument, build_provenance
from research.datasets.calendar import (
    CALENDAR_V1,
    CALENDAR_V2,
    classify_empty,
    holiday_reference,
    is_scheduled_weekend_hour,
)
from research.datasets.canonical import csv_to_bars, gunzip
from research.datasets.contracts import (
    MS_PER_HOUR,
    BarCoverage,
    DatasetIntegrityError,
    HourStatus,
    PriceSide,
)
from research.datasets.dukascopy import TICK_RECORD, hour_start_ms, instrument
from research.datasets.ledger import ConsultationLedger
from research.datasets.registry import DatasetRegistry
from research.tests.fixtures import (
    FakeClock,
    FakeTransport,
    encode,
    hour_ms,
    month_candles,
    ok,
    status,
    tick_payload,
    tick_records,
    url_hour,
)
from research.tests.test_d00_acquisition import sample_responder

EUR_JAN = governed_window("D01-B1-EURUSD-2018-01")
XAU_MAR = governed_window("D01-B1-XAUUSD-2018-03")
Responder = Callable[[str, int], HttpResponse]


def opened(window: AuthorizedWindow, days: int | None = None) -> AuthorizedWindow:
    """Test-only copy with the gate open (synthetic transport only)."""
    end = window.tick_end_ms if days is None else window.tick_start_ms + days * 24 * MS_PER_HOUR
    return replace(window, acquisition_open=True, tick_end_ms=end)


def month_responder(overrides: dict[str, HttpResponse] | None = None) -> Responder:
    overrides = overrides or {}

    def respond(url: str, _max: int) -> HttpResponse:
        for suffix, response in overrides.items():
            if url.endswith(suffix):
                return response
        symbol = url.split("/datafeed/", maxsplit=1)[1].split("/", maxsplit=1)[0]
        if url.endswith("_candles_hour_1.bi5"):
            side = PriceSide.BID if "/BID_" in url else PriceSide.ASK
            month0 = int(url.rsplit("/", 2)[1])
            year = int(url.rsplit("/", 3)[1])
            return ok(
                month_candles(
                    symbol,
                    year,
                    month0 + 1,
                    side,
                    lambda h: not is_scheduled_weekend_hour(h)
                    and not any(url_key(h) in k for k in overrides),
                )
            )
        return ok(tick_payload(tick_records(symbol, url_hour(url))))

    return respond


def url_key(hour: int) -> str:
    from datetime import UTC, datetime

    d = datetime.fromtimestamp(hour / 1000, tz=UTC)
    return f"/{d.year:04d}/{d.month - 1:02d}/{d.day:02d}/{d.hour:02d}h_ticks.bi5"


def acquire(window: AuthorizedWindow, root: Path, responder: Responder) -> None:
    clock = FakeClock()
    run_acquisition(window, root, FakeTransport(responder, clock=clock), clock)


# --- windows and boundaries ---------------------------------------------------------
def test_d01_b1_has_exactly_twelve_instrument_months() -> None:
    windows = batch_windows(D01_B1)
    assert [w.window_id for w in windows] == [
        f"D01-B1-{s}-2018-{m:02d}" for s in ("EURUSD", "XAUUSD") for m in range(1, 7)
    ]
    assert windows[0].tick_start_ms == hour_ms(2018, 1, 1, 0)
    assert windows[5].tick_end_ms == hour_ms(2018, 7, 1, 0)
    for w in windows:
        assert len(w.instruments) == 1 and w.candle_months[0][0] == 2018
        assert w.calendar_version == CALENDAR_V2 and w.skip_scheduled_weekend
        assert (w.max_planned_requests, w.max_requests, w.max_bytes) == (600, 1500, 100_000_000)
        assert w.acquisition_open is False
    assert set(AUTHORIZED_WINDOWS) == {"A01-SAMPLE-2012-03"}
    with pytest.raises(DatasetIntegrityError, match="not governance-authorized"):
        governed_window("D01-B1-EURUSD-2018-07")
    with pytest.raises(DatasetIntegrityError, match="batch"):
        batch_windows("D01-B9")
    assert governed_window("A01-SAMPLE-2012-03") is authorized_window("A01-SAMPLE-2012-03")


def test_month_and_leap_year_transitions() -> None:
    feb_2018 = _month_window("EURUSD", 2018, 2)
    assert (feb_2018.tick_end_ms - feb_2018.tick_start_ms) // MS_PER_HOUR == 28 * 24
    feb_2020 = _month_window("EURUSD", 2020, 2)
    assert (feb_2020.tick_end_ms - feb_2020.tick_start_ms) // MS_PER_HOUR == 29 * 24
    dec = _month_window("XAUUSD", 2018, 12)
    assert dec.tick_end_ms == hour_ms(2019, 1, 1, 0)
    starts = [w.tick_start_ms for w in batch_windows(D01_B1)[:6]]
    ends = [w.tick_end_ms for w in batch_windows(D01_B1)[:6]]
    assert starts[1:] == ends[:-1]


def test_plans_are_deterministic_bounded_and_skip_only_weekends() -> None:
    summary = batch_plan(D01_B1)
    assert summary["planned_requests_total"] == 6260
    assert all(row["planned_requests"] <= 600 for row in summary["windows"])
    plan = build_plan(EUR_JAN)
    assert plan == build_plan(EUR_JAN) and len(plan) == 554
    ticks = [p for p in plan if p.kind is FetchKind.TICKS]
    assert ticks[0].url.endswith("/EURUSD/2018/00/01/00h_ticks.bi5")
    requested = {p.hour_start_ms for p in ticks}
    for hour in range(EUR_JAN.tick_start_ms, EUR_JAN.tick_end_ms, MS_PER_HOUR):
        assert (hour in requested) is not is_scheduled_weekend_hour(hour)
    assert [p.side for p in plan if p.kind is FetchKind.CANDLES] == [PriceSide.BID, PriceSide.ASK]


def test_window_limits_are_validated() -> None:
    with pytest.raises(DatasetIntegrityError, match="max_planned_requests"):
        replace(EUR_JAN, max_planned_requests=2000)
    with pytest.raises(DatasetIntegrityError, match="calendar"):
        replace(EUR_JAN, calendar_version="other/1")
    with pytest.raises(DatasetIntegrityError, match="planned-request ceiling"):
        build_plan(replace(EUR_JAN, max_planned_requests=100))


# --- calendar v2 ------------------------------------------------------------------------
def test_dst_transitions_move_the_weekend_boundaries() -> None:
    # US DST began 2018-03-11 07:00 UTC: Sunday reopen at 21:00 UTC instead of 22:00.
    assert is_scheduled_weekend_hour(hour_ms(2018, 3, 4, 21))
    assert not is_scheduled_weekend_hour(hour_ms(2018, 3, 4, 22))
    assert is_scheduled_weekend_hour(hour_ms(2018, 3, 11, 20))
    assert not is_scheduled_weekend_hour(hour_ms(2018, 3, 11, 21))
    # Friday close at 22:00 UTC in winter, 21:00 UTC in summer.
    assert not is_scheduled_weekend_hour(hour_ms(2018, 3, 9, 21))
    assert is_scheduled_weekend_hour(hour_ms(2018, 3, 9, 22))
    assert is_scheduled_weekend_hour(hour_ms(2018, 3, 16, 21))
    with pytest.raises(DatasetIntegrityError, match="aligned"):
        is_scheduled_weekend_hour(hour_ms(2018, 3, 16, 21) + 1)


def test_v2_instrument_specific_breaks_and_v1_preservation() -> None:
    eur, xau = instrument("EURUSD"), instrument("XAUUSD")
    sunday_reopen = hour_ms(2018, 3, 11, 21)  # 17:00 New York, EDT
    assert classify_empty(xau, sunday_reopen, CALENDAR_V2) is HourStatus.EXPECTED_CLOSURE
    assert classify_empty(eur, sunday_reopen, CALENDAR_V2) is HourStatus.EMPTY_UNEXPLAINED
    assert classify_empty(xau, sunday_reopen, CALENDAR_V1) is HourStatus.EMPTY_UNEXPLAINED
    assert classify_empty(xau, hour_ms(2018, 3, 11, 22), CALENDAR_V2) is (
        HourStatus.EMPTY_UNEXPLAINED
    )
    wednesday_break = hour_ms(2018, 3, 14, 21)
    for version in (CALENDAR_V1, CALENDAR_V2):
        assert classify_empty(xau, wednesday_break, version) is HourStatus.EXPECTED_CLOSURE
        assert classify_empty(eur, wednesday_break, version) is HourStatus.EMPTY_UNEXPLAINED
    saturday = hour_ms(2018, 3, 10, 12)
    assert classify_empty(eur, saturday, CALENDAR_V2) is HourStatus.EXPECTED_CLOSURE
    with pytest.raises(DatasetIntegrityError, match="unsupported calendar"):
        classify_empty(eur, wednesday_break, "x/9")


def test_holidays_are_references_never_automatic_closures() -> None:
    eur = instrument("EURUSD")
    good_friday = hour_ms(2018, 3, 30, 12)
    assert classify_empty(eur, good_friday, CALENDAR_V2) is HourStatus.EMPTY_UNEXPLAINED
    reference = holiday_reference("EURUSD", good_friday, CALENDAR_V2)
    assert reference is not None and reference.name == "Good Friday" and "CME" in reference.source
    assert holiday_reference("EURUSD", good_friday, CALENDAR_V1) is None
    assert holiday_reference("EURUSD", hour_ms(2018, 3, 29, 12), CALENDAR_V2) is None
    assert holiday_reference("GBPUSD", good_friday, CALENDAR_V2) is None


# --- acquisition gate, limits, throttling, budget, resume, immutability ----------------
def test_acquisition_gate_is_closed_for_every_d01_window(tmp_path: Path) -> None:
    for window in batch_windows(D01_B1):
        with pytest.raises(DatasetIntegrityError, match="acquisition gate closed"):
            run_acquisition(window, tmp_path, FakeTransport(sample_responder), FakeClock())
    assert not any(tmp_path.iterdir())


def test_cli_refuses_gated_download_before_creating_a_transport(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden() -> object:
        raise AssertionError("transport must not be created")

    args = ["acquire", "--window", "D01-B1-EURUSD-2018-01", "--data-root", str(tmp_path)]
    assert cli.main([*args, "--confirm-provider-terms"], forbidden) == 1  # type: ignore[arg-type]
    assert "acquisition gate closed" in capsys.readouterr().err
    assert cli.main([*args, "--dry-run"], forbidden) == 0  # type: ignore[arg-type]
    plan = json.loads(capsys.readouterr().out)
    assert (plan["requests"], plan["acquisition_gate"], plan["calendar"]) == (
        554,
        "CLOSED",
        CALENDAR_V2,
    )
    assert cli.main(["batch-plan", "--batch", D01_B1], forbidden) == 0  # type: ignore[arg-type]
    assert json.loads(capsys.readouterr().out)["planned_requests_total"] == 6260
    assert not any(tmp_path.iterdir())


def test_throttling_retries_and_resume(tmp_path: Path) -> None:
    window = opened(EUR_JAN, days=3)
    hits: dict[str, int] = {}

    def flaky(url: str, budget: int) -> HttpResponse:
        hits[url] = hits.get(url, 0) + 1
        if url.endswith("/02/03h_ticks.bi5") and hits[url] <= 2:
            return status(503)
        if url.endswith("/02/04h_ticks.bi5"):
            return status(503)
        return month_responder()(url, budget)

    clock = FakeClock()
    report = run_acquisition(window, tmp_path, FakeTransport(flaky, clock=clock), clock)
    outcomes = dict(report.outcomes)
    assert outcomes["raw/dukascopy/EURUSD/ticks/2018/01/02/03h_ticks.bi5"] is FetchStatus.POPULATED
    failed = "raw/dukascopy/EURUSD/ticks/2018/01/02/04h_ticks.bi5"
    assert outcomes[failed] is FetchStatus.THROTTLED
    assert read_journal(tmp_path)[failed].detail == "HTTP 503"
    assert window_quality(window, tmp_path).status is MonthStatus.PENDING_ACQUISITION
    raw = tmp_path / "raw/dukascopy/EURUSD/ticks/2018/01/01/00h_ticks.bi5"
    before = (raw.read_bytes(), raw.stat().st_mtime_ns)
    second = run_acquisition(window, tmp_path, FakeTransport(month_responder(), clock=clock), clock)
    assert dict(second.outcomes)[failed] is FetchStatus.POPULATED
    assert sum(1 for _, s in second.outcomes if s is not FetchStatus.SKIPPED_VERIFIED) == 1
    assert (raw.read_bytes(), raw.stat().st_mtime_ns) == before


def test_daily_budget_persists_across_runs_and_days(tmp_path: Path) -> None:
    window = opened(EUR_JAN, days=1)
    clock = FakeClock()
    budget = DailyRequestBudget(tmp_path, ceiling=5)
    first = run_acquisition(
        window, tmp_path, FakeTransport(month_responder(), clock=clock), clock, daily_budget=budget
    )
    assert first.aborted == "daily request ceiling reached" and first.requests_used == 5
    again = DailyRequestBudget(tmp_path, ceiling=5)
    assert again.used("2026-11-22") == 5
    second = run_acquisition(
        window, tmp_path, FakeTransport(month_responder(), clock=clock), clock, daily_budget=again
    )
    assert second.aborted == "daily request ceiling reached" and second.requests_used == 0
    assert again.used("2026-11-23") == 0 and again.try_consume("2026-11-23", window.window_id)
    path = tmp_path / "acquisition/daily_requests.jsonl"
    assert len(path.read_text().splitlines()) == 6
    with path.open("a") as handle:
        handle.write("{broken\n")
    with pytest.raises(DatasetIntegrityError, match="daily request ledger line 7"):
        DailyRequestBudget(tmp_path).used("2026-11-22")
    with pytest.raises(DatasetIntegrityError, match="daily ceiling"):
        DailyRequestBudget(tmp_path, ceiling=0)


def test_unverified_existing_raw_file_is_never_overwritten(tmp_path: Path) -> None:
    window = opened(EUR_JAN, days=1)
    target = tmp_path / "raw/dukascopy/EURUSD/ticks/2018/01/01/00h_ticks.bi5"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"owner file")
    clock = FakeClock()
    report = run_acquisition(window, tmp_path, FakeTransport(month_responder(), clock=clock), clock)
    assert report.aborted is not None and "refusing to overwrite" in report.aborted
    assert target.read_bytes() == b"owner file"


# --- monthly quality gates ------------------------------------------------------------
def test_full_synthetic_month_passes_and_bars_span_weekends(tmp_path: Path) -> None:
    window = opened(EUR_JAN)
    acquire(window, tmp_path, month_responder())
    quality = window_quality(window, tmp_path)
    assert quality.status is MonthStatus.PASS and quality.build is not None
    counts = dict(quality.hour_status_counts)
    assert counts["POPULATED"] == 552 and counts["EXPECTED_CLOSURE_SCHEDULED_WEEKEND"] == 192
    registry = DatasetRegistry(tmp_path)
    tick = registry.verify(quality.build.tick_dataset_id)
    assert tick.coverage.hours_expected == 744
    assert (tick.coverage.hours_populated, tick.coverage.hours_expected_closure) == (552, 192)
    codes = [d.code for d in tick.diagnostics]
    assert codes == ["SESSION_CALENDAR", "SCHEDULED_CLOSURE_NOT_REQUESTED"]
    assert tick.diagnostics[0].message == CALENDAR_V2
    for bar_id in quality.build.bar_dataset_ids:
        bars = csv_to_bars(
            gunzip((tmp_path / registry.verify(bar_id).content.relative_path).read_bytes()),
            instrument("EURUSD"),
        )
        assert bars and all(b.coverage is BarCoverage.COMPLETE for b in bars)
        assert {b.side for b in bars} == {PriceSide.BID, PriceSide.ASK}
    assert quality.build.crosscheck_status == "CONSISTENT"
    assert ConsultationLedger(tmp_path).records() == ()


def test_holiday_gap_needs_an_explicit_owner_decision(tmp_path: Path) -> None:
    window = opened(XAU_MAR)
    good_friday = url_key(hour_ms(2018, 3, 30, 12))
    acquire(window, tmp_path, month_responder({good_friday: ok(b"")}))
    pending = window_quality(window, tmp_path)
    assert pending.status is MonthStatus.NEEDS_OWNER_DECISION
    assert pending.undecided_hours == ("2018-03-30T12:00:00Z",)
    decision = OwnerDecision(
        window.window_id,
        "2018-03-30T12:00:00Z",
        DecisionKind.DECLARE_EXPECTED_CLOSURE,
        "test source",
        "provider empty on Good Friday",
        "2026-11-24",
    )
    decided = window_quality(window, tmp_path, (decision,))
    assert decided.status is MonthStatus.PASS and decided.build is not None
    tick = DatasetRegistry(tmp_path).verify(decided.build.tick_dataset_id)
    codes = [d.code for d in tick.diagnostics]
    assert "HOLIDAY_REFERENCE" in codes and "OWNER_DECISION" in codes
    assert dict(tick.hour_classification)[hour_ms(2018, 3, 30, 12)] is HourStatus.EXPECTED_CLOSURE
    assert decided.detail == "cross-check CONSISTENT"


def test_decisions_must_match_observations(tmp_path: Path) -> None:
    window = opened(EUR_JAN, days=7)
    acquire(window, tmp_path, month_responder())

    def decide(kind: DecisionKind, hour: str = "2018-01-01T05:00:00Z") -> OwnerDecision:
        return OwnerDecision(window.window_id, hour, kind, "s", "r", "2026-11-24")

    with pytest.raises(DatasetIntegrityError, match="does not match an observed empty hour"):
        build_instrument(
            window,
            "EURUSD",
            tmp_path,
            {},
            decisions=(decide(DecisionKind.DECLARE_EXPECTED_CLOSURE),),
        )
    with pytest.raises(DatasetIntegrityError, match="does not match a failed hour"):
        build_instrument(
            window, "EURUSD", tmp_path, {}, decisions=(decide(DecisionKind.DECLARE_MISSING),)
        )
    with pytest.raises(DatasetIntegrityError, match="outside"):
        build_instrument(
            window,
            "EURUSD",
            tmp_path,
            {},
            decisions=(decide(DecisionKind.DECLARE_MISSING, "2018-01-20T05:00:00Z"),),
        )
    duplicate = (decide(DecisionKind.DECLARE_MISSING), decide(DecisionKind.DECLARE_MISSING))
    with pytest.raises(DatasetIntegrityError, match="duplicate owner decision"):
        build_instrument(window, "EURUSD", tmp_path, {}, decisions=duplicate)
    other = OwnerDecision(
        "D01-B1-EURUSD-2018-02", "", DecisionKind.EXCLUDE_MONTH, "s", "r", "2026-11-24"
    )
    with pytest.raises(DatasetIntegrityError, match="another window"):
        build_instrument(window, "EURUSD", tmp_path, {}, decisions=(other,))
    exclude = replace(other, window_id=window.window_id)
    with pytest.raises(DatasetIntegrityError, match="excluded by an owner decision"):
        build_instrument(window, "EURUSD", tmp_path, {}, decisions=(exclude,))
    assert window_quality(window, tmp_path, (exclude,)).status is MonthStatus.EXCLUDED
    weekend = decide(DecisionKind.DECLARE_MISSING, "2018-01-06T12:00:00Z")
    with pytest.raises(DatasetIntegrityError, match="outside the plan"):
        build_instrument(window, "EURUSD", tmp_path, {}, decisions=(weekend,))


def test_owner_decision_contract() -> None:
    assert OWNER_DECISIONS == ()
    good = ("D01-B1-EURUSD-2018-01", "2018-01-02T03:00:00Z")
    for bad in (
        ("A01-SAMPLE-2012-03", good[1], DecisionKind.DECLARE_MISSING, "s", "r", "2026-11-24"),
        (*good, "MISSING", "s", "r", "2026-11-24"),
        (*good, DecisionKind.DECLARE_MISSING, "", "r", "2026-11-24"),
        (*good, DecisionKind.DECLARE_MISSING, "s", "r", "24/11/2026"),
        (good[0], "2018-01-02T03:30:00Z", DecisionKind.DECLARE_MISSING, "s", "r", "2026-11-24"),
        (*good, DecisionKind.EXCLUDE_MONTH, "s", "r", "2026-11-24"),
    ):
        with pytest.raises(DatasetIntegrityError):
            OwnerDecision(*bad)  # type: ignore[arg-type]
    assert OwnerDecision(*good, DecisionKind.DECLARE_MISSING, "s", "r", "2026-11-24").hour_ms == (
        hour_start_ms(2018, 1, 2, 3)
    )


def test_missing_hours_block_until_declared_then_bars_are_incomplete(tmp_path: Path) -> None:
    window = opened(EUR_JAN, days=3)
    gap = url_key(hour_ms(2018, 1, 2, 5))
    acquire(window, tmp_path, month_responder({gap: status(404)}))
    assert window_quality(window, tmp_path).status is MonthStatus.PENDING_ACQUISITION
    decision = OwnerDecision(
        window.window_id,
        "2018-01-02T05:00:00Z",
        DecisionKind.DECLARE_MISSING,
        "provider 404 in three separate runs",
        "declared missing",
        "2026-11-24",
    )
    quality = window_quality(window, tmp_path, (decision,))
    assert quality.status is MonthStatus.PASS  # declared by the owner; affected bars flagged
    result = build_instrument(
        window, "EURUSD", tmp_path, build_provenance(window), decisions=(decision,)
    )
    registry = DatasetRegistry(tmp_path)
    tick = registry.verify(result.tick_dataset_id)
    assert dict(tick.hour_classification)[hour_ms(2018, 1, 2, 5)] is HourStatus.MISSING
    h4 = csv_to_bars(
        gunzip(
            (
                tmp_path / registry.verify(result.bar_dataset_ids[1]).content.relative_path
            ).read_bytes()
        ),
        instrument("EURUSD"),
    )
    incomplete = [b for b in h4 if b.coverage is BarCoverage.INCOMPLETE]
    assert {b.start_ms for b in incomplete} == {hour_ms(2018, 1, 2, 4)}


@pytest.mark.parametrize("kind", ["duplicate", "garbage"])
def test_duplicate_or_corrupted_ticks_stop_the_month(tmp_path: Path, kind: str) -> None:
    window = opened(EUR_JAN, days=2)
    hour = hour_ms(2018, 1, 1, 9)
    if kind == "duplicate":
        record = tick_records("EURUSD", hour)[0]
        payload = encode(TICK_RECORD.pack(*record) * 2)
    else:
        payload = b"\x00garbage"
    acquire(window, tmp_path, month_responder({url_key(hour): ok(payload)}))
    quality = window_quality(window, tmp_path)
    assert quality.status is MonthStatus.STOPPED_CORRUPTED
    assert "policy amendment" in quality.detail


def test_crosscheck_blocks_eurusd_and_reports_xauusd(tmp_path: Path) -> None:
    for window_id, expected in (
        ("D01-B1-EURUSD-2018-01", MonthStatus.BLOCKED_CROSSCHECK),
        ("D01-B1-XAUUSD-2018-01", MonthStatus.PASS),
    ):
        window = opened(governed_window(window_id), days=3)
        root = tmp_path / window_id
        symbol = window.instruments[0]

        def skewed(url: str, budget: int, symbol: str = symbol) -> HttpResponse:
            if url.endswith("_candles_hour_1.bi5"):
                side = PriceSide.BID if "/BID_" in url else PriceSide.ASK
                body = month_candles(symbol, 2018, 1, side, lambda h: h == hour_ms(2018, 1, 1, 2))
                return ok(body)
            return month_responder()(url, budget)

        acquire(window, root, skewed)
        quality = window_quality(window, root)
        assert quality.status is expected
        assert quality.build is not None
        assert quality.build.crosscheck_status == "DEVIATIONS_REPORTED"


# --- reproducibility, manifests, registry, CLI -----------------------------------------
def test_fresh_root_reproduction_and_manifest_export(tmp_path: Path) -> None:
    window = opened(EUR_JAN, days=4)
    data = tmp_path / "data"
    acquire(window, data, month_responder())
    result = reproduce(window, data, tmp_path / "fresh")
    assert result["identical"] is True
    assert len(result["instruments"]["EURUSD"]["dataset_ids"]) == 4
    with pytest.raises(DatasetIntegrityError, match="fresh root must be empty"):
        reproduce(window, data, tmp_path / "fresh")
    written = export_manifests(window, data, tmp_path / "manifests")
    assert len(written) == 4
    for path in written:
        assert path.read_bytes() == (data / "registry" / path.name).read_bytes()
        text = path.read_text()
        assert '"dataset_id"' in text and "bid_points" not in text
    tampered = data / "registry" / written[0].name
    tampered.write_bytes(
        tampered.read_bytes().replace(b'"schema_version":1', b'"schema_version":2')
    )
    with pytest.raises(DatasetIntegrityError):
        export_manifests(window, data, tmp_path / "again")


def test_cli_batch_quality_reproduce_and_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    window = opened(EUR_JAN, days=2)
    windows = (window, *batch_windows(D01_B1)[1:])
    monkeypatch.setitem(BATCH_WINDOWS, D01_B1, windows)
    import research.datasets.batches as batches_module

    monkeypatch.setitem(batches_module._BY_ID, window.window_id, window)
    data = tmp_path / "data"
    acquire(window, data, month_responder())
    common = ["--window", window.window_id, "--data-root", str(data)]
    assert cli.main(["build", *common]) == 0  # same provenance: no registry collision later
    capsys.readouterr()
    assert cli.main(["batch-quality", "--batch", D01_B1, "--data-root", str(data)]) == 2
    summary = json.loads(capsys.readouterr().out)
    statuses = [m["status"] for m in summary["months"]]
    assert statuses[0] == "PASS" and set(statuses[1:]) == {"PENDING_ACQUISITION"}
    assert summary["all_pass"] is False and len(summary["months"][0]["dataset_ids"]) == 4
    assert batch_quality(D01_B1, data)[0].status is MonthStatus.PASS
    assert cli.main(["reproduce", *common, "--fresh-root", str(tmp_path / "f")]) == 0
    assert json.loads(capsys.readouterr().out)["identical"] is True
    assert cli.main(["export-manifests", *common, "--destination", str(tmp_path / "m")]) == 0
    assert len(json.loads(capsys.readouterr().out)["manifests"]) == 4
    monkeypatch.setitem(BATCH_WINDOWS, D01_B1, (window,))
    assert cli.main(["batch-quality", "--batch", D01_B1, "--data-root", str(data)]) == 0
    capsys.readouterr()


def test_reproduce_reports_a_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    window = opened(EUR_JAN, days=2)
    data = tmp_path / "data"
    acquire(window, data, month_responder())
    import research.datasets.batch_ops as ops

    real = build_instrument
    calls = {"n": 0}

    def drifting(*args: object, **kwargs: object) -> object:
        calls["n"] += 1
        result = real(*args, **kwargs)  # type: ignore[arg-type]
        if calls["n"] == 2:
            return replace(result, tick_dataset_id="0" * 64)
        return result

    monkeypatch.setattr(ops, "build_instrument", drifting)
    result = reproduce(window, data, tmp_path / "fresh")
    assert result["identical"] is False
    assert result["instruments"]["EURUSD"]["reproduced"] is False


def test_d00_identities_are_unchanged_by_d01(tmp_path: Path) -> None:
    """Synthetic D00 build identities recorded before D01 changes (calendar v1 path)."""
    expected = {
        "EURUSD": [
            "69fad0d8e4a220a42a3bc577284176d7c03f277ec1a5cc80781df8085a116a5e",
            "3ea52ca3c48044c0dc04d590ce92c0b017eb6306ca8b841ed85ad2334ea61756",
            "ef52544254daab4320aff6aa0942224107f7c3340e814739d813214c2728060a",
            "883fadcf0c323738b967f75d0a08871a5d77a32397e063e13b2be1750325e496",
        ],
        "XAUUSD": [
            "cd14c03140640155336372ad13bd8918047d65def05574b8e484f98b7ed4f4c1",
            "2e63d1824c80ba4a4ab5cd7cf629e5e5a9f3e66cf586844e165ec837b79ca67d",
            "8e359c465dc91c8cdf2085ba4672767d25271f3e12872f00656650ed36d339ae",
            "69d002f88a67eefcf36468ba26e11bf54f5eb4d96bbeed5e227c7b0506a17cb5",
        ],
    }
    window = authorized_window("A01-SAMPLE-2012-03")
    assert window.calendar_version == CALENDAR_V1 and not window.skip_scheduled_weekend
    assert len(build_plan(window)) == 244
    acquire(window, tmp_path, sample_responder)
    for symbol, ids in expected.items():
        r = build_instrument(window, symbol, tmp_path, {"builder": "test"})
        assert [r.tick_dataset_id, *r.bar_dataset_ids, r.candle_dataset_id] == ids


def test_datasets_package_stays_isolated_from_production() -> None:
    root = Path(__file__).resolve().parents[2] / "research" / "datasets"
    pattern = re.compile(
        r"^\s*(from|import)\s+(epip|research\.elliott_causal|research\.harness)\b", re.MULTILINE
    )
    assert [p.name for p in root.rglob("*.py") if pattern.search(p.read_text("utf-8"))] == []
