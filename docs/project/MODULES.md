# Modules

## EPIP-001 — Core Domain

**Purpose:** shared domain vocabulary and framework kernel. **Responsibilities:** values,
contracts, events, evidence, hypotheses, scenarios, decisions, plugin registry and kernel.
**Public API:** `Candle`, `Price`, `Confidence`, `Probability`, `RiskScore`, `Evidence`, `Scenario`,
`Decision`, `EventBus`, `Kernel`, and plugin contracts. **Consumes:** primitive validated values.
**Produces:** core objects and events. **Dependencies:** standard library. **Future consumers:** every
engine. **Decision:** keep cross-domain primitives small and stable.

## EPIP-002 — Event Bus

**Purpose:** synchronous deterministic domain-event delivery. **Responsibilities:** subscribe,
unsubscribe, publish, ordered history, kernel/plugin integration. **Public API:** `EventBus`, event
types, `Kernel`, `Registry`, plugin protocols. **Consumes:** immutable event objects. **Produces:**
ordered listener delivery and event history. **Dependencies:** Core. **Future consumers:** monitoring
and integrations. **Decision:** producers never know downstream listeners.

## EPIP-003 — Feature Store

**Purpose:** reusable feature computation and storage. **Responsibilities:** features, feature sets,
providers, registries, pipelines, deterministic lookup. **Public API:** `Feature`, `FeatureSet`,
`FeatureStore`, `FeatureRegistry`, `FeaturePipeline`. **Consumes:** provider observations. **Produces:**
versioned features. **Dependencies:** Core. **Future consumers:** analysis and Strategy. **Decision:**
calculate once and reuse.

## EPIP-004 — Market Data

**Purpose:** isolate market-data acquisition and normalization. **Responsibilities:** provider
protocol, factory, registry, cache, configuration, CSV/fake providers, external adapter boundaries.
**Public API:** `DataSource`, `DataSourceProtocol`, `DataSourceFactory`, `DataSourceRegistry`,
`DataSourceCache`, request/result models. **Consumes:** provider data. **Produces:** normalized market
data. **Dependencies:** Core. **Future consumers:** Replay and live ingestion. **Decision:** external
vendors remain behind adapters.

## EPIP-005 — Replay Engine

**Purpose:** deterministic historical-time execution. **Responsibilities:** clock, scheduler,
iterator, session, controller, state, metrics, statistics, events. **Public API:** `ReplayEngine`,
`ReplayConfig`, `ReplayClock`, `ReplaySession`, `ReplayScheduler`. **Consumes:** ordered market data.
**Produces:** replay events and session state. **Dependencies:** Core, EventBus, Market Data.
**Future consumers:** backtests and Strategy. **Decision:** time is explicit and controllable.

## EPIP-006 — Swing Engine

**Purpose:** extract pivots and directional swing sequences. **Responsibilities:** pivot detection,
window strategies, filtering, validation, classification, statistics, events. **Public API:**
`SwingEngine`, `SwingDetector`, `Swing`, `SwingPoint`, `SwingSequence`, `SwingConfig`. **Consumes:**
ordered candles. **Produces:** swing objects and metrics. **Dependencies:** Core, EventBus. **Future
consumers:** Structure, Fibonacci, Elliott. **Decision:** pivot policy is configurable.

## EPIP-007 — Market Structure Engine

**Purpose:** classify structural market behavior. **Responsibilities:** BOS, CHOCH, trend, range,
state machine, observers, confidence, graph, history, serialization. **Public API:**
`MarketStructureEngine`, detectors, `StructureSnapshot`, `StructureGraph`, `StructureHistory`.
**Consumes:** swings and observations. **Produces:** immutable structure snapshots and events.
**Dependencies:** Core, EventBus, Swing. **Future consumers:** Liquidity, Context, Decision.
**Decision:** structural transitions are explicit and versioned.

## EPIP-008 — Liquidity Engine

**Purpose:** model liquidity locations and consumption. **Responsibilities:** pools, sweeps, equal
levels, internal/external liquidity, FVGs, voids, clusters, strength/ranking, state and timeframe
tree. **Public API:** `LiquidityEngine`, `LiquiditySnapshot`, `LiquidityGraph`, `LiquidityHistory`,
`LiquidityCluster`, `FairValueGap`, `LiquidityVoid`. **Consumes:** price and structure. **Produces:**
liquidity snapshots/events. **Dependencies:** Core, EventBus, Structure. **Future consumers:**
Fibonacci, Context, Decision. **Decision:** liquidity objects retain lifecycle and lineage.

