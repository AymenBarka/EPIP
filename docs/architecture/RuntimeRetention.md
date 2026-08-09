# Runtime Retention

`RuntimeRetentionAdapter` is a transparent component facade backed by a typed
`RetentionManager`. Existing methods are delegated to the unchanged component;
managed retained values use the effective H005 policy.

`RUNTIME_RETENTION_ADOPTIONS` covers EventBus history, Replay structures,
FeatureStore, DataSourceCache, histories, graphs, statistics collectors, and
all other components selected by the Programme C registry.

The registry audit detects missing migrations, missing policies, and incoherent
contract bindings. Adoption snapshots and eviction depend only on logical
ordering, explicit timestamps, and configuration.
