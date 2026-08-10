# ADR-H006 — Circuit Breakers

## Status

Accepted.

## Context

Repeated failures at external and component boundaries require an optional,
explicit isolation mechanism. Implicit adoption would change established
runtime behaviour and could affect financial processing.

## Decision

EPIP provides a deterministic circuit-breaker runtime in
`epip.core.circuit_breaker`. Adoption requires explicit construction with an
official contract. No existing engine, provider, adapter, EventBus, Replay, or
Kernel component constructs or invokes it.

State changes use caller-supplied logical time. Failure classification consumes
only the H006 retry, failure, and exception contracts. Snapshots and histories
contain circuit state and diagnostics only; business state is never modified.

## Consequences

- Failure isolation can be adopted boundary by boundary.
- Existing behaviour remains unchanged until explicit adoption.
- Transitions and half-open trials are deterministic and auditable.
- System time and implicit exception classification are forbidden.
