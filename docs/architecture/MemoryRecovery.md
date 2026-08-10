# Memory Recovery

The memory recovery boundary protects temporary allocations created during an
operation that may commit or roll back.

## Components

- `MemoryRecoveryManager` owns scopes, trace records, and audits.
- `RecoveryScope` represents one transactional cleanup boundary.
- `RecoveryHandle` binds a resource to its cleanup callback.
- `RecoveryAudit` reports incomplete cleanup and cleanup failures.
- `MemoryRecoveryAware` is the additive inspection protocol.

## Invariants

1. A resource is registered before it can participate in recovery.
2. Rollback attempts every cleanup callback in strict LIFO order.
3. Cleanup is idempotent at the handle boundary.
4. Nested commit transfers responsibility to the parent scope.
5. Top-level commit marks resources integrated.
6. Scope closure follows strict LIFO order.
7. Trace ordering is based only on a monotonic logical sequence.

No existing engine is forced to adopt the boundary, and no existing public API
or serialization format is changed.
