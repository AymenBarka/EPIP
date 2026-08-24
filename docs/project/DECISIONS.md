# Architecture Decision Record Index

This is the official index of EPIP Architecture Decision Records. An ADR marked **Accepted** is an
active architecture constraint until superseded by a later ADR. Release assignments follow the
EPIP module number and the first tagged release known to contain that module.

## ADR-0001 — Core Domain

- **Release:** foundation before `v1.0.0-pre`
- **Status:** record missing from `docs/adr/`
- **Purpose:** establish immutable core values, evidence, hypotheses, scenarios, decisions, and
  shared domain contracts.
- **Reference:** [Core Domain architecture](../architecture/CoreDomain.md)

The repository does not currently contain an `ADR-0001` source file. This index does not invent an
accepted decision record; a future documentation change should restore it from authoritative
history or create it through the normal ADR review process.

## ADR-0002 — Event Bus and Kernel for EPIP Execution

- **Release:** foundation before `v1.0.0-pre`
- **Status:** Accepted
- **Purpose:** introduce deterministic publish/subscribe, plugin registration, immutable plugin
  context/results, and Kernel orchestration without coupling Core to implementations.
- **ADR:** [ADR-0002](../adr/ADR-0002-EventBus.md)

## ADR-0003 — Feature Store as Single Enriched Data Source

- **Release:** foundation before `v1.0.0-pre`
- **Status:** Accepted
- **Purpose:** make immutable `Feature` and `FeatureSet` the canonical enriched-data contracts and
  prevent duplicated indicator or feature computation.
- **ADR:** [ADR-0003](../adr/ADR-0003-FeatureStore.md)

## ADR-0004 — Market Data Layer with Ports and Adapters

- **Release:** foundation before `v1.0.0-pre`
- **Status:** Accepted
- **Purpose:** establish one vendor-neutral market-data ingress with protocols, factory, registry,
  cache, and replaceable provider adapters.
- **ADR:** [ADR-0004](../adr/ADR-0004-MarketData.md)

## ADR-0005 — Replay Engine as Official EPIP Clock

- **Release:** foundation before `v1.0.0-pre`
- **Status:** Accepted
- **Purpose:** centralize deterministic historical time, lazy replay, state events, and downstream
  orchestration without embedding analysis logic.
- **ADR:** [ADR-0005](../adr/ADR-0005-ReplayEngine.md)

## ADR-0006 — Swing Engine as Official Pivot Source

- **Release:** foundation before `v1.0.0-pre`
- **Status:** Accepted
- **Purpose:** provide one canonical streaming source of pivots, swing labels, scopes, and
  extensible detection strategies.
- **ADR:** [ADR-0006](../adr/ADR-0006-SwingEngine.md)

## ADR-0007 — Market Structure Engine as Single Structure Source

- **Release:** `v0.7.0`; included in `v1.0.0-pre`
- **Status:** Accepted
- **Purpose:** centralize BOS, CHOCH, trend, range, guarded state transitions, observations,
  confidence, and versioned structure output.
- **ADR:** [ADR-0007](../adr/ADR-0007-MarketStructure.md)

## ADR-0008 — Liquidity Engine as Single Liquidity Source

- **Release:** `v0.8.0`; included in `v1.0.0-pre`
- **Status:** Accepted
- **Purpose:** provide one deterministic lifecycle and vocabulary for pools, sweeps, equal levels,
  FVGs, voids, clusters, ranking, and liquidity lineage.
- **ADR:** [ADR-0008](../adr/ADR-0008-LiquidityEngine.md)

## ADR-0009 — Fibonacci Engine as Single Fibonacci Source

- **Release:** `v0.9.0`; included in `v1.0.0-pre`
- **Status:** Accepted
- **Purpose:** centralize ratios, retracements, extensions, OTE, zones, projections, strength,
  alignment, and deterministic Fibonacci evidence.
- **ADR:** [ADR-0009](../adr/ADR-0009-FibonacciEngine.md)

## ADR-0010 — Market Context as Official Downstream Snapshot

- **Release:** `v1.0.0-pre`
- **Status:** Accepted
- **Purpose:** aggregate official analytical snapshots into one version-consistent phase, bias,
  confluence, history, and graph contract without replacing upstream ownership.
- **ADR:** [ADR-0010](../adr/ADR-0010-MarketContextEngine.md)

## ADR-0011 — Elliott Wave as a Single Official Engine

- **Release:** `v1.1.0`
- **Status:** Accepted
- **Purpose:** provide one deterministic, scored wave interpretation with explicit alternatives,
  rules, projections, context lineage, history, and graph.
- **ADR:** [ADR-0011](../adr/ADR-0011-ElliottWaveEngine.md)

## ADR-0012 — TradeDecision as the Single Official Trading Decision

- **Release:** `v1.2.0`
- **Status:** Accepted
- **Purpose:** make `TradeDecision` the only auditable trading-action contract and keep sizing and
  execution outside the Decision domain.
- **ADR:** [ADR-0012](../adr/ADR-0012-DecisionEngine.md)

## ADR-0013 — Risk Engine

- **Release:** `v1.3.0`
- **Status:** Accepted
- **Purpose:** make `PositionPlan` the sole position-sizing and risk-management output consumed by
  Execution, Portfolio, and AI.
- **ADR:** [ADR-0013](../adr/ADR-0013-RiskEngine.md)

## ADR-0014 — Execution Engine

- **Release:** `v1.4.0`
- **Status:** Accepted
- **Purpose:** make `ExecutionSnapshot` the official execution outcome and isolate all broker access
  behind `BrokerAdapterProtocol`.
- **ADR:** [ADR-0014](../adr/ADR-0014-ExecutionEngine.md)

## ADR-0015 — Portfolio Engine

- **Release:** `v1.5.0`
- **Status:** Accepted
- **Purpose:** establish `PortfolioSnapshot` as the official post-fill positions, capital, PnL,
  allocation, exposure, correlation, and portfolio-limit boundary.
- **ADR:** [ADR-0015](../adr/ADR-0015-PortfolioEngine.md)

## ADR-0016 — Post-v1.6.0 Canonical Strategy Pipeline and Semantic Ownership

- **Release:** post-`v1.6.0` governance
- **Status:** Accepted
- **Purpose:** establish A07 as the sole final strategy authority, reclassify Decision/Core Kernel
  outputs as analytical inputs, separate strategy geometry from Capital Risk, and govern the future
  Fact Adapter/Profile and shared Strategy Runtime boundaries.
- **ADR:** [ADR-0016](../adr/ADR-0016-CanonicalStrategyPipeline.md)
