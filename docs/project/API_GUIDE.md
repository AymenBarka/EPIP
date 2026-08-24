# API Guide

## Public API conventions

Import stable types from package roots such as `epip.context`, `epip.decision`, `epip.risk`, and
`epip.execution`. Constructor details and signatures are defined by those exports and their typed
models. Internal analyzers and helpers are extension details unless explicitly re-exported.

## Snapshots

Snapshots are immutable, versioned records of an engine result. Major snapshot families are
Structure, Liquidity, Fibonacci, Market Context, Wave, Decision, Risk, Execution, and Portfolio.
They carry
stream identity (for example symbol/timeframe), timestamp, monotonic version, engine version, and
the official domain result. Downstream consumers keep the snapshot or its official contained object
instead of copying its calculation.

The currently implemented historical compatibility boundary is:

```text
MarketContextSnapshot + WaveSnapshot -> DecisionSnapshot/TradeDecision
TradeDecision -> RiskSnapshot/PositionPlan
PositionPlan -> ExecutionSnapshot/ExecutionReport
ExecutionSnapshot -> PortfolioSnapshot
```

For new post-v1.6.0 integrations, `DecisionSnapshot`, `TradeDecision`, and Core Kernel `Decision`
are analytical outputs, not final strategy signals. A07 `StrategySignal` is the final strategy
output. The future boundary is Strategy Runtime -> `StrategySignal`/`StrategySignalEnvelope` ->
Capital Risk. Strategy Runtime, `StrategySignalEnvelope`, and the Capital Risk successor are
**NOT YET IMPLEMENTED**.

## Graphs

Structure, Liquidity, Fibonacci, Context, Wave, Decision, Risk, and Execution graphs preserve
lineage. Nodes contain immutable snapshots; typed edges represent previous/next, parent/child, or
links to source-domain objects. Graph methods expose deterministic traversal and prepare
downstream consumers without embedding them. Portfolio is implemented; AI remains future.

## Histories

Histories are immutable append-only sequences. Their shared behavioral vocabulary is `append`,
`latest`, `by_version`, `by_timestamp`, and `replay`. Append validates sequential versions; replay
returns original order. Engines expose empty histories when a stream has not produced data.

## Versioning and serialization

Snapshot versions increase per stream. Engine/schema versions identify the producer contract.
Public snapshots support deterministic `to_dict`, `from_dict`, `to_json`, and `from_json` round
trips. JSON uses stable key ordering where implemented. Persist the engine version with the payload
and reject incompatible migrations explicitly rather than silently coercing data.

## EventBus

`EventBus` provides thread-safe subscribe, unsubscribe, publish, bulk publish, listener inspection,
and ordered event history. Subscribe to concrete event types for domain-specific behavior or
`object` for a complete audit stream. Listeners execute synchronously; slow or unreliable external
work should be delegated by an adapter rather than blocking domain publication.

```python
from epip.core import EventBus

bus = EventBus()
events: list[object] = []
bus.subscribe(object, events.append)
```

## Engine lifecycle

Create configuration explicitly, inject a shared EventBus and any adapter protocols, process the
official upstream object, then query `snapshot`, `history`, `graph`, and `metrics`. Engines guard
internal mutable registries; returned domain objects remain immutable.
