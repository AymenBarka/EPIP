"""Typed immutable semantic-rule requests."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import TypeAlias, TypeVar

from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import exact, text, timestamp, unique_texts
from epip.strategy_mapping.confidence_policy import ModelParameter
from epip.strategy_mapping.profile import SemanticProfileIdentity
from epip.strategy_mapping.rule_identity import RuleIdentity
from epip.strategy_mapping.rule_values import (
    ConfidenceInputValue,
    SemanticCandidate,
    TimeframeDirectionValue,
)
from epip.strategy_mapping.source_binding import AnalyticalSourceBinding
from epip.strategy_runtime.mtf import TimeframeRole

T = TypeVar("T")


def _typed_tuple(  # noqa: UP047
    value: object, cls: type[T], field: str, *, empty: bool = False
) -> tuple[T, ...]:
    if (
        type(value) is not tuple
        or (not empty and not value)
        or any(type(x) is not cls for x in value)
    ):
        raise DataIntegrityError(
            f"{field} must be a{' non-empty' if not empty else ''} {cls.__name__} tuple"
        )
    return value


def _candidates(
    value: object, field: str = "candidates", *, empty: bool = False
) -> tuple[SemanticCandidate, ...]:
    values = _typed_tuple(value, SemanticCandidate, field, empty=empty)
    ordered = tuple(sorted(values, key=lambda item: item.candidate_id))
    if len({x.candidate_id for x in ordered}) != len(ordered):
        raise DataIntegrityError(f"{field} contains duplicate candidates")
    return ordered


@dataclass(frozen=True, slots=True)
class SemanticRuleInvocationContext:
    evaluation_id: str
    evaluation_timestamp: str
    semantic_profile_identity: SemanticProfileIdentity
    rule_identity: RuleIdentity
    instrument_binding_id: str
    timeframe: str | None
    timeframe_role: TimeframeRole | None
    source_binding_ids: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "evaluation_id", text(self.evaluation_id, "evaluation_id"))
        object.__setattr__(
            self,
            "evaluation_timestamp",
            timestamp(self.evaluation_timestamp, "evaluation_timestamp"),
        )
        exact(self.semantic_profile_identity, SemanticProfileIdentity, "semantic_profile_identity")
        exact(self.rule_identity, RuleIdentity, "rule_identity")
        object.__setattr__(
            self, "instrument_binding_id", text(self.instrument_binding_id, "instrument_binding_id")
        )
        if (self.timeframe is None) != (self.timeframe_role is None):
            raise DataIntegrityError(
                "timeframe and timeframe_role must be jointly present or absent"
            )
        if self.timeframe is not None:
            object.__setattr__(self, "timeframe", text(self.timeframe, "timeframe"))
            exact(self.timeframe_role, TimeframeRole, "timeframe_role")
        object.__setattr__(
            self,
            "source_binding_ids",
            unique_texts(self.source_binding_ids, "source_binding_ids", allow_empty=False),
        )
        object.__setattr__(
            self,
            "provenance_refs",
            unique_texts(self.provenance_refs, "provenance_refs", allow_empty=False),
        )


@dataclass(frozen=True, slots=True)
class SourceExtractionRequest:
    context: SemanticRuleInvocationContext
    source: AnalyticalSourceBinding

    def __post_init__(self) -> None:
        exact(self.context, SemanticRuleInvocationContext, "context")
        exact(self.source, AnalyticalSourceBinding, "source")
        if (
            self.source.source_binding_id not in self.context.source_binding_ids
            or self.source.provenance_ref not in self.context.provenance_refs
            or self.source.instrument.binding_id != self.context.instrument_binding_id
        ):
            raise DataIntegrityError("source does not match invocation context")


@dataclass(frozen=True, slots=True)
class DirectionRuleRequest:
    context: SemanticRuleInvocationContext
    candidates: tuple[SemanticCandidate, ...]
    allowed_source_states: tuple[str, ...]

    def __post_init__(self) -> None:
        exact(self.context, SemanticRuleInvocationContext, "context")
        object.__setattr__(self, "candidates", _candidates(self.candidates))
        object.__setattr__(
            self,
            "allowed_source_states",
            unique_texts(self.allowed_source_states, "allowed_source_states", allow_empty=False),
        )


@dataclass(frozen=True, slots=True)
class CandidateSelectionRequest:
    context: SemanticRuleInvocationContext
    candidates: tuple[SemanticCandidate, ...]
    direction: StrategyDirection | None

    def __post_init__(self) -> None:
        exact(self.context, SemanticRuleInvocationContext, "context")
        object.__setattr__(self, "candidates", _candidates(self.candidates))
        if self.direction is not None:
            exact(self.direction, StrategyDirection, "direction")


@dataclass(frozen=True, slots=True)
class RankedCandidateSelectionRequest:
    """Selection request whose caller-provided candidate order is semantic."""

    context: SemanticRuleInvocationContext
    candidates: tuple[SemanticCandidate, ...]
    direction: StrategyDirection | None

    def __post_init__(self) -> None:
        exact(self.context, SemanticRuleInvocationContext, "context")
        candidates = _typed_tuple(self.candidates, SemanticCandidate, "candidates")
        if len({item.candidate_id for item in candidates}) != len(candidates):
            raise DataIntegrityError("candidates contains duplicate candidates")
        object.__setattr__(self, "candidates", candidates)
        if self.direction is not None:
            exact(self.direction, StrategyDirection, "direction")


@dataclass(frozen=True, slots=True)
class CandidateRankingRequest(CandidateSelectionRequest):
    pass


@dataclass(frozen=True, slots=True)
class BoundarySelectionRequest:
    context: SemanticRuleInvocationContext
    candidate: SemanticCandidate
    direction: StrategyDirection

    def __post_init__(self) -> None:
        exact(self.context, SemanticRuleInvocationContext, "context")
        exact(self.candidate, SemanticCandidate, "candidate")
        exact(self.direction, StrategyDirection, "direction")


@dataclass(frozen=True, slots=True)
class ApplicabilityRequest(BoundarySelectionRequest):
    pass


@dataclass(frozen=True, slots=True)
class PriceTransformationRequest(BoundarySelectionRequest):
    pass


@dataclass(frozen=True, slots=True)
class ConfidenceRuleRequest:
    context: SemanticRuleInvocationContext
    inputs: tuple[ConfidenceInputValue, ...]
    parameters: tuple[ModelParameter, ...]
    base_confidence: float | None

    def __post_init__(self) -> None:
        exact(self.context, SemanticRuleInvocationContext, "context")
        inputs = tuple(
            sorted(
                _typed_tuple(self.inputs, ConfidenceInputValue, "inputs"), key=lambda x: x.input_key
            )
        )
        parameters = tuple(
            sorted(_typed_tuple(self.parameters, ModelParameter, "parameters", empty=True))
        )
        if len({x.input_key for x in inputs}) != len(inputs) or len(
            {x.parameter_key for x in parameters}
        ) != len(parameters):
            raise DataIntegrityError("confidence keys must be unique")
        object.__setattr__(self, "inputs", inputs)
        object.__setattr__(self, "parameters", parameters)
        if self.base_confidence is not None and (
            type(self.base_confidence) is not float
            or not isfinite(self.base_confidence)
            or not 0.0 <= self.base_confidence <= 1.0
        ):
            raise DataIntegrityError("base_confidence must be an exact finite float in [0, 1]")


@dataclass(frozen=True, slots=True)
class TemporalEligibilityRequest:
    context: SemanticRuleInvocationContext
    candidates: tuple[SemanticCandidate, ...]
    required_roles: tuple[TimeframeRole, ...]
    revision_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        exact(self.context, SemanticRuleInvocationContext, "context")
        object.__setattr__(self, "candidates", _candidates(self.candidates))
        roles = _typed_tuple(self.required_roles, TimeframeRole, "required_roles")
        if len(set(roles)) != len(roles):
            raise DataIntegrityError("required_roles must be unique")
        object.__setattr__(self, "required_roles", tuple(sorted(roles, key=lambda x: x.value)))
        object.__setattr__(
            self, "revision_ids", unique_texts(self.revision_ids, "revision_ids", allow_empty=False)
        )


@dataclass(frozen=True, slots=True)
class EvidenceMappingRequest:
    context: SemanticRuleInvocationContext
    evidence_key: str
    candidates: tuple[SemanticCandidate, ...]

    def __post_init__(self) -> None:
        exact(self.context, SemanticRuleInvocationContext, "context")
        object.__setattr__(self, "evidence_key", text(self.evidence_key, "evidence_key"))
        object.__setattr__(self, "candidates", _candidates(self.candidates))


@dataclass(frozen=True, slots=True)
class EvidenceOrderingRequest:
    context: SemanticRuleInvocationContext
    evidence_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        exact(self.context, SemanticRuleInvocationContext, "context")
        object.__setattr__(
            self,
            "evidence_keys",
            unique_texts(self.evidence_keys, "evidence_keys", allow_empty=False),
        )


@dataclass(frozen=True, slots=True)
class MtfAggregationRequest:
    context: SemanticRuleInvocationContext
    directions: tuple[TimeframeDirectionValue, ...]
    required_roles: tuple[TimeframeRole, ...]
    required_timeframes: tuple[str, ...]

    def __post_init__(self) -> None:
        exact(self.context, SemanticRuleInvocationContext, "context")
        values = tuple(
            sorted(
                _typed_tuple(self.directions, TimeframeDirectionValue, "directions"),
                key=lambda x: x.canonical_key(),
            )
        )
        if len({(x.timeframe, x.role) for x in values}) != len(values):
            raise DataIntegrityError("directions must be unique")
        roles = _typed_tuple(self.required_roles, TimeframeRole, "required_roles")
        if len(set(roles)) != len(roles):
            raise DataIntegrityError("required_roles must be unique")
        object.__setattr__(self, "directions", values)
        object.__setattr__(self, "required_roles", tuple(sorted(roles, key=lambda x: x.value)))
        object.__setattr__(
            self,
            "required_timeframes",
            unique_texts(self.required_timeframes, "required_timeframes", allow_empty=False),
        )


SemanticRuleRequest: TypeAlias = (
    SourceExtractionRequest
    | DirectionRuleRequest
    | CandidateSelectionRequest
    | RankedCandidateSelectionRequest
    | CandidateRankingRequest
    | BoundarySelectionRequest
    | ApplicabilityRequest
    | PriceTransformationRequest
    | ConfidenceRuleRequest
    | TemporalEligibilityRequest
    | EvidenceMappingRequest
    | EvidenceOrderingRequest
    | MtfAggregationRequest
)

__all__ = [
    "ApplicabilityRequest",
    "BoundarySelectionRequest",
    "CandidateRankingRequest",
    "CandidateSelectionRequest",
    "ConfidenceRuleRequest",
    "DirectionRuleRequest",
    "EvidenceMappingRequest",
    "EvidenceOrderingRequest",
    "MtfAggregationRequest",
    "PriceTransformationRequest",
    "RankedCandidateSelectionRequest",
    "SemanticRuleInvocationContext",
    "SemanticRuleRequest",
    "SourceExtractionRequest",
    "TemporalEligibilityRequest",
]
