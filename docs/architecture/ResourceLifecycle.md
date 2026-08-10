# Resource Lifecycle

Hardening-005 Programme B establishes a common runtime lifecycle for resources
that require deterministic cleanup.

## Public infrastructure

- `LifecycleState` defines the official state machine.
- `ResourceLifecycle` is an immutable state snapshot.
- `ResourceHandle` guards one existing resource.
- `LifecycleManager` groups resources under one stable owner.
- `AutoCloseableResource` supports structural `close()` discovery.
- `MemoryLifecycleAware` exposes lifecycle and cleanup capabilities.
- `ResourceOwner` defines owner-level cleanup.
- `ResourceAudit` reports misuse and potential retention.

## Integration model

The infrastructure is additive. Providers, adapters, sessions, caches, and
external handles may be wrapped without inheritance and without changing their
current public constructors. `resource_managed_components()` connects the
runtime boundary to the official Programme A memory classification.

## Guarantees

- deterministic state transitions;
- idempotent close;
- coherent failure state after cleanup errors;
- context-managed cleanup, including exceptional exits;
- explicit ownership transfer;
- immutable lifecycle and audit snapshots;
- stable cleanup order inside a manager.
