# Market Data Layer Architecture (EPIP-004)

## Purpose

The Market Data Layer is the single ingress point for market data across EPIP.
No downstream module should directly use CSV, TwelveData, MT5, or any external vendor SDK.

## Layer Position

```mermaid
flowchart TD
    Replay[Replay] --> MD[Market Data Layer]
    MD --> FS[Feature Store]
    FS --> MC[Market Context]
    MC --> K[Kernel]
    K --> P[Plugins]
```

## Ports & Adapters

```mermaid
classDiagram
    class DataSourceProtocol {
      <<port>>
      +connect()
      +disconnect()
      +health()
      +available_symbols()
      +available_timeframes()
      +history(request)
      +latest(symbol,timeframe)
      +stream(symbol,timeframe)
    }

    class DataSourceFactory
    class DataSourceRegistry
    class DataSourceCache
    class CSVProvider
    class FakeProvider
    class TwelveDataProvider
    class MT5Provider
    class TwelveDataAdapter
    class MT5Adapter

    DataSourceFactory --> DataSourceProtocol
    DataSourceRegistry --> DataSourceProtocol
    CSVProvider ..|> DataSourceProtocol
    FakeProvider ..|> DataSourceProtocol
    TwelveDataProvider ..|> DataSourceProtocol
    MT5Provider ..|> DataSourceProtocol
    TwelveDataProvider --> TwelveDataAdapter
    MT5Provider --> MT5Adapter
    CSVProvider --> DataSourceCache
    FakeProvider --> DataSourceCache
```

## Sequence (History Request)

```mermaid
sequenceDiagram
    participant Consumer
    participant Protocol as DataSourceProtocol
    participant Provider
    participant Cache

    Consumer->>Protocol: history(request)
    Protocol->>Provider: history(request)
    Provider->>Cache: get_history(request)
    alt cache hit
        Cache-->>Provider: HistoryResponse(from_cache=true)
    else cache miss
        Provider->>Provider: fetch/compute candles
        Provider->>Cache: set_history(request,response)
        Cache-->>Provider: stored
    end
    Provider-->>Protocol: HistoryResponse
    Protocol-->>Consumer: HistoryResponse
```

## Responsibilities

- DataSourceProtocol: stable ingress contract.
- DataSourceFactory: centralized provider construction from config.
- DataSourceRegistry: runtime provider registration and default resolution.
- DataSourceCache: thread-safe LRU + TTL for history/latest.
- Providers:
  - CSV: complete parsing and pagination.
  - Fake: deterministic test/benchmark provider.
  - TwelveData: adapter-based interface-only provider.
  - MT5: adapter-based architecture-only provider.

## Thread Safety

- Provider lifecycle and cache access are guarded by `RLock`.
- Cache structures are protected and mutated under lock.
- Registry operations are lock-protected.

## Dependency Rules

- Replay, Feature Store, Context, Kernel, and Plugins must depend on `DataSourceProtocol` only.
- Provider-specific concerns remain encapsulated behind this layer.
