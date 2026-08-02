# Market Context Engine Architecture (EPIP-010)

## Purpose

Market Context is the single official immutable market snapshot for downstream Elliott, Decision,
Risk, Execution, and AI engines. It consumes official Swing, Market Structure, Liquidity, and
Fibonacci outputs without recalculating their domain results.

## Aggregation and Builder

The validator enforces one symbol/timeframe stream and aligned upstream versions. The aggregator
maps the official structure state to a market phase and combines existing structure confidence,
resting-pool confluence, and Fibonacci confluence into a deterministic bounded score. The builder
retains every input snapshot by reference and exposes current BOS, CHOCH, liquidity pools,
premium/discount, OTE, and Golden Zone views.

## Snapshots and Versioning

`MarketContextSnapshot` contains an immutable `MarketContext` and a composite version identifying
the context, structure, liquidity, and Fibonacci revisions. Versioning is isolated per symbol and
timeframe. Deterministic JSON preserves the full official upstream state.

## History and Graph

History uses copy-on-append tuples and supports latest, version, timestamp, and replay queries. The
immutable graph supplies previous/next and parent/child traversal. Each node records links to the
official upstream snapshot versions.

## Future Elliott Integration

Elliott consumes only `MarketContextSnapshot`. Parent/child graph edges are reserved for wave
hierarchy, while linked snapshot identifiers preserve evidence provenance. The context package does
not depend on Elliott, preserving a one-way architecture boundary.

## Runtime

The engine serializes stream mutations with `RLock`, publishes typed events through EventBus, uses
standard logging, and exposes immutable operational metrics. No standard output is produced.
