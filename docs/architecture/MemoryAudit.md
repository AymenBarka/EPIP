# Memory Audit

The memory audit subsystem provides deterministic, read-only observability for
H005 resources.

## Architecture

- `MemoryAuditRegistry` stores named observation probes.
- `MemoryAuditManager` coordinates snapshots, diagnostics, and reports.
- `MemoryAuditEntry` normalizes one resource observation.
- `MemorySnapshot` contains ordered observations and aggregate statistics.
- `MemoryDiagnostics` contains contract violations and leak candidates.
- `MemoryReport` combines one snapshot with its diagnostics.

Native probes observe `MemoryRecoveryManager`, `LifecycleManager`, and
`RetentionManager` through their existing public inspection APIs. Custom
components may implement `MemoryAuditAware` or register an equivalent probe.

The audit path performs no cleanup and has no authority over runtime state.
