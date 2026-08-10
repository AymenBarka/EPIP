# Security Observability

Applications submit immutable `SecurityObservation` values with explicit logical
time, stable identity, component, classification, adoption state, and optional
policy. EPIP never samples runtime state implicitly.

Supported observation kinds are decisions, violations, incidents, and adoption.
This model preserves deterministic replay because the same declarations and
observations always produce the same snapshot and canonical report.
