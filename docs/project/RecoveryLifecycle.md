# Recovery Lifecycle

The official checkpoints are:

1. `BEGIN` — open a recovery scope.
2. `ALLOCATE` — create a temporary resource.
3. `REGISTER` — bind the resource to cleanup responsibility.
4. `COMMIT` — integrate the scope successfully.
5. `ROLLBACK` — begin deterministic recovery.
6. `RECOVER` — complete a cleanup callback successfully.
7. `RELEASE` — release recovery ownership.

Each trace record carries a monotonically increasing logical sequence. No
timestamp or runtime identity participates in ordering.

Scopes must close in LIFO order. Closing an outer scope while a nested scope is
still open is rejected with `RecoveryStateError`.
