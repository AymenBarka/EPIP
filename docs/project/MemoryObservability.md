# Memory Observability

## Metrics

Every snapshot provides deterministic counts for:

- active and closed resources;
- handles and recovery scopes;
- resources grouped by owner, lifecycle, and policy;
- cleanup, rollback, and eviction operations;
- retained and recovered objects;
- logical growth relative to an explicit previous snapshot.

Groups and entries are sorted by stable textual identity. No metric uses wall
clock time, object addresses, dictionary insertion order, garbage-collector
state, sampling, or probabilistic statistics.
