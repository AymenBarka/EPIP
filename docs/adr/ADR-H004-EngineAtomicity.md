# ADR-H004 — Engine Atomicity

## Status

Accepted.

## Decision

Stateful engines use an in-memory prepare/commit boundary. Validation,
calculation, immutable snapshot construction, history construction and graph
construction complete before any engine-owned reference is replaced.

The replacement set is committed under the engine's existing lock. Events are
published only after that commit and never while the engine lock is held.

## Consequences

- A failure before commit leaves the prior observable state unchanged.
- No database, WAL, external transaction manager or additional lock is used.
- Event delivery is outside the state transaction and follows the EventBus
  failure policy defined by ADR-H004-EventBusLocking.
