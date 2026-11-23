"""D00 acceptance 22-25 and 33-34: manifests, registry, consultation ledger, OOS status."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from research.datasets.canonical import deterministic_gzip, sha256_hex, ticks_to_csv
from research.datasets.contracts import (
    MANIFEST_SCHEMA_VERSION,
    TICK_NORMALIZATION_VERSION,
    ContentIdentity,
    Coverage,
    DatasetIntegrityError,
    Diagnostic,
    Granularity,
    HourStatus,
    OOSStatus,
    Partition,
    PriceSide,
    Provider,
    RawArtifact,
    Severity,
    SourceFormat,
)
from research.datasets.dukascopy import decode_ticks, instrument
from research.datasets.ledger import (
    BASELINE_LEDGER,
    Consultation,
    ConsultationLedger,
    instrument_status,
)
from research.datasets.manifest import (
    DatasetManifest,
    canonical_json,
    manifest_from_json,
    provenance_of,
    verify_files,
)
from research.datasets.registry import DatasetRegistry
from research.tests.fixtures import hour_ms, tick_payload, tick_records

H0 = hour_ms(2012, 3, 12, 0)


def make_dataset(root: Path, provenance: dict[str, str] | None = None) -> DatasetManifest:
    spec = instrument("EURUSD")
    raw = tick_payload(tick_records("EURUSD", H0))
    raw_rel = "raw/dukascopy/EURUSD/ticks/2012/03/12/00h_ticks.bi5"
    (root / raw_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / raw_rel).write_bytes(raw)
    canonical = ticks_to_csv(decode_ticks(raw, H0), spec)
    compressed = deterministic_gzip(canonical)
    content_rel = "canonical/ticks/test.csv.gz"
    (root / content_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / content_rel).write_bytes(compressed)
    return DatasetManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        dataset_kind="TICKS",
        provider=Provider.DUKASCOPY,
        instrument="EURUSD",
        price_decimals=5,
        granularity=Granularity.TICK,
        sides=(PriceSide.BID, PriceSide.ASK),
        source_format=SourceFormat.DUKASCOPY_TICKS_BI5,
        normalization_version=TICK_NORMALIZATION_VERSION,
        coverage=Coverage(H0, H0 + 3_600_000, 1, 1, 0, 0),
        sources=(
            RawArtifact(
                raw_rel,
                SourceFormat.DUKASCOPY_TICKS_BI5,
                len(raw),
                sha256_hex(raw),
                HourStatus.POPULATED,
            ),
        ),
        content=ContentIdentity(
            content_rel, sha256_hex(canonical), sha256_hex(compressed), canonical.count(b"\n") - 1
        ),
        lineage=(),
        hour_classification=((H0, HourStatus.POPULATED),),
        diagnostics=(Diagnostic("NOTE", Severity.INFO, "fixture", "here"),),
        provenance=provenance_of(provenance or {"acquired_at": "2026-11-22T00:00:00Z"}),
    )


def test_manifest_round_trip_is_canonical(tmp_path: Path) -> None:
    manifest = make_dataset(tmp_path)
    data = manifest.to_json()
    assert data.endswith(b"\n") and b" " not in data.split(b'"message"')[0]
    assert manifest_from_json(data) == manifest
    assert manifest_from_json(data).to_json() == data
    verify_files(manifest, tmp_path)


def test_provenance_never_changes_identity(tmp_path: Path) -> None:
    a = make_dataset(tmp_path, {"acquired_at": "2026-11-22T00:00:00Z"})
    b = make_dataset(tmp_path, {"acquired_at": "2027-01-01T00:00:00Z", "host": "other"})
    assert a.dataset_id == b.dataset_id and a.to_json() != b.to_json()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["identity"].__setitem__("instrument", "XAUUSD"),
        lambda d: d["identity"]["content"].__setitem__("row_count", 999),
        lambda d: d.__setitem__("dataset_id", "0" * 64),
        lambda d: d["identity"]["sources"][0].__setitem__("raw_sha256", "a" * 64),
    ],
)
def test_manifest_tampering_is_detected(tmp_path: Path, mutate: object) -> None:
    document = json.loads(make_dataset(tmp_path).to_json())
    mutate(document)  # type: ignore[operator]
    with pytest.raises(DatasetIntegrityError, match="tampered"):
        manifest_from_json(canonical_json(document))


def test_noncanonical_or_malformed_manifest_is_rejected(tmp_path: Path) -> None:
    data = make_dataset(tmp_path).to_json()
    pretty = json.dumps(json.loads(data), indent=1).encode() + b"\n"
    with pytest.raises(DatasetIntegrityError, match="canonical serialization"):
        manifest_from_json(pretty)
    for bad in (b"[]", b"{not json", "é".encode()):
        with pytest.raises(DatasetIntegrityError):
            manifest_from_json(bad)
    document = json.loads(data)
    del document["identity"]["coverage"]
    with pytest.raises(DatasetIntegrityError, match="missing"):
        manifest_from_json(canonical_json(document))
    document = json.loads(data)
    document["identity"]["provider"] = "NOPE"
    with pytest.raises(DatasetIntegrityError, match="invalid"):
        manifest_from_json(canonical_json(document))
    document = json.loads(data)
    document["extra"] = 1
    with pytest.raises(DatasetIntegrityError, match="sections"):
        manifest_from_json(canonical_json(document))


def test_unsupported_manifest_version_is_rejected(tmp_path: Path) -> None:
    document = json.loads(make_dataset(tmp_path).to_json())
    document["identity"]["schema_version"] = 2
    with pytest.raises(DatasetIntegrityError, match="unsupported manifest schema version"):
        manifest_from_json(canonical_json(document))
    with pytest.raises(DatasetIntegrityError, match="unsupported"):
        DatasetManifest(**{**_fields(make_dataset(tmp_path)), "schema_version": 0})


def _fields(manifest: DatasetManifest) -> dict[str, Any]:
    return {name: getattr(manifest, name) for name in manifest.__slots__}


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"dataset_kind": "OTHER"}, "dataset_kind"),
        ({"sides": ()}, "sides"),
        ({"sides": (PriceSide.BID, PriceSide.BID)}, "sides"),
        ({"lineage": ("xyz",)}, "SHA-256"),
        (
            {"hour_classification": ((2, HourStatus.POPULATED), (1, HourStatus.POPULATED))},
            "ordered",
        ),
        ({"provenance": (("b", "1"), ("a", "2"))}, "sorted"),
        ({"price_decimals": 0}, "decimals"),
    ],
)
def test_manifest_contract_validation(
    tmp_path: Path, change: dict[str, object], message: str
) -> None:
    with pytest.raises(DatasetIntegrityError, match=message):
        DatasetManifest(**{**_fields(make_dataset(tmp_path)), **change})


def test_file_tampering_is_detected(tmp_path: Path) -> None:
    manifest = make_dataset(tmp_path)
    raw = tmp_path / manifest.sources[0].relative_path
    raw.write_bytes(raw.read_bytes()[:-1] + b"\x00")
    with pytest.raises(DatasetIntegrityError, match="raw checksum mismatch"):
        verify_files(manifest, tmp_path)
    manifest = make_dataset(tmp_path)
    content = tmp_path / manifest.content.relative_path
    content.write_bytes(deterministic_gzip(b"other\n"))
    with pytest.raises(DatasetIntegrityError, match="compressed checksum mismatch"):
        verify_files(manifest, tmp_path)
    content.unlink()
    with pytest.raises(DatasetIntegrityError, match="canonical artifact missing"):
        verify_files(manifest, tmp_path)


def test_registry_register_list_resolve_verify(tmp_path: Path) -> None:
    registry = DatasetRegistry(tmp_path)
    assert registry.list() == ()
    manifest = make_dataset(tmp_path)
    assert registry.register(manifest) == "registered"
    assert registry.register(manifest) == "duplicate"
    (entry,) = registry.list()
    assert entry.dataset_id == manifest.dataset_id and entry.row_count == manifest.content.row_count
    assert registry.resolve(manifest.dataset_id[:8]) == manifest
    assert registry.inspect(manifest.dataset_id) == manifest
    assert registry.verify(manifest.dataset_id[:12]) == manifest


def test_registry_collision_and_corruption_are_rejected(tmp_path: Path) -> None:
    registry = DatasetRegistry(tmp_path)
    manifest = make_dataset(tmp_path)
    registry.register(manifest)
    path = tmp_path / "registry" / f"{manifest.dataset_id}.json"
    other = make_dataset(tmp_path, {"acquired_at": "2030-01-01T00:00:00Z"})
    assert other.dataset_id == manifest.dataset_id
    with pytest.raises(DatasetIntegrityError, match="collision"):
        registry.register(other)
    path.write_bytes(path.read_bytes().replace(b"EURUSD", b"XAUUSD"))
    with pytest.raises(DatasetIntegrityError, match="tampered"):
        registry.list()
    renamed = tmp_path / "registry" / ("f" * 64 + ".json")
    path.write_bytes(manifest.to_json())
    path.rename(renamed)
    with pytest.raises(DatasetIntegrityError, match="does not match its identity"):
        registry.resolve("ffffffff")


def test_registry_reference_rules(tmp_path: Path) -> None:
    registry = DatasetRegistry(tmp_path)
    with pytest.raises(DatasetIntegrityError, match="at least 8"):
        registry.resolve("abc")
    with pytest.raises(DatasetIntegrityError, match="no dataset"):
        registry.resolve("0" * 8)
    manifest = make_dataset(tmp_path)
    registry.register(manifest)
    (tmp_path / "registry" / f"{manifest.dataset_id[:8]}{'0' * 56}.json").write_bytes(b"x")
    with pytest.raises(DatasetIntegrityError, match="ambiguous"):
        registry.resolve(manifest.dataset_id[:8])


def test_registry_rejects_unverifiable_dataset(tmp_path: Path) -> None:
    manifest = make_dataset(tmp_path)
    (tmp_path / manifest.sources[0].relative_path).unlink()
    with pytest.raises(DatasetIntegrityError, match="raw artifact missing"):
        DatasetRegistry(tmp_path).register(manifest)


def test_consultation_ledger_append_and_read(tmp_path: Path) -> None:
    ledger = ConsultationLedger(tmp_path)
    assert ledger.records() == ()
    record = Consultation(
        "a" * 64,
        "b" * 64,
        "EXP-001",
        "pipeline smoke test",
        "2026-11-22T00:00:00Z",
        Partition.TECHNICAL,
        ("reports/x.json",),
    )
    ledger.append(record)
    ledger.append(record)
    assert ledger.records() == (record, record)
    path = tmp_path / "ledger" / "consultations.jsonl"
    path.write_bytes(path.read_bytes().replace(b'"purpose":"pipeline', b'"purpose": "pipeline'))
    with pytest.raises(DatasetIntegrityError, match="not canonical"):
        ledger.records()
    path.write_bytes(b'{"dataset_id": 1}\n')
    with pytest.raises(DatasetIntegrityError, match="corrupted"):
        ledger.records()
    path.write_bytes(b"[1]\n")
    with pytest.raises(DatasetIntegrityError, match="not an object"):
        ledger.records()


@pytest.mark.parametrize(
    "change",
    [
        {"dataset_id": "x"},
        {"consulted_at_utc": "2026-11-22"},
        {"partition": "OOS"},
        {"outputs": ("",)},
        {"experiment_id": " "},
    ],
)
def test_consultation_validation(change: dict[str, object]) -> None:
    values: dict[str, object] = {
        "dataset_id": "a" * 64,
        "dataset_digest": "b" * 64,
        "experiment_id": "EXP-1",
        "purpose": "p",
        "consulted_at_utc": "2026-11-22T00:00:00Z",
        "partition": Partition.DEVELOPMENT,
        "outputs": (),
    }
    with pytest.raises(DatasetIntegrityError):
        Consultation(**{**values, **change})  # type: ignore[arg-type]


def test_oos_status_is_preserved_and_never_inferred() -> None:
    assert instrument_status("GBPUSD") is OOSStatus.UNVERIFIED_NOT_ATTESTED_VIRGIN
    assert instrument_status("GBPUSD").value == "UNVERIFIED — NOT ATTESTED VIRGIN"
    assert instrument_status("USDJPY") is OOSStatus.CONSULTED
    assert instrument_status("USDJPY", frozenset({"USDJPY"})) is OOSStatus.CONSULTED
    assert instrument_status("AUDUSD") is OOSStatus.UNVERIFIED_NOT_ATTESTED_VIRGIN
    assert instrument_status("AUDUSD", frozenset({"AUDUSD"})) is OOSStatus.ATTESTED_VIRGIN
    assert {r.instrument for r in BASELINE_LEDGER} == {"EURUSD", "XAUUSD", "USDJPY", "GBPUSD"}
    assert all(r.status is not OOSStatus.ATTESTED_VIRGIN for r in BASELINE_LEDGER)
