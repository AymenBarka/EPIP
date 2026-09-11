# P03-F01 Implementation Authorization

## Decision

P03-F01 is **AUTHORIZED / READY FOR IMPLEMENTATION** as a narrow test-evidence milestone. It adds
no production behavior, public contract, runtime state, serialization shape, or immutable record.
P03-F00 remains **CLOSED / FROZEN** and is the complete production implementation of the governed
single-evaluation runtime boundary.

This authorization resolves the P03 governance description of F01 as the remaining runtime branch,
provenance, and public-boundary coverage closure found after F00. The F00 implementation and its
coverage evidence show no independently reachable production branch left for F01 to implement.

## Objective

F01 closes focused, externally observable evidence for the existing `StrategyRuntimeProtocol` and
`StrategyRuntime` boundary. Its output is tests proving uncovered combinations of already frozen
behavior. It must not change the behavior being observed.

The only authorized implementation file is:

```text
tests/strategy_runtime/test_runtime_f01.py
```

F01 completion may update this authorization record and `docs/project/ROADMAP.md` with validation
evidence. No production Python file or package export is authorized for modification.

## Inputs and outputs

F01 consumes only:

- frozen P01 request, result, options, state, diagnostics, profile, MTF, provenance, and signal
  envelope contracts;
- frozen P02 `FactAdapterProtocol`, `FactAdapterResult`, and `StrategyFactBundle` semantics;
- frozen A07 E00-E09 contracts and the closed E02/E08/R01 continuity correction; and
- the completed P03-F00 `StrategyRuntimeProtocol` and `StrategyRuntime` implementation.

Its output is test evidence over existing `StrategyRuntimeResult` values and observable dependency
calls. It creates no runtime output type, wrapper, binding, registry, state, diagnostic vocabulary,
or serializer.

## Owned test evidence

F01 must add only non-duplicative evidence for the following existing boundaries:

1. Public boundary: the package exports `StrategyRuntimeProtocol` and `StrategyRuntime`; the
   implementation structurally satisfies the protocol; `evaluate` retains the frozen one-request,
   one-result signature; and service configuration remains slot-bounded without evaluation state.
2. Runtime-owned validation: independently reachable profile-resolution, adapter-identity,
   compatibility, temporal, and provenance discontinuities return the already governed state,
   diagnostic code, diagnostic stage, and zero-call behavior.
3. Accepted-bundle continuity: independently reachable evaluation, strategy, policy, profile, MTF,
   provenance, and evidence-manifest discontinuities stop before A07 with the existing coherence
   failure result, without adding validation or recomputing P02 identities.
4. Diagnostic exposure: terminal adapter diagnostics remain exactly preserved, and P03-created
   diagnostics expose only deterministic governed content.
5. Boundary immutability: evaluation does not mutate the request or its nested immutable inputs.
6. F00 defensive-line classification: the currently uncovered `runtime.py` lines 142, 192, and 238
   are category B defensive states that valid frozen constructors cannot represent. F01 must not
   forge impossible contract states merely to raise line coverage and must not alter F00 to remove
   those defenses.

Tests may share fixtures from `tests/strategy_runtime/conftest.py` if useful. A new fixture file is
not authorized unless the F01 implementation review proves it necessary without changing behavior.

## Frozen F00 boundary and overlap audit

F00 correctly owns and has already implemented:

- exact dependency injection and identity checking;
- zero-or-one adapter invocation;
- terminal adapter-state translation;
- exact accepted-bundle identity and ordered-evidence handoff;
- frozen A07 E00-E09 sequencing and fail-fast behavior;
- `NO_SIGNAL`, `ACCEPTED_SIGNAL`, and `A07_REJECTION` outcomes;
- signal-envelope construction;
- exception sanitization; and
- synchronous, stateless repeated and concurrent evaluation.

These are category A F00 responsibilities, not prematurely shipped F01 functionality. F01 may use
the existing F00 tests as regression but must not duplicate them. No explicit F00 responsibility is
unfinished. If F01 evidence exposes a production defect, implementation must stop for a separate
F00 reconciliation; this authorization does not permit modifying frozen F00.

## Non-scope

F01 does not authorize:

- changes to `epip/strategy_runtime/runtime.py`, any other `epip/strategy_runtime` production file,
  or the public package exports;
- new profile resolution, adapter selection, registry, discovery, fallback, retry, or lifecycle;
- changes to A07 sequencing, failure mapping, signal semantics, envelope construction, diagnostics,
  runtime states, request options, serialization, or identities;
- recomputation or duplicate validation of P02 evidence identity, freshness, temporal eligibility,
  revision eligibility, semantic closure, or ordered evidence;
- interpretation of frame roles, timeframe ordering, cross-frame confirmation, or any concrete MTF
  semantics owned by P05;
- Elliott, Fibonacci, indicator, entry, stop, target, confidence, or other concrete strategy
  semantics owned by P04;
- caching, sessions, mutable shared evaluation state, locks, ambient clocks, random values, UUIDs,
  I/O, or nondeterministic iteration; or
- backtest, replay, walk-forward, paper/live scheduling, broker/MT5, execution, position, portfolio,
  persistence, observability, deployment, P04, P05, or any downstream runtime system.

`StrategyRuntimeOptions` receives no new meaning in F01. Optional-evidence freshness remains P02
policy behavior, and F01 has no authority to invent warning escalation semantics.

## F01 and successor boundary

P03-F02 remains **NOT AUTHORIZED**. It owns the final P03 determinism, concurrency, compliance, and
closure review. F01 must preserve those properties and run proportionate regressions, but it must
not create a second stress or compliance implementation milestone.

P04 and P05 remain **NOT AUTHORIZED**. F01 consumes no successor semantics and imports no successor
or downstream package.

## Frozen files and packages

F01 must not modify:

- `epip/strategy_runtime/**`, including the frozen F00 runtime;
- `epip/strategy_mapping/**` and `tests/strategy_mapping/**`;
- `epip/a07/**` and `tests/a07/**`;
- frozen P01 contract modules or their existing contract tests;
- the A07 E02/E08/R01 implementation or tests;
- P04/P05 packages or documents; or
- backtest, replay, execution, broker, portfolio, persistence, observability, and deployment code.

## Test and regression contract

New F01 tests are restricted to the six owned evidence categories above. Existing
`tests/strategy_runtime/test_runtime.py` is the F00 regression suite and remains unchanged.

F01 implementation validation must separately report:

- new F01 node count and pass result;
- F00 strategy-runtime regression;
- frozen P01 contract regression;
- frozen P02 regression;
- frozen A07 regression;
- frozen A07 E02/E08/R01 regression;
- repository-wide collection and full regression;
- aggregate repository coverage of at least 95 percent, with no meaningful untested reachable
  category A behavior introduced by F01;
- Black, Ruff, MyPy, documentation, and `git diff --check` results; and
- unchanged compliance inventory 606 and digest
  `2b2aa94b9f3a8fb7ebe305be5dc3697f645197df82f3d12bee598d8f08c0930b`.

No predecessor test node may be removed or renamed. The pre-F01 collection baseline is 2895.

## Acceptance gate

F01 may close only when its focused tests pass, every predecessor regression passes, collection
arithmetic reconciles with zero predecessor removals, aggregate coverage remains at least 95
percent, no reachable F00 defect is found, compliance is unchanged, production changes are zero,
successor imports and semantics are absent, local quality/documentation gates pass, and exact-final-
SHA Quality, CodeQL, and Documentation workflows pass.

No ADR is required. This artifact narrows an already governed coverage milestone and makes no new
architectural decision.
