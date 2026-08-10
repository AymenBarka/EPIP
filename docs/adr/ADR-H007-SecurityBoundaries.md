# ADR-H007 — Security Boundaries and Trust Model

## Status

Accepted for Hardening-007 Programme B.

## Context

EPIP already declares component-level security contracts. Institutional review
also requires an explicit model of where trust changes, who owns each boundary,
and which capabilities cross it.

## Decision

EPIP defines immutable, deterministic boundary contracts in
`epip.core.security_boundaries`. Contracts identify zones, trust assumptions,
direction, ownership, validation responsibility, capabilities, and declarative
policies. The official registry is read-only and can be audited without
executing framework logic.

Policies are architecture metadata only. They do not authenticate, authorize,
filter, sanitize, validate, or otherwise change runtime behavior.

## Consequences

- Trust transitions are reviewable and consistently named.
- Boundary ownership and expected validation are explicit.
- Missing or contradictory declarations can be detected in CI.
- Existing public APIs and runtime behavior remain unchanged.
