# ADR-0016: Post-v1.6.0 Canonical Strategy Pipeline and Semantic Ownership

## Status

Accepted

## Context

EPIP contains mature Market Data, Replay, Swing, Market Structure, Liquidity, Fibonacci, Context,
Elliott, Decision, Risk, Execution, and Portfolio domains, the Core Kernel inference path, and the
frozen A07 Strategy Engine. Before this decision, tracked documentation allowed three partially
parallel interpretations: manual historical-engine composition, Core Kernel inference, and direct
A07 construction from caller-supplied facts.

That ambiguity is implementation-significant. Historical `DecisionSnapshot` and Core `Decision`
objects can appear to be final trade authorities. Historical Risk selects or synthesizes stops and
targets and calculates reward-risk values. A07 now owns those final strategy semantics, but no
production Strategy Runtime binds official analysis to A07 and downstream capital risk.

This record supersedes the final-authority and future-module portions of ADR-0012, ADR-0013, and
ADR-0015 for the post-v1.6.0 canonical runtime. Their implemented APIs remain compatibility APIs
until separately migrated; this ADR does not change production code.

## Decision

### Canonical semantic owners

A07 is the sole canonical owner of strategy policy gating, evidence eligibility, final
`StrategyDirection`, entry geometry, stop geometry, target geometry, trade risk distance, reward
distance, reward-risk ratio and acceptance, strategy-confidence binding, expiration, and final
`StrategySignal`.

Historical Decision is reclassified in the canonical runtime as analytical assessment and
candidate generation. It may own scenarios, scores, probabilities, quality, priority, reasoning,
explanations, evidence, and suggested directions, entries, exits, and invalidations. Neither
`DecisionSnapshot` nor `TradeDecision` is a final strategy signal in new production integrations.
Core Kernel `Decision` output has the same analytical/evidence-only status unless a later ADR
governs it differently. Neither path may bypass A07.

Capital Risk owns account equity, available margin, capital-at-risk policy, position quantity and
notional, exposure, leverage, margin, drawdown, portfolio limits, and capital-constraint
acceptance. It consumes a canonical signal envelope plus immutable portfolio-risk facts. It must
reject a signal that violates constraints; it must not replace direction or entry, synthesize a
stop or target, recalculate strategy risk/reward/RR, or change confidence or expiration.

Execution owns execution-intent validation, order construction, submission, cancellation, retry,
order lifecycle, fills, slippage, commission, and execution reporting. It must not recompute
analysis or strategy semantics. Broker adapters may normalize tick size, quantity increments, lot
constraints, and venue formats only when they retain requested and normalized values, preserve
direction and protective ordering, and reject a normalization that violates canonical geometry.

Portfolio owns positions, cash, margin use, equity, realized and unrealized PnL, allocation,
exposure, correlation, portfolio limits, and rebalance views. It consumes fills/execution state and
may expose an immutable pre-trade constraint view to Capital Risk. It does not select strategy
direction, geometry, RR, or confidence.

### Strategy Fact Adapter and Strategy Profile

A future Strategy Fact Adapter/Profile boundary owns versioned, strategy-specific semantic mapping
from official analytical outputs into A07 caller-authoritative facts. This is not a field-copy
layer. It owns mappings for Elliott, trend, structure, MTF, primary, and alternate direction;
entry-source selection; stop/invalidation-source selection; target-source selection; confidence
calibration or aggregation; and evidence taxonomy and provenance mapping. It may consume public
analytical contracts and A07 fact contracts but may not modify A07 internals.

### Strategy Runtime

A future Strategy Runtime outside A07 owns immutable evaluation-context intake, source snapshot
and provenance coherence, temporal-alignment validation, strategy-profile selection, adapter
invocation, A07 E00-E09 orchestration, signal-context envelope creation, and runtime diagnostics.
It does not recompute analytics, modify A07 policy, size positions, execute orders, access broker
state, or read ambient wall time.

### Temporal authority

Evaluation time is explicit and injected. Replay and backtest use `ReplayClock` or the canonical
event timestamp. Paper uses an injected market/event timestamp. MT5 demo and live use normalized
venue/event time, with receipt time represented separately when required. Strategy Runtime passes
the explicit `evaluation_timestamp` into A07. Deterministic strategy evaluation must not call
`datetime.now()`, `time.time()`, or a local system clock. The same immutable input bundle, contract
and profile versions, and evaluation timestamp must produce the same result.

### Canonical pipeline

