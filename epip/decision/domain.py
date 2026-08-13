"""Immutable EPIP-016 decision-domain vocabulary.

This module contains data contracts only.  It deliberately performs no
ranking, recommendation, execution, or financial calculation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any, Protocol, cast

from epip.core.integrity import (
    RelationshipIntegrityError,
    require_text,
    require_unit_interval,
    require_version,
)


class EvidenceCategory(StrEnum):
    """Official evidence categories."""

    MARKET_DATA = "market_data"
    STRUCTURE = "structure"
    LIQUIDITY = "liquidity"
    FIBONACCI = "fibonacci"
    CONTEXT = "context"
    ELLIOTT = "elliott"
    RISK = "risk"
    EXECUTION = "execution"
    PORTFOLIO = "portfolio"


class HypothesisCategory(StrEnum):
    """Official hypothesis categories."""

    DIRECTIONAL = "directional"
    STRUCTURAL = "structural"
    LIQUIDITY = "liquidity"
    REVERSAL = "reversal"
    CONTINUATION = "continuation"


class ScenarioCategory(StrEnum):
    """Official scenario categories."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    INVALID = "invalid"


class CandidateType(StrEnum):
    """Candidate actions considered by the decision pipeline."""

    LONG = "long"
    SHORT = "short"
    WAIT = "wait"
    EXIT = "exit"
    REDUCE = "reduce"
    ADD = "add"
    INVALID = "invalid"


class DecisionType(StrEnum):
    """Final decision kinds."""

    ENTER = "enter"
    HOLD = "hold"
    EXIT = "exit"
    ADJUST = "adjust"
    REJECT = "reject"


class RecommendationType(StrEnum):
    """Recommendation outcomes."""

    EXECUTE = "execute"
    WAIT = "wait"
    REVIEW = "review"
    REJECT = "reject"


class ConstraintType(StrEnum):
    """Constraint ownership categories."""

    RISK = "risk"
    PORTFOLIO = "portfolio"
    EXPOSURE = "exposure"
    CAPITAL = "capital"
    POLICY = "policy"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    RUNTIME = "runtime"


class ConfidenceLevel(StrEnum):
    """Qualitative confidence bands."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class QualityLevel(StrEnum):
    """Qualitative quality bands."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ValidityLevel(StrEnum):
    """Validity states independent from confidence and quality."""

    UNKNOWN = "unknown"
    INVALID = "invalid"
    CONDITIONAL = "conditional"
    VALID = "valid"


class DecisionStatus(StrEnum):
    """Decision lifecycle states."""

    CREATED = "created"
    EVALUATED = "evaluated"
    APPROVED = "approved"
    REJECTED = "rejected"
    INVALIDATED = "invalidated"


