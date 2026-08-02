# ADR-0008 - Liquidity Engine as Single Liquidity Source

## Status

Accepted.

## Context

Multiple future strategies require consistent buy-side, sell-side, equal-level, pool, and sweep
semantics. Recalculation would create divergence and prevent deterministic replay.

## Decision

Introduce a dedicated EPIP-008 module consuming only immutable Swing and Market Structure outputs.
Detection is separated into equal-level, pool, sweep, and zone services. The engine owns per-stream
immutable snapshots, graph, history, events, and statistics.

## Consequences

- All downstream strategies share one liquidity truth.
- Algorithms remain deterministic and vendor-independent.
- Graph and history enable Elliott traversal and backtesting.
- Copy-on-append history and linear graph lookup trade memory/lookup efficiency for immutability and
  a small stable public API; indexed persistence can be added behind future adapters.

## Stabilization Decisions

Lifecycle transitions are explicit and terminal consumption/invalidation cannot be reversed.
Strength and ranking are deterministic value objects rather than detector side effects. FVGs,
voids and clusters enter the domain before their detectors mature, preserving API stability.
Multi-timeframe relationships use a constrained immutable tree. Confluence is normalized to
`[0, 1]` by producers and metrics are extended additively, retaining all EPIP-008 constructors.
