# Public Object Catalog

This catalog identifies public domain families and architectural roles. The historical 330-symbol
count was generated for v1.4.0 and is retained in `ARCHITECTURE_STATISTICS.md`; it is not asserted
as the post-v1.6.0 count. Current exports remain defined by typed source.

## Catalog by bounded context

### EPIP-001/002 — Core and runtime

- **Consumes:** validated primitives, candles, plugin registrations, events.
- **Produces:** shared values, evidence/scenario/decision primitives, events and kernel results.
- **Version:** EPIP-001 Core; EPIP-002 EventBus/Kernel.
- **Relationships:** foundation for every module; EventBus connects publishers and listeners.
- **Public objects:** `BaseEvent`, `Candle`, `Confidence`, `Decision`, `DecisionConsumer`,
  `DecisionCreated`, `DecisionRejected`, `EventBus`, `Evidence`, `EvidenceCreated`,
  `EvidenceProducer`, `EvidenceRejected`, `Hypothesis`, `Kernel`, `KernelResult`, `MarketContext`,
  `PluginContext`, `PluginProtocol`, `PluginResult`, `Price`, `Probability`, `Registry`, `RiskScore`,
  `Scenario`, `ScenarioBuilder`, `ScenarioCreated`, `ScenarioRejected`.

### EPIP-003 — Feature Store

- **Consumes:** provider observations and registered feature definitions.
- **Produces:** immutable features, sets, stored versions and pipeline results.
- **Version:** EPIP-003.
- **Relationships:** enriches Market Data/Replay inputs for analytical consumers.
- **Public objects:** `Feature`, `FeaturePipeline`, `FeatureRegistry`, `FeatureSet`, `FeatureStore`.

### EPIP-004 — Market Data

- **Consumes:** data-source configuration and external/file provider responses.
- **Produces:** normalized requests, responses, subscriptions, health, cache and source contracts.
- **Version:** EPIP-004.
- **Relationships:** official ingress for Replay and live-data consumers; providers implement the
  protocol.
- **Public objects:** `CSVConfig`, `CacheConfig`, `CacheStats`, `ConnectionError`, `ConnectionState`,
  `DataSource`, `DataSourceCache`, `DataSourceFactory`, `DataSourceProtocol`, `DataSourceRegistry`,
  `HealthCheck`, `HealthState`, `HistoryChunk`, `HistoryMetadata`, `HistoryRequest`,
  `HistoryResponse`, `InvalidRequestError`, `LiveRequest`, `LiveResponse`, `LiveSubscription`,
  `MT5Config`, `MarketDataConfig`, `MarketDataError`, `ProviderError`, `RateLimitError`,
  `TimeoutError`, `TwelveDataConfig`.

### EPIP-005 — Replay

- **Consumes:** normalized Market Data, replay configuration, time and scheduling controls.
- **Produces:** deterministic session state, scheduled candles, progression events and metrics.
- **Version:** EPIP-005.
- **Relationships:** drives Feature Store/Kernel and downstream analysis under an official clock.
- **Public objects:** `CandleLoaded`, `CandleProcessed`, `ContextUpdated`, `FeatureUpdated`,
  `ReplayClock`, `ReplayConfig`, `ReplayController`, `ReplayEngine`, `ReplayFinished`,
  `ReplayIterator`, `ReplayMetrics`, `ReplayPaused`, `ReplayResumed`, `ReplayScheduler`,
  `ReplaySession`, `ReplayStarted`, `ReplayState`, `ReplayStatistics`, `ScheduledCandle`.

### EPIP-006 — Swing

