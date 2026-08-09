# ADR-H006 — Retry Policies

## Status

Accepted.

## Context

Retry decisions were not represented by a single, inspectable framework model.
Implicit retry would threaten determinism, duplicate side effects, and obscure
responsibility across framework and external boundaries.

## Decision

EPIP defines immutable retry contracts in `epip.core.retry`. Contracts describe
eligibility, strategy, conditions, ownership, timing limits, budgets, and jitter.
The registry is deterministic and read-only.

Programme C is declarative only. It performs no sleeping, randomness, retry loop,
exception interception, or component integration.

## Consequences

- Retry intent is reviewable before runtime adoption.
- `NO_RETRY` is explicit for fatal, validation, configuration, and cancellation
  outcomes.
- External availability never becomes an implicit framework guarantee.
- Runtime adoption requires a later, separately reviewed programme.
