"""Local manifest-based dataset registry (no database, no network).

Layout under the data root: ``registry/<dataset_id>.json`` holds the canonical
manifest bytes. Registration is idempotent for identical bytes and rejects any
collision. Every read re-validates the manifest; ``verify`` also re-hashes the
referenced files.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from research.datasets.contracts import DatasetIntegrityError, require
from research.datasets.manifest import DatasetManifest, manifest_from_json, verify_files
from research.datasets.storage import atomic_write_bytes

REGISTRY_DIR = "registry"


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    dataset_id: str
    dataset_kind: str
    provider: str
    instrument: str
    granularity: str
    start_ms: int
    end_ms: int
    row_count: int


class DatasetRegistry:
    def __init__(self, data_root: Path) -> None:
        self._root = data_root
        self._dir = data_root / REGISTRY_DIR

    def _path(self, dataset_id: str) -> Path:
        return self._dir / f"{dataset_id}.json"

    def register(self, manifest: DatasetManifest) -> str:
        """Register after full file verification. Returns ``registered`` or ``duplicate``."""
        verify_files(manifest, self._root)
        data = manifest.to_json()
        path = self._path(manifest.dataset_id)
        if path.exists():
            existing = path.read_bytes()
            if existing != data:
                raise DatasetIntegrityError(
                    f"registry collision for {manifest.dataset_id}: different bytes on disk"
                )
            return "duplicate"
        atomic_write_bytes(path, data)
        return "registered"

    def _load(self, path: Path) -> DatasetManifest:
        manifest = manifest_from_json(path.read_bytes())
        if path.stem != manifest.dataset_id:
            raise DatasetIntegrityError(f"registry entry {path.name} does not match its identity")
        return manifest

    def list(self) -> tuple[RegistryEntry, ...]:
        if not self._dir.is_dir():
            return ()
        entries = []
        for path in sorted(self._dir.glob("*.json")):
            m = self._load(path)
            entries.append(
                RegistryEntry(
                    m.dataset_id,
                    m.dataset_kind,
                    m.provider.value,
                    m.instrument,
                    m.granularity.value,
                    m.coverage.start_ms,
                    m.coverage.end_ms,
                    m.content.row_count,
                )
            )
        return tuple(entries)

    def resolve(self, reference: str) -> DatasetManifest:
        require(
            len(reference) >= 8 and all(c in "0123456789abcdef" for c in reference),
            "reference must be at least 8 lowercase hex characters",
        )
        matches = sorted(self._dir.glob(f"{reference}*.json")) if self._dir.is_dir() else []
        if not matches:
            raise DatasetIntegrityError(f"no dataset matches {reference}")
        if len(matches) > 1:
            raise DatasetIntegrityError(f"reference {reference} is ambiguous")
        return self._load(matches[0])

    def inspect(self, reference: str) -> DatasetManifest:
        return self.resolve(reference)

    def verify(self, reference: str) -> DatasetManifest:
        manifest = self.resolve(reference)
        verify_files(manifest, self._root)
        return manifest
