# Determinism and Identity

EPIP separates business identity from technical metadata. Business fields determine
equality; timestamps, schema versions, and opaque persistence identifiers do not.

`ClockProtocol` supplies technical timestamps and `IdGeneratorProtocol` supplies opaque
identifiers. Every engine accepts optional implementations. The system implementations
preserve v1 behavior, while deterministic implementations provide controlled replay and
test execution.

For reproducible processing, construct one deterministic clock and one deterministic ID
generator per execution boundary, inject both into all engines, and retain the same engine
ordering. Serialized domain objects preserve their original identity during round trips.

The deterministic generator is thread-safe. Its sequence is stable for the same seed,
namespace, business parts, and call order. The deterministic clock only changes through
explicit `set` or `advance` operations.

## Equality rules

- Candle equality uses market timestamp, symbol, timeframe, OHLCV values.
- Evidence equality uses its business fields; free-form metadata and identity metadata are
  excluded.
- Core Market Context equality uses the market state; metadata, plugin caches, indicators,
  plugin outputs, creation time, UUID, and schema version are excluded.
- Plugin execution time, registries, event buses, and runtime metadata are never business
  identity.
- Market timestamps remain business fields when they identify an observation. Technical
  creation timestamps (`created_at`) never participate in equality.

## Performance measurements

Wall-clock measurements are operational telemetry, not deterministic domain output.
Deterministic Kernel execution normalizes plugin execution durations to zero. Deterministic
Replay normalizes elapsed time, throughput, latency, and peak-memory metrics to zero while
preserving deterministic counters. Other engine performance metrics remain explicitly
outside snapshot and event serialization.
