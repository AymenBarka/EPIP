"""Offline dataset build from acquired raw files (no network).

For each instrument of an authorized window:

1. classify every source hour from the journal and the raw bytes on disk;
2. decode and validate ticks of POPULATED hours (fail closed);
3. write the canonical tick dataset (deterministic gzip CSV) and manifest;
4. derive H1 and H4 BID/ASK bars with lineage to the tick dataset;
5. decode provider H1 candles and write their own dataset;
6. cross-check derived H1 against provider H1 and write a report;
7. register every manifest in the local registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from research.datasets.acquisition import (
    STORED_STATUSES,
    AuthorizedWindow,
    FetchKind,
    FetchStatus,
    JournalRecord,
    PlannedFetch,
    build_plan,
    read_journal,
)
from research.datasets.aggregate import aggregate
from research.datasets.canonical import (
    bars_to_csv,
    deterministic_gzip,
    sha256_hex,
    ticks_to_csv,
)
from research.datasets.contracts import (
    BAR_NORMALIZATION_VERSION,
    MANIFEST_SCHEMA_VERSION,
    MS_PER_HOUR,
    TICK_NORMALIZATION_VERSION,
    Bar,
    BarCoverage,
    ContentIdentity,
    Coverage,
    Diagnostic,
    Granularity,
    HourStatus,
    InstrumentSpec,
    PriceSide,
    Provider,
    RawArtifact,
    Severity,
    SourceFormat,
    Tick,
    require,
)
from research.datasets.crosscheck import CrossCheckReport, crosscheck_h1
from research.datasets.dukascopy import (
    ProviderCandle,
    decode_candles,
    decode_ticks,
    instrument,
    month_start_ms,
)
from research.datasets.manifest import DatasetManifest, canonical_json, provenance_of
from research.datasets.registry import DatasetRegistry
from research.datasets.storage import atomic_write_bytes, resolve_relative

_FETCH_TO_HOUR = {
    FetchStatus.POPULATED: HourStatus.POPULATED,
    FetchStatus.EXPECTED_CLOSURE: HourStatus.EXPECTED_CLOSURE,
    FetchStatus.EMPTY_UNEXPLAINED: HourStatus.EMPTY_UNEXPLAINED,
    FetchStatus.MISSING: HourStatus.MISSING,
    FetchStatus.PROVIDER_ERROR: HourStatus.PROVIDER_ERROR,
    FetchStatus.THROTTLED: HourStatus.THROTTLED,
    FetchStatus.CORRUPTED: HourStatus.CORRUPTED,
    FetchStatus.PARTIAL: HourStatus.PARTIAL,
    FetchStatus.TRANSPORT_FAILURE: HourStatus.PROVIDER_ERROR,
}


@dataclass(frozen=True, slots=True)
class BuildResult:
    instrument: str
    tick_dataset_id: str
    bar_dataset_ids: tuple[str, ...]
    candle_dataset_id: str | None
    crosscheck_status: str | None
    diagnostics: tuple[Diagnostic, ...]


def _write_deterministic(path: Path, data: bytes) -> None:
    if path.exists():
        require(path.read_bytes() == data, f"existing {path.name} differs from rebuilt bytes")
        return
    atomic_write_bytes(path, data)


def _source(
    data_root: Path, item: PlannedFetch, journal_status: FetchStatus | None, fmt: SourceFormat
) -> tuple[RawArtifact | None, HourStatus, bytes]:
    if journal_status is None:
        return None, HourStatus.NOT_ACQUIRED, b""
    status = _FETCH_TO_HOUR.get(journal_status, HourStatus.NOT_ACQUIRED)
    if journal_status not in STORED_STATUSES:
        return None, status, b""
    path = resolve_relative(data_root, item.relative_path)
    require(path.is_file(), f"journal lists {item.relative_path} but the file is missing")
    raw = path.read_bytes()
    return RawArtifact(item.relative_path, fmt, len(raw), sha256_hex(raw), status), status, raw


def _content(data_root: Path, relative: str, canonical: bytes) -> ContentIdentity:
    compressed = deterministic_gzip(canonical)
    _write_deterministic(resolve_relative(data_root, relative), compressed)
    return ContentIdentity(
        relative, sha256_hex(canonical), sha256_hex(compressed), canonical.count(b"\n") - 1
    )


def build_instrument(
    window: AuthorizedWindow,
    symbol: str,
    data_root: Path,
    provenance: dict[str, str],
) -> BuildResult:
    spec: InstrumentSpec = instrument(symbol)
    require(symbol in window.instruments, f"{symbol} not in window {window.window_id}")
    plan = [p for p in build_plan(window) if p.instrument == symbol]
    journal = read_journal(data_root)
    diagnostics: list[Diagnostic] = []
    sources: list[RawArtifact] = []
    hours: dict[int, HourStatus] = {}
    ticks: list[Tick] = []
    for item in (p for p in plan if p.kind is FetchKind.TICKS):
        assert item.hour_start_ms is not None
        record = journal.get(item.relative_path)
        artifact, status, raw = _source(
            data_root, item, record.status if record else None, SourceFormat.DUKASCOPY_TICKS_BI5
        )
        if artifact is not None:
            require(
                record is not None and artifact.raw_sha256 == record.raw_sha256,
                f"raw checksum differs from journal for {item.relative_path}",
            )
            sources.append(artifact)
        if status is HourStatus.POPULATED:
            ticks.extend(decode_ticks(raw, item.hour_start_ms))
        elif status is not HourStatus.EXPECTED_CLOSURE:
            diagnostics.append(
                Diagnostic(
                    f"HOUR_{status.value}",
                    Severity.WARNING,
                    "source hour not complete",
                    item.relative_path,
                )
            )
        hours[item.hour_start_ms] = status
    statuses = list(hours.values())
    populated = statuses.count(HourStatus.POPULATED)
    closure = statuses.count(HourStatus.EXPECTED_CLOSURE)
    coverage = Coverage(
        window.tick_start_ms,
        window.tick_end_ms,
        len(statuses),
        populated,
        closure,
        len(statuses) - populated - closure,
    )
    tag = f"{symbol}_{window.window_id}"
    tick_content = _content(
        data_root, f"canonical/ticks/{tag}_ticks.csv.gz", ticks_to_csv(ticks, spec)
    )
    common = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "provider": Provider.DUKASCOPY,
        "instrument": symbol,
        "price_decimals": spec.price_decimals,
        "coverage": coverage,
        "hour_classification": tuple(sorted(hours.items())),
        "provenance": provenance_of(provenance),
    }
    tick_manifest = DatasetManifest(
        dataset_kind="TICKS",
        granularity=Granularity.TICK,
        sides=(PriceSide.BID, PriceSide.ASK),
        source_format=SourceFormat.DUKASCOPY_TICKS_BI5,
        normalization_version=TICK_NORMALIZATION_VERSION,
        sources=tuple(sources),
        content=tick_content,
        lineage=(),
        diagnostics=tuple(diagnostics),
        **common,  # type: ignore[arg-type]
    )
    registry = DatasetRegistry(data_root)
    registry.register(tick_manifest)
    bar_ids: list[str] = []
    derived_h1: tuple[Bar, ...] = ()
    for granularity in (Granularity.H1, Granularity.H4):
        bars = aggregate(ticks, PriceSide.BID, granularity, hours) + aggregate(
            ticks, PriceSide.ASK, granularity, hours
        )
        if granularity is Granularity.H1:
            derived_h1 = bars
        incomplete = sum(1 for b in bars if b.coverage is BarCoverage.INCOMPLETE)
        content = _content(
            data_root, f"canonical/bars/{tag}_{granularity.value}.csv.gz", bars_to_csv(bars, spec)
        )
        bar_manifest = DatasetManifest(
            dataset_kind="BARS",
            granularity=granularity,
            sides=(PriceSide.BID, PriceSide.ASK),
            source_format=SourceFormat.DERIVED_FROM_TICKS,
            normalization_version=BAR_NORMALIZATION_VERSION,
            sources=(),
            content=content,
            lineage=(tick_manifest.dataset_id,),
            diagnostics=(
                (
                    Diagnostic(
                        "INCOMPLETE_BARS",
                        Severity.WARNING,
                        f"{incomplete} bars flagged INCOMPLETE",
                        granularity.value,
                    ),
                )
                if incomplete
                else ()
            ),
            **common,  # type: ignore[arg-type]
        )
        registry.register(bar_manifest)
        bar_ids.append(bar_manifest.dataset_id)
    candle_id, xstatus = _candles(
        window, spec, plan, journal, data_root, derived_h1, common, tag, registry
    )
    return BuildResult(
        symbol, tick_manifest.dataset_id, tuple(bar_ids), candle_id, xstatus, tuple(diagnostics)
    )


def _candles(
    window: AuthorizedWindow,
    spec: InstrumentSpec,
    plan: list[PlannedFetch],
    journal: dict[str, JournalRecord],
    data_root: Path,
    derived_h1: tuple[Bar, ...],
    common: dict[str, object],
    tag: str,
    registry: DatasetRegistry,
) -> tuple[str | None, str | None]:
    candles: list[ProviderCandle] = []
    sources: list[RawArtifact] = []
    for item in (p for p in plan if p.kind is FetchKind.CANDLES):
        assert item.side is not None
        record = journal.get(item.relative_path)
        artifact, hour_status, raw = _source(
            data_root,
            item,
            record.status if record else None,
            SourceFormat.DUKASCOPY_CANDLES_H1_BI5,
        )
        if artifact is None or hour_status is not HourStatus.POPULATED:
            return None, None
        sources.append(artifact)
        candles.extend(decode_candles(raw, item.year, item.month, item.side))
    if not sources:
        return None, None
    report = crosscheck_h1(derived_h1, candles, window.tick_start_ms, window.tick_end_ms)
    first = min(month_start_ms(y, m) for y, m in window.candle_months)
    last = max(month_start_ms(y + (m == 12), m % 12 + 1) for y, m in window.candle_months)
    expected = (last - first) // MS_PER_HOUR
    quoted = {c.start_ms for c in candles if c.volume_micro > 0}
    both_sides = sum(
        1
        for t in quoted
        if all(
            any(c.start_ms == t and c.side is s and c.volume_micro > 0 for c in candles)
            for s in (PriceSide.BID, PriceSide.ASK)
        )
    )
    candle_coverage = Coverage(first, last, expected, both_sides, 0, expected - both_sides)
    canonical = bars_to_csv(
        tuple(
            Bar(
                c.start_ms,
                c.start_ms + MS_PER_HOUR,
                c.side,
                c.open_points,
                c.high_points,
                c.low_points,
                c.close_points,
                0,
                BarCoverage.COMPLETE,
            )
            for c in candles
            if c.volume_micro > 0
        ),
        spec,
    )
    content = _content(data_root, f"canonical/provider_candles/{tag}_H1.csv.gz", canonical)
    manifest = DatasetManifest(
        dataset_kind="PROVIDER_CANDLES",
        granularity=Granularity.H1,
        sides=(PriceSide.BID, PriceSide.ASK),
        source_format=SourceFormat.DUKASCOPY_CANDLES_H1_BI5,
        normalization_version=BAR_NORMALIZATION_VERSION,
        sources=tuple(sources),
        content=content,
        lineage=(),
        diagnostics=(
            Diagnostic(
                "PROVIDER_FILLER_EXCLUDED",
                Severity.INFO,
                "zero-volume provider candles are not canonical rows",
                "candles",
            ),
        ),
        schema_version=MANIFEST_SCHEMA_VERSION,
        provider=Provider.DUKASCOPY,
        instrument=spec.symbol,
        price_decimals=spec.price_decimals,
        coverage=candle_coverage,
        hour_classification=(),
        provenance=common["provenance"],  # type: ignore[arg-type]
    )
    registry.register(manifest)
    _write_deterministic(
        resolve_relative(data_root, f"reports/{tag}_crosscheck_H1.json"), report_json(report)
    )
    return manifest.dataset_id, report.status


def report_json(report: CrossCheckReport) -> bytes:
    return canonical_json(
        {
            "policy_version": report.policy_version,
            "tolerance_points": report.tolerance_points,
            "window_start_ms": report.window_start_ms,
            "window_end_ms": report.window_end_ms,
            "status": report.status,
            "compared": report.compared,
            "matched": report.matched,
            "deviations": [
                [d.start_ms, d.side.value, d.field, d.derived_points, d.provider_points]
                for d in report.deviations
            ],
            "missing_in_derived": [[t, s.value] for t, s in report.missing_in_derived],
            "missing_in_provider": [[t, s.value] for t, s in report.missing_in_provider],
            "provider_filler": [[t, s.value] for t, s in report.provider_filler],
            "incomplete_derived": [[t, s.value] for t, s in report.incomplete_derived],
        }
    )
