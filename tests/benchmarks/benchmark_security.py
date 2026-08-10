"""Reproducible H007 security validation micro-benchmarks."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from epip.core.input_validation import (
    declared_input_validation_contracts,
    get_input_validation_contract,
)
from epip.core.security import declared_security_contracts, get_security_contract
from epip.core.security_audit import SECURITY_AUDIT_REGISTRY, SecurityAuditManager
from epip.core.security_boundaries import (
    declared_security_boundaries,
    get_security_boundary_contract,
)

ITERATIONS = 100_000


def _measure(name: str, operation: Callable[[int], object]) -> tuple[str, float, float]:
    started = perf_counter()
    for index in range(ITERATIONS):
        operation(index)
    elapsed = perf_counter() - started
    return name, elapsed, ITERATIONS / elapsed


def run() -> tuple[tuple[str, float, float], ...]:
    contracts = declared_security_contracts()
    boundaries = declared_security_boundaries()
    validations = declared_input_validation_contracts()
    manager = SecurityAuditManager(SECURITY_AUDIT_REGISTRY)
    return (
        _measure(
            "security-contract-resolution",
            lambda index: get_security_contract(contracts[index % len(contracts)].component),
        ),
        _measure(
            "boundary-contract-resolution",
            lambda index: get_security_boundary_contract(boundaries[index % len(boundaries)].name),
        ),
        _measure(
            "validation-contract-resolution",
            lambda index: get_input_validation_contract(validations[index % len(validations)].name),
        ),
        _measure("audit-snapshot", lambda index: manager.snapshot(index)),
    )


if __name__ == "__main__":
    for benchmark, elapsed, throughput in run():
        print(f"{benchmark}: {elapsed:.6f}s, {throughput:,.0f} operations/s")
