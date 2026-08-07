# ADR-0013: Risk Engine

## Status

Accepted

## Decision

EPIP-013 is the single official position-sizing boundary. It consumes only EPIP-012 decisions and
emits immutable `PositionPlan` instances. It may depend only on Core, EventBus, and Decision.
Sizing strategies and portfolio constraints remain pure domain services; orchestration, event
publication, history, graph maintenance, and synchronization remain in `RiskEngine`.

## Consequences

Execution, Portfolio, and AI must consume `PositionPlan` and may not duplicate sizing logic.
Immutable versioned snapshots preserve deterministic replay and serialization. Market data inputs
needed by ATR or volatility strategies are scalar observations, never dependencies on earlier
analysis engines.
