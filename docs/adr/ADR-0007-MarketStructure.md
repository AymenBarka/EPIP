# ADR-0007 - Market Structure Engine as Single Structure Source

## Status
Accepted

## Context
EPIP has validated Core Domain, Event Bus, Feature Store, Market Data, Replay, and Swing layers.
A dedicated Market Structure layer is required to avoid duplicated BOS/CHOCH/trend logic in downstream engines.

## Decision
Introduce EPIP-007 Market Structure Engine as the single official source of trend, BOS, CHOCH, and range state.

## Key Decisions
- Input contract is `SwingSequence` only.
- No dependency allowed on Replay, MarketData, FeatureStore, or external providers.
- Deterministic analyzer with explicit detectors:
  - TrendDetector
  - BOSDetector
  - CHOCHDetector
  - RangeDetector
- All detectors implement `StructureDetectorProtocol` for consistent pluggability.
- Event publication for all structure transitions.
- Event payloads include immutable metadata (`event_id`, `engine_version`, `source`).
- Thread-safe implementation using RLock.
- State transitions are enforced by `StructureStateMachine` with guarded illegal transitions.
- Structure output includes deterministic `confidence` and tiered `quality` classification.
- Statistics include false/invalid/duplicate counters and detection timings.
- Backward compatibility is preserved through additive fields and state aliases.

## Rationale
- Prevents structural inconsistency between advanced engines.
- Keeps dependency direction clean and composable.
- Simplifies testing and governance of market structure logic.

## Consequences
### Positive
- One canonical structure truth for all consumers.
- Easier auditability and reproducibility.
- Strong extension points for future algorithms.
- Transition safety prevents inconsistent regime jumps.
- Improved observability for production support and diagnostics.
- Forward-compatible contract for EPIP-008 liquidity logic.

### Trade-offs

## Finalization Decisions

### Immutable graph overlay

Structure relationships are represented by a separate immutable `StructureGraph`. Existing domain
objects are consumed by reference and remain unchanged. Directed chronological and parent/child
edges support future Elliott traversal without coupling the structure detector to wave logic.

### Persistent immutable history

History uses copy-on-append value semantics. Versions are sequential per symbol/timeframe and
timestamps are chronological. This favors safe replay, deterministic backtesting, and consumer
isolation over in-place mutation.

### Deterministic serialization

All public structure-domain aggregates use explicit schema-aware serialization rather than generic
pickle or implicit dataclass encoding. Sorted compact JSON makes payloads reproducible and suitable
for snapshots, caches, audit logs, and regression fixtures.

### Additive metadata and versioning

Metadata fields are appended with compatible defaults. Structures use deterministic UUIDv5 identity
because the Python 3.13 standard library does not expose UUIDv7. Snapshot versions advance per
stream; the original `version` API is retained and exposed through `structure_version` as well.

### Observer alongside EventBus

Observers receive committed immutable snapshots through an optional thread-safe registry. EventBus
events and their publication ordering are not changed. This separates state projection consumers
from domain-event consumers and enables persistence, UI, and live-trading adapters.

### Contextual domain errors

The exception hierarchy is extended beneath `MarketStructureError`. Every error accepts immutable
context metadata so infrastructure layers can report failures without parsing messages.

### Compatibility policy

EPIP-007 finalization is additive: algorithms, detectors, event contracts, and existing public
constructors are unchanged. New constructor parameters are optional, and new dataclass fields have
defaults. Future modules must depend on snapshots, graph/history contracts, or protocols rather than
detector internals.
- Additional abstraction layers and state management.
- Requires disciplined consumption by downstream teams.
