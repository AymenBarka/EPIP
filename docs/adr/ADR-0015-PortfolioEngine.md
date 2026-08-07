# ADR-0015: Portfolio Engine

## Status

Accepted

## Decision

EPIP-015 is the single official global portfolio-management boundary. It consumes only completed
`ExecutionSnapshot` objects and emits immutable `PortfolioSnapshot` values. It owns multi-position
accounting, allocation, capital, PnL, equity, drawdown, global exposure, correlation groups,
concentration, limits, history, graph, events and metrics.

No lower-level analytical, Decision, or Risk engine may be consumed or recomputed. Future Strategy
and AI modules consume PortfolioSnapshot only. Runtime state is protected with `RLock`, and
serialization is deterministic.

## Consequences

The framework has one global exposure truth and a traceable Execution-to-Portfolio lineage. A
future valuation feed, persistent ledger, tax-lot policy and covariance service may be added only
through new official contracts without weakening the ExecutionSnapshot-only boundary.
