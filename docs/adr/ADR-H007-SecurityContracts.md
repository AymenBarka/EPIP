# ADR-H007 — Security Contracts

## Status

Accepted for Hardening-007 Programme A.

## Context

EPIP needs explicit security assumptions before active controls can be designed.
Previously, trust, ownership, boundaries, and capabilities were implicit.

## Decision

EPIP adopts immutable, deterministic, declarative security contracts in
`epip.core.security`. Contracts classify components, identify trust assumptions,
assign responsibilities, list crossed boundaries and enumerate capabilities.

The registry is read-only. Diagnostics detect incomplete or contradictory
declarations. Resolution accepts qualified names, component types, and objects
implementing `SecurityAware`.

## Consequences

- Security metadata becomes reviewable and testable.
- No authentication, authorization, encryption, or access control is activated.
- Existing runtime behavior and public component APIs remain unchanged.
- Future active controls must be specified by a separate architectural decision.
