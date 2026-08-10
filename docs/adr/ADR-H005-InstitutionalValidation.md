# ADR-H005 — Institutional Memory Validation

## Status

Accepted.

## Context

Hardening-005 Programs A through F introduced contracts, lifecycle,
retention, recovery, and read-only audit infrastructure. Their stability must
be demonstrated under repeated use without creating another memory
architecture or changing business runtimes.

## Decision

EPIP uses two validation tiers:

- bounded deterministic stress tests executed in CI;
- explicit endurance benchmarks at 100,000, 500,000, and 1,000,000 cycles.

The campaigns validate logical bounds, completed cleanup, closed recovery
scopes, immutable snapshots, deterministic diagnostics, and collectability.
Wall-clock measurements are experimental baselines and are not service-level
agreements.

## Consequences

No public API, financial calculation, serialization format, Replay, Kernel,
EventBus, or engine behavior is changed. Unbounded audit traces remain an
explicit compatibility policy and must be accounted for by operators during
long-running campaigns.
