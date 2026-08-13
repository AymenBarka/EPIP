"""Deterministic confidence assessments for EPIP-016 decision candidates.

Assessments describe the strength and traceability of one candidate at a time.
They are not probabilities, rankings, recommendations, or trading signals.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass

from epip.core.integrity import RelationshipIntegrityError, require_text, require_unit_interval
from epip.decision.candidate import CandidateReferenceResolver, CandidateRegistry
from epip.decision.domain import (
    CandidateReference,
    Confidence,
    ConfidenceLevel,
    DecisionCandidate,
    Quality,
    QualityLevel,
    Uncertainty,
    Validity,
    ValidityLevel,
)
from epip.decision.models import DecisionConfidence, DecisionScore


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True
    )


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _confidence_level(value: float) -> ConfidenceLevel:
    return tuple(ConfidenceLevel)[min(int(value * 5), 4)]


def _quality_level(value: float) -> QualityLevel:
    return tuple(QualityLevel)[min(int(value * 5), 4)]


def _validity_level(value: float) -> ValidityLevel:
    if value == 0:
        return ValidityLevel.INVALID
    if value < 0.5:
        return ValidityLevel.UNKNOWN
    if value < 1:
        return ValidityLevel.CONDITIONAL
    return ValidityLevel.VALID


@dataclass(frozen=True, slots=True)
class ConfidenceDigest:
    """Canonical SHA-256 assessment or snapshot digest."""

    value: str
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if self.algorithm != "sha256" or len(self.value) != 64 or self.value != self.value.lower():
            raise RelationshipIntegrityError("confidence digest must be SHA-256")
        try:
            int(self.value, 16)
        except ValueError as exc:
            raise RelationshipIntegrityError("confidence digest must be hexadecimal") from exc

    @classmethod
    def of(cls, assessment: ConfidenceAssessment) -> ConfidenceDigest:
        return cls(_sha256(assessment.content_payload()))


@dataclass(frozen=True, slots=True)
class ConfidenceAssessment:
    """Eight independent descriptive metrics attached to one candidate."""

    assessment_id: str
    candidate: CandidateReference
    confidence: Confidence
    quality: Quality
    validity: Validity
    uncertainty: Uncertainty
    evidence_coverage: float
    scenario_consistency: float
    completeness: float
    traceability: float
    graph_node_ids: tuple[str, ...]
    digest: ConfidenceDigest

    def __post_init__(self) -> None:
        require_text(self.assessment_id, "assessment.identifier")
        if not isinstance(self.graph_node_ids, tuple):
            raise RelationshipIntegrityError("assessment graph references must be a tuple")
        if len(self.graph_node_ids) != len(set(self.graph_node_ids)):
            raise RelationshipIntegrityError("duplicate assessment graph reference")
        for name in ("evidence_coverage", "scenario_consistency", "completeness", "traceability"):
            require_unit_interval(getattr(self, name), f"assessment.{name}")
        if self.digest != ConfidenceDigest.of(self):
            raise RelationshipIntegrityError("confidence assessment digest mismatch")

    def content_payload(self) -> dict[str, object]:
        return {
            "assessment_id": self.assessment_id,
            "candidate": self.candidate.to_dict(),
            "completeness": self.completeness,
            "confidence": self.confidence.to_dict(),
            "evidence_coverage": self.evidence_coverage,
            "graph_node_ids": list(self.graph_node_ids),
            "quality": self.quality.to_dict(),
            "scenario_consistency": self.scenario_consistency,
            "traceability": self.traceability,
            "uncertainty": self.uncertainty.to_dict(),
            "validity": self.validity.to_dict(),
        }

    def to_payload(self) -> dict[str, object]:
        return {**self.content_payload(), "digest": self.digest.value}

    @classmethod
    def create(
        cls,
        assessment_id: str,
        candidate: CandidateReference,
        confidence: Confidence,
        quality: Quality,
        validity: Validity,
        uncertainty: Uncertainty,
        evidence_coverage: float,
        scenario_consistency: float,
        completeness: float,
        traceability: float,
        graph_node_ids: tuple[str, ...],
    ) -> ConfidenceAssessment:
        instance = object.__new__(cls)
        values = (
            ("assessment_id", assessment_id),
            ("candidate", candidate),
            ("confidence", confidence),
            ("quality", quality),
            ("validity", validity),
            ("uncertainty", uncertainty),
            ("evidence_coverage", evidence_coverage),
            ("scenario_consistency", scenario_consistency),
            ("completeness", completeness),
            ("traceability", traceability),
            ("graph_node_ids", graph_node_ids),
        )
        for name, value in values:
            object.__setattr__(instance, name, value)
        object.__setattr__(instance, "digest", ConfidenceDigest.of(instance))
        instance.__post_init__()
        return instance


@dataclass(frozen=True, slots=True)
class ConfidenceBuilder:
    """Propagate candidate provenance using explicit equal-weight arithmetic means."""

    resolver: CandidateReferenceResolver

    def build(
        self,
        candidate: DecisionCandidate,
        *,
        graph_node_ids: tuple[str, ...] = (),
        assessment_id: str | None = None,
    ) -> ConfidenceAssessment:
        graph_node_ids = tuple(sorted(graph_node_ids))
        self.resolver.validate(candidate, graph_node_ids)
        evidence = tuple(self.resolver.evidence.by_reference(item) for item in candidate.evidence)
        hypotheses = tuple(
            self.resolver.hypotheses.by_reference(item) for item in candidate.hypotheses
        )
        scenarios = tuple(
            self.resolver.scenarios.by_reference(item) for item in candidate.scenarios
        )
        sources = (candidate,) + tuple(item for item in evidence + hypotheses + scenarios if item)
        confidence_value = _mean(tuple(item.confidence.value for item in sources))
        quality_value = _mean(tuple(item.quality.value for item in sources))
        validity_value = _mean(tuple(item.validity.value for item in sources))
        uncertainty_value = _mean(tuple(item.uncertainty.value for item in sources))
        reference_total = (
            len(candidate.evidence) + len(candidate.hypotheses) + len(candidate.scenarios)
        )
        resolved_total = len(evidence) + len(hypotheses) + len(scenarios)
        coverage = resolved_total / reference_total if reference_total else 1.0
        consistent = sum(
            set(item.hypotheses).issubset(candidate.hypotheses)
            and set(item.supporting_evidence + item.contradicting_evidence).issubset(
                candidate.evidence
            )
            for item in scenarios
            if item is not None
        )
        scenario_consistency = consistent / len(scenarios) if scenarios else 1.0
        completeness = (
            sum(
                (
                    bool(candidate.candidate_id),
                    bool(candidate.evidence),
                    bool(candidate.hypotheses),
                    bool(candidate.scenarios),
                    bool(graph_node_ids),
                )
            )
            / 5
        )
        trace_expected = reference_total + len(graph_node_ids)
        traceability = (
            (resolved_total + len(graph_node_ids)) / trace_expected if trace_expected else 1.0
        )
        identifier = (
            assessment_id
            or f"confidence-{_sha256({'candidate': candidate.candidate_id, 'version': candidate.metadata.version, 'graph': graph_node_ids})[:24]}"
        )
        return ConfidenceAssessment.create(
            identifier,
            CandidateReference(candidate.candidate_id, candidate.metadata.version),
            Confidence(confidence_value, _confidence_level(confidence_value)),
            Quality(quality_value, _quality_level(quality_value)),
            Validity(validity_value, _validity_level(validity_value)),
            Uncertainty(uncertainty_value),
            coverage,
            scenario_consistency,
            completeness,
            traceability,
            graph_node_ids,
        )


@dataclass(frozen=True, slots=True)
class ConfidenceCollection:
    """Immutable identifier-ordered assessment collection."""

    items: tuple[ConfidenceAssessment, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.items, tuple):
            raise RelationshipIntegrityError("confidence collection must be a tuple")
        ordered = tuple(sorted(self.items, key=lambda item: item.assessment_id))
        identifiers = tuple(item.assessment_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise RelationshipIntegrityError("duplicate confidence assessment identifier")
        object.__setattr__(self, "items", ordered)

    def __iter__(self) -> Iterator[ConfidenceAssessment]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def get(self, identifier: str) -> ConfidenceAssessment | None:
        return next((item for item in self.items if item.assessment_id == identifier), None)

    def filter(self, predicate: Callable[[ConfidenceAssessment], bool]) -> ConfidenceCollection:
        return ConfidenceCollection(tuple(item for item in self.items if predicate(item)))

    def by_candidate(self, candidate: CandidateReference) -> ConfidenceCollection:
        return self.filter(lambda item: item.candidate == candidate)

    def by_confidence_level(self, level: ConfidenceLevel) -> ConfidenceCollection:
        return self.filter(lambda item: item.confidence.level is level)

    def by_quality_level(self, level: QualityLevel) -> ConfidenceCollection:
        return self.filter(lambda item: item.quality.level is level)

    def by_digest(self, digest: ConfidenceDigest) -> ConfidenceCollection:
        return self.filter(lambda item: item.digest == digest)

    def group_by_confidence_level(self) -> tuple[tuple[ConfidenceLevel, ConfidenceCollection], ...]:
        return tuple(
            (level, group)
            for level in ConfidenceLevel
            if (group := self.by_confidence_level(level)).items
        )

    def to_payload(self) -> list[dict[str, object]]:
        return [item.to_payload() for item in self.items]


@dataclass(frozen=True, slots=True)
class ConfidenceRegistry:
    """Immutable deterministic assessment registry."""

    assessments: tuple[ConfidenceAssessment, ...] = ()

    def __post_init__(self) -> None:
        collection = ConfidenceCollection(self.assessments)
        object.__setattr__(self, "assessments", collection.items)

    def register(self, assessment: ConfidenceAssessment) -> ConfidenceRegistry:
        if self.get(assessment.assessment_id) is not None:
            raise RelationshipIntegrityError("duplicate confidence assessment identifier")
        return ConfidenceRegistry(self.assessments + (assessment,))

    def get(self, identifier: str) -> ConfidenceAssessment | None:
        return self.collection().get(identifier)

    def collection(self) -> ConfidenceCollection:
        return ConfidenceCollection(self.assessments)

    def by_candidate(self, candidate: CandidateReference) -> ConfidenceCollection:
        return self.collection().by_candidate(candidate)

    def by_confidence_level(self, level: ConfidenceLevel) -> ConfidenceCollection:
        return self.collection().by_confidence_level(level)

    def by_quality_level(self, level: QualityLevel) -> ConfidenceCollection:
        return self.collection().by_quality_level(level)

    def by_digest(self, digest: ConfidenceDigest) -> ConfidenceCollection:
        return self.collection().by_digest(digest)


@dataclass(frozen=True, slots=True)
class ConfidenceStatistics:
    """Structural registry and coverage statistics."""

    total: int
    by_confidence_level: tuple[tuple[ConfidenceLevel, int], ...]
    by_quality_level: tuple[tuple[QualityLevel, int], ...]
    mean_evidence_coverage: float

    @classmethod
    def from_registry(cls, registry: ConfidenceRegistry) -> ConfidenceStatistics:
        values = registry.assessments
        return cls(
            len(values),
            tuple((level, len(registry.by_confidence_level(level))) for level in ConfidenceLevel),
            tuple((level, len(registry.by_quality_level(level))) for level in QualityLevel),
            _mean(tuple(item.evidence_coverage for item in values)) if values else 0.0,
        )


@dataclass(frozen=True, slots=True)
class ConfidenceAudit:
    """Read-only observable assessment counters."""

    assessments: int = 0
    duplicates: int = 0
    validation_failures: int = 0
    coverage: float = 0.0
    statistics: ConfidenceStatistics = ConfidenceStatistics(0, (), (), 0.0)


@dataclass(frozen=True, slots=True)
class ConfidenceSnapshot:
    """Canonical, serializable, replay-compatible confidence snapshot."""

    collection: ConfidenceCollection
    digest: ConfidenceDigest
    version: int = 1

    def __post_init__(self) -> None:
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise RelationshipIntegrityError("confidence snapshot version must be positive")
        if self.digest != ConfidenceDigest(_sha256(self.collection.to_payload())):
            raise RelationshipIntegrityError("confidence snapshot digest mismatch")

    @classmethod
    def capture(cls, collection: ConfidenceCollection) -> ConfidenceSnapshot:
        return cls(collection, ConfidenceDigest(_sha256(collection.to_payload())))

    def to_json(self) -> str:
        return _canonical_json(
            {
                "assessments": self.collection.to_payload(),
                "digest": self.digest.value,
                "version": self.version,
            }
        )

    @classmethod
    def from_json(cls, value: str) -> ConfidenceSnapshot:
        try:
            payload = json.loads(value)
            if not isinstance(payload, dict):
                raise RelationshipIntegrityError("confidence snapshot must be an object")
            version = payload["version"]
            digest = payload["digest"]
            assessments = payload["assessments"]
            if isinstance(version, bool) or not isinstance(version, int):
                raise RelationshipIntegrityError("confidence snapshot version must be an integer")
            if not isinstance(digest, str) or not isinstance(assessments, list):
                raise RelationshipIntegrityError("invalid confidence snapshot fields")
            collection = ConfidenceCollection(
                tuple(_assessment_from_payload(item) for item in assessments)
            )
            return cls(collection, ConfidenceDigest(digest), version)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            if isinstance(exc, RelationshipIntegrityError):
                raise
            raise RelationshipIntegrityError("invalid confidence snapshot") from exc


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise RelationshipIntegrityError(f"{label} must be an object")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise RelationshipIntegrityError(f"{label} must be text")
    return value


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RelationshipIntegrityError(f"{label} must be numeric")
    return float(value)


def _assessment_from_payload(value: object) -> ConfidenceAssessment:
    payload = _mapping(value, "assessment")
    candidate = _mapping(payload.get("candidate"), "candidate")
    confidence = _mapping(payload.get("confidence"), "confidence")
    quality = _mapping(payload.get("quality"), "quality")
    validity = _mapping(payload.get("validity"), "validity")
    uncertainty = _mapping(payload.get("uncertainty"), "uncertainty")
    graph = payload.get("graph_node_ids")
    if not isinstance(graph, list):
        raise RelationshipIntegrityError("graph references must be an array")
    return ConfidenceAssessment(
        _text(payload.get("assessment_id"), "assessment identifier"),
        CandidateReference(
            _text(candidate.get("identifier"), "candidate identifier"),
            int(_number(candidate.get("version"), "candidate version")),
        ),
        Confidence(
            _number(confidence.get("value"), "confidence value"),
            ConfidenceLevel(_text(confidence.get("level"), "confidence level")),
        ),
        Quality(
            _number(quality.get("value"), "quality value"),
            QualityLevel(_text(quality.get("level"), "quality level")),
        ),
        Validity(
            _number(validity.get("value"), "validity value"),
            ValidityLevel(_text(validity.get("level"), "validity level")),
        ),
        Uncertainty(_number(uncertainty.get("value"), "uncertainty value")),
        _number(payload.get("evidence_coverage"), "evidence coverage"),
        _number(payload.get("scenario_consistency"), "scenario consistency"),
        _number(payload.get("completeness"), "completeness"),
        _number(payload.get("traceability"), "traceability"),
        tuple(_text(item, "graph reference") for item in graph),
        ConfidenceDigest(_text(payload.get("digest"), "assessment digest")),
    )


@dataclass(frozen=True, slots=True)
class ConfidenceDiagnostics:
    """Read-only confidence consistency findings."""

    issues: tuple[str, ...] = ()

    @classmethod
    def inspect(
        cls,
        registry: ConfidenceRegistry,
        candidates: CandidateRegistry,
        resolver: CandidateReferenceResolver,
        snapshot: ConfidenceSnapshot | None = None,
    ) -> ConfidenceDiagnostics:
        issues: list[str] = []
        identifiers = tuple(item.assessment_id for item in registry.assessments)
        if len(identifiers) != len(set(identifiers)):
            issues.append("duplicate_assessment_identifiers")
        for item in registry.assessments:
            metrics = (
                item.confidence.value,
                item.quality.value,
                item.validity.value,
                item.uncertainty.value,
                item.evidence_coverage,
                item.scenario_consistency,
                item.traceability,
            )
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0.0 <= value <= 1.0
                for value in metrics
            ):
                issues.append(f"invalid_ranges:{item.assessment_id}")
            if (
                isinstance(item.completeness, bool)
                or not isinstance(item.completeness, (int, float))
                or not 0.0 <= item.completeness <= 1.0
            ):
                issues.append(f"invalid_completeness:{item.assessment_id}")
            candidate = candidates.get(item.candidate.identifier)
            if candidate is None or candidate.metadata.version != item.candidate.version:
                issues.append(f"missing_candidate:{item.assessment_id}")
                continue
            try:
                resolver.validate(candidate, item.graph_node_ids)
                if item.digest != ConfidenceDigest.of(item):
                    issues.append(f"digest_inconsistency:{item.assessment_id}")
            except (RelationshipIntegrityError, KeyError):
                issues.append(f"invalid_references:{item.assessment_id}")
        if snapshot is not None:
            if snapshot.collection != registry.collection():
                issues.append("snapshot_registry_mismatch")
            if snapshot.digest != ConfidenceDigest(_sha256(snapshot.collection.to_payload())):
                issues.append("snapshot_digest_mismatch")
        return cls(tuple(sorted(set(issues))))


@dataclass(frozen=True, slots=True)
class ConfidenceAssessmentReport:
    """Complete deterministic result of one assessment request."""

    assessments: ConfidenceCollection
    registry: ConfidenceRegistry
    snapshot: ConfidenceSnapshot
    audit: ConfidenceAudit
    diagnostics: ConfidenceDiagnostics


@dataclass(frozen=True, slots=True)
class ConfidenceEngine:
    """Assess candidates independently without comparing or selecting them."""

    resolver: CandidateReferenceResolver
    candidates: CandidateRegistry
    registry: ConfidenceRegistry = ConfidenceRegistry()

    def assess(
        self,
        candidate_ids: tuple[str, ...],
        *,
        graph_node_ids: tuple[str, ...] = (),
    ) -> ConfidenceAssessmentReport:
        registry = self.registry
        assessed = duplicates = failures = 0
        for identifier in sorted(candidate_ids):
            candidate = self.candidates.get(identifier)
            if candidate is None:
                failures += 1
                continue
            try:
                assessment = ConfidenceBuilder(self.resolver).build(
                    candidate, graph_node_ids=graph_node_ids
                )
                if registry.get(assessment.assessment_id) is not None:
                    duplicates += 1
                    continue
                registry = registry.register(assessment)
                assessed += 1
            except RelationshipIntegrityError:
                failures += 1
        collection = registry.collection()
        snapshot = ConfidenceSnapshot.capture(collection)
        statistics = ConfidenceStatistics.from_registry(registry)
        audit = ConfidenceAudit(
            assessed, duplicates, failures, statistics.mean_evidence_coverage, statistics
        )
        diagnostics = ConfidenceDiagnostics.inspect(
            registry, self.candidates, self.resolver, snapshot
        )
        return ConfidenceAssessmentReport(collection, registry, snapshot, audit, diagnostics)


class ConfidenceCalculator:
    """Legacy EPIP-012 score normalization API."""

    def calculate(self, score: DecisionScore) -> DecisionConfidence:
        return DecisionConfidence(max(0.0, min(1.0, score.total / 100.0)))


__all__ = [
    "ConfidenceAssessment",
    "ConfidenceAssessmentReport",
    "ConfidenceAudit",
    "ConfidenceBuilder",
    "ConfidenceCalculator",
    "ConfidenceCollection",
    "ConfidenceDiagnostics",
    "ConfidenceDigest",
    "ConfidenceEngine",
    "ConfidenceRegistry",
    "ConfidenceSnapshot",
    "ConfidenceStatistics",
]
