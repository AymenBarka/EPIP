"""Deterministic final decision selection for EPIP-016.

The engine selects from immutable candidates and assessments. It never analyses
markets, derives confidence, evaluates financial facts, or executes decisions.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum

from epip.core.integrity import RelationshipIntegrityError, require_text
from epip.decision.candidate import CandidateReferenceResolver, CandidateRegistry
from epip.decision.confidence import ConfidenceAssessment, ConfidenceRegistry
from epip.decision.domain import (
    CandidateReference,
    CandidateType,
    Confidence,
    ConfidenceLevel,
    ConstraintEvaluation,
    ConstraintType,
    Decision,
    DecisionAlternative,
    DecisionCandidate,
    DecisionContext,
    DecisionDigest,
    DecisionExplanation,
    DecisionMetadata,
    DecisionPriority,
    DecisionReason,
    DecisionStatus,
    DecisionType,
    EvidenceReference,
    ExplanationLevel,
    HypothesisReference,
    Recommendation,
    RecommendationType,
    ScenarioReference,
    Uncertainty,
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True
    )


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _content_digest(value: object) -> DecisionDigest:
    if not hasattr(value, "to_dict"):
        raise RelationshipIntegrityError("decision content is not canonical")
    payload = value.to_dict()
    payload.pop("content_digest", None)
    return DecisionDigest(_sha256(payload))


class DecisionLifecycleState(StrEnum):
    """Explicit Programme G decision lifecycle."""

    CREATED = "created"
    SELECTED = "selected"
    VALIDATED = "validated"
    REGISTERED = "registered"
    AVAILABLE = "available"
    SNAPSHOTTED = "snapshotted"
    ARCHIVED = "archived"
    DISCARDED = "discarded"


_TRANSITIONS = {
    DecisionLifecycleState.CREATED: DecisionLifecycleState.SELECTED,
    DecisionLifecycleState.SELECTED: DecisionLifecycleState.VALIDATED,
    DecisionLifecycleState.VALIDATED: DecisionLifecycleState.REGISTERED,
    DecisionLifecycleState.REGISTERED: DecisionLifecycleState.AVAILABLE,
    DecisionLifecycleState.AVAILABLE: DecisionLifecycleState.SNAPSHOTTED,
    DecisionLifecycleState.SNAPSHOTTED: DecisionLifecycleState.ARCHIVED,
    DecisionLifecycleState.ARCHIVED: DecisionLifecycleState.DISCARDED,
}


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    """Immutable causal trace for selected and rejected candidates."""

    selected_candidate: CandidateReference
    rejected_candidates: tuple[CandidateReference, ...]
    applied_constraints: tuple[tuple[str, bool, bool], ...]
    confidence_assessment_id: str
    confidence_digest: str
    evidence: tuple[EvidenceReference, ...]
    hypotheses: tuple[HypothesisReference, ...]
    scenarios: tuple[ScenarioReference, ...]
    graph_node_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        require_text(self.confidence_assessment_id, "trace.confidence_assessment_id")
        require_text(self.confidence_digest, "trace.confidence_digest")
        tuple_fields = (
            self.rejected_candidates,
            self.applied_constraints,
            self.evidence,
            self.hypotheses,
            self.scenarios,
            self.graph_node_ids,
        )
        if any(not isinstance(value, tuple) for value in tuple_fields):
            raise RelationshipIntegrityError("decision trace values must be tuples")
        if len(self.graph_node_ids) != len(set(self.graph_node_ids)):
            raise RelationshipIntegrityError("duplicate decision graph reference")

    def to_payload(self) -> dict[str, object]:
        return {
            "applied_constraints": [list(item) for item in self.applied_constraints],
            "confidence_assessment_id": self.confidence_assessment_id,
            "confidence_digest": self.confidence_digest,
            "evidence": [item.to_dict() for item in self.evidence],
            "graph_node_ids": list(self.graph_node_ids),
            "hypotheses": [item.to_dict() for item in self.hypotheses],
            "rejected_candidates": [item.to_dict() for item in self.rejected_candidates],
            "scenarios": [item.to_dict() for item in self.scenarios],
            "selected_candidate": self.selected_candidate.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class DecisionConstraintEvaluator:
    """Consume declared immutable constraint results without calculating them."""

    def evaluate(self, constraints: tuple[ConstraintEvaluation, ...]) -> bool:
        if not constraints:
            raise RelationshipIntegrityError("candidate has no declared decision constraints")
        identifiers = tuple(item.constraint_id for item in constraints)
        if len(identifiers) != len(set(identifiers)):
            raise RelationshipIntegrityError("duplicate decision constraint reference")
        return all(item.accepted for item in constraints if item.mandatory)


def _selection_key(item: tuple[DecisionCandidate, ConfidenceAssessment]) -> tuple[object, ...]:
    candidate, assessment = item
    return (
        -assessment.validity.value,
        -assessment.confidence.value,
        -assessment.quality.value,
        assessment.uncertainty.value,
        -assessment.evidence_coverage,
        -assessment.scenario_consistency,
        -assessment.completeness,
        -assessment.traceability,
        candidate.candidate_id,
    )


@dataclass(frozen=True, slots=True)
class DecisionSelector:
    """Apply the published constraint and lexicographic selection policy."""

    evaluator: DecisionConstraintEvaluator = DecisionConstraintEvaluator()

    def select(
        self,
        candidates: CandidateRegistry,
        assessments: ConfidenceRegistry,
    ) -> tuple[DecisionCandidate, ConfidenceAssessment, tuple[DecisionCandidate, ...]]:
        admissible: list[tuple[DecisionCandidate, ConfidenceAssessment]] = []
        rejected: list[DecisionCandidate] = []
        for entry in candidates.entries:
            candidate = entry.candidate
            matches = assessments.by_candidate(
                CandidateReference(candidate.candidate_id, candidate.metadata.version)
            ).items
            if len(matches) != 1:
                raise RelationshipIntegrityError(
                    "candidate requires exactly one confidence assessment"
                )
            if self.evaluator.evaluate(candidate.constraints):
                admissible.append((candidate, matches[0]))
            else:
                rejected.append(candidate)
        if not admissible:
            raise RelationshipIntegrityError("no admissible decision candidate")
        selected, assessment = min(admissible, key=_selection_key)
        rejected.extend(item[0] for item in admissible if item[0] != selected)
        rejected.sort(key=lambda item: item.candidate_id)
        return selected, assessment, tuple(rejected)


@dataclass(frozen=True, slots=True)
class DecisionExplanationBuilder:
    """Build explanation directly from candidate provenance and selection facts."""

    def build(
        self,
        selected: DecisionCandidate,
        rejected: tuple[DecisionCandidate, ...],
        assessment: ConfidenceAssessment,
    ) -> DecisionExplanation:
        alternatives = tuple(
            DecisionAlternative(
                CandidateReference(item.candidate_id, item.metadata.version),
                (
                    "mandatory_constraint_rejected"
                    if any(
                        constraint.mandatory and not constraint.accepted
                        for constraint in item.constraints
                    )
                    else "deterministic_selection_policy"
                ),
            )
            for item in rejected
        )
        reason = DecisionReason(
            "deterministic_selection",
            "Selected by declared constraints and the published lexicographic policy.",
            selected.evidence,
        )
        return DecisionExplanation(
            ExplanationLevel.AUDIT,
            selected.evidence,
            (),
            selected.hypotheses,
            (),
            selected.scenarios,
            selected.constraints,
            alternatives,
            (reason,),
            assessment.uncertainty,
        )


_DECISION_TYPES = {
    CandidateType.LONG: DecisionType.ENTER,
    CandidateType.SHORT: DecisionType.ENTER,
    CandidateType.WAIT: DecisionType.HOLD,
    CandidateType.EXIT: DecisionType.EXIT,
    CandidateType.REDUCE: DecisionType.ADJUST,
    CandidateType.ADD: DecisionType.ADJUST,
    CandidateType.INVALID: DecisionType.REJECT,
}


@dataclass(frozen=True, slots=True)
class _DecisionEntry:
    decision: Decision
    trace: DecisionTrace
    state: DecisionLifecycleState


@dataclass(frozen=True, slots=True)
class DecisionCollection:
    """Immutable identifier-ordered final decision collection."""

    items: tuple[Decision, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.items, tuple):
            raise RelationshipIntegrityError("decision collection must be a tuple")
        ordered = tuple(sorted(self.items, key=lambda item: item.decision_id))
        identifiers = tuple(item.decision_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise RelationshipIntegrityError("duplicate decision identifier")
        object.__setattr__(self, "items", ordered)

    def __iter__(self) -> Iterator[Decision]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def get(self, identifier: str) -> Decision | None:
        return next((item for item in self.items if item.decision_id == identifier), None)

    def filter(self, predicate: Callable[[Decision], bool]) -> DecisionCollection:
        return DecisionCollection(tuple(item for item in self.items if predicate(item)))

    def by_type(self, decision_type: DecisionType) -> DecisionCollection:
        return self.filter(lambda item: item.decision_type is decision_type)

    def by_candidate(self, candidate: CandidateReference) -> DecisionCollection:
        return self.filter(lambda item: item.candidate == candidate)

    def by_digest(self, digest: DecisionDigest) -> DecisionCollection:
        return self.filter(lambda item: item.content_digest == digest)

    def group_by_type(self) -> tuple[tuple[DecisionType, DecisionCollection], ...]:
        return tuple((kind, group) for kind in DecisionType if (group := self.by_type(kind)).items)


@dataclass(frozen=True, slots=True)
class DecisionRegistry:
    """Immutable decision registry with explicit lifecycle transitions."""

    entries: tuple[_DecisionEntry, ...] = ()

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.entries, key=lambda item: item.decision.decision_id))
        identifiers = tuple(item.decision.decision_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise RelationshipIntegrityError("duplicate decision identifier")
        object.__setattr__(self, "entries", ordered)

    def register(self, decision: Decision, trace: DecisionTrace) -> DecisionRegistry:
        if self.get(decision.decision_id) is not None:
            raise RelationshipIntegrityError("duplicate decision identifier")
        result = DecisionRegistry(
            self.entries + (_DecisionEntry(decision, trace, DecisionLifecycleState.CREATED),)
        )
        for state in (
            DecisionLifecycleState.SELECTED,
            DecisionLifecycleState.VALIDATED,
            DecisionLifecycleState.REGISTERED,
            DecisionLifecycleState.AVAILABLE,
        ):
            result = result.transition(decision.decision_id, state)
        return result

    def transition(self, identifier: str, target: DecisionLifecycleState) -> DecisionRegistry:
        entry = self.entry(identifier)
        if _TRANSITIONS.get(entry.state) is not target:
            raise RelationshipIntegrityError(
                f"invalid decision transition: {entry.state} -> {target}"
            )
        replacement = _DecisionEntry(entry.decision, entry.trace, target)
        return DecisionRegistry(
            tuple(
                replacement if item.decision.decision_id == identifier else item
                for item in self.entries
            )
        )

    def entry(self, identifier: str) -> _DecisionEntry:
        found = next(
            (item for item in self.entries if item.decision.decision_id == identifier), None
        )
        if found is None:
            raise KeyError(identifier)
        return found

    def get(self, identifier: str) -> Decision | None:
        found = next(
            (item for item in self.entries if item.decision.decision_id == identifier), None
        )
        return None if found is None else found.decision

    def collection(self) -> DecisionCollection:
        return DecisionCollection(tuple(item.decision for item in self.entries))

    def by_type(self, value: DecisionType) -> DecisionCollection:
        return self.collection().by_type(value)

    def by_candidate(self, value: CandidateReference) -> DecisionCollection:
        return self.collection().by_candidate(value)

    def by_digest(self, value: DecisionDigest) -> DecisionCollection:
        return self.collection().by_digest(value)


@dataclass(frozen=True, slots=True)
class DecisionStatistics:
    """Deterministic registry counts."""

    total: int
    by_type: tuple[tuple[DecisionType, int], ...]
    by_state: tuple[tuple[DecisionLifecycleState, int], ...]

    @classmethod
    def from_registry(cls, registry: DecisionRegistry) -> DecisionStatistics:
        return cls(
            len(registry.entries),
            tuple((kind, len(registry.by_type(kind))) for kind in DecisionType),
            tuple(
                (state, sum(entry.state is state for entry in registry.entries))
                for state in DecisionLifecycleState
            ),
        )


@dataclass(frozen=True, slots=True)
class DecisionAudit:
    """Read-only selection observations."""

    selected_decisions: int = 0
    rejected_candidates: int = 0
    constraint_applications: int = 0
    duplicates: int = 0
    validation_failures: int = 0
    statistics: DecisionStatistics = DecisionStatistics(0, (), ())


@dataclass(frozen=True, slots=True)
class DecisionSnapshot:
    """Immutable replay snapshot containing decisions and causal traces."""

    entries: tuple[_DecisionEntry, ...]
    digest: DecisionDigest
    version: int = 1

    def __post_init__(self) -> None:
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise RelationshipIntegrityError("decision snapshot version must be positive")
        if self.digest != DecisionDigest(_sha256(self.content_payload())):
            raise RelationshipIntegrityError("decision snapshot digest mismatch")

    def content_payload(self) -> list[dict[str, object]]:
        return [
            {
                "decision": entry.decision.to_dict(),
                "state": entry.state.value,
                "trace": entry.trace.to_payload(),
            }
            for entry in self.entries
        ]

    @classmethod
    def capture(cls, registry: DecisionRegistry) -> DecisionSnapshot:
        entries = registry.entries
        instance = object.__new__(cls)
        object.__setattr__(instance, "entries", entries)
        object.__setattr__(instance, "version", 1)
        object.__setattr__(instance, "digest", DecisionDigest(_sha256(instance.content_payload())))
        instance.__post_init__()
        return instance

    def to_json(self) -> str:
        return _canonical_json(
            {
                "digest": self.digest.value,
                "entries": self.content_payload(),
                "version": self.version,
            }
        )

    @classmethod
    def from_json(cls, value: str) -> DecisionSnapshot:
        try:
            payload = json.loads(value)
            if not isinstance(payload, dict):
                raise RelationshipIntegrityError("decision snapshot must be an object")
            version = payload["version"]
            digest = payload["digest"]
            entries = payload["entries"]
            if (
                isinstance(version, bool)
                or not isinstance(version, int)
                or not isinstance(digest, str)
                or not isinstance(entries, list)
            ):
                raise RelationshipIntegrityError("invalid decision snapshot fields")
            restored = tuple(_entry_from_payload(item) for item in entries)
            return cls(restored, DecisionDigest(digest), version)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            if isinstance(exc, RelationshipIntegrityError):
                raise
            raise RelationshipIntegrityError("invalid decision snapshot") from exc


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise RelationshipIntegrityError(f"{label} must be an object")
    return value


def _sequence(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise RelationshipIntegrityError(f"{label} must be an array")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise RelationshipIntegrityError(f"{label} must be text")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RelationshipIntegrityError(f"{label} must be an integer")
    return value


def _reference[
    ReferenceT: (CandidateReference, EvidenceReference, HypothesisReference, ScenarioReference)
](
    value: object, kind: type[ReferenceT]
) -> ReferenceT:
    payload = _mapping(value, "reference")
    return kind(
        _text(payload.get("identifier"), "reference identifier"),
        _integer(payload.get("version"), "reference version"),
    )


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RelationshipIntegrityError(f"{label} must be numeric")
    return float(value)


def _constraint(value: object) -> ConstraintEvaluation:
    item = _mapping(value, "constraint")
    accepted, mandatory = item.get("accepted"), item.get("mandatory")
    if not isinstance(accepted, bool) or not isinstance(mandatory, bool):
        raise RelationshipIntegrityError("constraint results must be boolean")
    return ConstraintEvaluation(
        _text(item.get("constraint_id"), "constraint identifier"),
        ConstraintType(_text(item.get("constraint_type"), "constraint type")),
        accepted,
        mandatory,
        _text(item.get("reason"), "constraint reason"),
        _integer(item.get("version"), "constraint version"),
    )


def _entry_from_payload(value: object) -> _DecisionEntry:
    entry = _mapping(value, "decision entry")
    decision = _mapping(entry.get("decision"), "decision")
    recommendation = _mapping(decision.get("recommendation"), "recommendation")
    explanation = _mapping(decision.get("explanation"), "explanation")
    context = _mapping(decision.get("context"), "context")
    metadata = _mapping(decision.get("metadata"), "metadata")
    confidence = _mapping(recommendation.get("confidence"), "confidence")
    uncertainty = _mapping(explanation.get("uncertainty"), "uncertainty")
    constraints = tuple(
        _constraint(item) for item in _sequence(explanation.get("constraints"), "constraints")
    )
    reasons = tuple(
        DecisionReason(
            _text(item.get("code"), "reason code"),
            _text(item.get("message"), "reason message"),
            tuple(
                _reference(ref, EvidenceReference)
                for ref in _sequence(item.get("evidence"), "reason evidence")
            ),
        )
        for raw in _sequence(explanation.get("reasons"), "reasons")
        for item in (_mapping(raw, "reason"),)
    )
    alternatives = tuple(
        DecisionAlternative(
            _reference(item.get("candidate"), CandidateReference),
            _text(item.get("reason"), "alternative reason"),
        )
        for raw in _sequence(explanation.get("alternatives"), "alternatives")
        for item in (_mapping(raw, "alternative"),)
    )
    recommendation_reasons = tuple(
        DecisionReason(
            _text(item.get("code"), "reason code"),
            _text(item.get("message"), "reason message"),
            tuple(
                _reference(ref, EvidenceReference)
                for ref in _sequence(item.get("evidence"), "reason evidence")
            ),
        )
        for raw in _sequence(recommendation.get("reasons"), "recommendation reasons")
        for item in (_mapping(raw, "reason"),)
    )
    restored_explanation = DecisionExplanation(
        ExplanationLevel(_text(explanation.get("level"), "explanation level")),
        tuple(
            _reference(item, EvidenceReference)
            for item in _sequence(explanation.get("supporting_evidence"), "supporting evidence")
        ),
        tuple(
            _reference(item, EvidenceReference)
            for item in _sequence(explanation.get("opposing_evidence"), "opposing evidence")
        ),
        tuple(
            _reference(item, HypothesisReference)
            for item in _sequence(explanation.get("accepted_hypotheses"), "accepted hypotheses")
        ),
        tuple(
            _reference(item, HypothesisReference)
            for item in _sequence(explanation.get("rejected_hypotheses"), "rejected hypotheses")
        ),
        tuple(
            _reference(item, ScenarioReference)
            for item in _sequence(explanation.get("scenarios"), "scenarios")
        ),
        constraints,
        alternatives,
        reasons,
        Uncertainty(_number(uncertainty.get("value"), "uncertainty value")),
    )
    restored_recommendation = Recommendation(
        _text(recommendation.get("recommendation_id"), "recommendation identifier"),
        RecommendationType(_text(recommendation.get("recommendation_type"), "recommendation type")),
        _reference(recommendation.get("candidate"), CandidateReference),
        recommendation_reasons,
        Confidence(
            _number(confidence.get("value"), "confidence value"),
            ConfidenceLevel(_text(confidence.get("level"), "confidence level")),
        ),
        DecisionMetadata(
            _integer(
                _mapping(recommendation.get("metadata"), "metadata").get("version"),
                "metadata version",
            ),
            _text(
                _mapping(recommendation.get("metadata"), "metadata").get("logical_timestamp"),
                "logical timestamp",
            ),
            _text(
                _mapping(recommendation.get("metadata"), "metadata").get("source"),
                "metadata source",
            ),
        ),
        DecisionDigest(
            _text(_mapping(recommendation.get("content_digest"), "digest").get("value"), "digest")
        ),
    )
    restored_decision = Decision(
        _text(decision.get("decision_id"), "decision identifier"),
        DecisionType(_text(decision.get("decision_type"), "decision type")),
        DecisionStatus(_text(decision.get("status"), "decision status")),
        DecisionPriority(_text(decision.get("priority"), "decision priority")),
        _reference(decision.get("candidate"), CandidateReference),
        restored_recommendation,
        restored_explanation,
        DecisionContext(
            _text(context.get("symbol"), "symbol"),
            _text(context.get("timeframe"), "timeframe"),
            _text(context.get("correlation_id"), "correlation identifier"),
        ),
        DecisionMetadata(
            _integer(metadata.get("version"), "metadata version"),
            _text(metadata.get("logical_timestamp"), "logical timestamp"),
            _text(metadata.get("source"), "metadata source"),
        ),
        DecisionDigest(
            _text(_mapping(decision.get("content_digest"), "digest").get("value"), "digest")
        ),
    )
    trace = _trace_from_payload(entry.get("trace"))
    return _DecisionEntry(
        restored_decision,
        trace,
        DecisionLifecycleState(_text(entry.get("state"), "lifecycle state")),
    )


def _trace_from_payload(value: object) -> DecisionTrace:
    trace = _mapping(value, "trace")
    applied = tuple(
        (_text(values[0], "constraint identifier"), values[1], values[2])
        for item in _sequence(trace.get("applied_constraints"), "applied constraints")
        for values in (_sequence(item, "applied constraint"),)
        if len(values) == 3 and isinstance(values[1], bool) and isinstance(values[2], bool)
    )
    return DecisionTrace(
        _reference(trace.get("selected_candidate"), CandidateReference),
        tuple(
            _reference(item, CandidateReference)
            for item in _sequence(trace.get("rejected_candidates"), "rejected candidates")
        ),
        applied,
        _text(trace.get("confidence_assessment_id"), "confidence assessment identifier"),
        _text(trace.get("confidence_digest"), "confidence digest"),
        tuple(
            _reference(item, EvidenceReference)
            for item in _sequence(trace.get("evidence"), "evidence")
        ),
        tuple(
            _reference(item, HypothesisReference)
            for item in _sequence(trace.get("hypotheses"), "hypotheses")
        ),
        tuple(
            _reference(item, ScenarioReference)
            for item in _sequence(trace.get("scenarios"), "scenarios")
        ),
        tuple(
            _text(item, "graph node")
            for item in _sequence(trace.get("graph_node_ids"), "graph nodes")
        ),
    )


@dataclass(frozen=True, slots=True)
class DecisionDiagnostics:
    """Read-only selection and registry consistency findings."""

    issues: tuple[str, ...] = ()

    @classmethod
    def inspect(
        cls, registry: DecisionRegistry, snapshot: DecisionSnapshot | None = None
    ) -> DecisionDiagnostics:
        issues: list[str] = []
        identifiers = tuple(entry.decision.decision_id for entry in registry.entries)
        if len(identifiers) != len(set(identifiers)):
            issues.append("duplicate_decision_identifiers")
        for entry in registry.entries:
            if not isinstance(entry.state, DecisionLifecycleState):
                issues.append(f"invalid_lifecycle:{entry.decision.decision_id}")
            if entry.decision.content_digest != _content_digest(entry.decision):
                issues.append(f"digest_inconsistency:{entry.decision.decision_id}")
            if entry.trace.selected_candidate != entry.decision.candidate:
                issues.append(f"invalid_references:{entry.decision.decision_id}")
            if not entry.decision.explanation.constraints:
                issues.append(f"missing_constraints:{entry.decision.decision_id}")
            if not entry.trace.confidence_assessment_id:
                issues.append(f"missing_confidence:{entry.decision.decision_id}")
        if snapshot is not None:
            if snapshot.entries != registry.entries:
                issues.append("snapshot_registry_mismatch")
            if snapshot.digest != DecisionDigest(_sha256(snapshot.content_payload())):
                issues.append("snapshot_digest_mismatch")
        return cls(tuple(sorted(set(issues))))


@dataclass(frozen=True, slots=True)
class DecisionSelectionReport:
    """Complete deterministic result of one selection request."""

    decision: Decision | None
    trace: DecisionTrace | None
    registry: DecisionRegistry
    snapshot: DecisionSnapshot
    audit: DecisionAudit
    diagnostics: DecisionDiagnostics


@dataclass(frozen=True, slots=True)
class DecisionEngine:
    """Select a final decision from immutable Programme E–F facts."""

    resolver: CandidateReferenceResolver
    candidates: CandidateRegistry
    assessments: ConfidenceRegistry
    registry: DecisionRegistry = DecisionRegistry()

    def decide(self, context: DecisionContext) -> DecisionSelectionReport:
        try:
            selected, assessment, rejected = DecisionSelector().select(
                self.candidates, self.assessments
            )
            self.resolver.validate(selected, assessment.graph_node_ids)
            explanation = DecisionExplanationBuilder().build(selected, rejected, assessment)
            reference = CandidateReference(selected.candidate_id, selected.metadata.version)
            recommendation_type = (
                RecommendationType.REJECT
                if selected.candidate_type is CandidateType.INVALID
                else (
                    RecommendationType.WAIT
                    if selected.candidate_type is CandidateType.WAIT
                    else RecommendationType.EXECUTE
                )
            )
            recommendation = Recommendation(
                f"recommendation-{_sha256({'candidate': reference.to_dict(), 'assessment': assessment.assessment_id})[:24]}",
                recommendation_type,
                reference,
                explanation.reasons,
                assessment.confidence,
                selected.metadata,
                DecisionDigest("0" * 64),
            )
            recommendation = replace(recommendation, content_digest=_content_digest(recommendation))
            identifier = f"decision-{_sha256({'candidate': reference.to_dict(), 'assessment': assessment.digest.value, 'context': context.to_dict()})[:24]}"
            decision = Decision(
                identifier,
                _DECISION_TYPES[selected.candidate_type],
                DecisionStatus.APPROVED,
                selected.priority,
                reference,
                recommendation,
                explanation,
                context,
                selected.metadata,
                DecisionDigest("0" * 64),
            )
            decision = replace(decision, content_digest=_content_digest(decision))
            trace = DecisionTrace(
                reference,
                tuple(
                    CandidateReference(item.candidate_id, item.metadata.version)
                    for item in rejected
                ),
                tuple(
                    sorted(
                        (item.constraint_id, item.accepted, item.mandatory)
                        for item in selected.constraints
                    )
                ),
                assessment.assessment_id,
                assessment.digest.value,
                selected.evidence,
                selected.hypotheses,
                selected.scenarios,
                assessment.graph_node_ids,
            )
            if self.registry.get(identifier) is not None:
                statistics = DecisionStatistics.from_registry(self.registry)
                snapshot = DecisionSnapshot.capture(self.registry)
                return DecisionSelectionReport(
                    None,
                    None,
                    self.registry,
                    snapshot,
                    DecisionAudit(0, len(rejected), len(selected.constraints), 1, 0, statistics),
                    DecisionDiagnostics.inspect(self.registry, snapshot),
                )
            registry = self.registry.register(decision, trace)
            snapshot = DecisionSnapshot.capture(registry)
            statistics = DecisionStatistics.from_registry(registry)
            audit = DecisionAudit(1, len(rejected), len(selected.constraints), 0, 0, statistics)
            return DecisionSelectionReport(
                decision,
                trace,
                registry,
                snapshot,
                audit,
                DecisionDiagnostics.inspect(registry, snapshot),
            )
        except RelationshipIntegrityError:
            snapshot = DecisionSnapshot.capture(self.registry)
            statistics = DecisionStatistics.from_registry(self.registry)
            audit = DecisionAudit(0, 0, 0, 0, 1, statistics)
            return DecisionSelectionReport(
                None,
                None,
                self.registry,
                snapshot,
                audit,
                DecisionDiagnostics.inspect(self.registry, snapshot),
            )


__all__ = [
    "DecisionAudit",
    "DecisionCollection",
    "DecisionConstraintEvaluator",
    "DecisionDiagnostics",
    "DecisionDigest",
    "DecisionEngine",
    "DecisionExplanationBuilder",
    "DecisionLifecycleState",
    "DecisionRegistry",
    "DecisionSelectionReport",
    "DecisionSelector",
    "DecisionSnapshot",
    "DecisionStatistics",
    "DecisionTrace",
]
