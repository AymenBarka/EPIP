# ADR-H006 — Reliability Validation

## Status

Accepted.

## Decision

H006 reliability contracts are validated through deterministic, test-only fault
injection and bounded stress campaigns. Validation consumes the existing retry,
circuit-breaker, fallback, exception, and audit APIs without changing them.

CI executes 100,000 decisions per mechanism and 1,000 combined cycles. Extended
and institutional endurance campaigns remain explicit operator-run profiles.
Benchmark figures are engineering references, never service-level commitments.

## Consequences

Fault campaigns are reproducible from logical ticks, canonical reports are
comparable byte-for-byte, and no wall-clock dependency enters validation logic.
The decision introduces no public API, financial, or serialization change.
