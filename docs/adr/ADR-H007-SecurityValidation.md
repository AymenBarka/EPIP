# ADR-H007 — Security Validation

## Status

Accepted.

## Decision

H007 security controls are accepted only after deterministic stress, fault-injection,
memory-retention, and performance campaigns execute against the public security
contracts. Validation remains outside the runtime and cannot alter policy decisions.

## Consequences

The campaign is reproducible, read-only, and additive. Failures identify an invalid
contract or integration; they do not silently repair production state.
