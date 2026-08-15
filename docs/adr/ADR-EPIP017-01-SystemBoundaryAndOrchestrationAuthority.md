# ADR-EPIP017-01 — System Boundary and Orchestration Authority

## Status

Approved and frozen.

This ADR is architectural documentation only. It authorizes no implementation. No EPIP-017
implementation programme may begin until this ADR and every mandatory dependent ADR identified
below have been accepted and the remediated EPIP-017 architecture has passed a second independent
institutional review.

## Purpose

Define the authoritative system boundary of EPIP-017, separate its semantic orchestration
authority from operational execution concerns, and establish the ownership rules that all later
EPIP-017 decisions must preserve.

This ADR resolves the ambiguity over whether EPIP-017 is a producer framework, an execution
runtime, a cache, a replay system, an audit system, or an extension of EPIP-016. EPIP-017 is the
institutional coordination authority for conforming evidence producers before the existing
EPIP-016 Decision Framework begins. It is none of those other domains, although it coordinates
with their authoritative boundaries.

## Problem Statement

The original EPIP-017 proposal concentrated producer discovery, dependency resolution, planning,
scheduling, caching, recovery, tracing, snapshotting, certification, and decision handoff in one
undifferentiated orchestrator. It described desirable guarantees without assigning final authority
for semantic planning, execution state, durable results, replay, policy, or certification.

That ambiguity creates the following unacceptable outcomes:

- a monolithic subsystem can become the de facto owner of unrelated platform concerns;
- producers can bypass orchestration through hidden calls or shared context;
- volatile operational state can silently change semantic computation meaning;
- the scheduler can become the unrecorded authority for plan mutation and recovery;
- cache, result storage, snapshots, and audit can become competing sources of truth;
- migration can leave legacy and EPIP-017 paths as permanent competing authorities;
- the example dependency chain can incorrectly treat Decision as an EPIP-017 producer;
- an implementation team can claim determinism or replay compatibility without an enforceable
  authority boundary.

A frozen architecture therefore requires explicit authorities, prohibited ownership transfers,
and a stable handoff boundary before component contracts are designed.

## Architectural Context

EPIP-016 is completed, frozen, and released in v1.5.17. It owns evidence registration, inference,
scenario construction, decision-graph construction, candidate generation, confidence assessment,
decision selection, explanation, and decision certification. EPIP-017 must not change those
responsibilities.

Existing analytical domains—including Swing, Market Structure, Liquidity, Fibonacci, Market
Context, and Elliott—own their analytical semantics. EPIP-017 must not reproduce, reinterpret, or
modify those semantics.

Existing hardening architecture remains authoritative:

- H001 for deterministic identity and clocks;
- H002 for data integrity and immutability;
- H004 for concurrency, atomicity, and ownership;
- H005 for resource lifecycle and retention;
- H006 for reliability and failure contracts;
- H007 for trust boundaries, secure failure, and auditability.

EPIP-017 composes these guarantees through explicit contracts. It does not fork them or weaken
them.

The term **orchestration run** means one frozen semantic request together with its authoritative
planning inputs and all operational attempts made to satisfy it. A run is not a producer, a
decision, a replay session, a cache entry, or an execution order.

## Alternatives Considered

### Alternative A — One monolithic orchestrator

One component owns registry, planning, execution, results, cache, replay, diagnostics, audit, and
handoff.

Rejected because it creates a god subsystem, prevents independent evolution, obscures ownership,
and makes every operational concern capable of changing semantic meaning.

### Alternative B — Producer-driven orchestration

Each producer discovers and directly invokes its dependencies.

Rejected because dependencies become hidden, cycles become runtime behavior, ordering becomes
producer-specific, failure propagation becomes inconsistent, and replay cannot reconstruct an
authoritative plan.

### Alternative C — Extend EPIP-016 to orchestrate producers

The Decision Framework discovers and executes analytical producers before registering evidence.

Rejected because it violates EPIP-016's frozen boundary, couples decision semantics to producer
lifecycle management, and makes backward compatibility dependent on modifying released decision
contracts.

### Alternative D — EventBus-only choreography

Producers react to events and publish their outputs without a central semantic plan.

Rejected because event order is not a substitute for dependency semantics, completeness cannot be
proven before handoff, and replay would reproduce incidental choreography rather than an approved
computation plan.

