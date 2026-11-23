"""End-to-end build, reproducibility proof, CLI, and frozen-contract isolation (35)."""

from __future__ import annotations

import json
import re
import runpy
import shutil
import socket
import sys
import urllib.request
from dataclasses import replace
from pathlib import Path

import pytest

from research.datasets import cli
from research.datasets.acquisition import FetchStatus, authorized_window, run_acquisition
from research.datasets.build import build_instrument
from research.datasets.canonical import csv_to_bars, gunzip
from research.datasets.contracts import MS_PER_HOUR, BarCoverage, DatasetIntegrityError
from research.datasets.dukascopy import instrument
from research.datasets.registry import DatasetRegistry
from research.tests.conftest import NetworkForbiddenError
from research.tests.fixtures import FakeClock, FakeTransport, hour_ms, ok
from research.tests.test_d00_acquisition import sample_responder

WINDOW = authorized_window("A01-SAMPLE-2012-03")
REPO = Path(__file__).resolve().parents[2]
PROVENANCE = {"builder": "test"}


def acquire(root: Path, responder: object = sample_responder) -> None:
    clock = FakeClock()
    report = run_acquisition(WINDOW, root, FakeTransport(responder, clock=clock), clock)  # type: ignore[arg-type]
    assert report.aborted is None


def test_end_to_end_build_registers_consistent_datasets(tmp_path: Path) -> None:
    acquire(tmp_path)
    results = [build_instrument(WINDOW, s, tmp_path, PROVENANCE) for s in WINDOW.instruments]
    registry = DatasetRegistry(tmp_path)
    entries = {e.dataset_id: e for e in registry.list()}
    assert len(entries) == 2 * 4
    for result in results:
        assert result.crosscheck_status == "CONSISTENT" and result.diagnostics == ()
        tick = registry.verify(result.tick_dataset_id)
        assert tick.coverage.hours_expected == 120 and tick.coverage.hours_populated == 120
        assert len(tick.sources) == 120
        for bar_id in result.bar_dataset_ids:
            bars = registry.verify(bar_id)
            assert bars.lineage == (result.tick_dataset_id,)
            parsed = csv_to_bars(
                gunzip((tmp_path / bars.content.relative_path).read_bytes()),
                instrument(result.instrument),
            )
            assert all(b.coverage is BarCoverage.COMPLETE for b in parsed)
        assert result.candle_dataset_id is not None
        report = json.loads(
            (
                tmp_path / f"reports/{result.instrument}_A01-SAMPLE-2012-03_crosscheck_H1.json"
            ).read_text()
        )
        assert report["status"] == "CONSISTENT" and report["compared"] == 240


def test_rebuild_is_reproducible_bit_for_bit(tmp_path: Path) -> None:
    first, second = tmp_path / "a", tmp_path / "b"
    acquire(first)
    shutil.copytree(first / "raw", second / "raw")
    shutil.copytree(first / "acquisition", second / "acquisition")
    a = build_instrument(WINDOW, "XAUUSD", first, PROVENANCE)
    b = build_instrument(WINDOW, "XAUUSD", second, {"builder": "other-machine"})
    assert (a.tick_dataset_id, a.bar_dataset_ids, a.candle_dataset_id) == (
        b.tick_dataset_id,
        b.bar_dataset_ids,
        b.candle_dataset_id,
    )
    for path in (first / "canonical").rglob("*.gz"):
        assert path.read_bytes() == (second / path.relative_to(first)).read_bytes()
    again = build_instrument(WINDOW, "XAUUSD", first, PROVENANCE)
    assert again == a


def test_incomplete_hours_are_flagged_and_crosscheck_reports(tmp_path: Path) -> None:
    gap = hour_ms(2012, 3, 13, 5)

    def responder(url: str, budget: int) -> object:
        if url.endswith("/EURUSD/2012/02/13/05h_ticks.bi5"):
            return ok(b"")
        return sample_responder(url, budget)

    acquire(tmp_path, responder)
    result = build_instrument(WINDOW, "EURUSD", tmp_path, PROVENANCE)
    assert [d.code for d in result.diagnostics] == ["HOUR_EMPTY_UNEXPLAINED"]
    assert result.crosscheck_status == "DEVIATIONS_REPORTED"
    registry = DatasetRegistry(tmp_path)
    h4 = registry.verify(result.bar_dataset_ids[1])
    assert [d.code for d in h4.diagnostics] == ["INCOMPLETE_BARS"]
    tick = registry.verify(result.tick_dataset_id)
    assert dict(tick.hour_classification)[gap].value == "EMPTY_UNEXPLAINED"
    assert tick.coverage.hours_unexplained_or_failed == 1


