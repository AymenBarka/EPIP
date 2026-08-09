# Cleanup Guarantees

## Guaranteed

- Explicit cleanup on rollback, abandonment, `Exception`, and `BaseException`.
- Strict reverse-registration cleanup order.
- Continued cleanup attempts after an individual callback failure.
- Idempotent repeated recovery requests at the handle boundary.
- Deterministic immutable traces and audits.
- Detection of open scopes, unrecovered resources, repeated cleanup attempts,
  and cleanup failures.

## Not delegated to the runtime

Correctness never depends on:

- garbage collection timing;
- object finalizers;
- system time;
- object addresses;
- dictionary iteration order;
- background cleanup threads.

Cleanup callbacks remain responsible for safely releasing the resource they
own. A callback failure is surfaced as `RecoveryCleanupError` after all other
callbacks have been attempted.
