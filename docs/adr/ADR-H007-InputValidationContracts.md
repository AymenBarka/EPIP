# ADR-H007 — Input Validation Contracts

## Status

Accepted for Hardening-007 Programme C.

## Context

EPIP receives values through public APIs, integrations, configuration,
serialization, storage, and messaging. Validation expectations previously
lacked one immutable and auditable architectural representation.

## Decision

EPIP defines declarative input-validation contracts in
`epip.core.input_validation`. Each contract names a boundary, responsible
party, expected rules, capabilities, policies, and severity.

The registry and declarations are deterministic and immutable. They do not
execute validation, normalize values, reject input, or raise new exceptions.

## Consequences

- Validation ownership is explicit and reviewable.
- Missing or contradictory declarations can be detected in CI.
- Runtime behavior and public APIs remain unchanged.
- Active enforcement requires a separate, explicitly approved programme.
