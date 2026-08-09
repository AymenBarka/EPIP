"""Engineering benchmark for H006 reliability primitives; not an SLA."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from time import perf_counter

from epip.core.circuit_breaker import CIRCUIT_BREAKER_CONTRACTS, CircuitBreaker
from epip.core.fallback import (
    DEGRADATION_CONTRACTS,
    AvailabilityLevel,
    FallbackContext,
    FallbackRuntime,
)
from epip.core.reliability_audit import RELIABILITY_AUDIT_REGISTRY, ReliabilityAuditManager
from epip.core.retry import RETRY_CONTRACTS


def _measure(name: str, cycles: int, operation: Callable[[int], object]) -> tuple[str, float]:
    started = perf_counter()
    for index in range(cycles):
        operation(index)
    elapsed = perf_counter() - started
    return name, cycles / elapsed


def run(cycles: int) -> tuple[tuple[str, float], ...]:
    """Measure deterministic reliability paths as engineering references."""

    breaker = CircuitBreaker(CIRCUIT_BREAKER_CONTRACTS["provider"])
    fallback = FallbackRuntime(DEGRADATION_CONTRACTS["fail"])
    audit = ReliabilityAuditManager(RELIABILITY_AUDIT_REGISTRY)
    snapshot = audit.snapshot(0)
    return (
        _measure(
            "retry_contract",
            cycles,
            lambda _: RETRY_CONTRACTS["temporary_external_failure"],
        ),
        _measure("circuit_decision", cycles, breaker.allow),
        _measure(
            "fallback_decision",
            cycles,
            lambda tick: fallback.evaluate(
                FallbackContext(
                    tick,
                    AvailabilityLevel.AVAILABLE,
                    breaker.state,
                    False,
                    False,
                )
            ),
        ),
        _measure("audit_snapshot", cycles, lambda tick: audit.snapshot(tick)),
        _measure("audit_report", cycles, lambda _: audit.report(snapshot)),
        _measure("diagnostics", cycles, lambda _: audit.report(snapshot).diagnostics),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, default=100_000)
    arguments = parser.parse_args()
    if arguments.cycles < 1:
        parser.error("--cycles must be positive")
    for name, throughput in run(arguments.cycles):
        print(f"{name}: {throughput:,.0f} operations/s")


if __name__ == "__main__":
    main()
