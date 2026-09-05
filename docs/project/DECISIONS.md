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

## ADR-0017 — Canonical Strategy Runtime Contracts

- **Release:** post-`v1.6.0` P01 contract milestone
- **Status:** Accepted
- **Purpose:** freeze deterministic evaluation, provenance, profile, MTF, fact-adapter, runtime
  result, signal-envelope, Capital Risk, Portfolio Risk View, dependency, and compatibility
  contracts without implementing runtime behavior.
- **ADR:** [ADR-0017](../adr/ADR-0017-CanonicalStrategyRuntimeContracts.md)

## ADR-0018 — Typed Strategy Mapping and Analytical Availability Boundaries

- **Milestone:** P02-F00 additive contract foundation
- **Status:** Accepted
- **Purpose:** preserve frozen P01 while adding typed instrument, availability, revision, MTF source,
  and semantic mapping-profile schemas. P04 retains concrete Elliott/Fibonacci rules and P05
  retains concrete MTF direction.
- **ADR:** [ADR-0018](../adr/ADR-0018-TypedStrategyMappingAndAvailabilityBoundaries.md)
- **Specification:**
  [P02-F00 Additive Strategy Mapping Foundation](P02_F00_ADDITIVE_MAPPING_FOUNDATION.md)

## ADR-0019 — Immutable Semantic Rule Execution and Exact-Version Resolution

- **Milestone:** P02-F02 additive execution contract
- **Status:** Accepted
- **Purpose:** separate persistent rule identity/manifests from explicitly injected executable
  implementations, freeze exact profile closure and adapter invocation binding, and preserve P04
  and P05 ownership of concrete semantic content.
- **ADR:** [ADR-0019](../adr/ADR-0019-ImmutableSemanticRuleExecution.md)
- **Specification:**
  [P02-F02 Semantic Rule Execution Contract](P02_F02_SEMANTIC_RULE_EXECUTION_CONTRACT.md)

## ADR-0020 — Evidence Mapping and Fail-Fast Semantic Execution

- **Milestone:** P02-F04 additive governance reconciliation
- **Status:** Accepted
- **Purpose:** bind executable evidence mapping per taxonomy key and freeze dependency-aware
  fail-fast execution, exception sanitization, and deterministic diagnostic translation.
- **ADR:** [ADR-0020](../adr/ADR-0020-EvidenceMappingAndFailFastSemanticExecution.md)
- **Specification:**
  [P02-F04 Evidence and Failure Control Contract](P02_F04_EVIDENCE_AND_FAILURE_CONTROL_CONTRACT.md)

## ADR-0021 — Evidence Identity Separation and Governed Semantic Transitions

- **Milestone:** P02-F06 additive governance reconciliation
- **Status:** Accepted
- **Purpose:** separate evidence-item and evidence-set identities, preserve governed evidence
  order, bind per-frame direction generation, and freeze entry/stop/target cardinality transitions.
- **ADR:** [ADR-0021](../adr/ADR-0021-EvidenceIdentityAndSemanticTransitions.md)
- **Specification:**
  [P02-F06 Transition and Evidence Identity Contract](P02_F06_TRANSITION_AND_EVIDENCE_IDENTITY_CONTRACT.md)

## ADR-0022 — Ordered Candidate Selection for Semantic Ranking

- **Milestone:** P02-F08 additive governance reconciliation
- **Status:** Accepted
- **Purpose:** preserve canonical unordered selection while adding an exact-order request for the
  Target extension transition, without changing rule taxonomy, resolution, P01, or A07.
- **ADR:** [ADR-0022](../adr/ADR-0022-OrderedCandidateSelectionForSemanticRanking.md)
- **Specification:**
  [P02-F08 Ranked Candidate Selection Contract](P02_F08_RANKED_CANDIDATE_SELECTION_CONTRACT.md)

## ADR-0023 — Explicit Frame Scope for Source Selectors

- **Milestone:** P02-F10 governance reconciliation
- **Status:** Accepted
- **Purpose:** make every ordinary selector's visible timeframe roles explicit, deterministic, and
  profile-identified while preserving F06 per-frame narrowing and P04/P05 semantic ownership.
- **ADR:** [ADR-0023](../adr/ADR-0023-ExplicitFrameScopeForSourceSelectors.md)
- **Specification:**
  [P02-F10 Source Selector Frame Scope Contract](P02_F10_SOURCE_SELECTOR_FRAME_SCOPE_CONTRACT.md)

## ADR-0024 — Confidence Source Extraction Participates in Exact Rule Closure

- **Milestone:** P02-F12 governance reconciliation
- **Status:** Accepted
- **Purpose:** require every confidence input selector's existing source-extraction rule in exact
  profile closure while preserving generic rule reuse and frozen P01/A07 boundaries.
- **ADR:**
  [ADR-0024](../adr/ADR-0024-ConfidenceSourceExtractionParticipatesInExactRuleClosure.md)
- **Specification:**
  [P02-F12 Confidence Source Extraction Closure Contract](P02_F12_CONFIDENCE_SOURCE_EXTRACTION_CLOSURE_CONTRACT.md)
