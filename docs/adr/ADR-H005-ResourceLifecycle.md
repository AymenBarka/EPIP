# ADR-H005 Resource Lifecycle

## Status

Accepted for Hardening-005 Programme B.

## Context

Memory contracts identify resource-managed components but do not enforce a
runtime acquisition and cleanup sequence. Institutional operation requires an
explicit, auditable lifecycle without changing existing engine behaviour.

## Decision

EPIP provides an additive lifecycle boundary in
`epip.core.resource_lifecycle`. A `ResourceHandle` owns lifecycle enforcement,
while `LifecycleManager` owns deterministic grouping, cleanup, and audit.

The official states are Created, Initialized, Active, Idle, Closing, Closed,
Failed, and Aborted. Invalid transitions raise a dedicated error. Close is
idempotent; cleanup failure leaves a coherent Failed state and permits an
explicit retry. Use after a terminal or cleanup state is rejected.

Ownership is explicit: Owner, Borrower, Shared Owner, Transferred Owner, and
External Owner. Borrowers cannot close or transfer a resource. Transfers
require a stable new owner identifier.

## Consequences

- Existing resources can opt in through a wrapper or context manager.
- Existing constructors, algorithms, serialization, and public behaviour are
  unchanged.
- Lifecycle violations and potential leaks are exposed through immutable,
  deterministic audit results.
- This decision does not add cache eviction or performance optimisation.
