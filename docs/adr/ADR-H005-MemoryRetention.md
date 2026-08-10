# ADR-H005 Memory Retention

## Status

Accepted for Hardening-005 Programme C.

## Decision

Every EPIP component classified Cached, Persistent, or retaining history has
an immutable `MemoryRetentionContract`. The official registry rejects missing
declarations. Runtime retention uses explicit logical timestamps and stable
ordered eviction; it never consults wall-clock time or garbage collection.

Existing behaviour remains the default. Previously complete histories are
declared Unbounded with a compatibility justification and manual cleanup.
Existing bounded caches are declared LRU. Applications opt into new runtime
limits through `RetentionManager` without changing existing public APIs.

## Consequences

Growth is no longer implicit. Bounded operation is available and reproducible,
while legacy serialization, replay, financial calculations, and APIs remain
unchanged.
