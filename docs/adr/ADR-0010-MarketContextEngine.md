# ADR-0010 - Market Context as the Official Downstream Snapshot

## Status

Accepted.

## Context

Future engines need a stable view of Swing, Market Structure, Liquidity, and Fibonacci without
depending on or recomputing each domain independently.

## Decision

Introduce an additive Market Context aggregation layer downstream of EPIP-006 through EPIP-009.
The layer retains official immutable snapshots, validates stream and version consistency, derives
only phase, bias, and bounded confluence from published values, and versions results per stream.
Downstream Elliott, Decision, Risk, Execution, and AI modules consume only Market Context.

History and graph structures are immutable. The engine uses `RLock`, EventBus, deterministic
serialization, and standard logging. No stable upstream API is modified.

## Consequences

Consumers receive one coherent and traceable snapshot. Upstream domain ownership remains intact.
Persistent histories, cross-timeframe context graphs, and calibrated scoring policies can be added
behind the new public contracts without changing prior engines.
