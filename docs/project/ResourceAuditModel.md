# Resource Audit Model

## Observation flow

1. Register a probe under a stable component name.
2. Read the component's public immutable audit or snapshot.
3. Normalize the result into `MemoryAuditEntry`.
4. Sort entries by component and resource.
5. Aggregate deterministic `MemoryStatistics`.
6. Evaluate explicit H005 invariants.
7. Return an immutable `MemoryReport`.

Snapshots accept an explicit logical sequence. Comparison uses retained-object
counts from an explicitly supplied previous snapshot. This preserves replay and
identity determinism while avoiding hidden time sources.
