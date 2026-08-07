"""Decision confidence service."""

from epip.decision.models import DecisionConfidence, DecisionScore


class ConfidenceCalculator:
    def calculate(self, score: DecisionScore) -> DecisionConfidence:
        return DecisionConfidence(max(0.0, min(1.0, score.total / 100.0)))
