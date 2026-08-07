# EPIP Documentation

EPIP is a typed, event-driven Python framework for deterministic market analysis, decision making,
risk planning, and order execution. This site is the authoritative entry point for architecture,
public contracts, governance, quality, and contribution guidance through release `v1.4.0`.

## Start here

- [Project overview](project/PROJECT_OVERVIEW.md) explains goals, audience, and philosophy.
- [Architecture](project/ARCHITECTURE.md) presents layers, data flow, and dependency direction.
- [Modules](project/MODULES.md) documents EPIP-001 through EPIP-014.
- [Pipeline](project/PIPELINE.md) follows data from Market Data to Execution.
- [API guide](project/API_GUIDE.md) explains snapshots, histories, graphs, EventBus, and versioning.
- [Developer guide](project/DEVELOPER_GUIDE.md) defines contribution and quality requirements.

## Official contracts

```mermaid
flowchart LR
    A[Market Analysis] --> C[MarketContextSnapshot]
    C --> W[WaveSnapshot]
    C --> D[TradeDecision]
    W --> D
    D --> R[PositionPlan]
    R --> E[ExecutionSnapshot]
```

Each output has one owning engine. Downstream modules consume immutable official objects and never
duplicate Decision, sizing, or broker-execution calculations.

## Governance and maintenance

Read the [architecture principles](project/ARCHITECTURE_PRINCIPLES.md),
[ADR index](project/DECISIONS.md), [API stability policy](project/API_STABILITY.md), and
[release policy](project/RELEASE_POLICY.md) before proposing framework changes. Security issues must
follow the private disclosure process in the repository security policy.

## Current status

- Release: `v1.4.0`
- Completed modules: 14
- Quality: Black, Ruff, strict MyPy, and Pytest passing
- Aggregate coverage: 97%
- License: Apache-2.0
