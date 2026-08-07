# Event Catalog

All events are immutable EventBus facts. `BaseEvent` supplies `id`, `timestamp`, `schema_version`,
`created_at`, and `uuid`. Domain event bases add stream or aggregate identifiers. Consumers should
subscribe to the qualified Python class, because names such as `DecisionCreated`, `ContextUpdated`,
or `ConfluenceUpdated` exist in different bounded contexts.

## Core Domain — EPIP-001/002

| Event | Purpose | Domain payload |
| --- | --- | --- |
| `EvidenceCreated` | Evidence accepted and published | `evidence_id` |
| `EvidenceRejected` | Evidence rejected | `evidence_id`, `reason` |
| `ScenarioCreated` | Scenario created | `scenario_id` |
| `ScenarioRejected` | Scenario rejected | `scenario_id`, `reason` |
| `DecisionCreated` | Core-domain decision created | `decision_id` |
| `DecisionRejected` | Core-domain decision rejected | `decision_id`, `reason` |

## Replay — EPIP-005

| Event | Purpose |
| --- | --- |
| `ReplayStarted` | Session entered running state |
| `ReplayPaused` | Replay clock/session paused |
| `ReplayResumed` | Paused replay resumed |
| `ReplayFinished` | Replay reached a terminal result |
| `CandleLoaded` | Candle obtained from the data source |
| `CandleProcessed` | Candle completed downstream processing |
| `ContextUpdated` | Replay's current market context changed |
| `FeatureUpdated` | Replay's feature state changed |

Replay events include their declared session, candle, context, feature, or progression metadata in
addition to BaseEvent fields.

## Swing — EPIP-006

| Event | Purpose |
| --- | --- |
| `SwingDetected` | Candidate swing detected |
| `SwingUpdated` | Existing swing information updated |
| `SwingConfirmed` | Swing passed confirmation rules |
| `SwingRejected` | Candidate failed validation/filtering |
| `SwingMerged` | Compatible swing information merged |

Swing events identify symbol, timeframe, timestamp and applicable swing/pivot data.

## Market Structure — EPIP-007

`MarketStructureEvent` is the domain base carrying `event_id`, `symbol`, `timeframe`, `version`,
`engine_version`, and `source`.

| Event | Purpose | Additional payload |
| --- | --- | --- |
| `StructureDetected` | New structure state published | structure state/details |
| `BOSDetected` | Break of Structure confirmed | BOS object |
| `CHOCHDetected` | Change of Character confirmed | CHOCH object |
| `TrendChanged` | Official trend changed | prior/new trend |
| `RangeDetected` | Range state identified | range object |
| `StructureReset` | Structure stream reset | reset metadata |

## Liquidity — EPIP-008

`LiquidityEvent` carries symbol, timeframe and version identifiers.

| Event | Purpose |
| --- | --- |
| `LiquidityDetected` | General liquidity object detected |
| `LiquidityPoolCreated` | New buy-side/sell-side pool created |
| `LiquiditySweepDetected` | Pool or level swept |
| `EqualHighDetected` | Equal-high cluster confirmed |
| `EqualLowDetected` | Equal-low cluster confirmed |
| `LiquidityConsumed` | Liquidity lifecycle reached consumption |
| `LiquidityInvalidated` | Liquidity object invalidated |

## Fibonacci — EPIP-009

`FibonacciEvent` carries symbol, timeframe and version identifiers.

| Event | Purpose |
| --- | --- |
| `FibonacciComputed` | Fibonacci snapshot/levels computed |
| `GoldenZoneDetected` | Golden Zone identified |
| `OTEFound` | OTE zone identified |
| `ExtensionComputed` | Projection extension computed |
| `ConfluenceUpdated` | Fibonacci confluence changed |

## Market Context — EPIP-010

`MarketContextEvent` carries symbol, timeframe and context version identifiers.

| Event | Purpose |
| --- | --- |
| `ContextCreated` | First context snapshot for a stream |
| `ContextUpdated` | Later context version published |
| `BiasChanged` | Institutional bias changed |
| `PhaseChanged` | Market phase changed |
| `ConfluenceUpdated` | Aggregate confluence changed |

## Elliott Wave — EPIP-011

`ElliottEvent` carries symbol, timeframe, version and wave-count identifiers.

| Event | Purpose |
| --- | --- |
| `WaveDetected` | Wave candidate detected |
| `WaveValidated` | Wave/count passed rules |
| `WaveInvalidated` | Wave/count violated rules |
| `AlternateCreated` | Alternate count added |
| `CountUpdated` | Official count changed |
| `ProjectionUpdated` | Wave projection/target changed |

## Decision — EPIP-012

`TradeDecisionEvent` carries symbol, timeframe, version and `decision_id`.

| Event | Purpose | Additional payload |
| --- | --- | --- |
| `DecisionCreated` | First official decision published | action |
| `DecisionUpdated` | New version of decision published | action |
| `DecisionInvalidated` | Decision became invalid | reason |
| `DecisionExecuted` | Consumer marked decision executed | none |
| `DecisionExpired` | Consumer marked decision expired | none |

## Risk — EPIP-013

`RiskEvent` carries symbol, `decision_id`, and `plan_id`.

| Event | Purpose | Additional payload |
| --- | --- | --- |
| `PositionPlanned` | PositionPlan produced | accepted flag |
| `RiskAccepted` | Plan passed risk constraints | none |
| `RiskRejected` | Plan failed one or more constraints | reason |
| `ExposureExceeded` | Symbol/correlated exposure exceeded | exposure |
| `DrawdownExceeded` | Drawdown policy exceeded | drawdown |

## Execution — EPIP-014

`ExecutionEvent` carries symbol, `order_id`, and `plan_id`.

| Event | Purpose | Additional payload |
| --- | --- | --- |
| `OrderCreated` | PositionPlan mapped to an order | none |
| `OrderSubmitted` | Order submitted to adapter | none |
| `OrderFilled` | Order reached filled state | quantity |
| `OrderRejected` | Broker or validation rejected order | reason |
| `OrderCancelled` | Cancellable order entered cancelled state | none |
| `ExecutionCompleted` | Execution report completed | commission |

## Consumer rules

Listeners must be idempotent when they trigger external side effects, must not mutate payloads, and
must not perform another domain's official calculation. Event schema changes follow the API
stability policy. Monitoring may subscribe to `object` for an audit stream; business consumers
should prefer concrete event classes.