- **Consumes:** ordered candles and swing configuration/filter strategies.
- **Produces:** pivots, swings, sequences, classifications, statistics, metrics and events.
- **Version:** EPIP-006.
- **Relationships:** canonical pivot source for Structure, Fibonacci, Context and Elliott.
- **Public objects:** `ATRAdaptiveStrategy`, `ATRFilter`, `CompositeSwingFilter`, `DistanceFilter`,
  `DuplicateFilter`, `FractalStrategy`, `HybridStrategy`, `MinimumMoveFilter`, `NoiseFilter`,
  `PivotType`, `PivotValidator`, `PivotWindowStrategy`, `PriceValidator`, `SequenceValidator`,
  `Swing`, `SwingClassification`, `SwingConfig`, `SwingConfirmed`, `SwingDetected`, `SwingDetector`,
  `SwingEngine`, `SwingMerged`, `SwingMetrics`, `SwingPoint`, `SwingRejected`, `SwingScope`,
  `SwingSequence`, `SwingStatistics`, `SwingStatisticsCollector`, `SwingUpdated`, `TrendBias`,
  `TrendFilter`, `ZigZagStrategy`, `build_default_filters`.

### EPIP-007 — Market Structure

- **Consumes:** official `SwingSequence` objects and configuration.
- **Produces:** structure analysis, trend/range/BOS/CHOCH objects, snapshots, events, graph/history,
  statistics, metrics and typed failures.
- **Version:** EPIP-007.
- **Relationships:** consumes Swing; feeds Liquidity, Fibonacci and Context.
- **Public objects:** `AnalyzerResult`, `BOSDetected`, `BOSDetector`, `BOSValidator`,
  `BreakOfStructure`, `CHOCHDetected`, `CHOCHDetector`, `CHOCHValidator`, `ChangeOfCharacter`,
  `HistoryError`, `IllegalStructureTransitionError`, `InvalidBOSError`, `InvalidCHOCHError`,
  `InvalidRangeError`, `InvalidStructureError`, `InvalidStructureInputError`, `InvalidTrendError`,
  `MarketStructure`, `MarketStructureAnalyzer`, `MarketStructureConfig`, `MarketStructureEngine`,
  `MarketStructureError`, `MarketStructureEvent`, `MarketStructureMetrics`,
  `MarketStructureProtocol`, `MarketStructureSnapshot`, `MarketStructureStatistics`,
  `ObserverRegistry`, `Range`, `RangeDetected`, `RangeDetector`, `StructureDetected`,
  `StructureDetectorProtocol`, `StructureEdge`, `StructureGraph`, `StructureHistory`,
  `StructureNode`, `StructureObserver`, `StructureQuality`, `StructureRelation`, `StructureReset`,
  `StructureState`, `StructureStateMachine`, `StructureStatistics`, `StructureVersionError`,
  `SwingSequenceValidator`, `Trend`, `TrendChanged`, `TrendDetector`, `TrendDirection`,
  `TrendValidator`.

### EPIP-008 — Liquidity

- **Consumes:** official Swing and Structure outputs.
- **Produces:** FVGs, voids, clusters, lifecycle/state, ranking/strength, tree, snapshot-owned graph,
  history and metrics.
- **Version:** EPIP-008.
- **Relationships:** feeds Fibonacci and Context; state machine governs liquidity lifecycle.
- **Public objects:** `BearishFVG`, `BullishFVG`, `FairValueGap`, `LiquidityCluster`,
  `LiquidityConfig`, `LiquidityEdge`, `LiquidityEngine`, `LiquidityGraph`, `LiquidityHistory`,
  `LiquidityMetrics`, `LiquidityNode`, `LiquidityProtocol`, `LiquidityRanking`, `LiquidityState`,
  `LiquidityStateMachine`, `LiquidityStrength`, `LiquidityTreeNode`, `LiquidityVoid`,
  `MultiTimeFrameLiquidityTree`.

### EPIP-009 — Fibonacci

- **Consumes:** official Swing, Structure and Liquidity geometry/evidence.
- **Produces:** levels, retracements/extensions, zones, clusters, projections, strength, alignment,
  snapshots, graph/history and metrics.
