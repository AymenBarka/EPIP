"""Governed access to the D00 technical sample (registry and ledger only).

Order of operations, all fail-closed:

1. the reference must be one of the authorized TECHNICAL H1 bar datasets;
2. the registry re-verifies every file of the manifest;
3. the manifest must declare complete coverage (no unexplained or failed hour);
4. the consultation is appended to the governed ledger **before** any
   canonical content is read;
5. the canonical bytes are re-hashed and parsed by the D00 reader; any
   INCOMPLETE bar is refused.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from research.datasets.canonical import csv_to_bars, gunzip, sha256_hex
from research.datasets.contracts import BarCoverage, Granularity, Partition, PriceSide
from research.datasets.dukascopy import instrument
from research.datasets.ledger import Consultation, ConsultationLedger
from research.datasets.registry import DatasetRegistry
from research.datasets.storage import resolve_relative
from research.elliott_causal.contracts import PriceBar, require

# D00 closure section 19: the only datasets E00 may read (TECHNICAL partition).
AUTHORIZED_TECHNICAL_H1: dict[str, str] = {
    "a4c33c19042a167c87928e934d46a6a90996616b25bd38567b38963428a05d31": "EURUSD",
    "ce4d98346a842b077e7b11a0320c471ca7e7dad87e8653d0385976ea60adff5a": "XAUUSD",
}
PURPOSE = "P04-R01-E00 technical validation of the causal Elliott prototype (no performance)"


@dataclass(frozen=True, slots=True)
class TechnicalSeries:
    dataset_id: str
    canonical_sha256: str
    instrument: str
    side: PriceSide
    bars: tuple[PriceBar, ...]


def load_technical_bars(
    data_root: Path,
    dataset_id: str,
    side: PriceSide,
    *,
    experiment_id: str,
    consulted_at_utc: str,
    outputs: tuple[str, ...],
    authorized: dict[str, str] = AUTHORIZED_TECHNICAL_H1,
) -> TechnicalSeries:
    symbol = authorized.get(dataset_id)
    require(symbol is not None, f"dataset {dataset_id} is not an authorized TECHNICAL H1 dataset")
    assert symbol is not None
    require(type(side) is PriceSide, "side invalid")
    manifest = DatasetRegistry(data_root).verify(dataset_id)
    require(manifest.dataset_id == dataset_id, "registry returned another dataset")
    require(
        manifest.dataset_kind == "BARS" and manifest.granularity is Granularity.H1,
        "E00 consumes tick-derived H1 bar datasets only",
    )
    require(manifest.instrument == symbol, "dataset instrument differs from the authorization")
    require(
        manifest.coverage.hours_unexplained_or_failed == 0,
        "incomplete source coverage: the manifest declares unexplained or failed hours",
    )
    ConsultationLedger(data_root).append(
        Consultation(
            dataset_id,
            manifest.content.canonical_sha256,
            experiment_id,
            PURPOSE,
            consulted_at_utc,
            Partition.TECHNICAL,
            outputs,
        )
    )
    canonical = gunzip(resolve_relative(data_root, manifest.content.relative_path).read_bytes())
    require(sha256_hex(canonical) == manifest.content.canonical_sha256, "canonical digest differs")
    spec = instrument(symbol)
    rows = [b for b in csv_to_bars(canonical, spec) if b.side is side]
    require(bool(rows), "dataset has no bar on the requested side")
    require(
        all(b.coverage is BarCoverage.COMPLETE for b in rows),
        "incomplete source coverage: INCOMPLETE bars are refused",
    )
    scale = 10**spec.price_decimals
    bars = tuple(
        PriceBar(
            i,
            b.start_ms,
            b.end_ms,
            b.open_points / scale,
            b.high_points / scale,
            b.low_points / scale,
            b.close_points / scale,
        )
        for i, b in enumerate(sorted(rows, key=lambda x: x.start_ms))
    )
    return TechnicalSeries(dataset_id, manifest.content.canonical_sha256, symbol, side, bars)
