# ADR-H007 — Security Audit and Observability

## Status

Accepted.

## Context

H007 defines security contracts, trust boundaries, input-validation declarations,
runtime policies, and secure-failure handling. Institutional review requires one
deterministic view of those declarations without introducing enforcement or
changing runtime behaviour.

## Decision

EPIP provides a read-only security-audit projection in
`epip.core.security_audit`. Audit entries reference existing registries by stable
name. Snapshots, diagnostics, metrics, history, and reports are immutable and
ordered deterministically. Observations are supplied explicitly with logical
time and stable identity; the audit layer never reads clocks, generates IDs, or
invokes an observed component.

The audit manager reports missing declarations, incoherent adoption, unknown
classifications, incompatible policies, and contradictory observations. It does
not block, authorize, validate, retry, recover, or mutate runtime state.

## Consequences

- H001 determinism and H002 integrity remain preserved.
- H003 financial calculations and H004/H005/H006 runtime guarantees are unchanged.
- Existing APIs and serialization formats remain unchanged.
- Applications may adopt the observability API without enabling runtime security.