### Alternative E — Separate semantic control plane and operational execution plane

An orchestration control plane owns producer admission, dependency meaning, semantic planning, and
handoff eligibility. An execution plane performs only authorized invocations and records their
outcomes through explicit state authorities.

Accepted because it prevents volatile execution behavior from redefining computation meaning and
allows planning, execution, storage, replay, and audit contracts to evolve independently under
their own ADRs.

## Decision

### 1. Architectural Position

EPIP-017 is the sole semantic orchestration authority for a run operating through the EPIP-017
path. Its authority begins when a pipeline request is admitted and ends when an immutable evidence
handoff manifest is accepted or rejected at the EPIP-016 boundary.

The authoritative lifecycle is:

```text
Approved producer registry snapshot
                 ↓
Admitted pipeline request and frozen input boundary
                 ↓
Semantic dependency resolution and semantic plan
                 ↓
Authorized operational dispatch and result commitment
                 ↓
Evidence-set completeness and provenance validation
                 ↓
EPIP-016 evidence handoff boundary
                 ↓
EPIP-016 Decision Framework
```

Decision is not an EvidenceProducer, an evidence capability, or an analytical node in an
EPIP-017 execution graph. The final graph terminal is an evidence-set handoff target. EPIP-016
starts only after that boundary accepts the handoff.

### 2. Control Plane

The EPIP-017 control plane owns semantic authority for:

- admission of a pipeline request;
- selection of one immutable approved registry snapshot;
- resolution of declared evidence capabilities and dependencies;
- construction and validation of the semantic execution graph;
- construction and identity of the semantic plan;
- evidence completeness requirements;
- authorization of dispatch work derived from that semantic plan;
- determination of handoff eligibility under the frozen policy profile.

The control plane does not execute analytical logic, own producer state, persist authoritative
results, perform replay, calculate market facts, or make decisions.

### 3. Execution Plane

The EPIP-017 execution plane owns operational coordination only:

- dispatch of invocations authorized by an accepted semantic plan;
- enforcement of declared readiness, resource, isolation, and cancellation rules;
- recording of attempts and terminal outcomes;
- submission of candidate results to the authoritative result-commit boundary;
- production of operational telemetry that cannot alter semantic meaning.

The execution plane may not add dependencies, substitute producers, change evidence completeness,
alter timeframe semantics, or amend the semantic plan. Any change to those items requires a new
semantic plan and identity.

The execution plane is an architectural role, not a commitment to a thread, process, service,
worker, or distributed deployment model. Deployment topology is deliberately deferred until the
invocation lifecycle, isolation, and concurrency ADRs establish safe semantics.

### 4. State Authorities

EPIP-017 recognizes distinct authorities; none may silently impersonate another:

- the **registry authority** admits producers and publishes immutable registry snapshots;
- the **semantic planning authority** publishes immutable semantic plans;
- the **execution ledger authority** records invocation lifecycle transitions and attempt facts;
- the **durable result authority** commits immutable produced results;
- the **cache** is disposable acceleration state and is never an authoritative result source by
  itself;
- the **replay authority** supplies the applicable historical or recorded execution boundary;
- the **audit authority** evaluates evidence from the other authorities and cannot rewrite it;
- the **handoff authority** validates a complete evidence manifest for EPIP-016 without changing
  EPIP-016 semantics.

The detailed contracts for these authorities belong to dependent ADRs. This ADR freezes their
separation.

### 5. Producer Boundary

An EvidenceProducer owns only its declared analytical transformation and the semantic validity of
the result it produces. It may consume only the inputs granted by its authorized invocation.

A producer may not:

- discover, register, schedule, or invoke another producer;
- read an undeclared dependency through global state or shared context;
- mutate a semantic plan, execution graph, registry snapshot, or upstream result;
- publish directly to EPIP-016;
- promote its output to a decision, recommendation, or execution instruction;
- claim orchestration, cache, replay, recovery, or audit authority.

Producer state, side effects, idempotency, cancellation, clocks, randomness, resource use, and
concurrency safety are governed by ADR-EPIP017-02 and may not be inferred from this boundary.

### 6. EPIP-016 Handoff Boundary