## EPIP-009 — Fibonacci Engine

**Purpose:** model retracement and projection geometry. **Responsibilities:** levels, retracements,
extensions, premium/discount, OTE, Golden Zone, clusters, institutional zones, targets, alignment,
probability. **Public API:** `FibonacciEngine`, `FibonacciSnapshot`, `FibonacciGraph`,
`FibonacciHistory`, `FibonacciCluster`, `ProjectionTarget`. **Consumes:** swing geometry and liquidity
context. **Produces:** Fibonacci snapshots. **Dependencies:** Core, EventBus, Swing. **Future
consumers:** Context and Decision. **Decision:** deterministic levels become immutable evidence.

## EPIP-010 — Market Context Engine

**Purpose:** aggregate official analytical outputs into a coherent context. **Responsibilities:**
builder, aggregator, phase, bias, confluence, graph/history, versioned serialization. **Public API:**
`MarketContextEngine`, `MarketContextBuilder`, `MarketContextSnapshot`, `MarketContextGraph`,
`MarketContextHistory`. **Consumes:** Structure, Liquidity, Fibonacci outputs. **Produces:** market
phase, bias and context snapshots. **Dependencies:** Core, EventBus and analytical contracts.
**Future consumers:** Elliott and Decision. **Decision:** aggregation never replaces source engines.

## EPIP-011 — Elliott Wave Engine

**Purpose:** produce validated Elliott wave interpretations. **Responsibilities:** detection,
validation, counts, alternates, degrees, rules, projections, targets, scores, graph/history.
**Public API:** `ElliottWaveEngine`, `WaveSnapshot`, `WaveGraph`, `WaveHistory`, wave models.
**Consumes:** `MarketContextSnapshot` and structural observations. **Produces:** wave snapshots and
events. **Dependencies:** Core, EventBus, Context. **Future consumers:** Decision and AI.
**Decision:** alternatives and probability remain explicit rather than hidden.

## EPIP-012 — Decision Engine

**Purpose:** single authority for trading intent. **Responsibilities:** rule evaluation, matrix,
scoring, confidence, probability, priority, rationale, risk profile, entry/exit suggestions,
history/graph/events. **Public API:** `DecisionEngine`, `DecisionSnapshot`, `TradeDecision`,
`DecisionGraph`, `DecisionHistory`. **Consumes:** aligned Context and Elliott snapshots. **Produces:**
the official `TradeDecision`. **Dependencies:** Core, EventBus, Context, Elliott. **Future
consumers:** Risk and AI. **Decision:** no downstream module may recreate trade intent.

## EPIP-013 — Risk Engine

**Purpose:** single authority for sizing and risk plans. **Responsibilities:** fixed/Kelly/ATR/
volatility sizing, stops, targets, exposure, drawdown, limits, leverage, margin, score,
history/graph/events. **Public API:** `RiskEngine`, `RiskSnapshot`, `PositionPlan`, `RiskGraph`,
`RiskHistory`, `RiskConfig`. **Consumes:** only `TradeDecision`/`DecisionSnapshot`. **Produces:** the
official `PositionPlan`. **Dependencies:** Core, EventBus, Decision. **Future consumers:** Execution,
Portfolio, AI. **Decision:** position sizing cannot be duplicated.

## EPIP-014 — Execution Engine

**Purpose:** single official order-execution and broker boundary. **Responsibilities:** order
creation, lifecycle, fills, retry, slippage, commission, adapters, history, graph, events.
**Public API:** `ExecutionEngine`, `ExecutionSnapshot`, `Order`, `ExecutionReport`,
`BrokerAdapterProtocol`, `PaperTradingAdapter`, `ExecutionGraph`, `ExecutionHistory`. **Consumes:**
only accepted `PositionPlan`. **Produces:** `ExecutionSnapshot` and broker lifecycle events.
**Dependencies:** Core, EventBus, Risk contract. **Future consumers:** Portfolio, Monitoring, AI.
**Decision:** no other module communicates directly with a broker.
