# P03-F02 Implementation Authorization

## Decision

P03-F02 is **AUTHORIZED / READY FOR IMPLEMENTATION** as the final P03 test-and-governance closure
milestone. It adds no production behavior, public contract, runtime state, diagnostic vocabulary,
serialization shape, or immutable record. P03-F00 and P03-F01 remain **CLOSED / FROZEN**.

The governing phrase "determinism, concurrency, compliance, and final P03 closure" is resolved as
evidence over the already completed runtime, followed by publication of final P03 closure status.
No production cleanup is authorized.

## Objective, inputs, and outputs

F02 proves that the complete P03 package remains deterministic, stateless, concurrently isolated,
compliant, serializable through frozen P01 contracts, stable at its public boundary, pure, and
isolated from successors. It then reconciles the final P03 validation evidence and closes P03.

F02 consumes only:

- frozen P01 runtime contracts and serialization;
- frozen P02 adapter and fact-bundle contracts;
- frozen A07 E00-E09 and E02/E08/R01 contracts;
- completed P03-F00 production runtime and focused tests; and
- completed P03-F01 public-boundary tests.

F02 outputs focused final-closure tests, validation evidence, a narrow P03 closure record, and
roadmap status. It produces no runtime value or service.

## Exact responsibilities

F02 owns:

1. mixed-request concurrency evidence using one shared `StrategyRuntime` instance, immutable
   dependencies, distinct valid requests, and deterministic request-specific adapter results;
2. proof that serial and concurrent results are value-equal per request, preserve distinct result
   identities, do not cross-contaminate bundles or diagnostics, and invoke the adapter exactly once
   per valid request;
3. comprehensive static closure for the canonical runtime package: no alternate runtime
   implementation, mutable evaluation global, ambient clock, random, UUID, filesystem, network,
   subprocess, environment selection, dynamic import, `eval`, `exec`, or pickle dependency;
4. final successor-isolation evidence covering P04, P05, backtest, replay scheduling, paper/live,
   broker/MT5, execution, position, portfolio, persistence, observability, dashboard, and scheduler
   packages;
5. final execution of existing P01 serialization and compliance evidence without duplicating it;
6. separate F00, F01, P01, P02, A07, and R01 regression accounting; and
7. final P03 collection, coverage, quality, documentation, exact-SHA remote-gate, and governance
   reconciliation.

## Non-responsibilities

F02 does not authorize:

- any modification under `epip/**`;
- new or changed request, result, protocol, state, envelope, diagnostic, identity, serializer,
  registry, adapter, profile, or runtime behavior;
- changes to orchestration, adapter mapping, A07 sequencing, evidence handoff, validation, or
  failure semantics;
- new locks, caches, sessions, retries, fallbacks, discovery, I/O, clocks, or process state;
- Elliott, Fibonacci, indicator, signal, entry, stop, target, confidence, or other concrete P04
  strategy semantics;
- frame hierarchy, trend/entry timeframe, cross-frame confirmation, or other P05 MTF semantics;
  or
- backtest, replay-loop, paper/live, broker, MT5, execution, position, portfolio, persistence,
  monitoring, dashboard, scheduler, deployment, or other downstream behavior.

## F00 and F01 boundaries

F00 validly owns the production runtime, deterministic sequencing, same-request repeated and
concurrent baseline, accepted-result round trip, diagnostics, exception sanitization, and
successor-free orchestration. Those are F00 category A responsibilities, not prematurely shipped
F02 behavior.

F01 validly owns protocol/export evidence, independently reachable validation axes, temporal and
provenance continuity, accepted-bundle continuity, structured diagnostic exposure, and immutable-
input preservation. Its preservation of determinism and compliance during validation does not
consume F02's final closure authority.

Both predecessors are complete. F02 must not repeat their behavioral matrices. The missing
category D evidence is mixed-request shared-instance isolation, comprehensive static package
purity/successor isolation, and the formal aggregate closure decision.

If an F02 test exposes a production defect or requires a new test seam, implementation must stop
for a separate reconciliation. Frozen F00/F01 files may not be patched under this authorization.

## Determinism, concurrency, and thread safety

