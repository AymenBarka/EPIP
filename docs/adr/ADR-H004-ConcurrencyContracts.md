# ADR-H004: Concurrency Contracts

## Status

Accepted for Hardening-004 Programme A.

## Context

EPIP historically described stateful components as thread-safe when their private mutations were
guarded by `RLock`. The concurrency audit established that a lock alone does not define callback,
reentrance, ownership, external-adapter, determinism, or lifecycle guarantees.

## Decision

EPIP adopts four official classifications: Thread Safe, Thread Compatible, Thread Confined, and
Non Thread Safe. Every classified public component receives an immutable `ThreadSafetyContract`
covering ownership, execution scope, capabilities, reentrance, concurrent determinism, and explicit
restrictions.

Existing components are classified in the immutable registry in `epip.core.concurrency`. The
`ConcurrencyAware` protocol is the extension point for future components that declare a contract
natively. Registry resolution preserves all existing constructors and behavior.

## Consequences

- Classification describes current guarantees; it does not add synchronization.
- Thread Compatible components require caller-controlled serialized use.
- Thread Confined components require a dedicated thread or run boundary.
- A Thread Safe classification applies only within its documented restrictions.
- Distributed, async, transactional, and deadlock corrections remain separate programmes.

## Compatibility

This decision adds an opt-in public API. No existing signature, algorithm, lock, event, snapshot,
serialization format, or runtime behavior changes.

## Programme B Extension

Programme B implements the EventBus locking model in `ADR-H004-EventBusLocking.md`. EventBus is
reentrant through bounded FIFO queuing, while engine publication occurs only after state-lock
release. The classification remains Thread Safe with documented synchronous listener semantics.

## Programme F Extension

`ADR-H004-ExternalBoundaries.md` completes the concurrency model. A thread-safety classification
does not imply transactionality, idempotence, rollback, compensation, or exactly-once behavior
across an external system boundary.

## Production evidence

The final evidence and validation policy are recorded in
`ADR-H004-ProductionValidation.md` and the production stress documentation.
