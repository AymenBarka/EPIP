# ADR-0005 - Replay Engine As Official EPIP Clock

## Status
Accepted

## Context
EPIP now has validated core domain, runtime orchestration, feature store, and market data layers.
A dedicated replay engine is required to drive deterministic historical progression for all downstream analytical and execution systems.

## Decision
Introduce EPIP-005 Replay Engine as the official time source and historical orchestrator.

## Key Decisions
- Replay uses MarketData through DataSourceProtocol only.
- Replay iterates lazily through paginated history requests.
- Replay publishes stateful progression events through EventBus.
- Replay builds FeatureStore incrementally and then MarketContext incrementally.
- Replay delegates analysis execution to Kernel instead of embedding plugin logic.

## Why This Design
- Keeps time control centralized.
- Prevents direct vendor coupling in replay consumers.
- Enables deterministic backtesting and future live-trading convergence.
- Preserves memory by avoiding full history materialization.

## Consequences
### Positive
- Clear orchestration boundary for historical progression.
- Extensible for multi-symbol, multi-timeframe, and live migration.
- Better observability through replay metrics and events.

### Trade-offs
- More coordination objects to maintain.
- Strict contracts required between MarketData, Replay, FeatureStore, and Kernel.