EPIP-017 delivers an immutable evidence-set handoff manifest through an adapter to the existing
EPIP-016 evidence-registration boundary. The handoff contains only evidence accepted under the
EPIP-016 public contract plus separately governed provenance and completeness references that do
not redefine evidence semantics.

The handoff adapter may translate representation but may not:

- create or reinterpret evidence;
- hide missing mandatory evidence;
- convert orchestration failure into evidence;
- invoke inference, candidate, confidence, or decision responsibilities;
- modify EPIP-016 public APIs or frozen behavior without a separately approved EPIP-016
  compatibility decision.

Exact completeness profiles, degradation rules, provenance mapping, and acceptance behavior are
deferred to ADR-EPIP017-15. Until that ADR is accepted, no handoff design is approved.

### 7. Legacy Authority During Migration

EPIP-017 adoption is initially explicit and opt-in. For any individual run, exactly one execution
path is authoritative: legacy or EPIP-017. Shadow execution may compare outputs, but its outputs
cannot become authoritative or be mixed with the selected path.

Dual execution is a migration observation mechanism, not a permanent runtime architecture.
Promotion, rollback, compatibility dimensions, and mandatory retirement criteria are governed by
ADR-EPIP017-16.

### 8. Scope of Initial Architecture

The architecture requires serial, parallel, incremental, cached, cross-timeframe, replay, failure,
and recovery capabilities to be fully specified before EPIP-017 is frozen. Their inclusion as
requirements does not authorize simultaneous implementation or allow unresolved semantics to be
delegated to code.

Distributed execution, streaming graphs, cyclic dependencies, iterative fixed-point computation,
and dynamic dependency expansion are not silently supported. Any future requirement for one of
these changes the system boundary or graph semantics and requires a new architectural decision.

## Consequences

### Positive

- EPIP-017 cannot absorb analytical, decision, persistence, replay, or audit ownership by
  convenience.
- Semantic computation remains stable even when scheduling or deployment changes.
- EPIP-016 remains frozen behind a narrow, auditable evidence handoff.
- Producers cannot form hidden orchestration graphs.
- Cache loss, worker failure, or telemetry changes cannot redefine the semantic plan.
- Each high-risk concern can receive an independently reviewable ADR and certification profile.
- Migration has one authoritative path per run and a defined future retirement obligation.

### Negative

- More architectural artifacts and authorities must be coordinated.
- A semantic plan and operational execution record cannot be collapsed into one convenient object.
- Producer integration requires admission and contractual conformance rather than discovery alone.
- Some optimizations must wait until their governing contracts are approved.
- The architecture cannot claim transparent support for distributed, streaming, cyclic, or dynamic
  workflows.

### Trade-offs

The additional separation is intentional. EPIP accepts more explicit governance and artifacts in
exchange for long-term determinism, replay credibility, replaceable infrastructure, and clear
ownership.

## Invariants

1. EPIP-017 is the sole semantic orchestration authority for every admitted EPIP-017 run.
2. Exactly one execution path is authoritative for a run.
3. EPIP-017 begins after request admission and ends at the EPIP-016 handoff boundary.
4. EPIP-016 begins only after the handoff boundary accepts an evidence manifest.
5. Decision is never an EPIP-017 producer or analytical graph node.
6. Existing analytical domains retain ownership of their analytical semantics.
7. The control plane never executes analytical logic.
8. The execution plane never changes semantic meaning.
9. A semantic-plan change always creates a new semantic-plan identity.
10. A registry change never mutates a previously frozen registry snapshot.
11. A producer never discovers or invokes another producer.
12. A producer consumes only declared, authorized inputs.
13. A producer never publishes directly to EPIP-016.
14. Durable results, caches, checkpoints, traces, and audits are distinct architectural artifacts.
15. A cache is never the sole authority for a certified result.
16. Operational telemetry never determines semantic output or identity.
17. Audit evaluates authoritative records and never rewrites execution history.
18. Shadow outputs never mix with authoritative outputs.
19. No deployment topology is permitted to weaken producer isolation or result-commit invariants.
20. Unsupported workflow semantics require a new ADR; they may not emerge implicitly in code.

## Compatibility

This decision is additive and changes no production behavior.

It preserves:

- EPIP-016 evidence, inference, graph, candidate, confidence, decision, explanation, validation,
  and certification contracts;
- existing analytical ownership in Swing, Market Structure, Liquidity, Fibonacci, Market Context,
  and Elliott;
