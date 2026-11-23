"""Storage convention and atomic, non-overwriting writes under ``data/``.

Layout (relative to the data root, normally repository-root ``data/``)::

    raw/dukascopy/<SYMBOL>/ticks/<YYYY>/<MM>/<DD>/<HH>h_ticks.bi5   immutable provider bytes
    raw/dukascopy/<SYMBOL>/candles_h1/<SIDE>/<YYYY>-<MM>.bi5        immutable provider bytes
    raw/mt5/<BROKER>/<file>                                         copied MT5 exports
    canonical/<kind>/<dataset_id-free name>.csv.gz                  deterministic gzip CSV
    manifests/<name>.json                                           canonical manifests
    registry/<dataset_id>.json                                      registered manifests
    reports/<name>.json                                             validation reports
    acquisition/journal.jsonl                                       volatile acquisition log
    ledger/consultations.jsonl                                      consultation ledger

Months and days in local paths are 1-based (the provider URL month is 0-based).
"""

from __future__ import annotations

import os
from pathlib import Path

from research.datasets.contracts import DatasetIntegrityError


def resolve_relative(data_root: Path, relative_path: str) -> Path:
    parts = relative_path.split("/")
    if relative_path.startswith("/") or "\\" in relative_path or ".." in parts:
        raise DatasetIntegrityError(f"unsafe relative path {relative_path!r}")
    return data_root.joinpath(*parts)


def atomic_write_bytes(path: Path, data: bytes, *, overwrite: bool = False) -> None:
    """Write via a sibling temporary file and ``os.replace``.

    Refuses to replace an existing file unless ``overwrite`` is True.
    """
    if path.exists() and not overwrite:
        raise DatasetIntegrityError(f"refusing to overwrite existing file {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    with open(temporary, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
