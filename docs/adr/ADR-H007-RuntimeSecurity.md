# ADR-H007 — Runtime Security Policies

## Status

Accepted

## Context

EPIP has declarative security, boundary, and input-validation contracts. They
must remain metadata until an application deliberately chooses enforcement.
Implicit enforcement would alter stable public behaviour.

## Decision

EPIP provides an additive runtime policy layer in `epip.core.runtime_security`.
Every official policy is registered disabled. A policy can run only after an
application creates an explicit adoption and registers it with a manager.
Evaluation consumes violations supplied by the caller; it never invokes an
existing engine, provider, adapter, or contract automatically.

All contexts, bindings, violations, results, diagnostics, snapshots, and
statistics are immutable. Ordering is canonical and snapshots have explicit
sequence numbers rather than implicit timestamps.

## Consequences

- Existing components retain their behaviour and APIs.
- Applications control adoption scope and enforcement policy.
- Custom enforcement is delegated to its owner.
- Runtime diagnostics can validate bindings without activating them.
