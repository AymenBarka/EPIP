# Architecture Principles

## Domain-driven design

Each EPIP module is a bounded context with its own vocabulary, invariants, public models, engine,
events, history, graph, and metrics where appropriate. Calculations belong to exactly one domain.
Decision owns action selection, Risk owns position sizing, and Execution owns broker interaction.

## SOLID design

- **Single responsibility:** engines orchestrate; analyzers calculate; validators enforce; adapters
  integrate.
- **Open/closed:** protocols and strategies allow extensions without rewriting stable consumers.
- **Liskov substitution:** protocol implementations preserve input/output and failure semantics.
- **Interface segregation:** narrow ports avoid forcing consumers to depend on unrelated operations.
- **Dependency inversion:** domain code depends on protocols and immutable upstream contracts rather
  than concrete vendors or downstream engines.

## Event-driven integration

EventBus carries immutable lifecycle facts in deterministic publication order. Events decouple
producers from audit, monitoring, reporting, and future integrations. Domain correctness must not
depend on an optional listener, and listeners must not mutate published objects.

## Immutable objects

Published values, snapshots, histories, graph nodes/edges, decisions, position plans, orders, and
reports are immutable. Engines may maintain private registries, but callers receive stable values.
Copy-on-append history and graph operations preserve earlier versions.

## No duplicated calculations

Consumers use official outputs. Structure is not recalculated in Liquidity; Decision is not
recreated in Risk; sizing is not repeated in Execution; broker communication is not performed by
Portfolio. Duplication creates contradictory truths and invalidates replay and auditability.

## Layer isolation

Core has no domain-engine dependency. Upstream analysis does not import downstream actions.
External vendors and brokers remain behind adapters. Domain models contain no transport,
credentials, network calls, or framework orchestration.

## Versioning and serialization

Snapshots carry stream versions and engine/schema metadata. Sequential histories validate version
progression. Deterministic dictionary and JSON round trips preserve enum and nested object types.
Compatibility changes follow the API stability and release policies.

## Thread safety

Stateful engines protect private mutable state with `RLock`, take consistent snapshots under lock,
and publish immutable results. Domain services should remain pure when possible. Thread safety does
not imply distributed transaction safety; adapters define their own external consistency semantics.

## Public APIs

Package-root exports in `__all__`, documented protocols, snapshots, official domain outputs, events,
graphs, histories, and configuration models are public contracts. Internal helpers are replaceable.
Stable APIs change only through additive evolution or governed deprecation.

## Architecture acceptance criteria

A change must have one owner, legal dependencies, immutable published contracts, deterministic
behavior, typed failures, tests, documentation, and quality evidence. Engine-level architecture
changes require an ADR and Chief Architect approval.
