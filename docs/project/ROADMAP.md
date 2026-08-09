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
    v1.5.1 : Foundation Hardening
    v1.5.2 : Determinism and Identity
    v1.5.3 : Release metadata correction
    v1.5.4 : Release workflow correction
    v1.5.5 : Hardening-002 Data Integrity
    v1.5.6 : Hardening-002 release metadata correction
    v1.5.7 : Hardening-003 Financial Correctness
    v1.5.8 : Hardening-003 release metadata correction
    v1.5.9 : Hardening-004 Thread Safety and Concurrency
    v1.5.10 : Hardening-005 Memory Safety and Resource Management
    v1.5.11 : Hardening-005 release metadata correction
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
- **v1.5.0:** established the Portfolio Engine for positions, allocation, cash, P&L, exposure,
  drawdown, correlation groups, and portfolio-level risk limits.
- **v1.5.1:** delivered repository governance, open-source infrastructure, security automation,
  MkDocs, CodeQL, Dependabot, and developer-experience hardening.
- **v1.5.2:** delivered Hardening-001 deterministic clocks, identity generators, event metadata,
  serialization identity preservation, and reproducible replay support.
- **v1.5.3:** corrects release metadata and Markdown validation for the Hardening-001 delivery.
- **v1.5.4:** makes annotated-tag validation reliable in GitHub Actions runners.
- **v1.5.5:** delivered Hardening-002 fail-fast validation, immutable payload protection,
  domain-specific integrity errors, and automated compliance coverage.
- **v1.5.6:** aligns all release metadata for the Hardening-002 delivery while preserving the
  already-published v1.5.5 tag.
- **v1.5.7:** delivered Hardening-003 periodic PnL semantics, average-cost accounting, commission
  and fill validation, and enforced portfolio financial identities.
- **v1.5.8:** aligns all release metadata for the Hardening-003 delivery while preserving the
  already-published v1.5.7 tag.
- **v1.5.9:** delivers Hardening-004 concurrency contracts, EventBus safety, engine and Replay
  atomicity, Kernel and plugin isolation, external-boundary contracts, and production stress
  validation.
- **v1.5.10:** delivered Hardening-005 memory contracts, bounded retention, deterministic resource
  lifecycles, recovery policies, memory audits, and institutional validation.
- **v1.5.11:** aligns all release metadata for the Hardening-005 delivery while preserving the
  already-published v1.5.10 tag.

## Planned releases

- **v1.6.0 — Strategy Engine:** orchestrate portfolio-aware strategy policies without duplicating
  analysis, decision, risk, or execution calculations.
- **v1.7.0 — Monitoring & Observability:** metrics, tracing, health, audit streams, operational
  dashboards, and alerting across engine boundaries.
- **v2.0.0 — AI Engine:** explainable AI assistance over official snapshots and histories, subject
  to deterministic safety, governance, and human-control boundaries.

Roadmap items are intentions, not compatibility guarantees, until accepted by an ADR and released.
