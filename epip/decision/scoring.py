"""Deterministic DecisionScore calculation."""

from epip.context import MarketContextSnapshot
from epip.decision.models import DecisionScore, RuleOutcome, RuleResult
from epip.elliott import WaveSnapshot


class DecisionScorer:
    def score(
        self,
        context: MarketContextSnapshot,
        elliott: WaveSnapshot,
        results: tuple[RuleResult, ...],
    ) -> DecisionScore:
        context_score = context.context.confluence_score * 100.0
        elliott_score = elliott.analysis.primary.probability * 100.0
        total_weight = sum(result.weight for result in results)
        passed_weight = sum(
            result.weight
            for result in results
            if result.outcome in (RuleOutcome.PASS, RuleOutcome.WARNING)
        )
        rules_score = passed_weight / total_weight * 100.0 if total_weight else 0.0
        total = max(0.0, min(100.0, 0.4 * context_score + 0.4 * elliott_score + 0.2 * rules_score))
        return DecisionScore(total, context_score, elliott_score, rules_score)
