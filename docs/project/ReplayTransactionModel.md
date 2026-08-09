# Replay Transaction Model

`BEGIN SESSION → VALIDATION → PREPARE → EXECUTION → BUILD → COMMIT → EVENTS → RETURN`

The transaction acquires existing locks in this order:

1. ReplaySession;
2. ReplayClock;
3. ReplayScheduler;
4. ReplayStatistics;
5. FeatureStore.

All Replay operations use reentrant locks, so internal calls retain their
existing behavior. Locks are released in reverse order.
