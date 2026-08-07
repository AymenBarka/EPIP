"""Decision probability service."""

from epip.decision.models import DecisionConfidence, DecisionProbability


class ProbabilityCalculator:
    def calculate(
        self, confidence: DecisionConfidence, wave_probability: float
    ) -> DecisionProbability:
        value = 0.6 * confidence.value + 0.4 * max(0.0, min(1.0, wave_probability))
        return DecisionProbability(max(0.0, min(1.0, value)))
