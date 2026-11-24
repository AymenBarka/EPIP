"""E00 governed data access, CLI, isolation and performance (requirements 19, 22-24)."""

from __future__ import annotations

import ast
import json
import re
import runpy
import socket
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest

import research.elliott_causal.dataset as dataset_module
from research.datasets.build import build_instrument
from research.datasets.canonical import csv_to_bars
from research.datasets.contracts import (
    BarCoverage,
    DatasetIntegrityError,
    Partition,
    PriceSide,
)
from research.datasets.ledger import ConsultationLedger
from research.elliott_causal import cli
from research.elliott_causal.contracts import ResearchContractError
from research.elliott_causal.dataset import AUTHORIZED_TECHNICAL_H1, load_technical_bars
from research.elliott_causal.pipeline import generated_bars, run_pipeline
from research.tests.conftest import NetworkForbiddenError
from research.tests.fixtures import status
from research.tests.test_d00_acquisition import sample_responder
from research.tests.test_d00_pipeline_cli_isolation import PROVENANCE, WINDOW, acquire

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "research" / "elliott_causal"
AT = "2026-11-24T06:00:00Z"


@pytest.fixture(scope="module")
def registry_root(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, str]]:
    root = tmp_path_factory.mktemp("e00-data")
    acquire(root)
    ids: dict[str, str] = {}
    for symbol in WINDOW.instruments:
        result = build_instrument(WINDOW, symbol, root, PROVENANCE)
        ids[symbol] = result.bar_dataset_ids[0]
        ids[f"{symbol}-ticks"] = result.tick_dataset_id
    return root, ids


def load(root: Path, dataset_id: str, symbol: str, **kw: object) -> object:
    return load_technical_bars(
        root,
        dataset_id,
        PriceSide.BID,
        experiment_id="test-e00",
        consulted_at_utc=AT,
        outputs=("test",),
        authorized={dataset_id: symbol},
        **kw,  # type: ignore[arg-type,unused-ignore]
    )


