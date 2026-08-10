# ADR-H006 — Reliability Audit

## Status

Accepted.

## Context

Hardening-006 defines failure, exception, retry, circuit-breaker, and fallback
contracts. Institutional operations require a consolidated view without an
observer changing the runtime it inspects.

## Decision

EPIP provides a read-only reliability audit layer. It consumes immutable
contract declarations, caller-supplied observations, and immutable runtime
snapshots. It must not invoke retry, circuit-breaker, fallback, recovery, or
business operations.

Audit time is logical and supplied by the caller. Ordering, diagnostics,
metrics, and JSON output are deterministic. Reports are frozen value objects.
Metrics are descriptive and have no authority over runtime decisions.

## Consequences

- Missing and contradictory contracts are visible before deployment.
- Failure behavior can be inspected without changing counters or state.
- Operational tooling receives stable, machine-readable reports.
- Runtime orchestration remains outside the audit boundary.
