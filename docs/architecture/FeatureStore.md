# Feature Store Architecture (EPIP-003)

## Purpose
The Feature Store is the single source of enriched market data used by analysis layers.
It receives raw candle payloads and produces immutable feature collections.

## Position in the Flow

```mermaid
flowchart TD
    Replay --> RawCandle[Raw Candle]
    RawCandle --> FeatureStore[Feature Store]
    FeatureStore --> MarketContext[Market Context]
    MarketContext --> Kernel[Kernel]
    Kernel --> Plugins[Plugins]
    Plugins --> Evidence[Evidence]
    Evidence --> Scenario[Scenario]
    Scenario --> Decision[Decision]
```

## Main Components

```mermaid
classDiagram
    class Feature {
      +id: str
      +name: str
      +category: str
      +value: Any
      +timestamp: str
      +metadata: Mapping[str, Any]
      +quality_score: float
      +source: str
      +to_dict() dict
      +to_json() str
    }

    class FeatureSet {
      +features: tuple[Feature]
      +get(name)
      +exists(name)
      +filter(category, source, names)
      +merge(other)
      +to_dict()
      +to_json()
    }

    class BaseFeatureProvider {
      <<abstract>>
      +name: str
      +priority: int
      +provide(symbol, timeframe, timestamp, payload, feature_set)
    }

    class OHLCProvider
    class IndicatorProvider
    class StructureProvider
    class SessionProvider

    class FeaturePipeline {
      +run(symbol, timeframe, timestamp, payload, feature_set)
    }

    class FeatureStore {
      +register_provider(provider, priority)
      +unregister_provider(provider_or_name)
      +build_feature_set(symbol, timeframe, timestamp, payload)
      +invalidate_cache(symbol, timeframe, timestamp)
      +history()
      +cache_size()
      +cache_keys()
    }

    class FeatureRegistry {
      +register(name, provider, category, priority)
      +unregister(name)
      +get(name)
      +names()
      +entries()
    }

    FeatureSet "1" --> "*" Feature
    FeaturePipeline --> BaseFeatureProvider
    OHLCProvider --|> BaseFeatureProvider
    IndicatorProvider --|> BaseFeatureProvider
    StructureProvider --|> BaseFeatureProvider
    SessionProvider --|> BaseFeatureProvider
    FeatureStore --> FeaturePipeline
    FeatureStore --> FeatureSet
    FeatureRegistry --> Feature
```

## Pipeline Behavior
1. A raw candle payload enters the Feature Store.
2. The store resolves `(symbol, timeframe, timestamp)` cache key.
3. On cache miss, providers run in deterministic priority order.
4. Each provider emits features and enriches the current FeatureSet.
5. The resulting immutable FeatureSet is cached and recorded in history.

## Responsibilities
- Feature: immutable atomic enriched value.
- FeatureSet: immutable aggregate for one candle.
- FeatureStore: provider orchestration, cache, history, thread safety.
- FeatureRegistry: metadata ownership and discovery for available features.
- Providers: isolated production units; each provider only depends on input payload and current feature set.

## Dependency Boundaries
- Feature Store is independent of Kernel, Plugin implementations, Elliott/ICT/Wyckoff strategies, and data vendors.
- Providers are isolated from each other.
- Plugins consume FeatureSet output but never call providers directly.

## Thread Safety and Cache
- FeatureStore uses an `RLock` to protect provider registration, cache mutations, and history.
- Cache key: `(symbol, timeframe, timestamp)`.
- Cache invalidation supports full clear or partial key-based purge.

## Logging
- Feature Store uses standard `logging` for cache hit traces and runtime observability.
