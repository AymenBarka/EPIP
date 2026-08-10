# Reliability Audit

The reliability audit is a read-only projection over Hardening-006 contracts.
`ReliabilityAuditRegistry` declares the contract references required for each
audited component. `ReliabilityAuditManager` validates those references and
builds deterministic snapshots, diagnostics, metrics, and reports.

## Boundary

The manager accepts observations and immutable snapshots supplied by callers.
It never calls a runtime method, triggers a retry, changes a circuit breaker,
selects a fallback, or initiates recovery. Consequently, audit execution cannot
alter production state.

## Model

- `ReliabilitySnapshot` is the immutable observed state at a logical time.
- `ReliabilityAuditSnapshot` contains violations and diagnostics.
- `ReliabilityReport` is comparable and canonically serializable to JSON.
- `ReliabilityHistory` holds immutable snapshots without hidden retention.
- `FailureMetric` contains descriptive counters with sorted dimensions.

Contract references cover reliability, exception, retry, circuit-breaker, and
fallback registries. Boundary and policy relationships are checked explicitly.