```text
DataSource
-> Candle
-> Replay / Evaluation Clock
-> SwingSequence
-> MarketStructureSnapshot
-> LiquiditySnapshot
-> FibonacciSnapshot
-> MarketContextSnapshot
-> WaveSnapshot
-> analytical candidate/evidence assessment
-> Strategy Fact Adapter + Strategy Profile
-> StrategyFactBundle [FUTURE CONTRACT]
-> Strategy Runtime [FUTURE]
-> A07 E00-E09
-> StrategySignal
-> StrategySignalEnvelope [FUTURE CONTRACT]
-> Capital Risk
-> sized/constrained capital-risk plan [FUTURE CONTRACT]
-> Execution
-> Broker Adapter
-> Fill / ExecutionSnapshot
-> Portfolio accounting
-> PortfolioSnapshot
```

Core Kernel may contribute evidence only through a governed adapter. Backtest, paper, MT5 demo,
and live use this same domain pipeline and Strategy Runtime; only data, clock, broker, persistence,
and telemetry adapters vary. No deployment mode may contain alternative strategy code.

### Object boundaries

| Owner | Input | Output | State |
| --- | --- | --- | --- |
| Market Data | provider/file response | `Candle` stream | Existing |
| Replay | candles and replay controls | `ReplayClock`, replay events | Existing |
| Swing | ordered candles | `SwingSequence` | Existing |
| Market Structure | `SwingSequence` | `MarketStructureSnapshot` | Existing |
| Liquidity | Swing and Structure outputs | `LiquiditySnapshot` | Existing |
| Fibonacci | Swing, Structure, Liquidity | `FibonacciSnapshot` | Existing |
| Context | aligned analytical snapshots | `MarketContextSnapshot` | Existing |
| Elliott | `MarketContextSnapshot` | `WaveSnapshot` | Existing |
| Decision analysis | Context and Wave snapshots | `DecisionSnapshot`/assessment | Existing compatibility API |
| Runtime boundary | snapshots, versions, explicit time | `EvaluationContext` | FUTURE CONTRACT |
| Fact Adapter/Profile | official analysis and profile | `StrategyFactBundle` | FUTURE CONTRACT |
| Strategy Runtime | evaluation context and fact bundle | `StrategyRuntimeRequest`/`StrategyRuntimeResult` | FUTURE CONTRACT |
| A07 | E00-E08 canonical predecessors | `StrategySignal` | Existing, frozen |
| Runtime boundary | signal plus source context | `StrategySignalEnvelope` | FUTURE CONTRACT |
| Portfolio | execution/fill state | immutable `PortfolioRiskSnapshot`/constraint view | FUTURE CONTRACT |
| Capital Risk | signal envelope and constraint view | capital-risk plan successor | FUTURE CONTRACT |
| Legacy Risk | `DecisionSnapshot` | `PositionPlan` | Existing compatibility API |
| Execution | accepted position/execution plan | `ExecutionSnapshot` | Existing |
| Portfolio | completed execution/fills | `PortfolioSnapshot` | Existing |

P01 owns field-level specification of every future contract. This ADR authorizes no implementation.

### Dependency rules

Infrastructure may feed domain inputs. Analysis may consume earlier public analytical outputs.
Fact Adapters may consume public analysis and A07 fact contracts. Strategy Runtime may consume
adapters and frozen A07. Capital Risk consumes the signal envelope and immutable portfolio-risk
facts. Execution consumes accepted Capital Risk output. Portfolio consumes execution/fills.

The following dependencies are forbidden: A07 to Runtime, Risk, Execution, Portfolio, broker, or
MT5; analytics to downstream execution state; Risk to analytical recomputation; Execution to
strategy recomputation; Portfolio to strategy authority; broker types to domain contracts; and
wall-clock services to deterministic Strategy Runtime. Immutable read models and domain-owned
protocols prevent Portfolio/Risk feedback and adapter/runtime circular dependencies.

### Deployment modes

- **Backtest:** historical market-data adapter, ReplayClock, and simulated broker.
- **Paper:** live or replayed data, injected event clock, and paper broker.
- **MT5 demo:** MT5 market-data and broker adapters with canonical EPIP contracts internally.
- **Live:** the same domain runtime with hardened adapter, reconciliation, safety controls,
  persistence, and observability.

## Consequences

EPIP has one final strategy authority, deterministic replay/live equivalence, no legitimate
downstream strategy recomputation, a preserved A07 freeze, Capital Risk separated from trade
geometry, broker-neutral Execution, testable adapter/profile contracts, and one runtime across all
deployment modes.

Migration requires Decision APIs to be treated as analytical compatibility APIs, a Capital Risk
successor boundary, possible adaptation of the legacy `PositionPlan` path, Strategy Runtime and
provenance contracts, and explicit MTF/profile rules. Backtest, paper, MT5, and live integration
remain future separately authorized work.

The next milestone is **P01 — Canonical Strategy Runtime and Fact Adapter Contract**. P01 is
contract/governance work only and requires separate authorization.
