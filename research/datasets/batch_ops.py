"""Batch planning, monthly quality gates, reproduction, and manifest export.

Built only on the D00 primitives (plan, journal, build, registry); no network.
"""

from __future__ import annotations

import shutil
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from research.datasets.acquisition import (
    JOURNAL_RELATIVE_PATH,
    STORED_STATUSES,
    AuthorizedWindow,
    FetchKind,
    FetchStatus,
    build_plan,
    pending_items,
    read_journal,
)
from research.datasets.batches import (
    OWNER_DECISIONS,
    DecisionKind,
    OwnerDecision,
    batch_windows,
    decisions_for,
)
from research.datasets.build import BuildResult, build_instrument, build_provenance
from research.datasets.calendar import classify_empty, is_scheduled_weekend_hour
from research.datasets.canonical import format_timestamp
from research.datasets.contracts import MS_PER_HOUR, HourStatus, require
from research.datasets.dukascopy import instrument
from research.datasets.registry import DatasetRegistry
from research.datasets.storage import resolve_relative

# D00 evidence (closure section 18): raw bytes per instrument-hour and the
# effective throughput observed under provider throttling.
D00_RAW_BYTES_PER_HOUR = 19_200
D00_FILES_PER_HOUR = (150, 250)
CANONICAL_TO_RAW_RATIO = 1.8


class MonthStatus(StrEnum):
    PASS = "PASS"
    PENDING_ACQUISITION = "PENDING_ACQUISITION"
    NEEDS_OWNER_DECISION = "NEEDS_OWNER_DECISION"
    STOPPED_CORRUPTED = "STOPPED_CORRUPTED"
    BLOCKED_CROSSCHECK = "BLOCKED_CROSSCHECK"
    EXCLUDED = "EXCLUDED"


def batch_plan(batch_id: str) -> dict[str, Any]:
    windows = batch_windows(batch_id)
    rows = []
    total = ticks_total = 0
    for w in windows:
        plan = build_plan(w)
        ticks = sum(1 for p in plan if p.kind is FetchKind.TICKS)
        hours = (w.tick_end_ms - w.tick_start_ms) // MS_PER_HOUR
        rows.append(
            {
                "window": w.window_id,
                "planned_requests": len(plan),
                "tick_files": ticks,
                "candle_files": len(plan) - ticks,
                "weekend_hours_not_requested": hours - ticks,
                "max_planned_requests": w.max_planned_requests,
                "max_requests_per_run": w.max_requests,
                "max_bytes_per_run": w.max_bytes,
                "calendar": w.calendar_version,
                "acquisition_gate": "OPEN" if w.acquisition_open else "CLOSED",
            }
        )
        total += len(plan)
        ticks_total += ticks
    raw = ticks_total * D00_RAW_BYTES_PER_HOUR
    return {
        "batch": batch_id,
        "windows": rows,
        "planned_requests_total": total,
        "estimates_from_d00_evidence": {
            "raw_bytes": raw,
            "canonical_gzip_bytes": round(raw * CANONICAL_TO_RAW_RATIO),
            "wall_clock_hours_at_observed_throughput": [
                round(total / D00_FILES_PER_HOUR[1], 1),
                round(total / D00_FILES_PER_HOUR[0], 1),
            ],
            "minimum_hours_at_one_request_per_second": round(total / 3600, 2),
            "basis": "2012 sample density; 2018 density is measured by the batch itself",
        },
    }


@dataclass(frozen=True, slots=True)
class MonthQuality:
    window_id: str
    status: MonthStatus
    detail: str
    hour_status_counts: tuple[tuple[str, int], ...]
    undecided_hours: tuple[str, ...]
    build: BuildResult | None


def _hour_text(hour_ms: int) -> str:
    return format_timestamp(hour_ms)[:13] + ":00:00Z"


