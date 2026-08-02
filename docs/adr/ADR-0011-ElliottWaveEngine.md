# ADR-0011 - Elliott Wave as a Single Official Engine

## Status

Accepted.

## Context

Downstream Decision, Risk, Execution, and AI engines require one deterministic wave interpretation
without duplicating structure, liquidity, or Fibonacci calculations.

## Decision

Create EPIP-011 downstream of Market Context. Production code depends only on Core, EventBus, and
Market Context. Wave segmentation consumes official context swings; validation consumes official
context Fibonacci and liquidity evidence. Canonical rules are modular, immutable, and configurable
for diagonal overlap.

The engine owns wave counts, alternates, projections, versioned snapshots, history, graph, events,
metrics, and deterministic serialization. State mutation is protected with `RLock` and logging uses
the standard library.

## Consequences

All future modules receive one official Elliott truth and traceable context version. Calibration,
persistent storage, expanded corrective combinations, and cross-degree parent inference remain
replaceable extensions behind the EPIP-011 contracts.