- **Version:** EPIP-009.
- **Relationships:** supplies Context, Elliott and Decision evidence.
- **Public objects:** `ConfluenceZone`, `DiscountZone`, `FibonacciCluster`, `FibonacciConfig`,
  `FibonacciDirection`, `FibonacciEdge`, `FibonacciEngine`, `FibonacciExtension`, `FibonacciGraph`,
  `FibonacciHistory`, `FibonacciLevel`, `FibonacciMetrics`, `FibonacciNode`, `FibonacciProtocol`,
  `FibonacciQuality`, `FibonacciRetracement`, `FibonacciSnapshot`, `FibonacciStrength`,
  `FibonacciZone`, `GoldenZone`, `InstitutionalEntryZone`, `MultiTimeFrameAlignment`, `OTEZone`,
  `PremiumZone`, `ProjectionLabel`, `ProjectionTarget`, `dynamic_projection`, `project_targets`.

### EPIP-010 — Market Context

- **Consumes:** aligned official Swing, Structure, Liquidity and Fibonacci snapshots.
- **Produces:** aggregate phase, bias, trend/confluence contexts, snapshot/version, graph/history and
  metrics.
- **Version:** EPIP-010.
- **Relationships:** official aggregate input for Elliott and Decision.
- **Public objects:** `BiasContext`, `ConfluenceContext`, `InstitutionalBias`, `MarketContext`,
  `MarketContextBuilder`, `MarketContextConfig`, `MarketContextEngine`, `MarketContextGraph`,
  `MarketContextHistory`, `MarketContextMetrics`, `MarketContextProtocol`, `MarketContextSnapshot`,
  `MarketContextVersion`, `MarketPhase`, `TrendContext`.

### EPIP-011 — Elliott Wave

- **Consumes:** official Market Context and its published structural evidence.
- **Produces:** wave models, counts/alternates, patterns, rules/violations, targets/projections,
  analysis, snapshot, graph/history and metrics.
- **Version:** EPIP-011 (`v1.1.0`).
- **Relationships:** feeds Decision and future AI; preserves Context lineage.
- **Public objects:** `AlternateCount`, `CountStatus`, `ElliottAnalysis`, `ElliottConfig`,
  `ElliottMetrics`, `ElliottProtocol`, `ElliottWaveEngine`, `Wave`, `WaveCount`, `WaveDegree`,
  `WaveEdge`, `WaveGraph`, `WaveHistory`, `WaveLabel`, `WaveNode`, `WavePattern`, `WaveProjection`,
  `WaveQuality`, `WaveRule`, `WaveSequence`, `WaveSnapshot`, `WaveTarget`, `WaveViolation`.

### EPIP-012 — Decision

- **Consumes:** aligned `MarketContextSnapshot` and `WaveSnapshot`.
- **Produces:** rule results, scores, confidence/probability, priority, zones, reasons,
  `TradeDecision`, snapshot, graph/history and metrics.
- **Version:** EPIP-012 (`v1.2.0`).
- **Relationships:** historical input to legacy Risk. In the post-v1.6.0 canonical runtime this is
  analytical candidate/evidence output, not a final strategy signal.
- **Public objects:** `DecisionAction`, `DecisionConfidence`, `DecisionConfig`, `DecisionEdge`,
  `DecisionEngine`, `DecisionGraph`, `DecisionHistory`, `DecisionMetrics`, `DecisionNode`,
  `DecisionProbability`, `DecisionProtocol`, `DecisionQuality`, `DecisionReason`, `DecisionScore`,
  `DecisionSnapshot`, `EntryZone`, `ExecutionPriority`, `ExitZone`, `Invalidation`, `PriorityLevel`,
  `RiskLevel`, `RiskProfile`, `RuleOutcome`, `RuleResult`, `TradeDecision`.

### EPIP-013 — Risk

- **Consumes:** only official Decision output plus explicit scalar risk observations.
- **Produces:** sizing, exposure/drawdown, leverage/margin, stops/targets, risk score/reasons,
  `PositionPlan`, snapshot, graph/history, events and metrics.
