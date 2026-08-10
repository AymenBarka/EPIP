# Recovery Model

EPIP recovery is an explicit transaction model for temporary memory and
resource ownership.

## Outcomes

- **Commit:** temporary resources become integrated into the owning operation.
- **Rollback:** registered resources are released in reverse registration
  order.
- **Abandon:** equivalent to an explicit rollback.
- **Failure:** cleanup continues for all registered resources and the aggregate
  failure is reported.

Nested scopes isolate local work. A successful nested scope transfers its live
handles to the parent. If the parent later rolls back, those handles are
released before resources registered earlier by the parent.

The model is deterministic because it uses explicit ownership, registration
order, and logical sequence numbers only.