- Kernel, EventBus, Replay, financial, risk, portfolio, execution, and serialization authorities;
- existing public APIs and the legacy execution path during the governed migration period.

Compatibility means more than unchanged signatures. ADR-EPIP017-15 must prove EPIP-016 behavioral
equivalence at handoff, and ADR-EPIP017-16 must define legacy comparison, rollback, and retirement.
This ADR does not claim those proofs have already been supplied.

## Certification Rules

This ADR is conformant only when architectural review can establish all of the following without
examining implementation code:

1. Every EPIP-017 responsibility is assigned to exactly one primary authority.
2. No authority can change another authority's immutable artifact in place.
3. A complete run can be described from admission through handoff without assigning Decision work
   to EPIP-017.
4. The semantic plan remains unchanged across permitted dispatch strategies.
5. Loss of cache or telemetry cannot change semantic meaning.
6. Producer-to-producer invocation is prohibited by contract.
7. The handoff boundary cannot reinterpret or fabricate evidence.
8. A shadow run cannot influence an authoritative run.
9. Every deferred high-risk contract maps to a mandatory dependent ADR.
10. No implementation programme is authorized solely by acceptance of this ADR.

Final implementation certification will later require evidence that runtime components conform to
these boundaries, but this ADR does not define or authorize those components.

## Non-goals

This ADR does not define:

- producer APIs or execution behavior;
- evidence schemas or capability-resolution algorithms;
- timeframe calendars or availability semantics;
- semantic-plan structure;
- dispatch-plan structure;
- invocation state transitions or commit protocols;
- digest formats or algorithms;
- durable result-store or cache technology;
- replay algorithms;
- snapshot or checkpoint formats;
- retry or recovery algorithms;
- concurrency mechanisms or worker topology;
- EPIP-016 handoff representation;
- migration dates or operational rollout procedures;
- trading, market-analysis, decision, risk, portfolio, execution, or financial logic.

Those omissions are deliberate ADR boundaries, not permission for implementation teams to decide
them informally.

## ADR Dependencies

This ADR depends on the frozen boundaries established by EPIP-016 and H001 through H007.

It creates mandatory downstream dependencies on:

- ADR-EPIP017-02 for producer capability and execution behavior;
- ADR-EPIP017-03 for registry governance, admission, trust, and certification;
- ADR-EPIP017-04 for evidence semantics and dependency resolution;
- ADR-EPIP017-05 for temporal availability and cross-timeframe semantics;
- ADR-EPIP017-06 for semantic-plan and dispatch-plan separation;
- ADR-EPIP017-07 for invocation lifecycle and atomic result commitment;
- ADR-EPIP017-08 for determinism profiles;
- ADR-EPIP017-09 for identity and digest hierarchy;
- ADR-EPIP017-10 for durable result storage, cache, and invalidation;
- ADR-EPIP017-11 for replay modes;
- ADR-EPIP017-12 for audit snapshots and resumable checkpoints;
- ADR-EPIP017-13 for failure, retry, and recovery;
- ADR-EPIP017-14 for concurrency and parallel equivalence;
- ADR-EPIP017-15 for EPIP-016 handoff and evidence completeness;
- ADR-EPIP017-16 for migration and compatibility governance.

ADR-EPIP017-17 provides the required observability, audit retention, and redaction governance.
ADR-EPIP017-18 provides the required capacity, graph-limit, and operational governance. These
mandatory dependencies are satisfied by the approved and frozen constitutional corpus.

## Future Evolution

Future architecture may introduce distributed workers, streaming producers, cyclic or iterative
graphs, dynamic graph expansion, or additional handoff consumers only through new ADRs that retain
the authority separations and invariants defined here.

A future deployment change does not automatically change semantic authority. A future storage
change does not automatically change result identity. A future producer capability does not
automatically expand the orchestration model. Each evolution must identify which authority is
affected, preserve compatibility, and define new certification rules before implementation.

## Approval Gate

Approval of this ADR confirms only that the EPIP-017 system boundary and orchestration authorities
are sufficiently explicit for dependent architecture work to continue.

It does not approve Programme A, production code, placeholders, interfaces, or implementation.
EPIP-017 remains blocked until the complete dependent ADR set has been accepted and the remediated
architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
