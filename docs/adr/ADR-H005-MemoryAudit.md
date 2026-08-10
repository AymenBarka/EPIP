# ADR-H005 — Memory Audit and Resource Observability

## Status

Accepted.

## Context

H005 defines memory contracts, resource lifecycles, retention policies, runtime
adoption, and recovery scopes. Institutional operation also requires a
deterministic way to observe violations without changing runtime state.

## Decision

EPIP provides a read-only audit layer based on explicit probes registered in a
`MemoryAuditRegistry`. `MemoryAuditManager` evaluates those probes and produces
immutable `MemorySnapshot`, `MemoryDiagnostics`, and `MemoryReport` objects.

Audits never clean resources, modify policies, inspect garbage-collector state,
or use system time and runtime identity. Ordering follows explicit component and
resource names. Growth is the logical difference between explicitly supplied
snapshots.

## Consequences

Memory and resource violations become comparable and serializable evidence.
Existing runtime objects require no modification and retain their current APIs
and behaviour.
