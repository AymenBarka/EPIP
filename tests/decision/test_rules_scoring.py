from epip.decision import DecisionConfig, RuleOutcome
from epip.decision.confidence import ConfidenceCalculator
from epip.decision.priority import PriorityCalculator
from epip.decision.probability import ProbabilityCalculator
from epip.decision.rule_engine import DecisionRuleEngine
from epip.decision.scoring import DecisionScorer
from tests.decision.helpers import snapshots


def test_rule_engine_scoring_confidence_probability_priority() -> None:
    context, elliott = snapshots()
    config = DecisionConfig()
    results = DecisionRuleEngine().evaluate(context, elliott, config)
    assert any(result.outcome == RuleOutcome.PASS for result in results)
    assert any(result.outcome == RuleOutcome.WARNING for result in results)
    score = DecisionScorer().score(context, elliott, results)
    confidence = ConfidenceCalculator().calculate(score)
    probability = ProbabilityCalculator().calculate(
        confidence, elliott.analysis.primary.probability
    )
    assert 0.0 <= score.total <= 100.0
    assert 0.0 <= confidence.value <= 1.0
    assert 0.0 <= probability.value <= 1.0
    assert PriorityCalculator().calculate(90).rank == 1
    assert PriorityCalculator().calculate(75).rank == 2
    assert PriorityCalculator().calculate(55).rank == 3
    assert PriorityCalculator().calculate(20).rank == 4


def test_rules_can_be_disabled() -> None:
    context, elliott = snapshots()
    results = DecisionRuleEngine().evaluate(
        context, elliott, DecisionConfig(enabled_rules=("OTE",))
    )
    assert len(results) == 1 and results[0].rule_id == "OTE"
