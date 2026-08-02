# ADR-0004 - Market Data Layer with Ports & Adapters

## Status
Accepted

## Context
EPIP already validates core domain, event orchestration, and feature store layers.
Without a dedicated market data abstraction, concrete vendors and file formats can leak into runtime and analysis modules.
This causes coupling, duplicate integrations, and lower testability.

## Decision
Introduce EPIP-004 Market Data Layer as the single entry point for all market data access.

### Key Decisions
- Use `DataSourceProtocol` as the only data ingress contract.
- Use `DataSourceFactory` for provider construction from configuration.
- Use `DataSourceRegistry` for runtime registration and default-provider resolution.
- Use thread-safe `DataSourceCache` with TTL and LRU behavior.
- Keep TwelveData/MT5 as adapter-based interface placeholders without live network or platform dependencies.

## Why Market Data Layer
- Prevent vendor leakage into Replay, Feature Store, Kernel, and Plugins.
- Standardize history/latest/stream semantics.
- Enable deterministic testing with a fake provider.

## Why Ports & Adapters
- Isolate external systems behind explicit ports.
- Enable multiple providers without changing consumer code.
- Improve replacement, mocking, and integration safety.

## Why Factory
- Centralize provider selection logic.
- Remove conditional provider branching from the rest of the framework.

## Why Registry
- Support runtime provider lifecycle and default resolution.
- Allow controlled dependency injection for different environments.

## Consequences
### Positive
- Strong decoupling and clearer architecture boundaries.
- Better testability and benchmarkability.
- Safer evolution for future vendor integrations.

### Trade-offs
- Additional abstraction to maintain.
- Need governance for protocol and model evolution.
