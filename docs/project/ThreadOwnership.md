# Thread Ownership

## Ownership Models

| Ownership | Responsibility |
| --- | --- |
| Shared | The component implements its documented in-process synchronization. |
| Caller | The caller serializes mutation and controls callback interactions. |
| Thread | One thread owns the component and its mutable dependencies. |
| Run | One execution run owns the component instance and resources. |
| External system | Safety is delegated to a broker, provider, client, or adapter contract. |

Ownership propagates to mutable dependencies unless a dependency has a stronger independent
contract. Sharing a Thread Confined provider through a Thread Safe cache does not make the provider
Thread Safe.

## Transfer Rules

- Do not transfer a Thread Confined component while an operation is active.
- Transfer its provider, adapter, clock, buffers, and session state together.
- Immutable histories, graphs, and snapshots may be shared after construction.
- Caller-owned components require one serialization boundary for the complete operation.
- Callback execution does not transfer ownership automatically.

## Scope Rules

`SHARED_INSTANCE` permits the documented concurrent calls. `SERIALIZED_INSTANCE` requires one
caller-controlled operation at a time. `PER_THREAD` and `PER_RUN` require isolated instances.
`EXTERNAL_ADAPTER` means EPIP cannot strengthen the adapter's own guarantee.
