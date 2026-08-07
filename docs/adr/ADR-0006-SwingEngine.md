# ADR-0006 - Swing Engine As Official Pivot Source

## Status

Accepted

## Context

EPIP now includes validated Core Domain, Event Bus, Feature Store, Market Data, and Replay Engine.
A dedicated swing layer is required so every downstream analytical module relies on the same pivot truth.

## Decision

Introduce EPIP-006 Swing Engine as the unique source of Swing High/Low and derived structure labels (HH/HL/LH/LL/EH/EL, Internal/External).

## Key Decisions

- Swing Engine is independent from Market Structure, Liquidity, Elliott, ICT, SMC, and Wyckoff logic.
- Swing Engine consumes candles and emits standardized swing events and models only.
- Strategy Pattern is mandatory for pivot detection extensibility.
- PivotWindowStrategy is implemented first as deterministic baseline.
- Fractal/ATRAdaptive/ZigZag/Hybrid strategies are declared as explicit interfaces/placeholders.
- Filter chain is modular and composable.
- Processing is streaming-only and memory bounded.

## Why Dedicated Engine

- Enforces one canonical pivot source across the framework.
- Prevents drift and contradictions caused by duplicate pivot calculations.
- Simplifies testing and validation of all higher-level engines.

## Why Strategy Pattern

- Isolates algorithmic concerns from orchestration and event publication.
- Allows incremental introduction of advanced detectors without changing consumers.
- Preserves stable contracts while enabling quantitative experimentation.

## Why Independent Filters

- Makes quality gates explicit and auditable.
- Allows strict or permissive behavior by configuration.
- Supports deterministic composition and future optimization.

## Consequences

### Positive

- Strong architectural boundary and clean dependency direction.
- Deterministic replay-compatible swing generation.
- Better performance control for large historical datasets.

### Trade-offs

- More classes and contracts to maintain.
- Additional complexity in validating multi-filter interaction.
