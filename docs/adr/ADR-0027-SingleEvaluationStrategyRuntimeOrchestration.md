# ADR-0027: Single-Evaluation Strategy Runtime Orchestration

- **Status:** Accepted
- **Milestone:** P03 governance authorization
- **Decision scope:** Generic Shared Strategy Runtime orchestration only

## Context

ADR-0016 assigns profile selection, adapter invocation, frozen A07 E00-E09 orchestration, envelope
construction, and runtime diagnostics to P03. ADR-0017 already supplies immutable request, result,
state, diagnostic, and envelope contracts. P02 supplies one configured adapter result. The
remaining decision is whether P03 adds bindings/states, repeated selection, or runtime lifecycle.

## Decision

One P03 invocation performs one synchronous deterministic evaluation. It reuses all P01 data
contracts; its only new public contract is behavioral `StrategyRuntimeProtocol`. Invalid
runtime-owned structure causes zero adapter calls. Otherwise P03 invokes one explicitly injected,
exact-identity adapter exactly once. It never retries, falls back, discovers plugins, polls,
schedules, or reads ambient time.

A terminal adapter outcome maps once to the existing runtime state. Accepted facts traverse frozen
A07 E00-E09 once in order; only accepted E09 output receives the existing signal envelope. Exact
semantic rules remain encapsulated by the configured P02 adapter/binding. The profile resolves by
exact identity. P03 creates no semantic closure, independent state machine, binding record, or
identity model.

Unexpected exceptions become deterministic sanitized failures. The runtime is pure, stateless,
and concurrent for independent calls subject to dependency contracts. Idempotence means equal
results for identical immutable inputs, not caching.

## Consequences

P03 remains minimal and preserves P01/P02/A07 ownership. Existing serialization and compliance
records suffice; P03-F00 preserves compliance inventory 606. Concrete Elliott/Fibonacci and MTF
semantics remain P04/P05. Backtest, scheduling, paper/live, broker, persistence, and monitoring
remain downstream.
