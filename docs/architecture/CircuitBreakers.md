# Circuit Breakers

The EPIP circuit breaker is an optional state machine for containing repeated
failures. A `CircuitBreakerContract` combines an isolation boundary,
configuration, retry contract, failure contract, and exception contract.

The runtime supports `CLOSED`, `OPEN`, `HALF_OPEN`, `FORCED_OPEN`, and
`DISABLED`. Invalid transitions are rejected. The transition from `OPEN` to
`HALF_OPEN` is based on monotonic logical time supplied by the caller.

All externally visible diagnostic data is returned through immutable snapshots.
The implementation neither invokes business operations nor changes business
models.