class DecisionPriority(StrEnum):
    """Decision processing priorities."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ExplanationLevel(StrEnum):
    """Explanation detail levels."""

    SUMMARY = "summary"
    DETAILED = "detailed"
    AUDIT = "audit"


def _canonical(value: object) -> object:
    if isinstance(value, _CanonicalModel):
        return {
            item.name: _canonical(getattr(value, item.name)) for item in fields(cast(Any, value))
        }
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    return value


class _CanonicalModel:
    """Deterministic equality, hashing, and serialization for domain records."""

    __slots__ = ()

    def to_dict(self) -> dict[str, object]:
        """Return the canonical serialization mapping."""
        result = _canonical(self)
        assert isinstance(result, dict)
        return result

    def to_json(self) -> str:
        """Return byte-stable canonical JSON."""
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    def deterministic_digest(self) -> str:
        """Return the SHA-256 digest of canonical JSON."""
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def __eq__(self, other: object) -> bool:
        return (
            type(self) is type(other)
            and isinstance(other, _CanonicalModel)
            and self.to_json() == other.to_json()
        )

    def __hash__(self) -> int:
        return int(self.deterministic_digest()[:16], 16)


@dataclass(frozen=True, slots=True, eq=False)
class Confidence(_CanonicalModel):
    """Normalized confidence with an explicit qualitative level."""

    value: float
    level: ConfidenceLevel

    def __post_init__(self) -> None:
        require_unit_interval(self.value, "confidence.value")


@dataclass(frozen=True, slots=True, eq=False)
class Quality(_CanonicalModel):
    """Normalized source or reasoning quality."""

    value: float
    level: QualityLevel

    def __post_init__(self) -> None:
        require_unit_interval(self.value, "quality.value")


@dataclass(frozen=True, slots=True, eq=False)
class Validity(_CanonicalModel):
    """Normalized validity assessment."""

    value: float
    level: ValidityLevel

    def __post_init__(self) -> None:
        require_unit_interval(self.value, "validity.value")


@dataclass(frozen=True, slots=True, eq=False)
class Uncertainty(_CanonicalModel):
    """Normalized residual uncertainty."""

    value: float

    def __post_init__(self) -> None:
        require_unit_interval(self.value, "uncertainty.value")


@dataclass(frozen=True, slots=True, eq=False)
class _Reference(_CanonicalModel):
    identifier: str
    version: int = 1

    def __post_init__(self) -> None:
        require_text(self.identifier, "reference.identifier")
        require_version(self.version)


@dataclass(frozen=True, slots=True, eq=False)
class EvidenceReference(_Reference):
    """Stable reference to evidence."""


@dataclass(frozen=True, slots=True, eq=False)
class HypothesisReference(_Reference):
    """Stable reference to a hypothesis."""


@dataclass(frozen=True, slots=True, eq=False)
class ScenarioReference(_Reference):
    """Stable reference to a scenario."""


@dataclass(frozen=True, slots=True, eq=False)
class CandidateReference(_Reference):
    """Stable reference to a candidate."""


@dataclass(frozen=True, slots=True, eq=False)
class DecisionReference(_Reference):
    """Stable reference to a decision."""


@dataclass(frozen=True, slots=True, eq=False)
class DecisionDigest(_CanonicalModel):
    """Validated SHA-256 content digest."""

    value: str
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        require_text(self.value, "digest.value")
        if self.algorithm != "sha256" or len(self.value) != 64 or self.value != self.value.lower():
            raise RelationshipIntegrityError("digest must be a 64-character SHA-256 value")
        try:
            int(self.value, 16)
        except ValueError as exc:
            raise RelationshipIntegrityError("digest must be hexadecimal") from exc


@dataclass(frozen=True, slots=True, eq=False)
class DecisionMetadata(_CanonicalModel):
    """Explicit deterministic technical metadata."""

    version: int
    logical_timestamp: str
    source: str

    def __post_init__(self) -> None:
        require_version(self.version)
        require_text(self.logical_timestamp, "metadata.logical_timestamp")
        require_text(self.source, "metadata.source")


@dataclass(frozen=True, slots=True, eq=False)
class DecisionContext(_CanonicalModel):
    """Business context carried through decision construction."""

    symbol: str
    timeframe: str
    correlation_id: str

    def __post_init__(self) -> None:
        require_text(self.symbol, "context.symbol")
        require_text(self.timeframe, "context.timeframe")
        require_text(self.correlation_id, "context.correlation_id")


@dataclass(frozen=True, slots=True, eq=False)
class DecisionReason(_CanonicalModel):
    """Structured reason supporting or opposing a decision."""

    code: str
    message: str
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        require_text(self.code, "reason.code")
        require_text(self.message, "reason.message")
        _require_tuple(self.evidence, "reason.evidence")


@dataclass(frozen=True, slots=True, eq=False)
class DecisionAlternative(_CanonicalModel):
    """Candidate alternative rejected during decision construction."""

    candidate: CandidateReference
    reason: str

    def __post_init__(self) -> None:
        require_text(self.reason, "alternative.reason")


@dataclass(frozen=True, slots=True, eq=False)
class ConstraintEvaluation(_CanonicalModel):
    """Result of evaluating one external constraint."""

    constraint_id: str
    constraint_type: ConstraintType
    accepted: bool
    mandatory: bool
    reason: str
    version: int = 1

    def __post_init__(self) -> None:
        require_text(self.constraint_id, "constraint.constraint_id")
        require_text(self.reason, "constraint.reason")
        require_version(self.version)


@dataclass(frozen=True, slots=True, eq=False)
class Evidence(_CanonicalModel):
    """Atomic, attributable input to decision reasoning."""

    evidence_id: str
    category: EvidenceCategory
    source: str
    source_version: int
    payload: tuple[tuple[str, str], ...]
    confidence: Confidence
    quality: Quality
    validity: Validity
    uncertainty: Uncertainty
    dependencies: tuple[str, ...]
    metadata: DecisionMetadata
    content_digest: DecisionDigest

    def __post_init__(self) -> None:
        require_text(self.evidence_id, "evidence.evidence_id")
        require_text(self.source, "evidence.source")
        require_version(self.source_version, "evidence.source_version")
        _require_tuple(self.payload, "evidence.payload")
        _require_tuple(self.dependencies, "evidence.dependencies")
        for item in self.payload:
            if not isinstance(item, tuple) or len(item) != 2:
                raise RelationshipIntegrityError("evidence.payload entries must be pairs")
            key, value = item
            require_text(key, "evidence.payload.key")
            require_text(value, "evidence.payload.value")
        for dependency in self.dependencies:
            require_text(dependency, "evidence.dependency")


@dataclass(frozen=True, slots=True, eq=False)
class Hypothesis(_CanonicalModel):
    """Testable interpretation supported by explicit evidence references."""

    hypothesis_id: str
    category: HypothesisCategory
    evidence: tuple[EvidenceReference, ...]
    supporting_evidence: tuple[EvidenceReference, ...]
    contradicting_evidence: tuple[EvidenceReference, ...]
    assumptions: tuple[str, ...]
    invalidation_conditions: tuple[str, ...]
    confidence: Confidence
    quality: Quality
    validity: Validity
    uncertainty: Uncertainty
    metadata: DecisionMetadata
    content_digest: DecisionDigest

    def __post_init__(self) -> None:
        require_text(self.hypothesis_id, "hypothesis.hypothesis_id")
        _require_tuples(
            self,
            "evidence",
            "supporting_evidence",
            "contradicting_evidence",
            "assumptions",
            "invalidation_conditions",
        )
        if not self.evidence:
            raise RelationshipIntegrityError("hypothesis must reference evidence")
        _require_text_items(self.assumptions, "hypothesis.assumption")
        _require_text_items(self.invalidation_conditions, "hypothesis.invalidation")


@dataclass(frozen=True, slots=True, eq=False)
class Scenario(_CanonicalModel):
    """Coherent collection of hypotheses that may coexist with alternatives."""

    scenario_id: str
    category: ScenarioCategory
    hypotheses: tuple[HypothesisReference, ...]
    parent_scenarios: tuple[ScenarioReference, ...]
    supporting_evidence: tuple[EvidenceReference, ...]
    contradicting_evidence: tuple[EvidenceReference, ...]
    assumptions: tuple[str, ...]
    invalidation_conditions: tuple[str, ...]
    ranking_inputs: tuple[tuple[str, float], ...]
    confidence: Confidence
    quality: Quality
    validity: Validity
    uncertainty: Uncertainty
    metadata: DecisionMetadata
    content_digest: DecisionDigest

    def __post_init__(self) -> None:
        require_text(self.scenario_id, "scenario.scenario_id")
        _require_tuples(
            self,
            "hypotheses",
            "parent_scenarios",
            "supporting_evidence",
            "contradicting_evidence",
            "assumptions",
            "invalidation_conditions",
            "ranking_inputs",
        )
        if not self.hypotheses:
            raise RelationshipIntegrityError("scenario must reference hypotheses")
        if any(item.identifier == self.scenario_id for item in self.parent_scenarios):
            raise RelationshipIntegrityError("scenario cannot reference itself")
        _require_text_items(self.assumptions, "scenario.assumption")
        _require_text_items(self.invalidation_conditions, "scenario.invalidation")
        for name, value in self.ranking_inputs:
            require_text(name, "scenario.ranking_input.name")
            require_unit_interval(value, "scenario.ranking_input.value")


@dataclass(frozen=True, slots=True, eq=False)
class DecisionCandidate(_CanonicalModel):
    """Potential action with complete reasoning inputs and constraints."""

    candidate_id: str
    candidate_type: CandidateType
    arguments: tuple[str, ...]
    evidence: tuple[EvidenceReference, ...]
    hypotheses: tuple[HypothesisReference, ...]
    scenarios: tuple[ScenarioReference, ...]
    constraints: tuple[ConstraintEvaluation, ...]
    confidence: Confidence
    quality: Quality
    validity: Validity
    uncertainty: Uncertainty
    priority: DecisionPriority
    invalidation_conditions: tuple[str, ...]
    metadata: DecisionMetadata
    content_digest: DecisionDigest

    def __post_init__(self) -> None:
        require_text(self.candidate_id, "candidate.candidate_id")
        _require_tuples(
            self,
            "arguments",
            "evidence",
            "hypotheses",
            "scenarios",
            "constraints",
            "invalidation_conditions",
        )
        _require_text_items(self.arguments, "candidate.argument")
        _require_text_items(self.invalidation_conditions, "candidate.invalidation")


@dataclass(frozen=True, slots=True, eq=False)
class Recommendation(_CanonicalModel):
    """Recommendation attached to exactly one candidate."""

    recommendation_id: str
    recommendation_type: RecommendationType
    candidate: CandidateReference
    reasons: tuple[DecisionReason, ...]
    confidence: Confidence
    metadata: DecisionMetadata
    content_digest: DecisionDigest

    def __post_init__(self) -> None:
        require_text(self.recommendation_id, "recommendation.recommendation_id")
        _require_tuple(self.reasons, "recommendation.reasons")
        if not self.reasons:
            raise RelationshipIntegrityError("recommendation must contain a reason")


@dataclass(frozen=True, slots=True, eq=False)
class DecisionExplanation(_CanonicalModel):
    """Auditable explanation without embedding decision algorithms."""

    level: ExplanationLevel
    supporting_evidence: tuple[EvidenceReference, ...]
    opposing_evidence: tuple[EvidenceReference, ...]
    accepted_hypotheses: tuple[HypothesisReference, ...]
    rejected_hypotheses: tuple[HypothesisReference, ...]
    scenarios: tuple[ScenarioReference, ...]
    constraints: tuple[ConstraintEvaluation, ...]
    alternatives: tuple[DecisionAlternative, ...]
    reasons: tuple[DecisionReason, ...]
    uncertainty: Uncertainty

    def __post_init__(self) -> None:
        _require_tuples(
            self,
            "supporting_evidence",
            "opposing_evidence",
            "accepted_hypotheses",
            "rejected_hypotheses",
            "scenarios",
            "constraints",
            "alternatives",
            "reasons",
        )


@dataclass(frozen=True, slots=True, eq=False)
class Decision(_CanonicalModel):
    """Immutable final decision record."""

    decision_id: str
    decision_type: DecisionType
    status: DecisionStatus
    priority: DecisionPriority
    candidate: CandidateReference
    recommendation: Recommendation
    explanation: DecisionExplanation
    context: DecisionContext
    metadata: DecisionMetadata
    content_digest: DecisionDigest

    def __post_init__(self) -> None:
        require_text(self.decision_id, "decision.decision_id")


@dataclass(frozen=True, slots=True, eq=False)
class DecisionSnapshot(_CanonicalModel):
    """Versioned immutable capture of one decision."""

    snapshot_id: str
    decision: Decision
    metadata: DecisionMetadata
    content_digest: DecisionDigest

    def __post_init__(self) -> None:
        require_text(self.snapshot_id, "snapshot.snapshot_id")


def _require_text_items(values: tuple[str, ...], field: str) -> None:
    for value in values:
        require_text(value, field)


def _require_tuple(value: object, field: str) -> None:
    if not isinstance(value, tuple):
        raise RelationshipIntegrityError(f"{field} must be an immutable tuple")


def _require_tuples(model: object, *names: str) -> None:
    for name in names:
        _require_tuple(getattr(model, name), name)


class EvidenceProvider(Protocol):
    """Structural provider of immutable evidence."""

    def provide_evidence(self, context: DecisionContext) -> tuple[Evidence, ...]: ...


class HypothesisProvider(Protocol):
    """Structural provider of immutable hypotheses."""

    def provide_hypotheses(self, evidence: tuple[Evidence, ...]) -> tuple[Hypothesis, ...]: ...


class ScenarioProvider(Protocol):
    """Structural provider of immutable scenarios."""

    def provide_scenarios(self, hypotheses: tuple[Hypothesis, ...]) -> tuple[Scenario, ...]: ...


class DecisionProvider(Protocol):
    """Structural provider of immutable decisions."""

    def provide_decision(self, context: DecisionContext) -> Decision: ...


class DecisionExplainer(Protocol):
    """Structural explanation boundary."""

    def explain_decision(self, decision: Decision) -> DecisionExplanation: ...


class DecisionSerializer(Protocol):
    """Structural canonical serialization boundary."""

    def serialize_decision(self, decision: Decision) -> str: ...


__all__ = [
    "CandidateReference",
    "CandidateType",
    "Confidence",
    "ConfidenceLevel",
    "ConstraintEvaluation",
    "ConstraintType",
    "Decision",
    "DecisionAlternative",
    "DecisionCandidate",
    "DecisionContext",
    "DecisionDigest",
    "DecisionExplainer",
    "DecisionExplanation",
    "DecisionMetadata",
    "DecisionPriority",
    "DecisionProvider",
    "DecisionReason",
    "DecisionReference",
    "DecisionSerializer",
    "DecisionSnapshot",
    "DecisionStatus",
    "DecisionType",
    "Evidence",
    "EvidenceCategory",
    "EvidenceProvider",
    "EvidenceReference",
    "ExplanationLevel",
    "Hypothesis",
    "HypothesisCategory",
    "HypothesisProvider",
    "HypothesisReference",
    "Quality",
    "QualityLevel",
    "Recommendation",
    "RecommendationType",
    "Scenario",
    "ScenarioCategory",
    "ScenarioProvider",
    "ScenarioReference",
    "Uncertainty",
    "Validity",
    "ValidityLevel",
]
