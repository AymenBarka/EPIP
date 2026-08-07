# Project Overview

## What EPIP is

EPIP is a modular Python framework for deterministic quantitative-market analysis and trade
infrastructure. It models a complete flow from market-data ingestion through broker execution while
keeping every analytical concern behind a stable public boundary.

## Goals and audience

EPIP exists to prevent tightly coupled trading systems, duplicated calculations, opaque mutable
state, and direct broker access from arbitrary modules. It targets quantitative developers,
research engineers, framework architects, execution engineers, and teams that need auditable
research-to-execution infrastructure.

Its goals are reproducibility, explainability, type safety, extensibility, testability, and stable
integration contracts. It is a framework, not a trading strategy or promise of profitability.

## Architecture philosophy

- **DDD:** each engine owns a bounded domain vocabulary and invariants.
- **SOLID:** engines have focused responsibilities and depend on protocols or immutable contracts.
- **Clean Architecture:** domain models and calculations remain isolated from adapters and runtime
  orchestration.
- **Event-driven integration:** EventBus publishes lifecycle facts without coupling producers to
  consumers.
- **Immutable models:** snapshots, histories, graph nodes, and domain values cannot change after
  publication.
- **Versioning:** snapshots carry monotonic versions and engine/schema metadata for replay.
- **Thread safety:** stateful engines use reentrant locks around internal mutation.
- **Determinism:** serialization, graph construction, history ordering, and calculations avoid
  hidden state.

These principles allow downstream engines to consume official outputs instead of reproducing
upstream analysis. Decision owns trade intent, Risk owns position sizing, and Execution owns broker
communication.