def test_build_without_candles_or_with_missing_raw(tmp_path: Path) -> None:
    window = replace(WINDOW, candle_months=())
    clock = FakeClock()
    run_acquisition(window, tmp_path, FakeTransport(sample_responder, clock=clock), clock)
    result = build_instrument(window, "EURUSD", tmp_path, PROVENANCE)
    assert result.candle_dataset_id is None and result.crosscheck_status is None
    (tmp_path / "raw/dukascopy/EURUSD/ticks/2012/03/12/00h_ticks.bi5").unlink()
    with pytest.raises(DatasetIntegrityError, match="file is missing"):
        build_instrument(window, "EURUSD", tmp_path, PROVENANCE)
    with pytest.raises(DatasetIntegrityError, match="not in window"):
        build_instrument(replace(window, instruments=("XAUUSD",)), "EURUSD", tmp_path, PROVENANCE)


def test_build_not_acquired_and_failed_candles(tmp_path: Path) -> None:
    def responder(url: str, budget: int) -> object:
        if "_candles_hour_1" in url:
            return ok(b"")
        return sample_responder(url, budget)

    acquire(tmp_path, responder)
    result = build_instrument(WINDOW, "EURUSD", tmp_path, PROVENANCE)
    assert result.candle_dataset_id is None
    empty_root = tmp_path / "empty"
    empty = build_instrument(WINDOW, "XAUUSD", empty_root, PROVENANCE)
    assert [d.code for d in empty.diagnostics][:1] == ["HOUR_NOT_ACQUIRED"]
    tick = DatasetRegistry(empty_root).verify(empty.tick_dataset_id)
    assert tick.content.row_count == 0 and tick.coverage.hours_populated == 0


def test_cli_plan_and_dry_run_are_offline(capsys: pytest.CaptureFixture[str]) -> None:
    def forbidden() -> object:
        raise AssertionError("transport must not be created")

    assert cli.main(["plan", "--window", "A01-SAMPLE-2012-03"], forbidden) == 0  # type: ignore[arg-type]
    plan = json.loads(capsys.readouterr().out)
    assert plan["requests"] == 244 and plan["max_bytes"] == 20_000_000
    assert cli.main(["acquire", "--window", "A01-SAMPLE-2012-03", "--dry-run"], forbidden) == 0  # type: ignore[arg-type]
    assert json.loads(capsys.readouterr().out)["requests"] == 244
    assert cli.main(["acquire", "--window", "A01-SAMPLE-2012-03"], forbidden) == 1  # type: ignore[arg-type]
    assert "--confirm-provider-terms" in capsys.readouterr().err
    assert cli.main(["plan", "--window", "OTHER"]) == 1


