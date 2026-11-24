"""Command-line interface (Windows and POSIX): ``python -m research.datasets``.

Subcommands:

- ``plan``      offline: print the deterministic acquisition plan (no network);
- ``acquire``   bounded download of an authorized window (``--dry-run`` is offline);
- ``build``     offline: decode, validate, normalize, aggregate, cross-check, register;
- ``registry``  offline: ``list``, ``inspect REF``, ``verify REF``;
- ``mt5-import`` offline: import a local MT5 bars/ticks export;
- ``ledger``    offline: show the conservative OOS status of an instrument.

Real acquisition additionally requires ``--confirm-provider-terms``, recording
that the owner verified the provider's terms of use (A01 section 7).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path

from research.datasets.acquisition import (
    SystemClock,
    Transport,
    UrllibTransport,
    authorized_window,
    build_plan,
    limits_for,
    pending_items,
    run_acquisition,
)
from research.datasets.build import build_instrument
from research.datasets.canonical import deterministic_gzip, sha256_hex
from research.datasets.contracts import (
    MANIFEST_SCHEMA_VERSION,
    ContentIdentity,
    Coverage,
    DatasetIntegrityError,
    Granularity,
    HourStatus,
    InstrumentSpec,
    PriceSide,
    Provider,
    RawArtifact,
    Severity,
    SourceFormat,
)
from research.datasets.ledger import instrument_status
from research.datasets.manifest import DatasetManifest, provenance_of
from research.datasets.mt5 import (
    MT5_NORMALIZATION_VERSION,
    OffsetSegment,
    ServerTimeConvention,
    canonical_bars_csv,
    canonical_ticks_csv,
    fixed_offset_convention,
    import_bars,
    import_ticks,
)
from research.datasets.registry import DatasetRegistry
from research.datasets.storage import atomic_write_bytes, resolve_relative


def _print(payload: object) -> None:
    sys.stdout.write(json.dumps(payload, sort_keys=True, indent=2) + "\n")


def _plan(args: argparse.Namespace) -> int:
    window = authorized_window(args.window)
    plan = build_plan(window)
    _print(
        {
            "window": window.window_id,
            "authority": window.authority,
            "requests": len(plan),
            "max_bytes": window.max_bytes,
            "max_requests": window.max_requests,
            "items": [[p.kind.value, p.instrument, p.url, p.relative_path] for p in plan],
        }
    )
    return 0


def _acquire(args: argparse.Namespace, transport_factory: Callable[[], Transport]) -> int:
    window = authorized_window(args.window)
    if args.dry_run:
        return _plan(args)
    if not args.confirm_provider_terms:
        raise DatasetIntegrityError(
            "real acquisition requires --confirm-provider-terms (A01 section 7)"
        )
    data_root = Path(args.data_root)
    report = run_acquisition(
        window,
        data_root,
        transport_factory(),
        SystemClock(),
        limits=replace(limits_for(window), timeout_s=args.timeout_seconds),
        allow_overwrite=args.allow_overwrite,
    )
    pending = pending_items(window, data_root)
    _print(
        {
            "window": report.window_id,
            "planned": report.planned,
            "requests_used": report.requests_used,
            "bytes_used": report.bytes_used,
            "aborted": report.aborted,
            "outcomes": [[path, status.value] for path, status in report.outcomes],
            "complete": not pending,
            "pending": list(pending),
        }
    )
    if pending:
        print(
            f"ACQUISITION INCOMPLETE: {len(pending)} of {report.planned} items pending. "
            "Relaunch the same acquire command; do not run build yet.",
            file=sys.stderr,
        )
        return 2
    print(
        f"ACQUISITION COMPLETE: all {report.planned} items stored. Next: build.",
        file=sys.stderr,
    )
    return 0


def _build(args: argparse.Namespace) -> int:
    window = authorized_window(args.window)
    provenance = {"builder": "research.datasets.build", "window": window.window_id}
    results = [
        build_instrument(
            window,
            symbol,
            Path(args.data_root),
            provenance,
            allow_incomplete=args.allow_incomplete,
        )
        for symbol in window.instruments
    ]
    _print(
        [
            {
                "instrument": r.instrument,
                "tick_dataset_id": r.tick_dataset_id,
                "bar_dataset_ids": list(r.bar_dataset_ids),
                "candle_dataset_id": r.candle_dataset_id,
                "crosscheck_status": r.crosscheck_status,
                "warnings": [
                    [d.code, d.location] for d in r.diagnostics if d.severity is Severity.WARNING
                ],
            }
            for r in results
        ]
    )
    return 0


def _registry(args: argparse.Namespace) -> int:
    registry = DatasetRegistry(Path(args.data_root))
    if args.action == "list":
        _print([asdict(e) for e in registry.list()])
        return 0
    if not args.reference:
        raise DatasetIntegrityError("a dataset reference is required")
    manifest = (
        registry.verify(args.reference)
        if args.action == "verify"
        else registry.inspect(args.reference)
    )
    _print(
        {
            "dataset_id": manifest.dataset_id,
            "verified": args.action == "verify",
            "identity": manifest.identity(),
        }
    )
    return 0


def _convention(args: argparse.Namespace) -> ServerTimeConvention | None:
    if args.offset_table:
        rows = json.loads(Path(args.offset_table).read_text(encoding="utf-8"))
        segments = tuple(
            OffsetSegment(
                datetime.strptime(r["effective_from_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=UTC
                ),
                int(r["offset_minutes"]),
            )
            for r in rows
        )
        return ServerTimeConvention(args.broker, f"table:{Path(args.offset_table).name}", segments)
    if args.utc_offset_minutes is not None:
        if not args.offset_source:
            raise DatasetIntegrityError("--offset-source must document the offset evidence")
        return fixed_offset_convention(args.broker, args.utc_offset_minutes, args.offset_source)
    return None


def _mt5_import(args: argparse.Namespace) -> int:
    data_root = Path(args.data_root)
    raw = Path(args.file).read_bytes()
    spec = InstrumentSpec(args.symbol, Provider.MT5, args.symbol, args.decimals)
    convention = _convention(args)
    if args.kind == "ticks":
        result = import_ticks(raw, args.broker, spec, convention)
        canonical = canonical_ticks_csv(result)
        start = result.ticks[0].timestamp_ms
        end = result.ticks[-1].timestamp_ms + 1
        rows_kind, granularity, fmt = "MT5_TICKS", Granularity.TICK, SourceFormat.MT5_TICKS_CSV
        sides: tuple[PriceSide, ...] = (PriceSide.BID, PriceSide.ASK)
    else:
        side = PriceSide(args.side) if args.side else None
        result = import_bars(raw, args.broker, spec, side, convention)
        canonical = canonical_bars_csv(result)
        start = result.bars[0].start_ms
        end = result.bars[-1].start_ms + 1
        rows_kind, granularity, fmt = (
            "MT5_BARS",
            Granularity(args.timeframe),
            SourceFormat.MT5_BARS_CSV,
        )
        assert side is not None
        sides = (side,)
    broker_dir = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.broker)
    raw_relative = f"raw/mt5/{broker_dir}/{sha256_hex(raw)}_{Path(args.file).name}"
    raw_path = resolve_relative(data_root, raw_relative)
    if not raw_path.exists():
        atomic_write_bytes(raw_path, raw)
    compressed = deterministic_gzip(canonical)
    content_relative = f"canonical/mt5/{broker_dir}/{sha256_hex(canonical)}.csv.gz"
    content_path = resolve_relative(data_root, content_relative)
    if not content_path.exists():
        atomic_write_bytes(content_path, compressed)
    manifest = DatasetManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        dataset_kind=rows_kind,
        provider=Provider.MT5,
        instrument=args.symbol,
        price_decimals=args.decimals,
        granularity=granularity,
        sides=sides,
        source_format=fmt,
        normalization_version=MT5_NORMALIZATION_VERSION,
        coverage=Coverage(start, end, 0, 0, 0, 0),
        sources=(RawArtifact(raw_relative, fmt, len(raw), sha256_hex(raw), HourStatus.POPULATED),),
        content=ContentIdentity(
            content_relative,
            sha256_hex(canonical),
            sha256_hex(compressed),
            canonical.count(b"\n") - 1,
        ),
        lineage=(),
        hour_classification=(),
        diagnostics=(),
        provenance=provenance_of(
            {"broker": args.broker, "time_convention": result.convention_source}
        ),
    )
    status = DatasetRegistry(data_root).register(manifest)
    _print({"dataset_id": manifest.dataset_id, "registry": status})
    return 0


def _ledger(args: argparse.Namespace) -> int:
    _print({"instrument": args.instrument, "status": instrument_status(args.instrument).value})
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="python -m research.datasets")
    sub = root.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--window", required=True)
    a = sub.add_parser("acquire")
    a.add_argument("--window", required=True)
    a.add_argument("--data-root", default="data")
    a.add_argument("--dry-run", action="store_true")
    a.add_argument("--confirm-provider-terms", action="store_true")
    a.add_argument("--allow-overwrite", action="store_true")
    a.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="per-request timeout, 1 to 120 seconds (default 30)",
    )
    b = sub.add_parser("build")
    b.add_argument("--window", required=True)
    b.add_argument("--data-root", default="data")
    b.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="diagnostic build despite pending acquisition items (coverage stays explicit)",
    )
    r = sub.add_parser("registry")
    r.add_argument("action", choices=("list", "inspect", "verify"))
    r.add_argument("reference", nargs="?")
    r.add_argument("--data-root", default="data")
    m = sub.add_parser("mt5-import")
    m.add_argument("--kind", choices=("ticks", "bars"), required=True)
    m.add_argument("--file", required=True)
    m.add_argument("--broker", required=True)
    m.add_argument("--symbol", required=True)
    m.add_argument("--decimals", type=int, required=True)
    m.add_argument("--side", choices=("BID", "ASK"))
    m.add_argument("--timeframe", choices=("H1", "H4"), default="H1")
    m.add_argument("--utc-offset-minutes", type=int)
    m.add_argument("--offset-source")
    m.add_argument("--offset-table")
    m.add_argument("--data-root", default="data")
    lg = sub.add_parser("ledger")
    lg.add_argument("instrument")
    return root


def main(
    argv: Sequence[str] | None = None,
    transport_factory: Callable[[], Transport] = UrllibTransport,
) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "plan":
            return _plan(args)
        if args.command == "acquire":
            return _acquire(args, transport_factory)
        if args.command == "build":
            return _build(args)
        if args.command == "registry":
            return _registry(args)
        if args.command == "mt5-import":
            return _mt5_import(args)
        return _ledger(args)
    except DatasetIntegrityError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1
