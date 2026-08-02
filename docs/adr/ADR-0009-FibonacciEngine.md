# ADR-0009 - Fibonacci Engine as Single Fibonacci Source

## Status

Accepted.

## Decision

All Fibonacci calculations live in an immutable, vendor-independent downstream engine. It consumes
official Swing, Market Structure, and Liquidity outputs and publishes versioned snapshots. Ratio
configuration, pure calculation services, graph/history ownership and EventBus integration are
separated to preserve SOLID and Clean Architecture boundaries.

## Consequences

Future Elliott, Decision, Risk, and Execution modules consume one deterministic truth. Persistent
history and indexed graph implementations remain replaceable future optimizations.

## Hardening Decision

Strength, clustering, institutional confluence, projections, and timeframe alignment are modeled as
immutable additive domain objects. Scoring is deterministic and bounded to `[0.0, 1.0]`. The
existing engine API remains unchanged; hardening services consume its snapshots and preserve the
dependency direction from Swing, Market Structure, and Liquidity toward Fibonacci.

Serialization is explicit for each aggregate so type information and enum values survive a
round-trip. Runtime metrics expose forward-compatible counters without coupling calculation logic
to persistence or telemetry backends.
