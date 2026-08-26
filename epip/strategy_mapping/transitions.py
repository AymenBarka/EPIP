"""Pure structural validations for governed semantic-rule transitions."""

from __future__ import annotations

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping.rule_execution import SemanticRuleState, SemanticValueKind
from epip.strategy_mapping.rule_requests import (
    CandidateRankingRequest,
    CandidateSelectionRequest,
    EvidenceOrderingRequest,
)
from epip.strategy_mapping.rule_results import (
    BoundaryRuleResult,
    EvidenceOrderingResult,
    RankingRuleResult,
    SelectionRuleResult,
)
from epip.strategy_mapping.rule_values import SemanticCandidate


def materialize_evidence_order(
    request: EvidenceOrderingRequest, result: EvidenceOrderingResult
) -> tuple[str, ...]:
    """Return a successful exact permutation without repairing semantic order."""
    if type(request) is not EvidenceOrderingRequest or type(result) is not EvidenceOrderingResult:
        raise DataIntegrityError("evidence ordering contracts have invalid types")
    ordered = result.ordered_evidence_keys
    if (
        result.state is not SemanticRuleState.SUCCESS
        or ordered is None
        or len(ordered) != len(request.evidence_keys)
        or set(ordered) != set(request.evidence_keys)
    ):
        raise DataIntegrityError("evidence ordering output is not an exact request permutation")
    return ordered


def boundary_entry_range(result: BoundaryRuleResult) -> tuple[float, float]:
    """Convert a successful boundary point or range to exact EntryFacts bounds."""
    if type(result) is not BoundaryRuleResult or result.state is not SemanticRuleState.SUCCESS:
        raise DataIntegrityError("boundary result must be successful")
    value = result.value
    if value is None:
        raise DataIntegrityError("boundary result is missing its value")
    if value.kind is SemanticValueKind.PRICE:
        assert value.float_value is not None
        return (value.float_value, value.float_value)
    if value.kind is SemanticValueKind.PRICE_RANGE:
        assert value.range_lower is not None and value.range_upper is not None
        return (value.range_lower, value.range_upper)
    raise DataIntegrityError("boundary result has an invalid value kind")


def ranking_winner(
    request: CandidateRankingRequest, result: RankingRuleResult
) -> SemanticCandidate:
    """Resolve the explicit first ranking output after exact permutation validation."""
    if type(request) is not CandidateRankingRequest or type(result) is not RankingRuleResult:
        raise DataIntegrityError("ranking contracts have invalid types")
    ordered = result.ordered_candidate_ids
    requested = tuple(item.candidate_id for item in request.candidates)
    if (
        result.state is not SemanticRuleState.SUCCESS
        or ordered is None
        or len(ordered) != len(requested)
        or set(ordered) != set(requested)
    ):
        raise DataIntegrityError("ranking output is not an exact request permutation")
    return {item.candidate_id: item for item in request.candidates}[ordered[0]]


def selection_winner(
    request: CandidateSelectionRequest,
    result: SelectionRuleResult,
    *,
    require_price: bool = False,
) -> SemanticCandidate:
    """Resolve an exact-one request-member winner for precedence or extension."""
    if type(request) is not CandidateSelectionRequest or type(result) is not SelectionRuleResult:
        raise DataIntegrityError("selection contracts have invalid types")
    selected = result.selected_candidate_ids
    by_id = {item.candidate_id: item for item in request.candidates}
    if (
        result.state is not SemanticRuleState.SUCCESS
        or selected is None
        or len(selected) != 1
        or selected[0] not in by_id
    ):
        raise DataIntegrityError("selection output must name exactly one request candidate")
    winner = by_id[selected[0]]
    if require_price and winner.value.kind is not SemanticValueKind.PRICE:
        raise DataIntegrityError("selected candidate must contain PRICE")
    return winner


__all__ = [
    "boundary_entry_range",
    "materialize_evidence_order",
    "ranking_winner",
    "selection_winner",
]
