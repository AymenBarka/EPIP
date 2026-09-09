# P03 Governance Authorization

## Decision

P03 governance is **AUTHORIZED**. This document freezes the Shared Strategy Runtime boundary before
production implementation. Only P03-F00 below is implementation-authorized. P04, P05, releases,
tags, and deployment work remain unauthorized.

## Objective and scope

P03 owns one pure, synchronous, deterministic strategy evaluation. It accepts the existing P01
`StrategyRuntimeRequest`, resolves explicitly injected profile and adapter dependencies, invokes
the configured `FactAdapterProtocol` at most once, executes frozen A07 E00-E09 after an accepted
fact bundle, and returns the existing P01 `StrategyRuntimeResult`.

```text
StrategyRuntimeRequest
-> P03 runtime coherence checks
-> exact profile and adapter checks
-> FactAdapterProtocol.adapt(...) exactly once
-> terminal adapter mapping, or frozen A07 E00-E09 orchestration
-> StrategySignalEnvelope only for an accepted signal
-> StrategyRuntimeResult
```

There are no hidden loops, retries, fallbacks, polling, scheduling, background tasks, or ambient
clocks.

## Responsibilities

P03 owns:

- a `StrategyRuntimeProtocol` invocation boundary and canonical implementation;
- request-level contract, profile, adapter, strategy, evaluation, input, policy, and provenance
  continuity checks not already guaranteed by P01 construction;
- runtime-level cross-input temporal alignment against the explicit evaluation context, without
  recomputing P02 evidence freshness, temporal validity, or revision eligibility;
- exact profile resolution through the existing exact-identity registry contract;
- injection of one `FactAdapterProtocol` and exact adapter-identity validation;
- the zero-or-one adapter invocation invariant and deterministic sequencing;
- terminal adapter-result translation into the existing runtime state model;
- frozen A07 E00-E09 orchestration without changing its semantics;
- the existing `StrategySignalEnvelope` for accepted signals only;
- P03-stage diagnostics and sanitized containment of unexpected implementation exceptions; and
- identity/provenance preservation and stateless concurrent invocation.

Evidence-set continuity at this layer is specifically an accepted-bundle-to-A07 preservation
responsibility. P02 first makes the ordered evidence-set identity authoritative in
`StrategyFactBundle`; P03 copies that exact value and ordered tuple into A07 without comparing it
to an absent pre-adaptation request value or recomputing it.

P03 consumes the explicit `EvaluationContext`; it does not create evaluation time.

## Non-responsibilities

P03 does not own source/frame resolution, exact semantic closure, candidate validation, direction,
entry, stop, target, confidence cardinality, evidence freshness, temporal validity, revision
eligibility, evidence ordering or identity derivation, or A07 fact construction. These remain
frozen P02, P01, temporal, or A07 responsibilities.

It does not own concrete Elliott, Fibonacci, indicator, or MTF rules; profile synthesis; portfolio
allocation; risk sizing; execution; broker or MT5 integration; persistence; network/filesystem
discovery; retry; live clocks/scheduling; backtest, replay, or walk-forward loops; paper trading;
order/fill/position lifecycle; slippage; or downstream monitoring and observability.

## Public contracts

P01 already supplies the immutable data surface: `StrategyRuntimeRequest`,
`StrategyRuntimeResult`, `StrategyRuntimeState`, `StrategyRuntimeDiagnostics`,
`RuntimeDiagnostic`, `StrategyRuntimeOptions`, `EvaluationContext`, and
`StrategySignalEnvelope`. P03 reuses them unchanged. It must not add a runtime request, result,
binding, identity, diagnostics, or state duplicate.

The only justified new public contract is behavioral:

```python
class StrategyRuntimeProtocol(Protocol):
    def evaluate(self, request: StrategyRuntimeRequest) -> StrategyRuntimeResult: ...
```

The implementation must confirm the package's additive export convention before exposing it.

## Result and state model

