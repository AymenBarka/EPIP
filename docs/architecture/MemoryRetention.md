# Memory Retention

`epip.core.retention` provides the institutional retention model.

- `RetentionPolicy` defines Unbounded, Fixed Size, Ring Buffer, LRU, FIFO,
  Time Window, Manual, and Disabled policies.
- `MemoryRetentionContract` records limits, cleanup, snapshots, compaction,
  determinism, and serialization impact.
- `MemoryRetentionRegistry` provides immutable declarations and automated
  coverage audit.
- `RetentionManager` implements deterministic, thread-safe runtime retention.
- `RetentionAware` supports structural contract discovery.

All snapshots preserve deterministic ordering. Time-window decisions require
an explicit caller-provided timestamp, keeping replay reproducible.
