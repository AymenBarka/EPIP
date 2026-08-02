# Fibonacci Engine Architecture (EPIP-009)

## Purpose and Dependencies

The engine is EPIP's single Fibonacci source. It depends only on Core/EventBus, Swing, Market
Structure, and Liquidity. It never recomputes pivots.

## Algorithms

The latest two confirmed swings define the measurement range. Market Structure selects bullish,
bearish, or range orientation. Configurable retracement and extension ratios produce immutable
levels. The midpoint separates premium and discount. OTE and Golden zones use configurable ratio
bands. Confluence deterministically combines structure, liquidity pools/sweeps, trend, swing quality,
and bounded distance evidence.

## Graph, History and Snapshots

Snapshots retain structure/liquidity versions. Graph nodes also link swing indices and support
previous/next and parent/child traversal for Elliott. Copy-on-append histories provide version,
timestamp, replay, and deterministic JSON serialization. Engine state is isolated per stream under
`RLock`; events cover computation, extensions, OTE, Golden Zone and confluence.

## Architecture Hardening

The additive hardening layer introduces deterministic strength and probability assessment,
Fibonacci clusters, institutional entry zones, typed TP1/TP2/TP3 and dynamic projections, and
multi-timeframe alignment across M15, H1, H4, and D1. These immutable domain objects remain
downstream of the existing engine and do not alter its calculation contract.

Every snapshot exposes a bounded probability. Dedicated serializers cover strength, clusters,
institutional zones, projections, and timeframe alignment. Metrics reserve stable dimensions for
projection accuracy, average probability, average alignment, and cluster usage so runtime
collectors can evolve without changing consumers.