def test_cli_acquire_build_registry_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "SystemClock", FakeClock)
    root = str(tmp_path)
    args = [
        "acquire",
        "--window",
        "A01-SAMPLE-2012-03",
        "--data-root",
        root,
        "--confirm-provider-terms",
    ]
    assert cli.main(args, lambda: FakeTransport(sample_responder)) == 0
    acquired = json.loads(capsys.readouterr().out)
    assert acquired["aborted"] is None and acquired["requests_used"] == 244
    assert {s for _, s in acquired["outcomes"]} == {FetchStatus.POPULATED.value}
    assert cli.main(["build", "--window", "A01-SAMPLE-2012-03", "--data-root", root]) == 0
    built = json.loads(capsys.readouterr().out)
    assert [b["crosscheck_status"] for b in built] == ["CONSISTENT", "CONSISTENT"]
    assert cli.main(["registry", "list", "--data-root", root]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert len(listed) == 8
    ref = built[0]["tick_dataset_id"][:10]
    assert cli.main(["registry", "verify", ref, "--data-root", root]) == 0
    assert json.loads(capsys.readouterr().out)["verified"] is True
    assert cli.main(["registry", "inspect", ref, "--data-root", root]) == 0
    capsys.readouterr()
    assert cli.main(["registry", "inspect", "--data-root", root]) == 1
    assert cli.main(["ledger", "GBPUSD"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "UNVERIFIED — NOT ATTESTED VIRGIN"
    failing = [
        "acquire",
        "--window",
        "A01-SAMPLE-2012-03",
        "--data-root",
        str(tmp_path / "x"),
        "--confirm-provider-terms",
    ]
    assert cli.main(failing, lambda: FakeTransport(lambda u, m: ok(b"bad"))) == 2


MT5_TICKS = (
    "<DATE>\t<TIME>\t<BID>\t<ASK>\t<LAST>\t<VOLUME>\t<FLAGS>\n"
    "2012.03.12\t02:00:00.125\t1.30000\t1.30003\t\t0\t6\n"
)
MT5_BARS = (
    "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n"
    "2012.03.12\t02:00:00\t1.30000\t1.30100\t1.29900\t1.30050\t812\t0\t12\n"
)


def test_cli_mt5_import(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ticks = tmp_path / "EURUSD_ticks.csv"
    ticks.write_text(MT5_TICKS, encoding="utf-8")
    bars = tmp_path / "EURUSD_H1.csv"
    bars.write_text(MT5_BARS, encoding="utf-8")
    table = tmp_path / "offsets.json"
    table.write_text(
        json.dumps([{"effective_from_utc": "2011-01-01T00:00:00Z", "offset_minutes": 120}])
    )
    root = str(tmp_path / "data")
    base = [
        "mt5-import",
        "--broker",
        "Admirals",
        "--symbol",
        "EURUSD",
        "--decimals",
        "5",
        "--data-root",
        root,
    ]
    assert cli.main(base + ["--kind", "ticks", "--file", str(ticks)]) == 1
    assert "quarantined" in capsys.readouterr().err
    assert (
        cli.main(base + ["--kind", "ticks", "--file", str(ticks), "--utc-offset-minutes", "120"])
        == 1
    )
    assert "--offset-source" in capsys.readouterr().err
    ok_ticks = base + [
        "--kind",
        "ticks",
        "--file",
        str(ticks),
        "--utc-offset-minutes",
        "120",
        "--offset-source",
        "owner verified",
    ]
    assert cli.main(ok_ticks) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["registry"] == "registered"
    assert cli.main(ok_ticks) == 0
    assert json.loads(capsys.readouterr().out)["registry"] == "duplicate"
    ok_bars = base + [
        "--kind",
        "bars",
        "--file",
        str(bars),
        "--side",
        "BID",
        "--offset-table",
        str(table),
    ]
    assert cli.main(ok_bars) == 0
    capsys.readouterr()
    no_side = base + ["--kind", "bars", "--file", str(bars), "--offset-table", str(table)]
    assert cli.main(no_side) == 1


def test_module_entry_point(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["research.datasets", "ledger", "USDJPY"])
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("research.datasets", run_name="__main__")
    assert exit_info.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "CONSULTED"


def test_network_is_forbidden_in_research_tests() -> None:
    with pytest.raises(NetworkForbiddenError):
        socket.create_connection(("example.com", 80))
    with pytest.raises(Exception):  # noqa: B017 - urllib wraps the guard error
        urllib.request.urlopen("http://example.com", timeout=1)


def test_frozen_production_contract_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    pattern = re.compile(r"^\s*(from|import)\s+research\b", re.MULTILINE)
    offenders = [p for p in (REPO / "epip").rglob("*.py") if pattern.search(p.read_text("utf-8"))]
    assert offenders == []
    research_imports = re.compile(r"^\s*(from|import)\s+epip\b", re.MULTILINE)
    package = REPO / "research" / "datasets"
    assert [p for p in package.rglob("*.py") if research_imports.search(p.read_text("utf-8"))] == []
    from epip.core.integrity_compliance import compliance_digest, scan_immutable_dataclasses

    monkeypatch.chdir(REPO)
    entries = scan_immutable_dataclasses(Path("epip"))
    assert len(entries) == 612
    assert compliance_digest(entries) == (
        "92b40f1dfec340c886345710bf4a446b5a2dafa753b7129c12c7d3488c46f3f1"
    )


def test_hour_constant_sanity() -> None:
    assert MS_PER_HOUR == 3_600_000


def test_system_clock_contract() -> None:
    from research.datasets.acquisition import SystemClock

    clock = SystemClock()
    before = clock.monotonic()
    clock.sleep(0)
    assert clock.monotonic() >= before
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", clock.utc_now_text())


def test_missing_hour_is_reported_on_both_sides(tmp_path: Path) -> None:
    from research.tests.fixtures import status

    def responder(url: str, budget: int) -> object:
        if url.endswith("/XAUUSD/2012/02/14/09h_ticks.bi5"):
            return status(404)
        return sample_responder(url, budget)

    acquire(tmp_path, responder)
    result = build_instrument(WINDOW, "XAUUSD", tmp_path, PROVENANCE)
    assert [d.code for d in result.diagnostics] == ["HOUR_MISSING"]
    report = json.loads(
        (tmp_path / "reports/XAUUSD_A01-SAMPLE-2012-03_crosscheck_H1.json").read_text()
    )
    assert report["status"] == "DEVIATIONS_REPORTED"
    gap = hour_ms(2012, 3, 14, 9)
    assert report["missing_in_derived"] == [[gap, "ASK"], [gap, "BID"]]


def test_crosscheck_report_serializes_field_deviations() -> None:
    from research.datasets.build import report_json
    from research.datasets.contracts import PriceSide
    from research.datasets.crosscheck import (
        CROSSCHECK_POLICY_VERSION,
        CrossCheckReport,
        FieldDeviation,
    )

    report = CrossCheckReport(
        CROSSCHECK_POLICY_VERSION,
        0,
        0,
        MS_PER_HOUR,
        1,
        0,
        (FieldDeviation(0, PriceSide.ASK, "low", 5, 6),),
        (),
        (),
        (),
        (),
    )
    document = json.loads(report_json(report))
    assert document["deviations"] == [[0, "ASK", "low", 5, 6]]
    assert document["status"] == "DEVIATIONS_REPORTED"
