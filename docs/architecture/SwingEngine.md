# Swing Engine Architecture (EPIP-006)

## Purpose

Swing Engine is the unique official source of pivots and swing classifications in EPIP.
All downstream modules (Market Structure, Liquidity, Elliott, ICT/SMC/Wyckoff/Fibonacci layers) must consume swings from this engine and must never recalculate pivots independently.

## Architecture

```mermaid
flowchart TD
    Replay[Replay Engine] --> MarketData[MarketData Layer]
    MarketData --> FeatureStore[Feature Store]
    FeatureStore --> SwingEngine[Swing Engine]
    SwingEngine --> MarketStructure[Market Structure]
    MarketStructure --> Liquidity[Liquidity]
    Liquidity --> Elliott[Elliott]
    Elliott --> Decision[Decision Engine]
```

## Component Diagram

```mermaid
classDiagram
    class SwingEngine {
      +process_candle(candle) tuple[Swing]
      +run(candles) SwingMetrics
      +sequence(symbol, timeframe) tuple[Swing]
    }

    class SwingDetector {
      +process(candle) tuple[Swing]
      +sequence(symbol, timeframe) SwingSequence
    }

    class PivotWindowStrategy {
      +on_candle(candle) tuple[SwingPoint]
    }

    class CompositeSwingFilter {
      +allow(candidate, sequence, config) bool
    }

    class SwingStatisticsCollector {
      +record_swing(...)
      +snapshot_metrics() SwingMetrics
    }

    SwingEngine --> SwingDetector
    SwingDetector --> PivotWindowStrategy
    SwingDetector --> CompositeSwingFilter
    SwingEngine --> SwingStatisticsCollector
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Replay
    participant SwingEngine
    participant SwingDetector
    participant Strategy as PivotWindowStrategy
    participant Filters
    participant EventBus

    Replay->>SwingEngine: process_candle(candle)
    SwingEngine->>SwingDetector: process(candle)
    SwingDetector->>Strategy: on_candle(candle)
    Strategy-->>SwingDetector: pivot candidates
    SwingDetector->>Filters: allow(candidate)
    Filters-->>SwingDetector: accepted/rejected
    SwingDetector-->>SwingEngine: swings
    SwingEngine->>EventBus: SwingDetected
    SwingEngine->>EventBus: SwingUpdated (optional)
    SwingEngine->>EventBus: SwingConfirmed
```

## Strategy Pattern

- Implemented: PivotWindowStrategy (official EPIP-006 baseline).
- Declared interfaces/placeholders: FractalStrategy, ATRAdaptiveStrategy, ZigZagStrategy, HybridStrategy.
- Rationale: maintain deterministic baseline while opening a controlled extension path.

## Algorithms

### PivotWindowStrategy

- Maintain a rolling buffer.
- Confirm pivot only after right_bars candles are available.
- Swing High: center high is maximum of local window.
- Swing Low: center low is minimum of local window.

### Classification

- High pivots: Swing High, Higher High, Lower High, Equal High.
- Low pivots: Swing Low, Higher Low, Lower Low, Equal Low.
- Scope: Internal/External by distance regime.

## Filters (Composable)

- Distance Filter
- ATR Filter
- Noise Filter
- Duplicate Filter
- Trend Filter
- Minimum Move Filter

All filters are combined by CompositeSwingFilter with logical AND.

## Streaming and Memory

- Streaming-only processing.
- No full candle history materialization.
- Per-stream rolling windows only.
- Designed for very large runs (1M/5M/10M candles) without OOM.

## Thread Safety

- SwingEngine, SwingDetector and SwingStatisticsCollector are protected by RLock.
- Public read/write operations are deterministic under concurrent access.

## Logging

- Uses logging module only.
- No print() in runtime path.
