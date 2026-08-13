"""Deterministic evidence infrastructure for the EPIP-016 decision domain.

The module manages evidence as immutable data.  It performs structural
validation and lifecycle management only; it contains no ranking, inference,
recommendation, or financial calculation.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from epip.core.integrity import RelationshipIntegrityError, require_text, require_version
from epip.decision.domain import (
    Confidence,
    ConfidenceLevel,
    DecisionDigest,
    DecisionMetadata,
    Evidence,
    EvidenceCategory,
    EvidenceReference,
    Quality,
    QualityLevel,
    Uncertainty,
    Validity,
    ValidityLevel,
)


class EvidenceLifecycleState(StrEnum):
    """Official evidence lifecycle states."""

    CREATED = "created"
    VALIDATED = "validated"
    REGISTERED = "registered"
    AVAILABLE = "available"
    SNAPSHOTTED = "snapshotted"
    ARCHIVED = "archived"
    DISCARDED = "discarded"


_TRANSITIONS: Mapping[EvidenceLifecycleState, EvidenceLifecycleState] = MappingProxyType(
    {
        EvidenceLifecycleState.CREATED: EvidenceLifecycleState.VALIDATED,
        EvidenceLifecycleState.VALIDATED: EvidenceLifecycleState.REGISTERED,
        EvidenceLifecycleState.REGISTERED: EvidenceLifecycleState.AVAILABLE,
        EvidenceLifecycleState.AVAILABLE: EvidenceLifecycleState.SNAPSHOTTED,
        EvidenceLifecycleState.SNAPSHOTTED: EvidenceLifecycleState.ARCHIVED,
        EvidenceLifecycleState.ARCHIVED: EvidenceLifecycleState.DISCARDED,
    }
)


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _evidence_content(evidence: Evidence) -> dict[str, object]:
    content = evidence.to_dict()
    content.pop("content_digest")
    return content


@dataclass(frozen=True, slots=True)
class EvidenceDigest:
    """Canonical SHA-256 digest of immutable evidence infrastructure state."""

    value: str
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if self.algorithm != "sha256" or len(self.value) != 64:
            raise RelationshipIntegrityError("evidence digest must be SHA-256")
        try:
            int(self.value, 16)
        except ValueError as exc:
            raise RelationshipIntegrityError("evidence digest must be hexadecimal") from exc

    @classmethod
    def from_value(cls, value: object) -> EvidenceDigest:
        """Create a digest from canonical JSON-compatible content."""
        payload = _canonical_json(value).encode("utf-8")
        return cls(hashlib.sha256(payload).hexdigest())


@dataclass(frozen=True, slots=True)
class EvidenceCollection:
    """Immutable, identifier-ordered collection of unique evidence."""

    items: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.items, tuple):
            raise RelationshipIntegrityError("evidence collection must use a tuple")
        ordered = tuple(sorted(self.items, key=lambda item: item.evidence_id))
        identifiers = tuple(item.evidence_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise RelationshipIntegrityError("duplicate evidence identifier")
        object.__setattr__(self, "items", ordered)

    def __iter__(self) -> Iterator[Evidence]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def get(self, identifier: str) -> Evidence | None:
        """Return evidence by stable identifier."""
        return next((item for item in self.items if item.evidence_id == identifier), None)

    def by_category(self, category: EvidenceCategory) -> EvidenceCollection:
        """Filter deterministically by category."""
        return EvidenceCollection(tuple(item for item in self.items if item.category is category))

    def by_source(self, source: str) -> EvidenceCollection:
        """Filter deterministically by source."""
        return EvidenceCollection(tuple(item for item in self.items if item.source == source))

    def group_by_category(self) -> tuple[tuple[EvidenceCategory, EvidenceCollection], ...]:
        """Return non-empty category groups in enum order."""
        return tuple(
            (category, group)
            for category in EvidenceCategory
            if (group := self.by_category(category)).items
        )

    def to_data(self) -> list[dict[str, object]]:
        """Return canonical JSON-compatible content."""
        return [item.to_dict() for item in self.items]


@dataclass(frozen=True, slots=True)
class _RegistryEntry:
    evidence: Evidence
    state: EvidenceLifecycleState


@dataclass(frozen=True, slots=True)
class EvidenceRegistry:
    """Immutable registry with deterministic indexes and lifecycle state."""

    entries: tuple[_RegistryEntry, ...] = ()

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.entries, key=lambda item: item.evidence.evidence_id))
        identifiers = tuple(item.evidence.evidence_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise RelationshipIntegrityError("duplicate evidence identifier")
        if any(not isinstance(item.state, EvidenceLifecycleState) for item in ordered):
            raise RelationshipIntegrityError("invalid evidence lifecycle state")
        object.__setattr__(self, "entries", ordered)

    def register(self, evidence: Evidence) -> EvidenceRegistry:
        """Register validated evidence at the REGISTERED lifecycle state."""
        if self.get(evidence.evidence_id) is not None:
            raise RelationshipIntegrityError("duplicate evidence identifier")
        created = EvidenceRegistry(
            self.entries + (_RegistryEntry(evidence, EvidenceLifecycleState.CREATED),)
        )
        EvidenceValidator().validate(evidence)
        validated = created.transition(evidence.evidence_id, EvidenceLifecycleState.VALIDATED)
        return validated.transition(evidence.evidence_id, EvidenceLifecycleState.REGISTERED)

    def transition(self, identifier: str, target: EvidenceLifecycleState) -> EvidenceRegistry:
        """Apply exactly one explicit lifecycle transition."""
        entry = self.entry(identifier)
        expected = _TRANSITIONS.get(entry.state)
        if expected is not target:
            raise RelationshipIntegrityError(
                f"invalid evidence transition: {entry.state.value} -> {target.value}"
            )
        replacement = _RegistryEntry(entry.evidence, target)
        return EvidenceRegistry(
            tuple(
                replacement if item.evidence.evidence_id == identifier else item
                for item in self.entries
            )
        )

    def entry(self, identifier: str) -> _RegistryEntry:
        """Return the complete registry entry or reject an unknown identifier."""
        found = next(
            (item for item in self.entries if item.evidence.evidence_id == identifier), None
        )
        if found is None:
            raise KeyError(identifier)
        return found

    def get(self, identifier: str) -> Evidence | None:
        """Look up evidence by identifier."""
        found = next(
            (item.evidence for item in self.entries if item.evidence.evidence_id == identifier),
            None,
        )
        return found

    def by_type(self, evidence_type: type[Evidence]) -> EvidenceCollection:
        """Look up evidence by concrete domain type."""
        return EvidenceCollection(
            tuple(item.evidence for item in self.entries if type(item.evidence) is evidence_type)
        )

    def by_category(self, category: EvidenceCategory) -> EvidenceCollection:
        """Look up evidence by official category."""
        return self.collection().by_category(category)

    def by_source(self, source: str) -> EvidenceCollection:
        """Look up evidence by source."""
        return self.collection().by_source(source)

    def by_reference(self, reference: EvidenceReference) -> Evidence | None:
        """Resolve a versioned reference."""
        evidence = self.get(reference.identifier)
        if evidence is None or evidence.metadata.version != reference.version:
            return None
        return evidence

    def by_digest(self, digest: str | DecisionDigest) -> Evidence | None:
        """Look up evidence by its preserved domain digest."""
        value = digest.value if isinstance(digest, DecisionDigest) else digest
        return next(
            (item.evidence for item in self.entries if item.evidence.content_digest.value == value),
            None,
        )

    def collection(self, state: EvidenceLifecycleState | None = None) -> EvidenceCollection:
        """Return all evidence, optionally filtered by lifecycle state."""
        return EvidenceCollection(
            tuple(item.evidence for item in self.entries if state is None or item.state is state)
        )

    def digest(self) -> EvidenceDigest:
        """Return the canonical registry digest."""
        return EvidenceDigest.from_value(
            [
                {"evidence": item.evidence.to_dict(), "state": item.state.value}
                for item in self.entries
            ]
        )


class EvidenceValidator:
    """Structural validator that performs no semantic interpretation."""

    def validate(self, evidence: Evidence) -> None:
        """Reject structurally incomplete or digest-inconsistent evidence."""
        require_text(evidence.evidence_id, "evidence.evidence_id")
        require_text(evidence.source, "evidence.source")
        require_version(evidence.source_version, "evidence.source_version")
        if not isinstance(evidence.category, EvidenceCategory):
            raise RelationshipIntegrityError("unknown evidence category")
        expected = EvidenceDigest.from_value(_evidence_content(evidence)).value
        if evidence.content_digest.value != expected:
            raise RelationshipIntegrityError("evidence content digest mismatch")
        dependencies = set(evidence.dependencies)
        if evidence.evidence_id in dependencies:
            raise RelationshipIntegrityError("evidence cannot depend on itself")

    def validate_references(self, evidence: Evidence, available_identifiers: Iterable[str]) -> None:
        """Reject unresolved dependency identifiers."""
        available = frozenset(available_identifiers)
        missing = tuple(item for item in evidence.dependencies if item not in available)
        if missing:
            raise RelationshipIntegrityError(f"unknown evidence dependencies: {missing!r}")


class EvidenceBuilder:
    """Build immutable evidence with a canonical content digest."""

    def build(
        self,
        *,
        evidence_id: str,
        category: EvidenceCategory,
        source: str,
        source_version: int,
        payload: Iterable[tuple[str, str]],
        confidence: Confidence,
        quality: Quality,
        validity: Validity,
        uncertainty: Uncertainty,
        dependencies: Iterable[str],
        metadata: DecisionMetadata,
    ) -> Evidence:
        """Create validated evidence without implicit identity or time sources."""
        normalized_payload = tuple(sorted(payload, key=lambda item: item[0]))
        normalized_dependencies = tuple(sorted(set(dependencies)))
        provisional = Evidence(
            evidence_id=evidence_id,
            category=category,
            source=source,
            source_version=source_version,
            payload=normalized_payload,
            confidence=confidence,
            quality=quality,
            validity=validity,
            uncertainty=uncertainty,
            dependencies=normalized_dependencies,
            metadata=metadata,
            content_digest=DecisionDigest("0" * 64),
        )
        evidence = Evidence(
            evidence_id=provisional.evidence_id,
            category=provisional.category,
            source=provisional.source,
            source_version=provisional.source_version,
            payload=provisional.payload,
            confidence=provisional.confidence,
            quality=provisional.quality,
            validity=provisional.validity,
            uncertainty=provisional.uncertainty,
            dependencies=provisional.dependencies,
            metadata=provisional.metadata,
            content_digest=DecisionDigest(
                EvidenceDigest.from_value(_evidence_content(provisional)).value
            ),
        )
        EvidenceValidator().validate(evidence)
        return evidence


@dataclass(frozen=True, slots=True)
class EvidenceStatistics:
    """Read-only deterministic evidence registry statistics."""

    total: int
    by_category: tuple[tuple[str, int], ...]
    by_source: tuple[tuple[str, int], ...]
    duplicate_rejections: int = 0
    validation_failures: int = 0


@dataclass(frozen=True, slots=True)
class EvidenceAudit:
    """Immutable audit view derived from an engine state."""

    statistics: EvidenceStatistics
    registered_identifiers: tuple[str, ...]
    rejection_messages: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvidenceDiagnostics:
    """Immutable diagnostics with no automatic correction behavior."""

    duplicates: tuple[str, ...] = ()
    invalid_references: tuple[str, ...] = ()
    unknown_categories: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()
    inconsistencies: tuple[str, ...] = ()

    @property
    def is_consistent(self) -> bool:
        """Return whether no diagnostic issue was observed."""
        return not any(
            (
                self.duplicates,
                self.invalid_references,
                self.unknown_categories,
                self.missing_fields,
                self.inconsistencies,
            )
        )

    @classmethod
    def inspect(
        cls,
        registry: EvidenceRegistry,
        snapshot: EvidenceSnapshot | None = None,
    ) -> EvidenceDiagnostics:
        """Inspect registry, references, and digests without mutation."""
        identifiers = tuple(item.evidence.evidence_id for item in registry.entries)
        duplicate_ids = tuple(sorted({item for item in identifiers if identifiers.count(item) > 1}))
        available = frozenset(identifiers)
        invalid_references: list[str] = []
        unknown_categories: list[str] = []
        missing_fields: list[str] = []
        inconsistencies: list[str] = []
        for entry in registry.entries:
            evidence = entry.evidence
            invalid_references.extend(
                f"{evidence.evidence_id}:{reference}"
                for reference in evidence.dependencies
                if reference not in available
            )
            if not evidence.evidence_id or not evidence.source:
                missing_fields.append(evidence.evidence_id or "<missing-id>")
            if not isinstance(evidence.category, EvidenceCategory):
                unknown_categories.append(evidence.evidence_id or "<missing-id>")
            expected = EvidenceDigest.from_value(_evidence_content(evidence)).value
            if expected != evidence.content_digest.value:
                inconsistencies.append(evidence.evidence_id)
        if snapshot is not None and snapshot.registry_digest != registry.digest():
            inconsistencies.append(f"snapshot:{snapshot.snapshot_id}:registry-digest")
        return cls(
            duplicates=duplicate_ids,
            invalid_references=tuple(sorted(set(invalid_references))),
            unknown_categories=tuple(sorted(set(unknown_categories))),
            missing_fields=tuple(sorted(set(missing_fields))),
            inconsistencies=tuple(sorted(set(inconsistencies))),
        )


class EvidenceReferenceResolver:
    """Deterministic resolver for evidence references."""

    def __init__(self, registry: EvidenceRegistry) -> None:
        self._registry = registry

    def resolve(self, reference: EvidenceReference) -> Evidence:
        """Resolve one reference or reject it."""
        result = self._registry.by_reference(reference)
        if result is None:
            raise KeyError(reference.identifier)
        return result

    def resolve_all(self, references: Iterable[EvidenceReference]) -> EvidenceCollection:
        """Resolve references into a deterministic immutable collection."""
        return EvidenceCollection(tuple(self.resolve(reference) for reference in references))


def _evidence_from_data(data: Mapping[str, Any]) -> Evidence:
    confidence = data["confidence"]
    quality = data["quality"]
    validity = data["validity"]
    metadata = data["metadata"]
    digest = data["content_digest"]
    return Evidence(
        evidence_id=data["evidence_id"],
        category=EvidenceCategory(data["category"]),
        source=data["source"],
        source_version=data["source_version"],
        payload=tuple(tuple(item) for item in data["payload"]),
        confidence=Confidence(confidence["value"], ConfidenceLevel(confidence["level"])),
        quality=Quality(quality["value"], QualityLevel(quality["level"])),
        validity=Validity(validity["value"], ValidityLevel(validity["level"])),
        uncertainty=Uncertainty(data["uncertainty"]["value"]),
        dependencies=tuple(data["dependencies"]),
        metadata=DecisionMetadata(
            metadata["version"], metadata["logical_timestamp"], metadata["source"]
        ),
        content_digest=DecisionDigest(digest["value"], digest["algorithm"]),
    )


@dataclass(frozen=True, slots=True)
class EvidenceSnapshot:
    """Immutable versioned capture preserving evidence identity and state."""

    snapshot_id: str
    version: int
    entries: tuple[tuple[Evidence, EvidenceLifecycleState], ...]
    registry_digest: EvidenceDigest
    content_digest: EvidenceDigest

    def __post_init__(self) -> None:
        require_text(self.snapshot_id, "evidence_snapshot.snapshot_id")
        require_version(self.version, "evidence_snapshot.version")
        identifiers = tuple(item.evidence_id for item, _ in self.entries)
        if identifiers != tuple(sorted(identifiers)) or len(identifiers) != len(set(identifiers)):
            raise RelationshipIntegrityError("snapshot entries must be unique and ordered")
        expected = EvidenceDigest.from_value(self._content_data())
        if expected != self.content_digest:
            raise RelationshipIntegrityError("snapshot content digest mismatch")
        expected_registry = EvidenceDigest.from_value(
            [
                {"evidence": evidence.to_dict(), "state": state.value}
                for evidence, state in self.entries
            ]
        )
        if expected_registry != self.registry_digest:
            raise RelationshipIntegrityError("snapshot registry digest mismatch")

    def _content_data(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id,
            "version": self.version,
            "entries": [
                {"evidence": evidence.to_dict(), "state": state.value}
                for evidence, state in self.entries
            ],
            "registry_digest": {
                "value": self.registry_digest.value,
                "algorithm": self.registry_digest.algorithm,
            },
        }

    def to_dict(self) -> dict[str, object]:
        """Return canonical snapshot content including its digest."""
        result = self._content_data()
        result["content_digest"] = {
            "value": self.content_digest.value,
            "algorithm": self.content_digest.algorithm,
        }
        return result

    def to_json(self) -> str:
        """Return byte-stable snapshot JSON."""
        return _canonical_json(self.to_dict())

    @classmethod
    def create(cls, snapshot_id: str, version: int, registry: EvidenceRegistry) -> EvidenceSnapshot:
        """Create a deterministic snapshot from a registry."""
        entries = tuple((item.evidence, item.state) for item in registry.entries)
        provisional = {
            "snapshot_id": snapshot_id,
            "version": version,
            "entries": [
                {"evidence": evidence.to_dict(), "state": state.value}
                for evidence, state in entries
            ],
            "registry_digest": {
                "value": registry.digest().value,
                "algorithm": registry.digest().algorithm,
            },
        }
        return cls(
            snapshot_id,
            version,
            entries,
            registry.digest(),
            EvidenceDigest.from_value(provisional),
        )

    @classmethod
    def from_json(cls, payload: str) -> EvidenceSnapshot:
        """Restore a snapshot while preserving all identities and digests."""
        data = json.loads(payload)
        entries = tuple(
            (
                _evidence_from_data(item["evidence"]),
                EvidenceLifecycleState(item["state"]),
            )
            for item in data["entries"]
        )
        registry_digest = data["registry_digest"]
        content_digest = data["content_digest"]
        return cls(
            data["snapshot_id"],
            data["version"],
            entries,
            EvidenceDigest(registry_digest["value"], registry_digest["algorithm"]),
            EvidenceDigest(content_digest["value"], content_digest["algorithm"]),
        )


@dataclass(frozen=True, slots=True)
class EvidenceEngine:
    """Functional facade for validation, registration, lifecycle, and snapshots."""

    registry: EvidenceRegistry = EvidenceRegistry()
    duplicate_rejections: int = 0
    validation_failures: int = 0
    rejection_messages: tuple[str, ...] = ()

    def register(self, evidence: Evidence) -> EvidenceEngine:
        """Validate and register evidence, returning a new engine."""
        registry = self.registry.register(evidence)
        return EvidenceEngine(
            registry,
            self.duplicate_rejections,
            self.validation_failures,
            self.rejection_messages,
        )

    def try_register(self, evidence: Evidence) -> tuple[EvidenceEngine, bool]:
        """Register without mutation and preserve failure audit information."""
        try:
            return self.register(evidence), True
        except RelationshipIntegrityError as exc:
            duplicate = self.registry.get(evidence.evidence_id) is not None
            return (
                EvidenceEngine(
                    self.registry,
                    self.duplicate_rejections + int(duplicate),
                    self.validation_failures + int(not duplicate),
                    self.rejection_messages + (str(exc),),
                ),
                False,
            )

    def transition(self, identifier: str, target: EvidenceLifecycleState) -> EvidenceEngine:
        """Return an engine with one lifecycle transition applied."""
        return EvidenceEngine(
            self.registry.transition(identifier, target),
            self.duplicate_rejections,
            self.validation_failures,
            self.rejection_messages,
        )

    def make_available(self, identifier: str) -> EvidenceEngine:
        """Apply REGISTERED -> AVAILABLE."""
        return self.transition(identifier, EvidenceLifecycleState.AVAILABLE)

    def snapshot(
        self, snapshot_id: str, version: int = 1
    ) -> tuple[EvidenceEngine, EvidenceSnapshot]:
        """Snapshot available evidence and advance it to SNAPSHOTTED."""
        engine = self
        for entry in self.registry.entries:
            if entry.state is EvidenceLifecycleState.AVAILABLE:
                engine = engine.transition(
                    entry.evidence.evidence_id, EvidenceLifecycleState.SNAPSHOTTED
                )
        return engine, EvidenceSnapshot.create(snapshot_id, version, engine.registry)

    def audit(self) -> EvidenceAudit:
        """Return a read-only audit derived from current state."""
        categories = tuple(
            (category.value, len(self.registry.by_category(category)))
            for category in EvidenceCategory
            if self.registry.by_category(category).items
        )
        sources = tuple(
            (source, len(self.registry.by_source(source)))
            for source in sorted({item.evidence.source for item in self.registry.entries})
        )
        statistics = EvidenceStatistics(
            total=len(self.registry.entries),
            by_category=categories,
            by_source=sources,
            duplicate_rejections=self.duplicate_rejections,
            validation_failures=self.validation_failures,
        )
        return EvidenceAudit(
            statistics,
            tuple(item.evidence.evidence_id for item in self.registry.entries),
            self.rejection_messages,
        )


__all__ = [
    "EvidenceAudit",
    "EvidenceBuilder",
    "EvidenceCollection",
    "EvidenceDiagnostics",
    "EvidenceDigest",
    "EvidenceEngine",
    "EvidenceLifecycleState",
    "EvidenceReferenceResolver",
    "EvidenceRegistry",
    "EvidenceSnapshot",
    "EvidenceStatistics",
    "EvidenceValidator",
]
