# Architecture Principles

## Single semantic owner

Every calculation and decision has one owner. A07 is the sole final strategy authority. Historical
Decision and Core Kernel Decision are analytical inputs only. Parallel final authorities are
forbidden.

## No downstream recomputation

Consumers use official upstream outputs. Capital Risk does not recompute strategy geometry or RR;
Execution does not recompute strategy or analysis; Portfolio does not select trades.

## Rejection instead of semantic repair

When a canonical signal violates capital, venue, or portfolio constraints, the downstream domain
rejects it. It does not change direction, geometry, confidence, expiration, or RR to make it pass.

## Frozen A07 strategy authority

A07 E00-E09 own policy gating, evidence eligibility, final direction, entry, stop, target,
risk/reward distance, RR acceptance, confidence binding, expiration, and `StrategySignal`. Runtime,
Risk, Execution, Portfolio, broker, and MT5 dependencies must not enter A07.

## Immutable boundary contracts

Published outputs, fact bundles, evaluation context, signal envelopes, capital-risk views, and
execution/portfolio snapshots are immutable, versioned, reconstructable, and fail closed. Mutable
implementation state stays private.

## Explicit evaluation time

Deterministic evaluation receives time explicitly from ReplayClock or an injected event/venue
clock. Strategy evaluation does not use ambient wall time. Receipt time is distinct from event time.

## Shared runtime across modes

Backtest, paper, MT5 demo, and live use one Strategy Runtime and the same domain semantics. Only
data, clock, broker, persistence, safety, and telemetry adapters vary.

## Broker types stay at the boundary

Vendor and MT5 types do not leak into domain contracts. Broker normalization records requested and
normalized representations and preserves strategy intent and protective ordering.

## One-way dependencies

Infrastructure feeds analysis; analysis feeds Fact Adapters; adapters and A07 feed Strategy
Runtime; its signal envelope feeds Capital Risk; an accepted plan feeds Execution; fills feed
Portfolio. Immutable read views and domain-owned protocols prevent cycles.

## Determinism and provenance

The same immutable inputs, policy/profile versions, and evaluation timestamp produce the same
result. Every downstream output retains enough identity and provenance to audit its sources.

## Compatibility and governance

Existing Decision, Risk, and `PositionPlan` APIs remain compatibility APIs until separately
migrated. Public API changes require governed deprecation. Architecture changes require an ADR,
documentation, tests, quality evidence, and architecture approval.
