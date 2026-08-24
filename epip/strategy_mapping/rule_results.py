"""Closed immutable semantic-rule results."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Protocol, TypeAlias

from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import exact, unique_texts
from epip.strategy_mapping.rule_execution import (
    SemanticRuleDiagnosticCode,
    SemanticRuleState,
    SemanticValueKind,
)
from epip.strategy_mapping.rule_values import SemanticCandidate, SemanticValue


def _diagnostics(value: object) -> tuple[SemanticRuleDiagnosticCode, ...]:
    if type(value) is not tuple or any(type(x) is not SemanticRuleDiagnosticCode for x in value):
        raise DataIntegrityError("diagnostic_codes must be a SemanticRuleDiagnosticCode tuple")
    ordered = tuple(sorted(value, key=lambda x: x.value))
    if len(set(ordered)) != len(ordered):
        raise DataIntegrityError("diagnostic_codes must be unique")
    return ordered


class _ResultShape(Protocol):
    @property
    def state(self) -> SemanticRuleState: ...

    @property
    def diagnostic_codes(self) -> tuple[SemanticRuleDiagnosticCode, ...]: ...


def _state(instance: _ResultShape, output: bool) -> None:
    state = instance.state
    exact(state, SemanticRuleState, "state")
    diagnostics = _diagnostics(instance.diagnostic_codes)
    object.__setattr__(instance, "diagnostic_codes", diagnostics)
    if (state is SemanticRuleState.SUCCESS) != output:
        raise DataIntegrityError("result state and output shape contradict")
    if (
        state is SemanticRuleState.SUCCESS
        and SemanticRuleDiagnosticCode.RULE_REJECTED in diagnostics
    ):
        raise DataIntegrityError("SUCCESS cannot contain rejection diagnostics")


def _candidates(value: object) -> tuple[SemanticCandidate, ...]:
    if type(value) is not tuple or any(type(x) is not SemanticCandidate for x in value):
        raise DataIntegrityError("candidates must be a SemanticCandidate tuple")
    ordered = tuple(sorted(value, key=lambda x: x.candidate_id))
    if len({x.candidate_id for x in ordered}) != len(ordered):
        raise DataIntegrityError("candidates must be unique")
    return ordered


@dataclass(frozen=True, slots=True)
class CandidateRuleResult:
    state: SemanticRuleState
    diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]
    candidates: tuple[SemanticCandidate, ...] | None

    def __post_init__(self) -> None:
        if self.candidates is not None:
            object.__setattr__(self, "candidates", _candidates(self.candidates))
        _state(self, self.candidates is not None)


@dataclass(frozen=True, slots=True)
class DirectionRuleResult:
    state: SemanticRuleState
    diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]
    direction: StrategyDirection | None

    def __post_init__(self) -> None:
        if self.direction is not None:
            exact(self.direction, StrategyDirection, "direction")
        _state(self, self.direction is not None)


@dataclass(frozen=True, slots=True)
class SelectionRuleResult:
    state: SemanticRuleState
    diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]
    selected_candidate_ids: tuple[str, ...] | None

    def __post_init__(self) -> None:
        if self.selected_candidate_ids is not None:
            object.__setattr__(
                self,
                "selected_candidate_ids",
                unique_texts(
                    self.selected_candidate_ids, "selected_candidate_ids", allow_empty=False
                ),
            )
        _state(self, self.selected_candidate_ids is not None)


@dataclass(frozen=True, slots=True)
class RankingRuleResult:
    state: SemanticRuleState
    diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]
    ordered_candidate_ids: tuple[str, ...] | None

    def __post_init__(self) -> None:
        if self.ordered_candidate_ids is not None and (
            type(self.ordered_candidate_ids) is not tuple
            or not self.ordered_candidate_ids
            or any(type(x) is not str or not x.strip() for x in self.ordered_candidate_ids)
            or len(set(self.ordered_candidate_ids)) != len(self.ordered_candidate_ids)
        ):
            raise DataIntegrityError("ordered_candidate_ids must be an ordered unique text tuple")
        _state(self, self.ordered_candidate_ids is not None)


@dataclass(frozen=True, slots=True)
class BoundaryRuleResult:
    state: SemanticRuleState
    diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]
    value: SemanticValue | None

    def __post_init__(self) -> None:
        if self.value is not None:
            exact(self.value, SemanticValue, "value")
            if self.value.kind not in (SemanticValueKind.PRICE, SemanticValueKind.PRICE_RANGE):
                raise DataIntegrityError("boundary value must be PRICE or PRICE_RANGE")
        _state(self, self.value is not None)


@dataclass(frozen=True, slots=True)
class ApplicabilityResult:
    state: SemanticRuleState
    diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]
    applicable: bool | None

    def __post_init__(self) -> None:
        if self.applicable is not None and type(self.applicable) is not bool:
            raise DataIntegrityError("applicable must be a bool")
        _state(self, self.applicable is not None)


@dataclass(frozen=True, slots=True)
class PriceTransformationResult:
    state: SemanticRuleState
    diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]
    candidate: SemanticCandidate | None

    def __post_init__(self) -> None:
        if self.candidate is not None:
            exact(self.candidate, SemanticCandidate, "candidate")
            if self.candidate.value.kind is not SemanticValueKind.PRICE:
                raise DataIntegrityError("transformed candidate must contain PRICE")
        _state(self, self.candidate is not None)


@dataclass(frozen=True, slots=True)
class ConfidenceRuleResult:
    state: SemanticRuleState
    diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]
    confidence: float | None

    def __post_init__(self) -> None:
        if self.confidence is not None and (
            type(self.confidence) is not float
            or not isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 1.0
        ):
            raise DataIntegrityError("confidence must be an exact finite float in [0, 1]")
        _state(self, self.confidence is not None)


@dataclass(frozen=True, slots=True)
class TemporalEligibilityResult:
    state: SemanticRuleState
    diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]
    eligible: bool | None

    def __post_init__(self) -> None:
        if self.eligible is not None and type(self.eligible) is not bool:
            raise DataIntegrityError("eligible must be a bool")
        _state(self, self.eligible is not None)


@dataclass(frozen=True, slots=True)
class EvidenceMappingResult:
    state: SemanticRuleState
    diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]
    selected_candidate_ids: tuple[str, ...] | None

    def __post_init__(self) -> None:
        if self.selected_candidate_ids is not None:
            object.__setattr__(
                self,
                "selected_candidate_ids",
                unique_texts(
                    self.selected_candidate_ids, "selected_candidate_ids", allow_empty=False
                ),
            )
        _state(self, self.selected_candidate_ids is not None)


@dataclass(frozen=True, slots=True)
class EvidenceOrderingResult:
    state: SemanticRuleState
    diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]
    ordered_evidence_keys: tuple[str, ...] | None

    def __post_init__(self) -> None:
        if self.ordered_evidence_keys is not None and (
            type(self.ordered_evidence_keys) is not tuple
            or not self.ordered_evidence_keys
            or any(type(x) is not str or not x.strip() for x in self.ordered_evidence_keys)
            or len(set(self.ordered_evidence_keys)) != len(self.ordered_evidence_keys)
        ):
            raise DataIntegrityError("ordered_evidence_keys must be an ordered unique text tuple")
        _state(self, self.ordered_evidence_keys is not None)


@dataclass(frozen=True, slots=True)
class MtfAggregationResult(DirectionRuleResult):
    pass


SemanticRuleResult: TypeAlias = (
    CandidateRuleResult
    | DirectionRuleResult
    | SelectionRuleResult
    | RankingRuleResult
    | BoundaryRuleResult
    | ApplicabilityResult
    | PriceTransformationResult
    | ConfidenceRuleResult
    | TemporalEligibilityResult
    | EvidenceMappingResult
    | EvidenceOrderingResult
    | MtfAggregationResult
)

__all__ = [
    "ApplicabilityResult",
    "BoundaryRuleResult",
    "CandidateRuleResult",
    "ConfidenceRuleResult",
    "DirectionRuleResult",
    "EvidenceMappingResult",
    "EvidenceOrderingResult",
    "MtfAggregationResult",
    "PriceTransformationResult",
    "RankingRuleResult",
    "SelectionRuleResult",
    "SemanticRuleResult",
    "TemporalEligibilityResult",
]
