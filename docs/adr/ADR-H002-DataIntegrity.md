# ADR-H002 — Data Integrity and Fail-Fast Validation

## Status

Accepted for EPIP v2 Institutional Hardening.

## Context

Immutable objects previously relied on uneven, domain-local checks. Some constructors accepted
NaN or infinity, some deserializers leaked generic `KeyError` or `TypeError`, and some models
silently clamped corrupted scores. Invalid data could therefore survive until a downstream engine.

## Decision

EPIP defines a shared integrity policy in `epip.core.integrity`. Every published snapshot validates
mandatory identity, numeric domains, versions, and cross-object relationships at construction.
Serialization entry points translate malformed input into `SerializationIntegrityError`. EventBus
validates objects exposing the `IntegrityValidatable` protocol before recording or dispatching them.

Validation is fail-fast and never changes an invalid value. Algorithmic bounding that is part of a
documented calculation remains separate from validation. Signed values such as PnL and bias retain
their business domains, while probabilities use `0..1` and percentage scores use `0..100`.

## Compatibility

Valid legacy payloads remain readable. Optional metadata keeps its historical defaults. Inputs that
were always outside the documented domain now raise a dedicated integrity exception earlier than
before; this is an intentional safety correction rather than a public API break.

## Consequences

- Invalid objects cannot enter EventBus history.
- NaN and infinity are rejected for all validated financial numbers.
- Snapshot and upstream version identifiers must be positive integers.
- Duplicate identifiers and inconsistent parent-child relationships fail explicitly.
- Consumers may catch `DataIntegrityError` or a more specific subclass.
- Every official engine validates immutable inputs and outputs through the common boundary policy.
- EventBus rejects objects that do not implement the explicit integrity contract.
- Metadata and arbitrary payloads use recursively immutable copies.
