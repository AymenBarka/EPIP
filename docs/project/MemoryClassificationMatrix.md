# Memory Classification Matrix

This matrix summarizes the official component-family policies. The
machine-readable source of truth is `MEMORY_CONTRACTS`.

| Component family | Primary classification | Ownership | Lifecycle | Growth |
| --- | --- | --- | --- | --- |
| Kernel and Registry | Memory Owned | Component | Instance | Input bounded |
| EventBus | Memory Owned, Persistent | Component | Instance | History dependent |
| Replay components | Memory Owned | Component | Run | Input bounded |
| FeatureStore | Memory Owned | Component | Instance | Input bounded |
| DataSourceCache | Memory Owned, Shared, Cached | Component | Instance | Cache dependent |
| Stateless feature providers | Memory Stateless, Ephemeral | Caller | Call | Constant |
| CSV and remote providers | Resource Managed, External | External system | External | External |
| Financial engines | Memory Owned | Component | Instance | Input bounded |
| Histories | Memory Owned, Persistent | Component | Instance | History dependent |
| Graphs | Memory Owned, Ephemeral | Caller | Instance | Input bounded |
| Statistics collectors | Memory Owned | Component | Instance | Input bounded |
| Context values | Memory Owned, Ephemeral | Caller | Instance | Input bounded |
| System identity services | Memory Stateless, Ephemeral | Caller | Call | Constant |
| Deterministic identity services | Memory Owned | Component | Instance | Input bounded |
| Paper adapter | Memory Owned | Component | Instance | Input bounded |
| Broker adapters | Resource Managed, External | External system | External | External |

## Explicit retention

Histories and EventBus history are classified as history-dependent and
unbounded because Programme A must describe current behaviour. DataSourceCache
is cache-dependent and unbounded for the same reason. No retention policy is
changed by this classification.
