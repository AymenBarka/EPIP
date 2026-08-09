# ADR-H004: External Effects and Distributed Boundaries

## Status

Accepted.

## Context

EPIP provides atomic in-memory engine, Replay, and Kernel boundaries. Providers, brokers, user
callbacks, logging handlers, clocks, identity sources, filesystems, and networks remain controlled
partly or entirely by external systems. Treating those effects as part of an EPIP transaction would
create a false distributed-atomicity guarantee.

## Decision

Every existing external boundary has an immutable `ExternalEffectContract` declaring ownership,
thread safety, ordering, observability, rollback, compensation, idempotence, determinism, delivery,
and failure policy. External effects are never included in an EPIP local commit. They either finish
before a dependent local commit or execute explicitly after it.

EPIP does not claim exactly-once delivery and does not implement 2PC, saga, outbox, inbox, event
sourcing, network rollback, filesystem rollback, broker rollback, or provider rollback.

## Consequences

Callers can reason precisely about uncertain remote outcomes and apply adapter-specific policies.
Retries may provide at-least-once attempts but may duplicate non-idempotent effects. Post-commit
callback or publication failure cannot reverse already committed local state.
