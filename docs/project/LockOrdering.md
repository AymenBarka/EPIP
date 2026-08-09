# Lock Ordering

## Official Hierarchy

EPIP uses a release-before-callback hierarchy:

1. acquire one component state lock;
2. compute and commit immutable state;
3. release the component state lock;
4. acquire the EventBus lock only to accept an event and snapshot listeners;
5. release the EventBus lock;
6. invoke listeners with no EPIP state or EventBus lock held.

Event publication is therefore a boundary, not a nested lock level. A component must never retain
its state lock across that boundary.

## Allowed Acquisition

- Component state lock for local mutation.
- Statistics lock while the owning component lock is held, where already required.
- EventBus lock only after all component locks have been released.
- Listener-owned locks only during callback execution.

## Forbidden Acquisition

- Engine lock followed by EventBus publication.
- EventBus lock followed by a user callback.
- Listener callback while a source engine lock is retained.
- Waiting for another publisher while holding a component lock.
- Acquiring two engine locks in opposite domain order.

Providers and external brokers remain governed by their Thread Confined or external contracts.
Programme B does not change their lifecycle synchronization.
