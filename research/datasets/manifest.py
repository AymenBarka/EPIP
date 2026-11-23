"""Deterministic dataset manifests with tamper detection.

``dataset_id`` = SHA-256 of the canonical JSON of the identity section.
The volatile ``provenance`` section (who/when/how acquired) is stored next to
the identity but never participates in ``dataset_id``. Canonical JSON: sorted
keys, ``(",", ":")`` separators, ASCII escaping, trailing newline.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from research.datasets.canonical import gunzip, sha256_hex
from research.datasets.contracts import (
    SUPPORTED_MANIFEST_SCHEMA_VERSIONS,
    ContentIdentity,
    Coverage,
    DatasetIntegrityError,
    Diagnostic,
    Granularity,
    HourStatus,
    PriceSide,
    Provider,
    RawArtifact,
    Severity,
    SourceFormat,
    require,
    require_sha256,
    require_text,
)

DATASET_KINDS = frozenset({"TICKS", "BARS", "PROVIDER_CANDLES", "MT5_TICKS", "MT5_BARS"})


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    ).encode("ascii")


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    schema_version: int
    dataset_kind: str
    provider: Provider
    instrument: str
    price_decimals: int
    granularity: Granularity
    sides: tuple[PriceSide, ...]
    source_format: SourceFormat
    normalization_version: str
    coverage: Coverage
    sources: tuple[RawArtifact, ...]
    content: ContentIdentity
    lineage: tuple[str, ...]
    hour_classification: tuple[tuple[int, HourStatus], ...]
    diagnostics: tuple[Diagnostic, ...]
    provenance: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        require(
            type(self.schema_version) is int
            and self.schema_version in SUPPORTED_MANIFEST_SCHEMA_VERSIONS,
            f"unsupported manifest schema version {self.schema_version!r}",
        )
        require(self.dataset_kind in DATASET_KINDS, "dataset_kind invalid")
        require(type(self.provider) is Provider, "provider invalid")
        require_text(self.instrument, "instrument")
        require(type(self.price_decimals) is int and 1 <= self.price_decimals <= 8, "decimals")
        require(type(self.granularity) is Granularity, "granularity invalid")
        require(len(self.sides) > 0 and len(set(self.sides)) == len(self.sides), "sides invalid")
        require(all(type(s) is PriceSide for s in self.sides), "sides invalid")
        require(type(self.source_format) is SourceFormat, "source_format invalid")
        require_text(self.normalization_version, "normalization_version")
        require(type(self.coverage) is Coverage, "coverage invalid")
        require(all(type(s) is RawArtifact for s in self.sources), "sources invalid")
        paths = [s.relative_path for s in self.sources]
        require(len(set(paths)) == len(paths), "duplicate source artifact")
        require(type(self.content) is ContentIdentity, "content invalid")
        for parent in self.lineage:
            require_sha256(parent, "lineage id")
        hours = [h for h, _ in self.hour_classification]
        require(hours == sorted(set(hours)), "hour classification must be unique and ordered")
        require(
            all(type(s) is HourStatus for _, s in self.hour_classification), "hour status invalid"
        )
        require(all(type(d) is Diagnostic for d in self.diagnostics), "diagnostics invalid")
        require(
            all(
                type(pair) is tuple and len(pair) == 2 and all(type(x) is str for x in pair)
                for pair in self.provenance
            ),
            "provenance must be (str, str) pairs",
        )
        keys = [k for k, _ in self.provenance]
        require(keys == sorted(set(keys)), "provenance keys must be unique and sorted")

    def identity(self) -> dict[str, Any]:
        c = self.coverage
        return {
            "schema_version": self.schema_version,
            "dataset_kind": self.dataset_kind,
            "provider": self.provider.value,
            "instrument": self.instrument,
            "price_decimals": self.price_decimals,
            "granularity": self.granularity.value,
            "sides": [s.value for s in self.sides],
            "source_format": self.source_format.value,
            "normalization_version": self.normalization_version,
            "coverage": {
                "start_ms": c.start_ms,
                "end_ms": c.end_ms,
                "hours_expected": c.hours_expected,
                "hours_populated": c.hours_populated,
                "hours_expected_closure": c.hours_expected_closure,
                "hours_unexplained_or_failed": c.hours_unexplained_or_failed,
            },
            "sources": [
                {
                    "relative_path": s.relative_path,
                    "source_format": s.source_format.value,
                    "size_bytes": s.size_bytes,
                    "raw_sha256": s.raw_sha256,
                    "hour_status": s.hour_status.value,
                }
                for s in self.sources
            ],
            "content": {
                "relative_path": self.content.relative_path,
                "canonical_sha256": self.content.canonical_sha256,
                "compressed_sha256": self.content.compressed_sha256,
                "row_count": self.content.row_count,
            },
            "lineage": list(self.lineage),
            "hour_classification": [[h, s.value] for h, s in self.hour_classification],
            "diagnostics": [
                {
                    "code": d.code,
                    "severity": d.severity.value,
                    "message": d.message,
                    "location": d.location,
                }
                for d in self.diagnostics
            ],
        }

    @property
    def dataset_id(self) -> str:
        return sha256_hex(canonical_json(self.identity()))

    def to_json(self) -> bytes:
        return canonical_json(
            {
                "dataset_id": self.dataset_id,
                "identity": self.identity(),
                "provenance": dict(self.provenance),
            }
        )


def _get(mapping: Mapping[str, Any], key: str) -> Any:
    if key not in mapping:
        raise DatasetIntegrityError(f"manifest field {key!r} is missing")
    return mapping[key]


def _provenance(value: object) -> tuple[tuple[str, str], ...]:
    require(isinstance(value, dict), "provenance must be an object")
    assert isinstance(value, dict)
    return tuple(sorted((str(k), v) for k, v in value.items()))


def provenance_of(values: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(values.items()))


def manifest_from_json(data: bytes) -> DatasetManifest:
    try:
        document = json.loads(data.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DatasetIntegrityError(f"manifest is not canonical ASCII JSON ({exc})") from exc
    require(isinstance(document, dict), "manifest must be a JSON object")
    require(set(document) == {"dataset_id", "identity", "provenance"}, "manifest sections invalid")
    ident = _get(document, "identity")
    require(isinstance(ident, dict), "identity must be an object")
    version = _get(ident, "schema_version")
    require(
        type(version) is int and version in SUPPORTED_MANIFEST_SCHEMA_VERSIONS,
        f"unsupported manifest schema version {version!r}",
    )
    try:
        cov = _get(ident, "coverage")
        content = _get(ident, "content")
        manifest = DatasetManifest(
            schema_version=version,
            dataset_kind=_get(ident, "dataset_kind"),
            provider=Provider(_get(ident, "provider")),
            instrument=_get(ident, "instrument"),
            price_decimals=_get(ident, "price_decimals"),
            granularity=Granularity(_get(ident, "granularity")),
            sides=tuple(PriceSide(s) for s in _get(ident, "sides")),
            source_format=SourceFormat(_get(ident, "source_format")),
            normalization_version=_get(ident, "normalization_version"),
            coverage=Coverage(
                _get(cov, "start_ms"),
                _get(cov, "end_ms"),
                _get(cov, "hours_expected"),
                _get(cov, "hours_populated"),
                _get(cov, "hours_expected_closure"),
                _get(cov, "hours_unexplained_or_failed"),
            ),
            sources=tuple(
                RawArtifact(
                    _get(s, "relative_path"),
                    SourceFormat(_get(s, "source_format")),
                    _get(s, "size_bytes"),
                    _get(s, "raw_sha256"),
                    HourStatus(_get(s, "hour_status")),
                )
                for s in _get(ident, "sources")
            ),
            content=ContentIdentity(
                _get(content, "relative_path"),
                _get(content, "canonical_sha256"),
                _get(content, "compressed_sha256"),
                _get(content, "row_count"),
            ),
            lineage=tuple(_get(ident, "lineage")),
            hour_classification=tuple(
                (int(h), HourStatus(s)) for h, s in _get(ident, "hour_classification")
            ),
            diagnostics=tuple(
                Diagnostic(
                    _get(d, "code"),
                    Severity(_get(d, "severity")),
                    _get(d, "message"),
                    _get(d, "location"),
                )
                for d in _get(ident, "diagnostics")
            ),
            provenance=_provenance(_get(document, "provenance")),
        )
    except (TypeError, ValueError, AttributeError) as exc:
        if isinstance(exc, DatasetIntegrityError):
            raise
        raise DatasetIntegrityError(f"manifest content invalid ({exc})") from exc
    if manifest.dataset_id != _get(document, "dataset_id"):
        raise DatasetIntegrityError("manifest tampered: dataset_id does not match identity")
    if manifest.to_json() != data:
        raise DatasetIntegrityError("manifest is not in canonical serialization")
    return manifest


def verify_files(manifest: DatasetManifest, data_root: Path) -> None:
    """Fail closed unless every referenced file exists with the recorded digests."""
    for source in manifest.sources:
        path = data_root.joinpath(*source.relative_path.split("/"))
        require(path.is_file(), f"raw artifact missing: {source.relative_path}")
        raw = path.read_bytes()
        require(len(raw) == source.size_bytes, f"raw size mismatch: {source.relative_path}")
        require(
            sha256_hex(raw) == source.raw_sha256, f"raw checksum mismatch: {source.relative_path}"
        )
    content_path = data_root.joinpath(*manifest.content.relative_path.split("/"))
    require(content_path.is_file(), f"canonical artifact missing: {manifest.content.relative_path}")
    compressed = content_path.read_bytes()
    require(
        sha256_hex(compressed) == manifest.content.compressed_sha256, "compressed checksum mismatch"
    )
    canonical = gunzip(compressed)
    require(
        sha256_hex(canonical) == manifest.content.canonical_sha256, "canonical checksum mismatch"
    )
    require(canonical.count(b"\n") - 1 == manifest.content.row_count, "row count mismatch")
