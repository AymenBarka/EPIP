"""Deterministic candidate generation for EPIP-016.

This module turns validated scenarios into immutable decision candidates.  It
does not rank, recommend, price, or otherwise interpret those candidates.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from types import MappingProxyType

from epip.core.integrity import RelationshipIntegrityError
from epip.decision.domain import (
    CandidateType,
    Confidence,
    ConfidenceLevel,
    ConstraintEvaluation,
    ConstraintType,
    DecisionCandidate,
    DecisionDigest,
    DecisionMetadata,
    DecisionPriority,
    EvidenceReference,
    HypothesisReference,
    Quality,
    QualityLevel,
    ScenarioReference,
    Uncertainty,
    Validity,
    ValidityLevel,
)
from epip.decision.evidence import EvidenceRegistry
from epip.decision.graph import DecisionDependencyGraph
from epip.decision.inference import (
    HypothesisRegistry,
    InferenceLifecycleState,
    ScenarioRegistry,
)


class CandidateLifecycleState(StrEnum):
    """Explicit candidate lifecycle."""

    CREATED = "created"
    GENERATED = "generated"
    VALIDATED = "validated"
    REGISTERED = "registered"
    AVAILABLE = "available"
    SNAPSHOTTED = "snapshotted"
    ARCHIVED = "archived"
    DISCARDED = "discarded"


_TRANSITIONS: Mapping[CandidateLifecycleState, CandidateLifecycleState] = MappingProxyType(
    {
        CandidateLifecycleState.CREATED: CandidateLifecycleState.GENERATED,
        CandidateLifecycleState.GENERATED: CandidateLifecycleState.VALIDATED,
        CandidateLifecycleState.VALIDATED: CandidateLifecycleState.REGISTERED,
        CandidateLifecycleState.REGISTERED: CandidateLifecycleState.AVAILABLE,
        CandidateLifecycleState.AVAILABLE: CandidateLifecycleState.SNAPSHOTTED,
        CandidateLifecycleState.SNAPSHOTTED: CandidateLifecycleState.ARCHIVED,
        CandidateLifecycleState.ARCHIVED: CandidateLifecycleState.DISCARDED,
    }
)

_VALID_SCENARIO_STATES = frozenset(
    {
        InferenceLifecycleState.VALIDATED,
        InferenceLifecycleState.REGISTERED,
        InferenceLifecycleState.AVAILABLE,
        InferenceLifecycleState.SNAPSHOTTED,
        InferenceLifecycleState.ARCHIVED,
    }
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CandidateDigest:
    """SHA-256 digest of canonical candidate content."""

    value: str
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if self.algorithm != "sha256" or len(self.value) != 64 or self.value != self.value.lower():
            raise RelationshipIntegrityError("candidate digest must be SHA-256")
        try:
            int(self.value, 16)
        except ValueError as exc:
            raise RelationshipIntegrityError("candidate digest must be hexadecimal") from exc

    @classmethod
    def of(cls, candidate: DecisionCandidate) -> CandidateDigest:
        content = candidate.to_dict()
        content.pop("content_digest")
        return cls(_digest(content))


@dataclass(frozen=True, slots=True)
class CandidateReferenceResolver:
    """Read-only resolver for all candidate dependencies."""

    evidence: EvidenceRegistry
    hypotheses: HypothesisRegistry
    scenarios: ScenarioRegistry
    graph: DecisionDependencyGraph

    def validate(self, candidate: DecisionCandidate, graph_node_ids: tuple[str, ...] = ()) -> None:
        if not candidate.scenarios:
            raise RelationshipIntegrityError("candidate requires a scenario reference")
        if len(candidate.evidence) != len(set(candidate.evidence)):
            raise RelationshipIntegrityError("duplicate candidate evidence reference")
        if len(candidate.hypotheses) != len(set(candidate.hypotheses)):
            raise RelationshipIntegrityError("duplicate candidate hypothesis reference")
        if len(candidate.scenarios) != len(set(candidate.scenarios)):
            raise RelationshipIntegrityError("duplicate candidate scenario reference")
        if len(graph_node_ids) != len(set(graph_node_ids)):
            raise RelationshipIntegrityError("duplicate candidate graph node reference")
        if any(self.evidence.by_reference(item) is None for item in candidate.evidence):
            raise RelationshipIntegrityError("missing candidate evidence reference")
        if any(self.hypotheses.by_reference(item) is None for item in candidate.hypotheses):
            raise RelationshipIntegrityError("missing candidate hypothesis reference")
        for reference in candidate.scenarios:
            scenario = self.scenarios.by_reference(reference)
            if scenario is None:
                raise RelationshipIntegrityError("missing candidate scenario reference")
            if self.scenarios.entry(reference.identifier).state not in _VALID_SCENARIO_STATES:
                raise RelationshipIntegrityError("candidate scenario is not validated")
        for node_id in graph_node_ids:
            try:
                self.graph.node(node_id)
            except KeyError as exc:
                raise RelationshipIntegrityError("missing candidate graph node reference") from exc
        if CandidateDigest.of(candidate).value != candidate.content_digest.value:
            raise RelationshipIntegrityError("candidate content digest mismatch")


@dataclass(frozen=True, slots=True)
class CandidateBuilder:
    """Build candidates by copying, never recomputing, scenario assessments."""

    resolver: CandidateReferenceResolver

    def build(
        self,
        scenario_id: str,
        candidate_type: CandidateType,
        *,
        candidate_id: str | None = None,
        arguments: tuple[str, ...] = (),
        constraints: tuple[ConstraintEvaluation, ...] = (),
        graph_node_ids: tuple[str, ...] = (),
    ) -> DecisionCandidate:
        scenario = self.resolver.scenarios.get(scenario_id)
        if scenario is None:
            raise RelationshipIntegrityError("unknown candidate scenario")
        if self.resolver.scenarios.entry(scenario_id).state not in _VALID_SCENARIO_STATES:
            raise RelationshipIntegrityError("candidate scenario is not validated")
        evidence = tuple(
            sorted(
                set(scenario.supporting_evidence + scenario.contradicting_evidence),
                key=lambda item: (item.identifier, item.version),
            )
        )
        hypotheses = tuple(
            sorted(scenario.hypotheses, key=lambda item: (item.identifier, item.version))
        )
        scenario_reference = ScenarioReference(scenario.scenario_id, scenario.metadata.version)
        identifier = (
            candidate_id
            or f"candidate-{_digest({'scenario': scenario_reference.to_dict(), 'type': candidate_type.value, 'arguments': arguments, 'graph_nodes': tuple(sorted(graph_node_ids))})[:24]}"
        )
        candidate = DecisionCandidate(
            candidate_id=identifier,
            candidate_type=candidate_type,
            arguments=arguments,
            evidence=evidence,
            hypotheses=hypotheses,
            scenarios=(scenario_reference,),
            constraints=constraints,
            confidence=scenario.confidence,
            quality=scenario.quality,
            validity=scenario.validity,
            uncertainty=scenario.uncertainty,
            priority=DecisionPriority.NORMAL,
            invalidation_conditions=scenario.invalidation_conditions,
            metadata=scenario.metadata,
            content_digest=DecisionDigest("0" * 64),
        )
        candidate = replace(
            candidate, content_digest=DecisionDigest(CandidateDigest.of(candidate).value)
        )
        self.resolver.validate(candidate, graph_node_ids)
        return candidate


@dataclass(frozen=True, slots=True)
class CandidateCollection:
    """Immutable identifier-ordered candidate collection."""

    items: tuple[DecisionCandidate, ...] = ()
    graph_links: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.items, tuple) or not isinstance(self.graph_links, tuple):
            raise RelationshipIntegrityError("candidate collection values must be tuples")
        ordered = tuple(sorted(self.items, key=lambda item: item.candidate_id))
        identifiers = tuple(item.candidate_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise RelationshipIntegrityError("duplicate candidate identifier")
        links = tuple(
            sorted(
                ((identifier, tuple(sorted(nodes))) for identifier, nodes in self.graph_links),
                key=lambda item: item[0],
            )
        )
        link_identifiers = tuple(identifier for identifier, _ in links)
        if len(link_identifiers) != len(set(link_identifiers)):
            raise RelationshipIntegrityError("duplicate candidate graph link identifier")
        if any(identifier not in set(identifiers) for identifier, _ in links):
            raise RelationshipIntegrityError("candidate graph link has no candidate")
        if any(len(nodes) != len(set(nodes)) for _, nodes in links):
            raise RelationshipIntegrityError("duplicate candidate graph link")
        object.__setattr__(self, "items", ordered)
        object.__setattr__(self, "graph_links", links)

    def __iter__(self) -> Iterator[DecisionCandidate]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def get(self, identifier: str) -> DecisionCandidate | None:
        return next((item for item in self.items if item.candidate_id == identifier), None)

    def filter(self, predicate: Callable[[DecisionCandidate], bool]) -> CandidateCollection:
        selected = tuple(item for item in self.items if predicate(item))
        ids = {item.candidate_id for item in selected}
        return CandidateCollection(
            selected, tuple(link for link in self.graph_links if link[0] in ids)
        )

    def by_type(self, candidate_type: CandidateType) -> CandidateCollection:
        return self.filter(lambda item: item.candidate_type is candidate_type)

    def by_scenario(self, reference: ScenarioReference) -> CandidateCollection:
        return self.filter(lambda item: reference in item.scenarios)

    def by_evidence(self, reference: EvidenceReference) -> CandidateCollection:
        return self.filter(lambda item: reference in item.evidence)

    def by_graph_node(self, node_id: str) -> CandidateCollection:
        ids = {identifier for identifier, nodes in self.graph_links if node_id in nodes}
        return self.filter(lambda item: item.candidate_id in ids)

    def by_digest(self, digest: CandidateDigest) -> CandidateCollection:
        return self.filter(lambda item: item.content_digest.value == digest.value)

    def group_by_type(self) -> tuple[tuple[CandidateType, CandidateCollection], ...]:
        return tuple((kind, group) for kind in CandidateType if (group := self.by_type(kind)).items)

    def to_payload(self) -> dict[str, object]:
        """Return the canonical, serialization-safe collection payload."""
        return {
            "candidates": [item.to_dict() for item in self.items],
            "graph_links": [[identifier, list(nodes)] for identifier, nodes in self.graph_links],
        }


@dataclass(frozen=True, slots=True)
class _CandidateEntry:
    candidate: DecisionCandidate
    state: CandidateLifecycleState
    graph_node_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CandidateRegistry:
    """Immutable candidate registry with deterministic indexes."""

    entries: tuple[_CandidateEntry, ...] = ()

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.entries, key=lambda item: item.candidate.candidate_id))
        identifiers = tuple(item.candidate.candidate_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise RelationshipIntegrityError("duplicate candidate identifier")
        object.__setattr__(self, "entries", ordered)

    def register(
        self,
        candidate: DecisionCandidate,
        resolver: CandidateReferenceResolver,
        graph_node_ids: tuple[str, ...] = (),
    ) -> CandidateRegistry:
        if self.get(candidate.candidate_id) is not None:
            raise RelationshipIntegrityError("duplicate candidate identifier")
        graph_node_ids = tuple(sorted(graph_node_ids))
        resolver.validate(candidate, graph_node_ids)
        result = CandidateRegistry(
            self.entries
            + (_CandidateEntry(candidate, CandidateLifecycleState.CREATED, graph_node_ids),)
        )
        for state in (
            CandidateLifecycleState.GENERATED,
            CandidateLifecycleState.VALIDATED,
            CandidateLifecycleState.REGISTERED,
            CandidateLifecycleState.AVAILABLE,
        ):
            result = result.transition(candidate.candidate_id, state)
        return result

    def transition(self, identifier: str, target: CandidateLifecycleState) -> CandidateRegistry:
        entry = self.entry(identifier)
        if _TRANSITIONS.get(entry.state) is not target:
            raise RelationshipIntegrityError(
                f"invalid candidate transition: {entry.state} -> {target}"
            )
        replacement = _CandidateEntry(entry.candidate, target, entry.graph_node_ids)
        return CandidateRegistry(
            tuple(
                replacement if item.candidate.candidate_id == identifier else item
                for item in self.entries
            )
        )

    def entry(self, identifier: str) -> _CandidateEntry:
        found = next(
            (item for item in self.entries if item.candidate.candidate_id == identifier),
            None,
        )
        if found is None:
            raise KeyError(identifier)
        return found

    def get(self, identifier: str) -> DecisionCandidate | None:
        found = next(
            (item for item in self.entries if item.candidate.candidate_id == identifier),
            None,
        )
        return None if found is None else found.candidate

    def collection(self) -> CandidateCollection:
        return CandidateCollection(
            tuple(item.candidate for item in self.entries),
            tuple((item.candidate.candidate_id, item.graph_node_ids) for item in self.entries),
        )

    def by_type(self, value: CandidateType) -> CandidateCollection:
        return self.collection().by_type(value)

    def by_scenario(self, value: ScenarioReference) -> CandidateCollection:
        return self.collection().by_scenario(value)

    def by_evidence(self, value: EvidenceReference) -> CandidateCollection:
        return self.collection().by_evidence(value)

    def by_graph_node(self, value: str) -> CandidateCollection:
        return self.collection().by_graph_node(value)

    def by_digest(self, value: CandidateDigest) -> CandidateCollection:
        return self.collection().by_digest(value)


@dataclass(frozen=True, slots=True)
class CandidateStatistics:
    """Structural candidate counts only."""

    total: int
    by_type: tuple[tuple[CandidateType, int], ...]
    by_state: tuple[tuple[CandidateLifecycleState, int], ...]

    @classmethod
    def from_registry(cls, registry: CandidateRegistry) -> CandidateStatistics:
        return cls(
            len(registry.entries),
            tuple((kind, len(registry.by_type(kind))) for kind in CandidateType),
            tuple(
                (state, sum(item.state is state for item in registry.entries))
                for state in CandidateLifecycleState
            ),
        )


@dataclass(frozen=True, slots=True)
class CandidateAudit:
    """Read-only generation counters and statistics."""

    generated: int = 0
    registered: int = 0
    duplicates: int = 0
    validation_failures: int = 0
    statistics: CandidateStatistics = CandidateStatistics(0, (), ())


@dataclass(frozen=True, slots=True)
class CandidateDiagnostics:
    """Detected inconsistencies; diagnostics never mutate state."""

    issues: tuple[str, ...] = ()

    @classmethod
    def inspect(
        cls,
        registry: CandidateRegistry,
        resolver: CandidateReferenceResolver,
        snapshot: CandidateSnapshot | None = None,
    ) -> CandidateDiagnostics:
        issues: list[str] = []
        identifiers = [item.candidate.candidate_id for item in registry.entries]
        if len(identifiers) != len(set(identifiers)):
            issues.append("duplicate_candidate_identifiers")
        for entry in registry.entries:
            if not isinstance(entry.candidate.candidate_type, CandidateType):
                issues.append(f"invalid_type:{entry.candidate.candidate_id}")
            if not isinstance(entry.state, CandidateLifecycleState):
                issues.append(f"invalid_lifecycle:{entry.candidate.candidate_id}")
            try:
                resolver.validate(entry.candidate, entry.graph_node_ids)
            except (RelationshipIntegrityError, KeyError):
                issues.append(f"invalid_references:{entry.candidate.candidate_id}")
        if snapshot is not None:
            if snapshot.collection != registry.collection():
                issues.append("snapshot_registry_mismatch")
            if snapshot.digest != CandidateDigest(_digest(snapshot.collection.to_payload())):
                issues.append("snapshot_digest_mismatch")
        return cls(tuple(sorted(set(issues))))


@dataclass(frozen=True, slots=True)
class CandidateSnapshot:
    """Immutable, comparable canonical snapshot."""

    collection: CandidateCollection
    digest: CandidateDigest
    version: int = 1

    def __post_init__(self) -> None:
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise RelationshipIntegrityError("candidate snapshot version must be positive")
        expected = CandidateDigest(_digest(self.collection.to_payload()))
        if self.digest != expected:
            raise RelationshipIntegrityError("candidate snapshot digest mismatch")

    @classmethod
    def capture(cls, collection: CandidateCollection) -> CandidateSnapshot:
        return cls(collection, CandidateDigest(_digest(collection.to_payload())))

    def to_json(self) -> str:
        return _canonical_json(
            {"version": self.version, "digest": self.digest.value, **self.collection.to_payload()}
        )

    @classmethod
    def from_json(cls, value: str) -> CandidateSnapshot:
        """Restore a snapshot and verify its canonical identity."""
        try:
            payload = _as_mapping(json.loads(value), "candidate snapshot")
            candidates = tuple(
                _candidate_from_payload(item)
                for item in _as_sequence(payload.get("candidates"), "candidates")
            )
            graph_links = tuple(
                _graph_link_from_payload(item)
                for item in _as_sequence(payload.get("graph_links"), "graph links")
            )
            collection = CandidateCollection(candidates, graph_links)
            return cls(
                collection,
                CandidateDigest(_as_text(payload.get("digest"), "digest")),
                _as_integer(payload.get("version"), "version"),
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, RelationshipIntegrityError):
                raise
            raise RelationshipIntegrityError("invalid candidate snapshot") from exc


def _as_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise RelationshipIntegrityError(f"{label} must be an object")
    return value


def _as_sequence(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise RelationshipIntegrityError(f"{label} must be an array")
    return value


def _as_text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise RelationshipIntegrityError(f"{label} must be text")
    return value


def _as_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RelationshipIntegrityError(f"{label} must be an integer")
    return value


def _as_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RelationshipIntegrityError(f"{label} must be numeric")
    return float(value)


def _as_boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise RelationshipIntegrityError(f"{label} must be boolean")
    return value


def _reference_from_payload[
    ReferenceT: (EvidenceReference, HypothesisReference, ScenarioReference)
](
    value: object, reference_type: type[ReferenceT]
) -> ReferenceT:
    payload = _as_mapping(value, "reference")
    return reference_type(
        _as_text(payload.get("identifier"), "reference identifier"),
        _as_integer(payload.get("version"), "reference version"),
    )


def _candidate_from_payload(value: object) -> DecisionCandidate:
    payload = _as_mapping(value, "candidate")
    confidence = _as_mapping(payload.get("confidence"), "confidence")
    quality = _as_mapping(payload.get("quality"), "quality")
    validity = _as_mapping(payload.get("validity"), "validity")
    uncertainty = _as_mapping(payload.get("uncertainty"), "uncertainty")
    metadata = _as_mapping(payload.get("metadata"), "metadata")
    digest = _as_mapping(payload.get("content_digest"), "content digest")
    constraints: list[ConstraintEvaluation] = []
    for item in _as_sequence(payload.get("constraints"), "constraints"):
        constraint = _as_mapping(item, "constraint")
        constraints.append(
            ConstraintEvaluation(
                _as_text(constraint.get("constraint_id"), "constraint identifier"),
                ConstraintType(_as_text(constraint.get("constraint_type"), "constraint type")),
                _as_boolean(constraint.get("accepted"), "constraint accepted"),
                _as_boolean(constraint.get("mandatory"), "constraint mandatory"),
                _as_text(constraint.get("reason"), "constraint reason"),
                _as_integer(constraint.get("version"), "constraint version"),
            )
        )
    return DecisionCandidate(
        candidate_id=_as_text(payload.get("candidate_id"), "candidate identifier"),
        candidate_type=CandidateType(_as_text(payload.get("candidate_type"), "candidate type")),
        arguments=tuple(
            _as_text(item, "argument")
            for item in _as_sequence(payload.get("arguments"), "arguments")
        ),
        evidence=tuple(
            _reference_from_payload(item, EvidenceReference)
            for item in _as_sequence(payload.get("evidence"), "evidence")
        ),
        hypotheses=tuple(
            _reference_from_payload(item, HypothesisReference)
            for item in _as_sequence(payload.get("hypotheses"), "hypotheses")
        ),
        scenarios=tuple(
            _reference_from_payload(item, ScenarioReference)
            for item in _as_sequence(payload.get("scenarios"), "scenarios")
        ),
        constraints=tuple(constraints),
        confidence=Confidence(
            _as_number(confidence.get("value"), "confidence value"),
            ConfidenceLevel(_as_text(confidence.get("level"), "confidence level")),
        ),
        quality=Quality(
            _as_number(quality.get("value"), "quality value"),
            QualityLevel(_as_text(quality.get("level"), "quality level")),
        ),
        validity=Validity(
            _as_number(validity.get("value"), "validity value"),
            ValidityLevel(_as_text(validity.get("level"), "validity level")),
        ),
        uncertainty=Uncertainty(_as_number(uncertainty.get("value"), "uncertainty value")),
        priority=DecisionPriority(_as_text(payload.get("priority"), "priority")),
        invalidation_conditions=tuple(
            _as_text(item, "invalidation condition")
            for item in _as_sequence(
                payload.get("invalidation_conditions"), "invalidation conditions"
            )
        ),
        metadata=DecisionMetadata(
            _as_integer(metadata.get("version"), "metadata version"),
            _as_text(metadata.get("logical_timestamp"), "logical timestamp"),
            _as_text(metadata.get("source"), "metadata source"),
        ),
        content_digest=DecisionDigest(
            _as_text(digest.get("value"), "content digest value"),
            _as_text(digest.get("algorithm"), "content digest algorithm"),
        ),
    )


def _graph_link_from_payload(value: object) -> tuple[str, tuple[str, ...]]:
    payload = _as_sequence(value, "graph link")
    if len(payload) != 2:
        raise RelationshipIntegrityError("graph link must contain two values")
    return (
        _as_text(payload[0], "graph link candidate"),
        tuple(_as_text(item, "graph node") for item in _as_sequence(payload[1], "graph nodes")),
    )


@dataclass(frozen=True, slots=True)
class CandidateGenerationReport:
    """Complete deterministic result of one generation request."""

    candidates: CandidateCollection
    registry: CandidateRegistry
    snapshot: CandidateSnapshot
    audit: CandidateAudit
    diagnostics: CandidateDiagnostics


@dataclass(frozen=True, slots=True)
class CandidateEngine:
    """Generate zero, one, or multiple candidates from a validated scenario."""

    resolver: CandidateReferenceResolver
    registry: CandidateRegistry = CandidateRegistry()

    def generate(
        self,
        scenario_id: str,
        candidate_types: tuple[CandidateType, ...],
        *,
        graph_node_ids: tuple[str, ...] = (),
    ) -> CandidateGenerationReport:
        registry = self.registry
        generated = 0
        registered = 0
        duplicates = 0
        failures = 0
        for candidate_type in sorted(candidate_types, key=lambda item: item.value):
            try:
                candidate = CandidateBuilder(self.resolver).build(
                    scenario_id, candidate_type, graph_node_ids=graph_node_ids
                )
                generated += 1
                if registry.get(candidate.candidate_id) is not None:
                    duplicates += 1
                    continue
                registry = registry.register(candidate, self.resolver, graph_node_ids)
                registered += 1
            except RelationshipIntegrityError:
                failures += 1
        collection = registry.collection()
        snapshot = CandidateSnapshot.capture(collection)
        audit = CandidateAudit(
            generated,
            registered,
            duplicates,
            failures,
            CandidateStatistics.from_registry(registry),
        )
        diagnostics = CandidateDiagnostics.inspect(registry, self.resolver, snapshot)
        return CandidateGenerationReport(collection, registry, snapshot, audit, diagnostics)


__all__ = [
    "CandidateAudit",
    "CandidateBuilder",
    "CandidateCollection",
    "CandidateDiagnostics",
    "CandidateDigest",
    "CandidateEngine",
    "CandidateGenerationReport",
    "CandidateLifecycleState",
    "CandidateReferenceResolver",
    "CandidateRegistry",
    "CandidateSnapshot",
    "CandidateStatistics",
]
