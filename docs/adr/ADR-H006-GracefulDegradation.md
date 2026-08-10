# ADR-H006 — Graceful Degradation

## Status

Accepted.

## Context

External dependencies can become degraded or unavailable without invalidating
the framework itself. EPIP requires explicit, deterministic fallback decisions
without silently changing the behaviour of existing components.

## Decision

EPIP provides an optional fallback runtime built from immutable contracts. A
contract declares its policy, concrete action, resulting availability,
remaining capabilities, disabled features, and the applicable failure, retry,
circuit-breaker, and exception contracts.

Fallback evaluation uses caller-supplied logical time and typed classification.
Exception messages, regular expressions, ambient clocks, and implicit policies
are forbidden. Existing components adopt this runtime only through an explicit
`FallbackAware` contract and explicit invocation.

## Consequences

- Degradation decisions are deterministic and auditable.
- Availability transitions and capability loss are explicit.
- Snapshots and bounded logical history are immutable.
- No existing engine or boundary changes behaviour automatically.