def test_registry_load_records_the_consultation_first(
    registry_root: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    root, ids = registry_root
    before = len(ConsultationLedger(root).records())
    series = load_technical_bars(
        root,
        ids["EURUSD"],
        PriceSide.BID,
        experiment_id="test-e00",
        consulted_at_utc=AT,
        outputs=("test",),
        authorized={ids["EURUSD"]: "EURUSD"},
    )
    assert len(series.bars) == 120 and series.instrument == "EURUSD"
    assert [b.index for b in series.bars] == list(range(120))
    records = ConsultationLedger(root).records()
    assert len(records) == before + 1
    record = records[-1]
    assert (record.dataset_id, record.partition, record.experiment_id) == (
        ids["EURUSD"],
        Partition.TECHNICAL,
        "test-e00",
    )
    assert record.dataset_digest == series.canonical_sha256
    published = run_pipeline(series.bars, symbol="EURUSD")
    assert all(p.event.available_ms <= series.bars[-1].end_ms for p in published)


def test_ledger_is_written_before_canonical_content_is_read(
    registry_root: tuple[Path, dict[str, str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, ids = registry_root
    seen: list[int] = []

    def spy(data: bytes) -> bytes:
        seen.append(len(ConsultationLedger(root).records()))
        raise RuntimeError("stop after the ledger check")

    before = len(ConsultationLedger(root).records())
    monkeypatch.setattr(dataset_module, "gunzip", spy)
    with pytest.raises(RuntimeError):
        load(root, ids["XAUUSD"], "XAUUSD")
    assert seen == [before + 1]


# 24. no OOS consultation ---------------------------------------------------------------
def test_only_authorized_technical_datasets_are_readable(
    registry_root: tuple[Path, dict[str, str]],
) -> None:
    root, ids = registry_root
    before = len(ConsultationLedger(root).records())
    with pytest.raises(ResearchContractError, match="not an authorized TECHNICAL H1 dataset"):
        load_technical_bars(
            root,
            ids["EURUSD"],
            PriceSide.BID,
            experiment_id="x",
            consulted_at_utc=AT,
            outputs=("x",),
        )
    with pytest.raises(ResearchContractError, match="tick-derived H1 bar datasets only"):
        load(root, ids["EURUSD-ticks"], "EURUSD")
    with pytest.raises(ResearchContractError, match="instrument differs"):
        load(root, ids["EURUSD"], "XAUUSD")
    assert len(ConsultationLedger(root).records()) == before


def test_authorized_ids_are_exactly_the_d00_technical_h1_identities() -> None:
    closure = (REPO / "docs/project/P04_R01_D00_DATASET_CLOSURE.md").read_text("utf-8")
    rows = re.findall(
        r"\| (EURUSD|XAUUSD) \| H1 bars \(from ticks\) \|.*`([0-9a-f]{64})` \|", closure
    )
    assert {dataset_id: symbol for symbol, dataset_id in rows} == AUTHORIZED_TECHNICAL_H1
    source = "\n".join(p.read_text("utf-8") for p in PACKAGE.glob("*.py"))
    assert "Partition.TECHNICAL" in source
    for other in ("DEVELOPMENT", "VALIDATION", "FINAL_OOS"):
        assert f"Partition.{other}" not in source


# 19. incomplete source coverage --------------------------------------------------------
def test_incomplete_coverage_is_refused_before_consultation(tmp_path: Path) -> None:
    def responder(url: str, budget: int) -> object:
        if url.endswith("/EURUSD/2012/02/13/05h_ticks.bi5"):
            return status(404)
        return sample_responder(url, budget)

    acquire(tmp_path, responder)
    result = build_instrument(WINDOW, "EURUSD", tmp_path, PROVENANCE, allow_incomplete=True)
    with pytest.raises(ResearchContractError, match="incomplete source coverage"):
        load(tmp_path, result.bar_dataset_ids[0], "EURUSD")
    assert ConsultationLedger(tmp_path).records() == ()


def test_incomplete_bars_and_tampering_are_refused(
    registry_root: tuple[Path, dict[str, str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, ids = registry_root
    monkeypatch.setattr(
        dataset_module,
        "csv_to_bars",
        lambda data, spec: tuple(
            replace(b, coverage=BarCoverage.INCOMPLETE) for b in csv_to_bars(data, spec)
        ),
    )
    with pytest.raises(ResearchContractError, match="INCOMPLETE bars are refused"):
        load(root, ids["EURUSD"], "EURUSD")
    monkeypatch.setattr(dataset_module, "csv_to_bars", lambda data, spec: ())
    with pytest.raises(ResearchContractError, match="no bar on the requested side"):
        load(root, ids["EURUSD"], "EURUSD")
    monkeypatch.setattr(dataset_module, "gunzip", lambda data: b"forged")
    with pytest.raises(ResearchContractError, match="canonical digest differs"):
        load(root, ids["EURUSD"], "EURUSD")


def test_tampered_files_fail_registry_verification(tmp_path: Path) -> None:
    acquire(tmp_path)
    result = build_instrument(WINDOW, "EURUSD", tmp_path, PROVENANCE)
    (content,) = (tmp_path / "canonical/bars").glob("EURUSD_*_H1_*.csv.gz")
    content.write_bytes(content.read_bytes() + b"x")
    with pytest.raises(DatasetIntegrityError):
        load(tmp_path, result.bar_dataset_ids[0], "EURUSD")
    assert ConsultationLedger(tmp_path).records() == ()


# CLI -----------------------------------------------------------------------------------
def test_cli_technical_report_is_deterministic_and_non_economic(
    registry_root: tuple[Path, dict[str, str]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, ids = registry_root
    for real_id in list(AUTHORIZED_TECHNICAL_H1):
        monkeypatch.delitem(AUTHORIZED_TECHNICAL_H1, real_id)
    monkeypatch.setitem(AUTHORIZED_TECHNICAL_H1, ids["EURUSD"], "EURUSD")
    monkeypatch.setitem(AUTHORIZED_TECHNICAL_H1, ids["XAUUSD"], "XAUUSD")
    before = len(ConsultationLedger(root).records())
    args = ["technical", "--data-root", str(root)]
    assert cli.main(args, clock=lambda: AT) == 0
    first = json.loads(capsys.readouterr().out)
    assert cli.main(args, clock=lambda: "2026-11-24T07:00:00Z") == 0
    second = json.loads(capsys.readouterr().out)
    assert first == second
    report = (root / first["report"]).read_bytes()
    assert json.loads(report)["experiment_id"] == first["experiment_id"]
    assert len(ConsultationLedger(root).records()) == before + 4
    for item in first["datasets"]:
        metrics = item["metrics"]
        assert item["partition"] == "TECHNICAL"
        assert metrics["prefix_invariance"] == {"checked_bars": 120, "violations": 0}
        assert metrics["anchor_continuity_failures"] == 0
    text = report.decode().lower()
    for word in ("profit", "drawdown", "win_rate", "expectancy", "r_multiple", "pnl", "return"):
        assert word not in text


def test_cli_errors_and_benchmark(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["technical", "--data-root", str(tmp_path)]) == 1
    assert "ERROR:" in capsys.readouterr().err
    assert cli.main(["benchmark", "--bars", "3000", "--seed", "2"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["bars"] == 3000 and result["deterministic_rerun"] is True
    assert cli.main(["benchmark", "--bars", "500", "--no-qualify"]) == 0
    assert json.loads(capsys.readouterr().out)["qualified"] is False


def test_module_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["research.elliott_causal", "benchmark", "--bars", "300"])
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("research.elliott_causal", run_name="__main__")
    assert caught.value.code == 0


# 22. no network, 23. no production modification ----------------------------------------
def test_network_is_forbidden() -> None:
    with pytest.raises(NetworkForbiddenError):
        socket.create_connection(("example.com", 443))


def test_research_package_never_subclasses_or_patches_production() -> None:
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        epip_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("epip"):
                assert not any(part.startswith("_") for part in node.module.split(".")), path
                epip_names.update(alias.asname or alias.name for alias in node.names)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = {b.id for b in node.bases if isinstance(b, ast.Name)}
                assert not bases & epip_names, f"{path.name}: {node.name} subclasses production"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"setattr", "delattr"}, path
            if isinstance(node, ast.Attribute):
                assert node.attr != "__setattr__", path
    pattern = re.compile(r"^\s*(from|import)\s+research\b", re.MULTILINE)
    assert [p for p in (REPO / "epip").rglob("*.py") if pattern.search(p.read_text("utf-8"))] == []


def test_frozen_f01_identities_are_unchanged() -> None:
    from epip.strategy_profiles.elliott_fibonacci import RULE_IDENTITIES

    contract = (
        REPO / "docs/project/P04_F01_R01_ELLIOTT_FIBONACCI_WAVE3_SETUP_QUALIFICATION_CONTRACT.md"
    ).read_text("utf-8")
    table = dict(re.findall(r"\| `([a-z0-9.-]+)` \| `([0-9a-f]{64})` \|", contract))
    assert len(table) == 5
    assert {k: RULE_IDENTITIES[k].fingerprint for k in table} == table


# performance (indicative, generous bound for CI runners) -----------------------------------
def test_prototype_throughput_on_generated_series() -> None:
    bars = generated_bars(20_000, 11)
    started = time.perf_counter()
    published = run_pipeline(bars)
    assert time.perf_counter() - started < 30.0
    assert len(published) > 1000


def test_technical_metrics_on_generated_series_without_prefix_check() -> None:
    from research.elliott_causal.contracts import EngineConfig
    from research.elliott_causal.metrics import technical_metrics

    metrics = technical_metrics(
        generated_bars(3000, 4), "XAUUSD", EngineConfig(), check_prefix=False
    )
    assert metrics["prefix_invariance"] is None
    assert metrics["anchor_continuity_failures"] == 0
    restrictions = metrics["frozen_f01_restrictions"]
    assert restrictions and all(k.startswith("FAITHFUL:") for k in restrictions)
    assert metrics["confirmed_pivots"] == metrics["count_searches"]
    assert (
        sum(metrics["eligible_candidates_per_utc_day"].values())
        == metrics["eligible_w1w2_candidates"]
    )


def test_benchmark_detects_a_non_deterministic_run(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls = iter(((), (object(),)))
    monkeypatch.setattr(cli, "run_pipeline", lambda bars, qualify_counts: next(calls))
    assert cli.main(["benchmark", "--bars", "50"]) == 1
    assert "not deterministic" in capsys.readouterr().err
