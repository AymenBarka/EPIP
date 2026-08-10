# ADR-H005 — Deterministic Memory Recovery

## Status

Accepted.

## Context

Transactional operations allocate temporary resources before their outcome is
known. Exceptions, interruptions, failed initialization, and failed commit must
not leave those resources reachable or partially registered.

## Decision

EPIP provides an additive recovery boundary composed of
`MemoryRecoveryManager`, `RecoveryScope`, and `RecoveryHandle`.

- Resources are registered explicitly with an explicit cleanup callback.
- Rollback releases resources in reverse registration order.
- Nested committed scopes transfer ownership to their parent.
- A top-level commit integrates resources and performs no cleanup.
- `Exception` and `BaseException` paths execute the same rollback protocol.
- Cleanup failures do not prevent cleanup attempts for remaining resources.
- Every lifecycle checkpoint uses a deterministic sequence number.

The recovery layer does not depend on garbage collection, wall-clock time,
object addresses, dictionary iteration order, or an external cleanup thread.

## Consequences

Cleanup is explicit, deterministic, auditable, and independent from Python
finalization. Existing APIs and financial algorithms remain unchanged.
