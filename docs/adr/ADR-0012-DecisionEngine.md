# ADR-0012 - TradeDecision as the Single Official Trading Decision

## Status

Accepted.

## Context

Risk, Execution, Portfolio, and AI require one deterministic, explainable source of trading actions
without duplicating Market Context or Elliott analysis.

## Decision

Create EPIP-012 downstream of Market Context and Elliott. Only the Decision Engine may create LONG,
SHORT, WAIT, EXIT, REDUCE, ADD, or INVALID actions. The engine uses independent configurable rules,
a deterministic 0–100 score, an explicit decision matrix, structured reasoning, and immutable
entry, exit, invalidation, priority, and risk suggestions.

The engine owns versioned snapshots, graph, history, events, metrics, and deterministic
serialization. Runtime state uses `RLock`. No stable upstream public API is modified.

## Consequences

Future consumers depend only on `TradeDecision`, providing one auditable action contract. Execution
and position sizing remain outside EPIP-012. Persistent storage, calibrated scoring, and an official
volatility input can be introduced behind the public interfaces.
