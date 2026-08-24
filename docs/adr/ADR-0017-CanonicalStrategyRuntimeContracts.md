# ADR-0017: Canonical Strategy Runtime Contracts

## Status

Accepted

## Context

ADR-0016 establishes A07 as EPIP's sole final strategy authority and defines the future Fact
Adapter, shared Strategy Runtime, Capital Risk, and Portfolio constraint boundaries. P01 must make
those boundaries implementable without creating runtime behavior or changing frozen A07 E00-E09.

Existing `DecisionSnapshot`, Risk `PositionPlan`, and their protocols form a compatibility path.
They cannot be silently reused as the canonical path because historical Risk may derive strategy
geometry. No prior contract represents a coherent evaluation, per-fact provenance, a cross-domain
MTF boundary, or the metadata envelope required around `StrategySignal`.

## Decision

P01 introduces immutable, hashable contracts under `epip.strategy_runtime` and additive Capital
Risk contracts under `epip.risk`. Contract version `p01-v1` uses canonical tagged JSON and SHA-256
over canonical semantic content. Derived identity fields are excluded from their own digest and are
verified during reconstruction. NaN, infinity, malformed timestamps, unsupported versions, unknown
enums, and mismatched identities fail closed.

`EvaluationContext` carries venue-neutral instrument identity, symbol, primary timeframe, explicit
event/evaluation/optional receipt timestamps, runtime mode, exact profile identity, source-set and
run identities. Timestamps normalize to UTC. Receipt and correlation metadata do not affect the
strategy evaluation identity. No contract reads a clock or generates a random identity.

`ProvenanceManifest` contains unique `SourceProvenance` and per-fact `FactProvenance`. All fact and
parent references must resolve. Profile and adapter identities must match every transformation.
Anonymous facts are invalid.

`StrategyProfile` contains immutable references to mapping, confidence, evidence-taxonomy, MTF,
and enabled-source rules. Exact identity/fingerprint resolution is required. P01 defines no
Elliott/Fibonacci rules, fallback, latest, or nearest-compatible behavior.

`AnalyticalInputBundle` contains typed immutable official outputs. `StrategyFactBundle` reuses
frozen A07 evidence, direction, entry, stop, and target fact types and adds confidence and complete
provenance. It contains no signal, final normalized geometry, RR, or expiration.

`FactAdapterProtocol` is the only P01 adapter artifact. Its accepted result contains one complete
fact bundle; rejected, invalid, and failed results contain none. Concrete transformations are P02.

`MultiTimeframeInputSet` requires one primary timeframe, unique closed frames, canonical ordering,
and windows not later than alignment time. Actual MTF analysis and profile-specific stale/missing
behavior are P05.

`StrategyRuntimeRequest`, its closed options, structured diagnostics, and
`StrategyRuntimeResult` define the future orchestration boundary. Only `ACCEPTED_SIGNAL` contains a
`StrategySignalEnvelope`; `NO_SIGNAL`, validation rejection, invalid input, adapter failure, and
A07 rejection remain distinct. P03 owns orchestration.

`StrategySignalEnvelope` nests the frozen `StrategySignal` and adds evaluation, instrument,
profile, adapter, provenance, runtime, and source-set identity. It does not duplicate direction,
geometry, RR, confidence, or expiration. It has no creation wall clock.

Capital Risk receives the envelope and `PortfolioRiskView`. `SizedPositionPlan` nests the envelope
and adds sizing/capital fields only. Capital Risk may reject but cannot repair strategy intent.
`PortfolioRiskView` is a Risk input-port projection so Risk does not import Portfolio and create the
Risk -> Execution -> Portfolio -> Risk cycle. A future adapter will project Portfolio/ledger state.

## Dependency and compatibility rules

A07 never imports Strategy Runtime or downstream packages. Analytics never imports Strategy
Runtime, Risk, or Execution. Strategy Runtime has no broker or Portfolio implementation dependency.
Capital Risk has no broker or Portfolio implementation dependency. Execution does not import
analytics or A07 stage logic. Deterministic modules do not use wall clocks, random identities,
network clients, or broker clients.

The existing Decision -> Risk -> `PositionPlan` -> Execution -> Portfolio path remains a
COMPATIBILITY API. P01 is additive and does not modify those contracts or frozen A07.

## Consequences

P01 contracts are IMPLEMENTED. Strategy Runtime behavior remains FUTURE / P03; concrete Fact
Adapters remain FUTURE / P02; Elliott/Fibonacci profile behavior remains FUTURE / P04; MTF analysis
remains FUTURE / P05. Backtest, paper, demo, and live will share the same future runtime.
