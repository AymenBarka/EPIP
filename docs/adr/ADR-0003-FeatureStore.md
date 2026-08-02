# ADR-0003 - Feature Store As Single Enriched Data Source

## Status
Accepted

## Context
EPIP-001 introduced immutable core domain models.
EPIP-002 introduced Event Bus + Registry + Kernel orchestration.
Without a dedicated Feature Store, analysis plugins risk recalculating indicators and structural signals independently, causing:
- duplicated compute,
- inconsistent feature definitions,
- weak reproducibility in replay,
- tighter coupling between analysis code and raw candle handling.

## Decision
Adopt EPIP-003 Feature Store as the unique enriched-data provider.
All future analysis modules (Elliott, ICT, Wyckoff, AI, and others) must consume FeatureSet outputs from Feature Store.

Key decisions:
- Immutable `Feature` and `FeatureSet` are the feature contracts.
- Provider pipeline enriches data in deterministic order.
- Feature Store remains independent from Kernel and plugin internals.
- In-memory cache keyed by `(symbol, timeframe, timestamp)`.
- Thread-safe store operations using lock protection.

## Alternatives Considered
1. Plugin-local feature computation
   - Pros: simpler in each plugin.
   - Cons: duplicated logic, inconsistent outputs, difficult governance.

2. Kernel-managed indicator engine
   - Pros: central place in runtime flow.
   - Cons: kernel becomes domain-heavy and loses orchestration focus.

3. External feature microservice (deferred)
   - Pros: scalability and language-agnostic access.
   - Cons: operational complexity too high for current phase.

## Consequences
### Positive
- Single source of truth for enriched market data.
- Deterministic replay and better auditability.
- Clear separation of concerns across EPIP layers.
- Easier benchmarking and targeted optimization.

### Negative
- Initial integration overhead for migrating consumers to FeatureSet.
- Feature metadata and provider lifecycle require governance.

## Compliance Rules
- No provider may depend on another provider implementation.
- Kernel does not know provider internals.
- Plugins do not call providers directly.
- Feature Store does not depend on plugin implementations.

## Follow-up
- Add concrete indicator providers (RSI/EMA etc.) incrementally.
- Define feature naming governance and quality thresholds.
- Evaluate optional persisted cache if replay scale increases.