- **Version:** EPIP-013 (`v1.3.0`).
- **Relationships:** legacy sizing path and official input to current Execution. Its future Capital
  Risk successor preserves A07 geometry and owns capital allocation and constraints.
- **Public objects:** `Drawdown`, `DrawdownExceeded`, `Exposure`, `ExposureExceeded`, `Leverage`,
  `Margin`, `PortfolioLimits`, `PositionPlan`, `PositionPlanned`, `PositionSize`, `RiskAccepted`,
  `RiskConfig`, `RiskEdge`, `RiskEngine`, `RiskGraph`, `RiskHistory`, `RiskLevel`, `RiskMetrics`,
  `RiskNode`, `RiskProfile`, `RiskQuality`, `RiskReason`, `RiskRejected`, `RiskRelation`, `RiskScore`,
  `RiskSnapshot`, `SizingMethod`, `StopLoss`, `TakeProfit`.

### EPIP-014 — Execution

- **Consumes:** only accepted official `PositionPlan` objects and adapter responses.
- **Produces:** orders/fills, broker responses, reports, official `ExecutionSnapshot`, graph/history,
  events and statistics.
- **Version:** EPIP-014 (`v1.4.0`).
- **Relationships:** sole broker boundary; official input to implemented Portfolio and future
  Monitoring/AI consumers.
- **Public objects:** `BrokerAdapterProtocol`, `BrokerResponse`, `CommissionMode`,
  `ExecutionCompleted`, `ExecutionConfig`, `ExecutionEdge`, `ExecutionEngine`, `ExecutionGraph`,
  `ExecutionHistory`, `ExecutionNode`, `ExecutionReason`, `ExecutionRelation`, `ExecutionReport`,
  `ExecutionSnapshot`, `ExecutionStatistics`, `MT5Adapter`, `Order`, `OrderCancelled`,
  `OrderCreated`, `OrderFill`, `OrderFilled`, `OrderRejected`, `OrderSide`, `OrderState`,
  `OrderSubmitted`, `OrderType`, `PaperTradingAdapter`, `SlippageMode`.

### EPIP-015 — Portfolio

- **Consumes:** completed `ExecutionSnapshot` objects and fills.
- **Produces:** positions, cash/equity, PnL, allocations, exposure, correlation, limit reasons, and
  `PortfolioSnapshot`.
- **Version:** EPIP-015 (`v1.5.0`).
- **Relationships:** post-fill accounting and portfolio-constraint authority, not strategy
  authority. A future immutable constraint view may feed Capital Risk.

### A07 — Strategy Engine E00-E09

- **Consumes:** immutable caller-supplied identity, policy, evidence, direction, geometry,
  reward-risk, confidence, expiration, and evaluation-request contracts.
- **Produces:** validated predecessor objects and final immutable `StrategySignal`.
- **Version:** A07 (`v1.6.0`), COMPLETE / CLOSED / FROZEN.
- **Relationships:** sole canonical final strategy authority; broker-, execution-, sizing-,
  portfolio-, and wall-clock-independent.

## Proposed post-v1.6 contracts

These are **PROPOSED / FUTURE CONTRACTS**, not implemented APIs. P01 owns their fields:

- `EvaluationContext` and a snapshot/provenance bundle.
- `StrategyFactBundle`, strategy-profile identity/version, and adapter protocols.
- `StrategyRuntimeRequest`, `StrategyRuntimeResult`, and runtime diagnostics.
- `StrategySignalEnvelope` binding a signal to instrument, timeframe, and sources.
- `PortfolioRiskSnapshot` or another immutable constraint view.
- A Capital Risk plan successor preserving A07 direction and geometry.

The existing `PositionPlan` remains a legacy compatibility output until separately migrated.

## Stability note

Package-root exports are governed by [API_STABILITY.md](API_STABILITY.md). A symbol listed here may
be a model, enum, protocol, engine, event, exception, strategy, adapter, function, graph/history, or
metric. The owning module defines its detailed fields and valid operations; relationships above
define its allowed architectural role.
