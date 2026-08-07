# Roadmap

```mermaid
timeline
    title EPIP release roadmap
    v1.0.0-pre : Market Context and analytical foundation
    v1.1.0 : Elliott Wave Engine
    v1.2.0 : Decision Engine
    v1.3.0 : Risk Engine
    v1.4.0 : Execution Engine
    v1.5.0 : Portfolio Engine
    v1.6.0 : Strategy Engine
    v1.7.0 : Monitoring and Observability
    v2.0.0 : AI Engine
```

## Completed releases

- **v1.0.0-pre:** completed the core analytical pipeline through Market Context, combining Core,
  EventBus, Feature Store, Market Data, Replay, Swing, Structure, Liquidity, and Fibonacci outputs.
- **v1.1.0:** added Elliott wave detection, validation, alternate counts, degrees, projections,
  graph/history, scoring, and Market Context integration.
- **v1.2.0:** established the single Decision Engine for rules, scores, confidence, probability,
  priority, rationale, entry/exit suggestions, and immutable `TradeDecision` snapshots.
- **v1.3.0:** established the Risk Engine as the sole sizing authority and introduced
  `PositionPlan`, portfolio limits, stops, targets, exposure, drawdown, leverage, and margin.
- **v1.4.0:** established the Execution Engine as the sole broker boundary with explicit order
  lifecycle, paper trading, adapters, fills, retry, costs, history, and graph.

## Planned releases

- **v1.5.0 — Portfolio Engine:** aggregate execution outcomes, positions, cash, P&L, exposure, and
  portfolio constraints using `ExecutionSnapshot` as the official input.
- **v1.6.0 — Strategy Engine:** orchestrate portfolio-aware strategy policies without duplicating
  analysis, decision, risk, or execution calculations.
- **v1.7.0 — Monitoring & Observability:** metrics, tracing, health, audit streams, operational
  dashboards, and alerting across engine boundaries.
- **v2.0.0 — AI Engine:** explainable AI assistance over official snapshots and histories, subject
  to deterministic safety, governance, and human-control boundaries.

Roadmap items are intentions, not compatibility guarantees, until accepted by an ADR and released.