P03 returns the existing runtime result rather than exposing `FactAdapterResult`, because P03 owns
post-adapter A07 outcomes and signal metadata. No second state machine is introduced.

| Origin | Existing runtime state | Envelope |
| --- | --- | --- |
| Adapter `REJECTED` | `REJECTED` | none |
| Adapter `INVALID_INPUT` | `INVALID_INPUT` | none |
| Adapter `FAILED` or unexpected adapter exception | `ADAPTER_FAILURE` | none |
| Accepted facts, non-actionable A07 completion | `NO_SIGNAL` | none |
| A07 validation/contract rejection | `A07_REJECTION` | none |
| Accepted A07 E09 signal | `ACCEPTED_SIGNAL` | exactly one |
| P03 request/coherence failure | `INVALID_INPUT` | none |

Adapter acceptance alone is not runtime success. Only accepted E09 completion yields a signal.

## Validation and zero-invocation failures

P01 constructors remain the first structural boundary. P03 additionally checks exact request type
and version, coherent request identity, exact profile resolution, injected adapter identity, and
the strategy, policy, evaluation, analytical-bundle, source-set, and provenance continuity needed
by orchestration.

A malformed/forged request, unsupported runtime contract, missing/mismatched dependency, profile
or adapter mismatch, or visible strategy/evaluation mismatch produces `INVALID_INPUT` with zero
adapter calls. P03 must not pre-run P02 source, candidate, closure, freshness, or mapping checks.
Those inputs reach P02 once and P02's governed result is preserved.

## Adapter, profile, and rule handoff

The runtime receives one adapter by explicit constructor/configuration injection and validates its
exact identity. Profile lookup is allowed only through the existing exact-identity
`StrategyProfileRegistryProtocol`. Latest, compatible, reflection, environment, filesystem, and
fallback selection are forbidden. P03 never synthesizes a profile.

The configured P02 adapter already contains the exact resolved semantic rules and invocation
binding. P03 therefore accepts no parallel rule-set input and never discovers, rebuilds, or
revalidates semantic closure. For a valid request it invokes
`adapt(context, inputs, profile, policy)` exactly once; for invalid runtime structure, zero times.

## A07 orchestration

After adapter acceptance, P03 consumes the complete `StrategyFactBundle` and constructs the
predecessor chain required by frozen A07 E00-E09 in public stage order. It does not bypass stages,
reinterpret acceptance, repair facts, calculate alternate geometry, or mutate policy. It stops at
the first terminal nonaccepted outcome.

## Determinism, purity, and idempotence

Identical immutable request, adapter, exact profile, resolved-rule configuration, analytical
input, policy, and context produce value-equal results and identities. P03 uses no wall clock,
randomness, UUIDs, environment, filesystem, network, mutable globals, process state, or
nondeterministic iteration. Logical idempotence is result equivalence, not caching.

The runtime is pure and synchronous. It performs no I/O and owns no shared mutable state.

## Fail-fast, diagnostics, and exceptions

Every terminal outcome stops later work. P03 adds diagnostics only for P03-owned request,
coherence, profile, adapter-boundary, A07-stage, and result events using existing P01 codes and
stages. Adapter diagnostics are preserved unchanged and not duplicated.

Unexpected adapter exceptions become deterministic sanitized `ADAPTER_FAILURE`; unexpected
failures after accepted adaptation become `A07_REJECTION`. Diagnostics may contain governed stage
and stable subject identities, but not raw exception text, tracebacks, paths, secrets, or
process-dependent details. P03 contract-construction defects remain test-visible bugs rather than
being hidden behind fabricated contracts.

## Provenance

P03 reuses identities. Request/result IDs bind input/output; `EvaluationContext` binds evaluation,
run, source set, instrument, and profile; adapter/profile identities, fact provenance, and the
signal envelope preserve the rest. An accepted envelope must reference the same evaluation,
instrument, profile, adapter, provenance, runtime, source set, fact bundle, and signal produced by
the invocation.

## Thread safety and stress

