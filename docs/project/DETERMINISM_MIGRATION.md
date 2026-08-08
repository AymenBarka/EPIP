# Deterministic Identity Migration

Existing integrations require no changes. Constructors continue to use production system
services when no identity dependencies are supplied.

Deterministic deployments should create shared services and inject them into each engine:

```python
from epip.core import DeterministicClock, DeterministicIdGenerator

clock = DeterministicClock("2025-01-01T00:00:00Z")
ids = DeterministicIdGenerator("simulation-42")

# The same optional keywords are accepted by EPIP engines.
engine = SomeEngine(..., clock=clock, id_generator=ids)
```

Reset or recreate the generator before repeating a replay. Preserve serialized `uuid` and
`created_at` fields when loading existing records. Consumers must not use technical
metadata as business equality keys.

Legacy payloads that omit `schema_version`, `created_at`, and `uuid` remain supported and
receive backward-compatible defaults. Runtime performance metrics are normalized in
deterministic Replay; compare events, contexts, counters, and serialized snapshots rather
than wall-clock benchmark telemetry.

Custom services need only implement `now() -> str` or
`generate(namespace, *parts) -> str`. Clock values must be ISO-8601 timestamps.
