# ADR-H006: Reliability Contracts

## Status

Accepted for Hardening-006 Programme A.

## Context

EPIP components already expose domain-specific errors and external-boundary policies, but the
framework had no uniform, machine-readable declaration of failure categories, handling policy,
recovery expectations, responsibility, or availability limitations.

## Decision

EPIP defines immutable `FailureContract` and `ReliabilityContract` declarations in
`epip.core.reliability`. `RELIABILITY_CONTRACTS` is an immutable registry that resolves contracts
by qualified name, type, or protocol-aware instance and enumerates them deterministically.

The registry is descriptive only. It does not catch exceptions, retry operations, alter rollback,
or change component runtime behaviour.

## Consequences

- Failure ownership and recovery expectations are explicit and auditable.
- Missing or contradictory declarations can be detected automatically.
- Existing exception surfaces and public constructors remain unchanged.
- Runtime enforcement remains outside Programme A.
