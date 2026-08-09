# ADR-H005: Memory and Resource Contracts

## Status

Accepted for Hardening-005 Programme A.

## Context

EPIP components retain different forms of state, histories, caches, and
external resources. These responsibilities existed in the implementation but
were not represented by a uniform, machine-readable architecture contract.

## Decision

EPIP defines immutable `MemoryContract` declarations in
`epip.core.memory`. The `MEMORY_CONTRACTS` registry is immutable and resolves
contracts by qualified name, type, or instance. Contracts describe ownership,
lifecycle, allocation, release, caching, history, visibility, mutability,
cleanup, garbage collection, resource type, external dependencies, failure
behaviour, and expected growth.

The registry is descriptive. It must not allocate resources, add caches,
change cleanup behaviour, or alter component execution.

## Consequences

- Memory responsibilities are testable and discoverable.
- Public components can additively implement `MemoryAware`.
- Existing runtime and serialization behaviour remain unchanged.
- Unbounded retention is documented rather than silently reclassified.
