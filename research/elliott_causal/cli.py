"""Command line: ``python -m research.elliott_causal``.

- ``technical``  reads the authorized D00 TECHNICAL H1 datasets through the
  registry, records each consultation in the ledger first, and writes a
  deterministic technical report under ``<data-root>/reports/`` (never in Git);
- ``benchmark``  times the prototype on a deterministic generated series.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import tracemalloc
from collections.abc import Callable, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from research.datasets.contracts import DatasetIntegrityError, PriceSide
from research.datasets.manifest import canonical_json
from research.datasets.storage import atomic_write_bytes, resolve_relative
from research.elliott_causal.contracts import EngineConfig, ResearchContractError
from research.elliott_causal.dataset import AUTHORIZED_TECHNICAL_H1, load_technical_bars
from research.elliott_causal.metrics import technical_metrics
from research.elliott_causal.pipeline import generated_bars, run_pipeline

REPORT_VERSION = "e00-technical-report/1"


def config_hash(config: EngineConfig) -> str:
    return hashlib.sha256(canonical_json(asdict(config))).hexdigest()[:16]


def _utc_now() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _technical(args: argparse.Namespace, clock: Callable[[], str]) -> int:
    root = Path(args.data_root)
    config = EngineConfig()
    experiment = f"P04-R01-E00-technical-{config_hash(config)}"
    side = PriceSide(args.side)
    datasets: list[dict[str, Any]] = []
    for dataset_id in sorted(AUTHORIZED_TECHNICAL_H1):
        series = load_technical_bars(
            root,
            dataset_id,
            side,
            experiment_id=experiment,
            consulted_at_utc=clock(),
            outputs=("technical metrics", "prefix-invariance check", "frozen F01 outcomes"),
        )
        datasets.append(
            {
                "dataset_id": series.dataset_id,
                "canonical_sha256": series.canonical_sha256,
                "instrument": series.instrument,
                "side": series.side.value,
                "partition": "TECHNICAL",
                "metrics": technical_metrics(series.bars, series.instrument, config),
            }
        )
    report = {
        "report_version": REPORT_VERSION,
        "experiment_id": experiment,
        "engine_config": asdict(config),
        "economic_metrics": "none (E00 scope)",
        "datasets": datasets,
    }
    data = canonical_json(report)
    relative = f"reports/e00_technical_{side.value}_{hashlib.sha256(data).hexdigest()[:16]}.json"
    target = resolve_relative(root, relative)
    if not target.exists():
        atomic_write_bytes(target, data)
    print(json.dumps({"report": relative, **report}, indent=2, sort_keys=True))
    return 0


def _benchmark(args: argparse.Namespace) -> int:
    bars = generated_bars(args.bars, args.seed)
    qualify_counts = not args.no_qualify
    started = time.perf_counter()
    published = run_pipeline(bars, qualify_counts=qualify_counts)
    elapsed = time.perf_counter() - started
    tracemalloc.start()
    again = run_pipeline(bars, qualify_counts=qualify_counts)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if again != published:
        raise ResearchContractError("benchmark runs are not deterministic")
    print(
        json.dumps(
            {
                "bars": len(bars),
                "seed": args.seed,
                "qualified": not args.no_qualify,
                "published_events": len(published),
                "deterministic_rerun": True,
                "seconds": round(elapsed, 3),
                "peak_traced_mib": round(peak / 2**20, 1),
                "target": "about 100,000 H1 bars in under 60 seconds (G00 16.2, indicative)",
            },
            indent=2,
        )
    )
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="python -m research.elliott_causal")
    sub = root.add_subparsers(dest="command", required=True)
    t = sub.add_parser("technical")
    t.add_argument("--data-root", default="data")
    t.add_argument("--side", choices=("BID", "ASK"), default="BID")
    b = sub.add_parser("benchmark")
    b.add_argument("--bars", type=int, default=100_000)
    b.add_argument("--seed", type=int, default=1)
    b.add_argument("--no-qualify", action="store_true")
    return root


def main(argv: Sequence[str] | None = None, clock: Callable[[], str] = _utc_now) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "technical":
            return _technical(args, clock)
        return _benchmark(args)
    except (DatasetIntegrityError, ResearchContractError) as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1
