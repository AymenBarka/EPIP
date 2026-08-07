"""Structured human-readable decision reasoning."""

from epip.decision.models import DecisionReason, RuleOutcome, RuleResult


class DecisionReasoner:
    def explain(self, results: tuple[RuleResult, ...]) -> DecisionReason:
        positive = tuple(result.message for result in results if result.outcome == RuleOutcome.PASS)
        negative = tuple(result.message for result in results if result.outcome == RuleOutcome.FAIL)
        warnings = tuple(
            result.message for result in results if result.outcome == RuleOutcome.WARNING
        )
        return DecisionReason(positive, negative, warnings, negative)
