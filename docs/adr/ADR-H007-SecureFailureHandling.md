# ADR-H007 — Secure Failure Handling

## Status

Accepted for Programme E.

## Context

EPIP needs a common vocabulary for security-relevant failures without changing
the exception behaviour of existing engines or infrastructure.

## Decision

Introduce immutable secure-failure contracts, incident classifications,
containment boundaries, policies, deterministic decisions, diagnostics, and an
inert official registry. Adoption is explicit. The infrastructure performs no
exception interception, recovery, retry, suppression, or propagation.

## Consequences

Applications can audit and resolve declared policies consistently. Existing
runtime behaviour, financial calculations, serialization, and APIs remain
unchanged.