A stateless runtime with immutable dependencies supports concurrent independent calls when those
dependencies honor their contracts. P03 adds no locks. Tests must compare serial/concurrent
results, per-call counts, and cross-request isolation. EventBus-scale stress is not justified for
a bounded no-queue call; focused repeated and concurrent determinism testing is sufficient.

## Serialization, identity, and compliance

No serialization extension is authorized: P01 request/result/envelope contracts already have
canonical tagged serialization; a protocol/service is not serialized. Existing P01 equality,
hashing, identities, and reconstruction validation remain authoritative.

No new immutable record is authorized, so P03-F00 must preserve compliance inventory 606 and
digest `2b2aa94b9f3a8fb7ebe305be5dc3697f645197df82f3d12bee598d8f08c0930b`. The
protocol is structural; the stateless service configuration needs no new hashable value object.
A later need for a new record requires governance, not implementation convenience.

## Boundaries

P02 remains CLOSED / FROZEN. Its configured adapter receives validated inputs, immutable profile,
exact resolved rules, policy, and explicit context, and returns a complete fact bundle or governed
nonaccepted result. P03 invokes and propagates it without reinterpretation.

P04 will provide concrete Elliott/Fibonacci profiles, semantic rules/identities, and strategy
configuration; it will not orchestrate runtime. P05 will provide concrete MTF semantics and
inputs; P03 only passes configured immutable values. Both remain unauthorized.

P06+ retain end-to-end integration, backtest/replay scheduling, walk-forward, metrics, paper/live
modes, broker sessions, execution lifecycle, persistence, operational retry, monitoring, and
deployment.

## Package design

The existing `epip.strategy_runtime` package stays canonical. P03-F00 may add only:

```text
epip/strategy_runtime/runtime.py  # protocol and canonical stateless orchestrator
```

Existing P01/P02 modules are reused; no parallel contracts or identities modules are warranted.
Necessary exports are additive P03 work, not predecessor semantic changes.

## Implementation milestones and order

| Milestone | State | Scope |
| --- | --- | --- |
| P03-F00 | AUTHORIZED | Protocol; canonical single-evaluation orchestrator; dependency checks; zero/one adapter call; existing-state mapping; frozen A07 sequencing; envelope; sanitized diagnostics; focused tests |
| P03-F01 | NOT AUTHORIZED | Remaining runtime branch, provenance, and public-boundary coverage closure found by F00 |
| P03-F02 | NOT AUTHORIZED | Determinism, concurrency, compliance, and final P03 closure |

Order is P03-F00 -> P03-F01 -> P03-F02. F00 implements the frozen boundary end to end; it may not
defer an undefined contract. F00 authorization does not authorize later phases.

## Future test strategy

P03-F00 tests must cover accepted signals; every adapter outcome; A07 no-signal/rejection; every
zero-call structural failure; exactly one call; adapter/profile/strategy/evaluation/source/provenance
identity mismatches; explicit timestamps; terminal short-circuiting; no retry/fallback; unexpected
exceptions; sanitization; adapter-diagnostic preservation; envelope continuity; repeated and
concurrent equivalence; immutable-input preservation; absence of clock/random/I/O/successor
dependencies; and public API/compliance inventory. Repository regression, formatting, linting,
typing, documentation, coverage, EventBus stress, and diff gates remain mandatory as applicable.

Evidence continuity tests must capture the actual A07 E00 request and prove that its
`evidence_identity` is exactly the accepted bundle identity, including multi-item ordered evidence
and repeated evaluations. A public `StrategyRuntimeRequest`/bundle evidence mismatch test is not a
valid requirement because the frozen runtime request has no evidence-set field. P03 must not add
one, introduce a wrapper/binding, recompute the identity, or import P02 identity helpers.

## Authorization decision

The boundary has no unresolved normative ambiguity. P03 governance and P03-F00 implementation are
authorized. No production code changes in this milestone; no release, tag, P04, or P05 is
authorized.