def window_quality(
    window: AuthorizedWindow,
    data_root: Path,
    decisions: tuple[OwnerDecision, ...] | None = None,
) -> MonthQuality:
    """Gate one instrument-month (Q00-G00 section 6.6). Builds only when clean."""
    chosen = decisions_for(window.window_id) if decisions is None else decisions
    if any(d.kind is DecisionKind.EXCLUDE_MONTH for d in chosen):
        return MonthQuality(window.window_id, MonthStatus.EXCLUDED, "owner decision", (), (), None)
    decided = {d.hour_ms: d for d in chosen}
    journal = read_journal(data_root)
    counts: Counter[str] = Counter()
    undecided: list[str] = []
    corrupted: list[str] = []
    for item in build_plan(window):
        if item.kind is not FetchKind.TICKS:
            continue
        assert item.hour_start_ms is not None
        record = journal.get(item.relative_path)
        status = record.status if record else None
        if status is FetchStatus.CORRUPTED:
            corrupted.append(item.relative_path)
        if status in (FetchStatus.EMPTY_UNEXPLAINED, FetchStatus.EXPECTED_CLOSURE):
            hour = classify_empty(
                instrument(item.instrument), item.hour_start_ms, window.calendar_version
            )
            counts[hour.value] += 1
            if hour is HourStatus.EMPTY_UNEXPLAINED and item.hour_start_ms not in decided:
                undecided.append(_hour_text(item.hour_start_ms))
        else:
            counts[status.value if status else "NOT_ACQUIRED"] += 1
    weekend = sum(
        1
        for h in range(window.tick_start_ms, window.tick_end_ms, MS_PER_HOUR)
        if window.skip_scheduled_weekend and is_scheduled_weekend_hour(h)
    )
    counts["EXPECTED_CLOSURE_SCHEDULED_WEEKEND"] = weekend
    frozen_counts = tuple(sorted(counts.items()))
    if corrupted:
        return MonthQuality(
            window.window_id,
            MonthStatus.STOPPED_CORRUPTED,
            f"{len(corrupted)} corrupted or duplicate-tick hours: acquisition stops; "
            "a policy amendment is required",
            frozen_counts,
            tuple(undecided),
            None,
        )
    declared_missing = {
        p.relative_path
        for p in build_plan(window)
        if p.hour_start_ms is not None
        and (d := decided.get(p.hour_start_ms)) is not None
        and d.kind is DecisionKind.DECLARE_MISSING
    }
    pending = [p for p in pending_items(window, data_root) if p not in declared_missing]
    if pending:
        return MonthQuality(
            window.window_id,
            MonthStatus.PENDING_ACQUISITION,
            f"{len(pending)} planned items not stored; relaunch acquire",
            frozen_counts,
            tuple(undecided),
            None,
        )
    if undecided:
        return MonthQuality(
            window.window_id,
            MonthStatus.NEEDS_OWNER_DECISION,
            f"{len(undecided)} unexplained empty hours need an owner decision",
            frozen_counts,
            tuple(undecided),
            None,
        )
    symbol = window.instruments[0]
    result = build_instrument(
        window,
        symbol,
        data_root,
        build_provenance(window),
        decisions=tuple(chosen),
    )
    if symbol == "EURUSD" and result.crosscheck_status != "CONSISTENT":
        return MonthQuality(
            window.window_id,
            MonthStatus.BLOCKED_CROSSCHECK,
            f"EURUSD H1 cross-check {result.crosscheck_status}: investigate before use",
            frozen_counts,
            (),
            result,
        )
    detail = (
        "XAUUSD cross-check differences reported, values unaltered"
        if result.crosscheck_status == "DEVIATIONS_REPORTED"
        else f"cross-check {result.crosscheck_status}"
    )
    return MonthQuality(window.window_id, MonthStatus.PASS, detail, frozen_counts, (), result)


def batch_quality(
    batch_id: str, data_root: Path, decisions: tuple[OwnerDecision, ...] = OWNER_DECISIONS
) -> tuple[MonthQuality, ...]:
    return tuple(
        window_quality(w, data_root, tuple(d for d in decisions if d.window_id == w.window_id))
        for w in batch_windows(batch_id)
    )


def _dataset_ids(result: BuildResult) -> tuple[str, ...]:
    ids = [result.tick_dataset_id, *result.bar_dataset_ids]
    if result.candle_dataset_id is not None:
        ids.append(result.candle_dataset_id)
    return tuple(ids)


def reproduce(
    window: AuthorizedWindow,
    data_root: Path,
    fresh_root: Path,
    decisions: tuple[OwnerDecision, ...] | None = None,
) -> dict[str, Any]:
    """Rebuild from copies of the original raw files in an empty root and compare."""
    require(not fresh_root.exists() or not any(fresh_root.iterdir()), "fresh root must be empty")
    journal = read_journal(data_root)
    for item in build_plan(window):
        record = journal.get(item.relative_path)
        if record is not None and record.status in STORED_STATUSES:
            source = resolve_relative(data_root, item.relative_path)
            target = resolve_relative(fresh_root, item.relative_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    journal_target = resolve_relative(fresh_root, JOURNAL_RELATIVE_PATH)
    journal_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(resolve_relative(data_root, JOURNAL_RELATIVE_PATH), journal_target)
    provenance = build_provenance(window)
    out: dict[str, Any] = {"window": window.window_id, "instruments": {}}
    identical = True
    for symbol in window.instruments:
        original = build_instrument(window, symbol, data_root, provenance, decisions=decisions)
        rebuilt = build_instrument(window, symbol, fresh_root, provenance, decisions=decisions)
        same = _dataset_ids(original) == _dataset_ids(rebuilt)
        a, b = DatasetRegistry(data_root), DatasetRegistry(fresh_root)
        hashes_same = (
            all(
                a.resolve(i).content.canonical_sha256 == b.resolve(i).content.canonical_sha256
                for i in _dataset_ids(rebuilt)
            )
            if same
            else False
        )
        identical &= same and hashes_same
        out["instruments"][symbol] = {
            "dataset_ids": list(_dataset_ids(original)),
            "reproduced": same and hashes_same,
        }
    out["identical"] = identical
    return out


def export_manifests(
    window: AuthorizedWindow,
    data_root: Path,
    destination: Path,
    decisions: tuple[OwnerDecision, ...] | None = None,
) -> tuple[Path, ...]:
    """Copy the canonical manifest JSON (hashes, coverage, diagnostics; no market
    data) of every dataset of ``window`` for committing under
    ``research/datasets/manifests/`` (G00 section 8)."""
    registry = DatasetRegistry(data_root)
    provenance = build_provenance(window)
    written = []
    for symbol in window.instruments:
        result = build_instrument(window, symbol, data_root, provenance, decisions=decisions)
        for dataset_id in _dataset_ids(result):
            registry.verify(dataset_id)
            data = resolve_relative(data_root, f"registry/{dataset_id}.json").read_bytes()
            target = destination / window.window_id / f"{dataset_id}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            written.append(target)
    return tuple(written)
