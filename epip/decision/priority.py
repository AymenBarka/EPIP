"""Execution priority classification."""

from epip.decision.models import ExecutionPriority, PriorityLevel


class PriorityCalculator:
    def calculate(self, score: float) -> ExecutionPriority:
        if score >= 85.0:
            return ExecutionPriority(PriorityLevel.CRITICAL, 1)
        if score >= 70.0:
            return ExecutionPriority(PriorityLevel.HIGH, 2)
        if score >= 50.0:
            return ExecutionPriority(PriorityLevel.NORMAL, 3)
        return ExecutionPriority(PriorityLevel.LOW, 4)
