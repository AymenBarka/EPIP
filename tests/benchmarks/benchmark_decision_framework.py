"""Real EPIP-016 engineering reference benchmark and stress campaigns."""

from __future__ import annotations

from epip.decision.validation import (
    DecisionBenchmarkReport,
    DecisionFrameworkHarness,
    DecisionStressReport,
    DecisionValidationManager,
)

REFERENCE_OPERATIONS = 100_000
COMPLETE_PIPELINES = 1_000


def run_reference_benchmarks(count: int = REFERENCE_OPERATIONS) -> DecisionBenchmarkReport:
    """Measure actual Evidence through Decision framework operations."""
    return DecisionValidationManager().framework_benchmarks(count, DecisionFrameworkHarness())


def run_reference_stress_campaign() -> DecisionStressReport:
    """Execute the mandated real-operation campaign counts without retaining outputs."""
    manager = DecisionValidationManager()
    return manager.stress(
        manager.framework_campaigns(
            REFERENCE_OPERATIONS, COMPLETE_PIPELINES, DecisionFrameworkHarness()
        )
    )


if __name__ == "__main__":
    benchmark = run_reference_benchmarks()
    stress = run_reference_stress_campaign()
    for measurement in benchmark.measurements:
        print(*measurement)
    print(stress.operations)
    print(stress.failures)
    print(stress.digest.value)
