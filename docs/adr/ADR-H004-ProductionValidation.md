# ADR-H004 — Production Validation

## Status

Accepted.

## Decision

Hardening-004 is validated through reproducible CI campaigns plus explicitly recorded heavy-load
campaigns. Thread progress is measured without claiming operating-system scheduler fairness.
Intentional histories are cleared before leak assertions; retained history is capacity management,
not an allocation leak.

## Consequences

CI covers 1 through 256 publishers and a 100,000-event longevity run. The existing dedicated stress
campaign covers 640,000 concurrent events. Million-event campaigns remain release validations rather
than mandatory checks on every pull request.
