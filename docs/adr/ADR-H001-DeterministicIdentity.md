# ADR-H001 — Deterministic Identity Infrastructure

## Status

Accepted for EPIP v2 Institutional Hardening.

## Context

Domain objects and events previously acquired technical metadata from the system clock,
random UUID generation, or Python object addresses. Those sources prevent reproducible
replay and make audit comparisons depend on process timing.

## Decision

EPIP exposes `ClockProtocol` and `IdGeneratorProtocol`. Production defaults remain
`SystemClock` and `SystemIdGenerator`; deterministic workflows inject
`DeterministicClock` and `DeterministicIdGenerator` into engines. Business logic must not
read the system clock, generate UUIDs, or derive identity from memory addresses.

Technical metadata (`created_at`, `uuid`, and schema version) is excluded from domain
equality. Explicit metadata supplied during deserialization is preserved unchanged.
Events obtain IDs and creation timestamps from the engine services and carry an explicit
schema version.

Provider dependencies propagate through Candle into every numeric Price identity. Kernel
dependencies propagate through plugin context and all Scenario, Hypothesis, Decision, and
event construction paths. Runtime performance measurements are normalized in deterministic
Kernel and Replay results and never define business equality.

## Consequences

- Existing constructors remain valid because the services are optional keyword arguments.
- Production behavior retains random technical identifiers by default.
- Tests and replay can reproduce byte-identical serialized output by resetting the clock
  and generator to the same initial state.
- Generator call order is part of the deterministic execution contract.

## Prohibited practices

Direct calls to `datetime.now()`, `uuid4()`, `time.time()`, random generators, and
`id(self)` are prohibited outside the identity infrastructure or explicit performance
instrumentation.