The new concurrency proof must use at least two distinct valid immutable requests and one shared
runtime. A deterministic protocol-compatible adapter may route solely on explicit request context
and must record calls safely for test observation. Serial baselines and concurrent results must
match by request, including state, result ID, bundle ID, envelope, and diagnostics.

The test must prove per-request isolation and exact call counts without sleep, random scheduling
assumptions, timing thresholds, shared runtime mutation, or a large stress workload. Dependencies
remain responsible for honoring their protocols; P03 adds no locks.

## Compliance and serialization closure

Compliance closes by running the existing authoritative scanner regression and directly reporting
inventory 606 and digest
`2b2aa94b9f3a8fb7ebe305be5dc3697f645197df82f3d12bee598d8f08c0930b`. F02 must not
add a duplicate immutable-inventory test. Any inventory change is unauthorized.

Serialization closes through the existing P01 round-trip/tamper tests plus the F00 accepted-result
round trip. No schema, serializer, tag, version, or new all-state behavioral matrix is authorized.

## Package, API, diagnostics, and failure closure

The public surface remains the frozen P01 contracts plus `StrategyRuntimeProtocol` and
`StrategyRuntime`. F02 verifies one canonical implementation and no accidental successor imports;
it adds no export. Existing typed diagnostics, deterministic ordering, sanitization, and
deduplication close through F00/F01 and P01 regressions.

The complete state vocabulary remains `ACCEPTED_SIGNAL`, `NO_SIGNAL`, `REJECTED`, `INVALID_INPUT`,
`ADAPTER_FAILURE`, and `A07_REJECTION`. No new failure state is authorized.

## Authorized files

F02 implementation may add or update only:

```text
tests/strategy_runtime/test_runtime_f02.py
docs/project/P03_FINAL_CLOSURE.md
docs/project/ROADMAP.md
```

The closure record and roadmap may change only after all implementation gates pass. No other test
or documentation file is authorized without a new reconciliation.

## Frozen files and packages

F02 must not modify:

- `epip/**`, including `epip/strategy_runtime/runtime.py` and all frozen P01 contract modules;
- `tests/strategy_runtime/test_runtime.py` and
  `tests/strategy_runtime/test_runtime_f01.py`;
- `epip/strategy_mapping/**` and `tests/strategy_mapping/**`;
- `epip/a07/**`, `tests/a07/**`, and the E02/E08/R01 implementation and tests;
- P04/P05 files; or
- any downstream backtest, replay, paper/live, broker, execution, position, portfolio, persistence,
  observability, dashboard, scheduler, or deployment package.

## Test and validation contract

The new F02 file contains only:

- one focused mixed-request shared-runtime concurrency-isolation proof, parameterized only where it
  represents distinct request outcomes; and
- one comprehensive static canonical-package, purity, public-surface, and successor-isolation
  proof.

F02 closure must separately report new F02 nodes; unchanged F00 and F01 suites; P01, P02, A07, and
R01 regressions; the authoritative compliance regression; repository collection and full
regression; aggregate coverage of at least 95 percent; `runtime.py` coverage and any justified
unreachable defenses; Black, Ruff, MyPy, Markdownlint, MkDocs strict, and `git diff --check`; and
exact-final-SHA Quality, CodeQL, and Documentation results.

The pre-F02 collection baseline is 2909. No predecessor node may be removed or renamed. The
repository-designated EventBus stress remains a repository gate; F02 adds no P03 stress test.

## Final P03 closure gate

P03 may become **CLOSED / FROZEN** only when F00, F01, and F02 are closed; all focused and
predecessor regressions pass; mixed-request determinism and concurrency isolation pass; compliance
is unchanged; serialization, package/API, diagnostics, failure model, purity, and successor
isolation are reconciled; aggregate coverage remains at least 95 percent; production changes are
zero; collection arithmetic has zero predecessor removals; documentation is complete; exact-SHA
remote gates pass; and no normative ambiguity or production defect remains.

Successful P03 closure makes P04 **READY FOR AUTHORIZATION**, but does not authorize it. P05 remains
**NOT AUTHORIZED** and awaits P04 closure plus its own governance authorization.

No ADR is required because F02 verifies and closes the architecture already accepted by ADR-0027
and ADR-0028.
