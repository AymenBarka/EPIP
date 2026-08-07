"""Reusable decision filters."""

from epip.decision.models import RuleOutcome, RuleResult


def blocking_results(results: tuple[RuleResult, ...]) -> tuple[RuleResult, ...]:
    return tuple(result for result in results if result.outcome == RuleOutcome.FAIL)
