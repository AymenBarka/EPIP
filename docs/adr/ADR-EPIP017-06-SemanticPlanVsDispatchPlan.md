# ADR-EPIP017-06 — Semantic Plan vs Dispatch Plan

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-05 are approved, frozen, and normative. This ADR MUST NOT
modify their orchestration authority, producer contract, governance, Evidence semantics, temporal
model, EPIP-016 boundary, or single-authoritative-path rule.

This ADR defines architecture only. It authorizes no implementation, planner, scheduler, worker,
queue, plan class, interface, placeholder, or Programme A activity.

## Executive Summary

EPIP-017 SHALL represent meaning and execution through separate immutable artifacts.

The **Semantic Plan** defines what evidence outcome is required and why: admitted intent, frozen
inputs, selected capabilities and producers, Evidence requirements, dependency graph, temporal
boundaries, semantic constraints, completeness, and handoff eligibility requirements. It SHALL be
the sole planning authority for semantic meaning.

The **Dispatch Plan** defines one authorized operational strategy for attempting that Semantic
Plan: execution units, eligible groups, batches, barriers, fences, resource classes, worker
allocations, scheduling order, timeout policies, and retry authorizations. It SHALL NOT add,
remove, substitute, reinterpret, or weaken any semantic requirement.

The **Execution Ledger**, governed by ADR-EPIP017-07, SHALL record what actually happened. Runtime
facts MUST NOT be written back into either plan. A changed operational strategy requires a new
Dispatch Plan identity. A changed semantic input or requirement requires a new Semantic Plan
identity.

Cache eligibility SHALL NOT appear in the Semantic Plan. A Dispatch Plan MAY authorize a durable
result lookup or cache lookup as an operational execution unit, but the result MUST satisfy the
same frozen semantic requirement and commitment rules as fresh execution. Cache hit, cache miss,
eviction, retry, timeout, worker failure, or resource pressure MUST NOT change semantic intent.

Semantic equivalence permits different Dispatch Plans only when they preserve the same Semantic
Plan and produce an evidence set conforming to the same semantic and handoff contracts. Operational
equivalence and parallel equivalence remain subject to ADR-EPIP017-07 and ADR-EPIP017-14.

## Purpose

Establish the constitutional separation between semantic planning and operational dispatch for the
lifetime of EPIP.

This ADR defines:

- the authoritative contents and ownership of a Semantic Plan;
- the permitted contents and limits of a Dispatch Plan;
- execution intent, units, groups, stages, batches, windows, barriers, and fences;
- separation of semantic, execution, operational, scheduling, and diagnostic context;
- plan identities, versions, certification, replay, diagnostics, and audit;
- rules ensuring scheduling and runtime behavior never change semantic decisions.

## Problem Statement

The original EPIP-017 proposal placed producer selection, dependency meaning, cache decisions,
parallel stages, retry policy, timeout policy, and resource assignment in one immutable execution
plan. That design combined stable semantic intent with volatile operational state.

Such a combined plan cannot remain truthful when:

- a cache entry disappears or fails integrity validation;
- a worker becomes unavailable;
- a resource limit changes;
- an invocation times out or is cancelled;
- an authorized retry becomes necessary;
- an equivalent serial strategy replaces a parallel strategy;
- execution is resumed after failure;
- diagnostic or operational context changes.

Implementations would either mutate the allegedly immutable plan or keep undocumented side state
that becomes the real execution authority. Worse, runtime availability could alter producer
selection, dependencies, optional inputs, temporal meaning, or evidence completeness.

EPIP therefore requires one immutable artifact for meaning, a separate immutable artifact for each
authorized operational strategy, and a separate append-only record of runtime facts.

## Architectural Context

ADR-EPIP017-01 separates the semantic control plane from the operational execution plane and
requires separate registry, planning, ledger, result, replay, audit, and handoff authorities.

ADR-EPIP017-02 limits producers to authorized immutable input manifests and prohibits scheduling,
retry, cache, discovery, and result-commit authority.

ADR-EPIP017-03 requires every Semantic Plan to use one immutable registry snapshot and prevents
runtime governance changes from mutating an active run.

ADR-EPIP017-04 defines immutable Evidence requirements, deterministic dependency resolution,
selection stability, graph semantics, and fail-closed ambiguity.

ADR-EPIP017-05 defines immutable Knowledge Boundaries, timeframe and calendar semantics, revision
visibility, and cross-timeframe mappings.

This ADR binds those frozen semantic facts into a Semantic Plan and strictly limits what may enter
a Dispatch Plan.

## Definitions

### Planning Request

The admitted immutable request that states terminal evidence outcomes, subject scope, policy
profile, temporal boundary, execution eligibility constraints, and certification requirements.

### Planning Input Manifest

The complete immutable set of authoritative facts from which a Semantic Plan is derived, including
the Planning Request, registry snapshot, context projections, temporal boundary, capability and
Evidence contracts, compatibility decisions, resolution profile, and semantic policy versions.

### Semantic Plan

The immutable authoritative statement of what semantic computation is required to satisfy one
Planning Request.

### Dispatch Request

An immutable request to derive one operational strategy for one accepted Semantic Plan under one
operational policy and resource-admissibility boundary.

### Dispatch Plan

An immutable authorization describing how the execution plane MAY attempt the exact work fixed by
one Semantic Plan without changing semantic meaning.

### Execution Intent

The immutable association between one semantic graph node and the exact producer, capability,
input requirements, output requirements, temporal boundary, and completion obligation authorized
by the Semantic Plan.

### Execution Unit

The smallest dispatch-authorized operational action. It MAY invoke one producer, validate or
retrieve one exact durable result, perform one governed commitment action, or perform another
explicitly approved operational action. An Execution Unit MUST map to semantic intent or an
operational obligation and MUST NOT create semantic work.

### Execution Group

A set of Execution Units that share one declared operational relationship, such as mutual
exclusion, bounded concurrency, resource class, or failure domain. Group membership MUST NOT imply
semantic dependency.

### Execution Barrier

An immutable readiness predicate that prevents an Execution Unit from becoming dispatch-eligible
until specified semantic-result commitments or operational prerequisites have reached declared
states.

### Execution Stage

A deterministic explanatory partition of Execution Units by readiness or operational policy. A
stage MUST NOT create a global synchronization requirement unless explicit barriers require it.

### Execution Batch

A bounded dispatch grouping of eligible Execution Units selected for one operational submission.
Batch membership MUST NOT change semantics, dependency, result ordering, or commitment.

### Execution Window

A governed operational interval or logical admission boundary during which specified dispatch
actions MAY begin. It is not Observation Time, Knowledge Time, Validity Time, or an execution
timeout.

### Execution Fence

An immutable authority token or logical generation boundary that prevents obsolete, duplicate,
cancelled, timed-out, or superseded attempts from committing results.

### Execution Ledger

The append-only authoritative record of actual invocation, attempt, dispatch, cancellation,
timeout, failure, and commitment facts. It is neither a Semantic Plan nor a Dispatch Plan.

### Semantic Equivalence

The relation by which two executions satisfy the same Semantic Plan and yield evidence conforming
to the same semantic, temporal, completeness, provenance, and handoff contracts.

### Dispatch Equivalence

The relation by which two Dispatch Plans differ operationally but are both authorized to attempt
the same Semantic Plan without changing any semantic artifact or obligation.

## Semantic Plan

### Semantic Intent

The Semantic Plan MUST state the requested terminal evidence set, its subject and scope, and the
complete semantic conditions for acceptance. It MUST explain why every included node and edge is
required.

### Required Capabilities and Producers

The Semantic Plan MUST contain the exact selected producer identity and version, capability
identity and version, producer contract version, certification profile, implementation identity,
and configuration identity for every producer invocation.

The Semantic Plan MUST preserve rejected material candidates and deterministic selection reasons
for audit, without making them executable alternatives.

### Required Evidence

Every input and output Evidence requirement MUST identify evidence type, semantic version,
cardinality, compatibility, validity, completeness, provenance, independence, conflict, and
temporal requirements.

### Dependency Graph

The Semantic Plan MUST contain one complete, finite, bounded, immutable, acyclic dependency graph
as defined by ADR-EPIP017-04. The graph MUST include explicit optional absence and conditional
predicate outcomes. It MUST terminate at an evidence-set handoff requirement, never at Decision.

### Temporal Requirements

The Semantic Plan MUST freeze Observation, Availability, Knowledge, Validity, Revision, Calendar,
Timeframe, Temporal Mapping, watermark, closure, and completeness facts required by
ADR-EPIP017-05.

### Semantic Constraints

The Semantic Plan MUST freeze all policy facts capable of changing producer selection, dependency
meaning, Evidence semantics, temporal interpretation, completeness, compatibility, or handoff
eligibility.

### Planner Ownership and Authority

The semantic planning authority SHALL own plan derivation and validation. It MUST NOT own producer
analytics, worker allocation, retry, timeout, cache state, scheduling, result commitment, or
EPIP-016 Decision semantics.

An accepted Semantic Plan MUST be immutable. Any changed planning input, selected producer,
capability, dependency, Evidence requirement, temporal fact, context projection, completeness rule,
or semantic policy MUST produce a new Semantic Plan identity.

## Dispatch Plan

The Dispatch Plan MUST reference exactly one accepted Semantic Plan and MUST preserve every
Execution Intent derived from it.

It MAY define:

- Execution Units and their semantic-intent mappings;
- serial and parallel-eligible groups;
- execution batches and stages;
- readiness barriers and execution fences;
- resource classes and bounded assignments;
- worker eligibility and allocation constraints;
- queue or scheduling classes;
- canonical dispatch ordering and fairness policy references;
- operational deadlines, timeout policies, and cancellation scopes;
- retry authorization profiles owned by ADR-EPIP017-13;
- durable-result and cache lookup authorization owned by ADR-EPIP017-10;
- observability and operational-diagnostic policies;
- dispatch-plan validity and supersession rules.

It MUST NOT define or change:

- terminal semantic intent;
- capability or producer selection;
- Evidence type, meaning, validity, compatibility, completeness, or provenance;
- dependency nodes, edges, cardinality, optionality, or conditions;
- semantic context projections;
- Observation, Knowledge, Availability, Validity, Revision, Calendar, or Timeframe semantics;
- input or output schemas;
- EPIP-016 handoff eligibility;
- result identity or atomic commitment semantics.

Cache presence, worker availability, queue state, runtime timing, or resource pressure MUST NOT
cause dispatch to select a different semantic producer or dependency. If the exact planned work
cannot be attempted, dispatch MUST fail, wait, or request a new governed plan; it MUST NOT repair
semantics.

## Execution Intent

Every executable semantic graph node MUST produce exactly one Execution Intent. One Execution
Intent MAY have multiple operational attempts, but all attempts MUST preserve identical semantic
inputs and expected outputs.

Execution Intent MUST identify:

- run and Semantic Plan identities;
- semantic graph node identity;
- selected producer and capability identities;
- exact input-manifest identity;
- expected output and completeness contracts;
- temporal boundary identity;
- applicable deterministic, replay, security, and certification profiles;
- result-commit obligation and failure policy reference.

Execution Intent MUST NOT identify workers, threads, queues, batches, attempts, elapsed-time
outcomes, cache hits, or retry counts.

## Execution Units

### Execution Unit

An Execution Unit MUST be operationally indivisible for dispatch authority. It MUST reference one
Execution Intent or one explicit operational obligation. It MUST have no authority to expand its
semantic inputs or outputs.

### Execution Group

An Execution Group MUST describe only operational relationships. A group MUST NOT be used as a
hidden semantic edge or evidence aggregation mechanism.

### Execution Barrier

A barrier MUST state an explicit readiness predicate over committed semantic results or governed
operational states. Barrier evaluation MUST NOT inspect analytical values unless the Semantic Plan
already declared that value as a frozen conditional-planning input. Runtime producer output MUST
NOT create a new dependency or barrier.

### Execution Stage

Stages MAY summarize topological depth or dispatch phases. Stage labels MUST NOT impose ordering
beyond explicit semantic dependencies and operational barriers.

### Execution Batch

Batches MAY optimize submission. A batch MUST NOT establish result atomicity across unrelated
Execution Units, hide per-unit failures, or change canonical result collection.

### Execution Window

An Execution Window MAY constrain operational admission. It MUST NOT be interpreted as Evidence
Validity Time, Knowledge Time, or timeframe closure. Missing an Execution Window MUST produce an
operational disposition, not temporal reinterpretation.

### Execution Fence

Every attempt capable of result submission MUST be governed by a fence. A superseded fence MUST
make later submissions from that attempt ineligible for authoritative commitment. Fence lifecycle
and atomicity are completed by ADR-EPIP017-07.

## Execution Barriers

Barriers SHALL be node-level readiness predicates. A barrier MAY require:

- successful commitment of all mandatory upstream results;
- explicit optional-absence commitment;
- completion of an authorized prior attempt state;
- resource or isolation admission;
- a valid execution fence;
- an authorized dispatch or recovery epoch.

Barriers MUST NOT:

- infer dependencies from runtime behavior;
- require whole-stage completion when node-level prerequisites are satisfied unless an explicit
  operational safety policy requires it;
- convert failed, missing, invalid, or uncommitted results into successful prerequisites;
- reopen semantic planning;
- inspect future temporal facts;
- change after Dispatch Plan acceptance except through a new Dispatch Plan identity or ledger state
  transition explicitly authorized by the same immutable predicate.

## Dependency Ordering

Dependency ordering SHALL be fixed by the Semantic Plan's directed graph and canonical semantic
ordering. A consumer MUST NOT become eligible before all required upstream commitments satisfy its
declared dependency contract.

Semantic ordering MUST be independent of worker, queue, batch, attempt, completion, storage, and
telemetry order.

The Dispatch Plan MAY exploit independence among ready nodes. It MUST NOT infer independence merely
from stage membership; semantic graph reachability and ADR-EPIP017-14 isolation rules SHALL govern
parallel eligibility.

## Dispatch Ordering

Dispatch ordering MAY choose among semantically ready Execution Units according to one immutable,
versioned operational policy. The policy MUST define stable precedence and fairness without
changing output meaning.

Physical start and completion order MAY differ from canonical dispatch order. Result association,
commitment, collection, diagnostics, and audit MUST use stable identities rather than incidental
completion order.

Changing dispatch ordering policy MUST create a new Dispatch Plan version and identity. It MUST NOT
create a new Semantic Plan unless a semantic input also changes.

## Execution Context

Context SHALL be separated into non-overlapping authority domains.

### Semantic Context

Semantic Context contains only immutable facts capable of changing analytical meaning: subject,
scope, admitted external inputs, declared producer context projections, portfolio facts explicitly
authorized as Evidence or external inputs, semantic policies, and completeness requirements.

The semantic planning authority SHALL own its projection into the Planning Input Manifest. Any
change MUST create a new Semantic Plan identity.

### Execution Context

Execution Context contains immutable per-intent facts granted to producer execution: exact input
manifest, producer configuration, capability, temporal boundary, deterministic profile, security
scope, and cancellation contract.

The execution plane SHALL materialize it from the Semantic Plan and approved execution policy. It
MUST NOT add semantic facts.

### Operational Context

Operational Context contains resource availability, worker health, deployment location, queue
state, circuit state, capacity, and operational admission facts. The Operational Authority SHALL
own it. It MUST NOT be visible to producer analytics or enter Semantic Plan identity.

### Scheduling Context

Scheduling Context contains batch, priority, fairness, worker eligibility, resource assignment,
barrier, fence, timeout, and retry authorization facts. The scheduler authority SHALL own it under
the Dispatch Plan. It MUST NOT become producer input or change semantic readiness.

### Diagnostic Context

Diagnostic Context contains stable identifiers and approved observations needed to explain
planning, dispatch, or execution. It SHALL be assembled by the authority producing the diagnostic.
It MUST NOT act as a service locator, hidden input, mutable shared context, or semantic authority.

No context category may contain an undeclared reference that grants access to another category.
Context projection, ownership, visibility, identity, and audit MUST remain explicit.

## Dispatch Context

The Dispatch Plan SHALL reference only the operational and scheduling context snapshot necessary
to authorize its strategy. Volatile observations after acceptance belong to the Execution Ledger
and MAY cause failure, wait, cancellation, or derivation of a new Dispatch Plan. They MUST NOT
mutate the existing Dispatch Plan.

Workers MUST receive only their authorized Execution Context and minimal scheduling control. They
MUST NOT receive the mutable planner, live registry, complete semantic graph, unrelated context, or
alternative producer candidates.

## Plan Identity

### Semantic Plan Identity

Semantic Plan identity MUST derive from all semantically relevant planning inputs, including:

- Planning Request and policy versions;
- registry snapshot;
- selected producer, capability, implementation, contract, configuration, and certification
  identities;
- Evidence requirements and dependency graph;
- Semantic Context projections;
- temporal boundaries, calendars, timeframes, revisions, and mappings;
- compatibility, optionality, conditional outcomes, cardinality, and completeness;
- terminal handoff requirements;
- canonical semantic ordering.

It MUST exclude workers, queues, batches, resource availability, retry attempts, timeout outcomes,
cache state, telemetry, and execution timing.

### Dispatch Plan Identity

Dispatch Plan identity MUST derive from:

- referenced Semantic Plan identity;
- dispatch-policy version;
- Execution Units and mappings;
- operational groups, barriers, stages, batches, windows, and fences;
- resource and worker eligibility classes;
- canonical dispatch ordering;
- retry, timeout, cancellation, cache-lookup, and observability authorizations;
- Dispatch Plan validity and supersession rules.

It MUST exclude actual worker assignment where assignment remains a runtime ledger fact, actual
attempt outcomes, elapsed time, cache hit or miss, and mutable telemetry.

### Execution Identity

Execution identity SHALL remain separate and SHALL bind the Semantic Plan, selected Dispatch Plan,
run, invocation, attempts, and ledger under ADR-EPIP017-07 and ADR-EPIP017-09.

## Plan Versioning

Semantic Plan schema version, semantic policy version, and individual Semantic Plan identity MUST
remain distinct. A schema evolution MUST NOT reinterpret historical plans.

Dispatch Plan schema version, dispatch-policy version, and individual Dispatch Plan identity MUST
remain distinct.

A Semantic Plan MUST be superseded, never mutated. Supersession requires a new Semantic Plan when
any semantic fact changes.

A Dispatch Plan MUST be superseded, never mutated. Operational replanning MAY create a new
Dispatch Plan for the same Semantic Plan only when every semantic obligation remains identical and
the applicable recovery policy authorizes it.

An accepted plan MUST declare its validity, compatibility, and retention requirements. Expiration
MUST be an explicit logical policy, never implicit wall-clock mutation.

## Plan Certification

Semantic Plan certification MUST verify:

- complete and authoritative Planning Input Manifest;
- exact registry and governance eligibility;
- deterministic producer and capability selection;
- complete Evidence requirements and dependency graph;
- temporal correctness and absence of future leakage;
- explicit Semantic Context projections;
- semantic constraints, compatibility, completeness, and handoff requirements;
- canonical identity and reproducibility;
- absence of operational state.

Dispatch Plan certification MUST verify:

- exact reference to one certified Semantic Plan;
- complete mapping from semantic intents to Execution Units;
- no created, removed, substituted, or weakened semantics;
- valid readiness barriers, fences, and operational policies;
- permitted resource, retry, timeout, cancellation, and cache-lookup authorizations;
- no producer-facing operational leakage;
- reproducibility under identical dispatch inputs;
- conformance with invocation, failure, concurrency, and capacity ADRs.

Certification of a Dispatch Plan MUST NOT certify producer analytical correctness. Certification of
a Semantic Plan MUST NOT certify worker availability or operational success.

## Plan Invariants

1. The Semantic Plan defines intent; the Dispatch Plan defines an authorized attempt strategy.
2. Both plans are immutable after acceptance.
3. Semantic identity never changes in place.
4. Dispatch identity never changes in place.
5. Every Dispatch Plan references exactly one Semantic Plan.
6. Different Dispatch Plans MAY reference one Semantic Plan only under explicit equivalence rules.
7. The Semantic Plan contains no workers, threads, queues, batches, retries, timeouts, cache state,
   or execution resources.
8. The Dispatch Plan creates no producer, capability, Evidence requirement, dependency, temporal
   meaning, or context fact.
9. Dispatch failure never repairs or weakens semantic intent.
10. Cache outcome never changes semantic intent.
11. Runtime facts are recorded in the Execution Ledger and never written into a plan.
12. Planning never depends on execution timing or completion order.
13. Execution never mutates planning.
14. Semantic readiness derives only from committed required results and frozen absence semantics.
15. Operational grouping never implies semantic dependency.
16. Barriers are explicit predicates and never hidden planning rules.
17. Every attempt preserves one Execution Intent.
18. Semantic Context never contains operational or scheduling state.
19. Operational Context never becomes producer analytical input.
20. A changed semantic fact always creates a new Semantic Plan.
21. A changed operational strategy always creates a new Dispatch Plan.
22. The Semantic Plan is replayable independently of worker topology.
23. Dispatch reconstruction never changes the referenced Semantic Plan.
24. Decision remains outside both plans.

## Determinism

Given identical Planning Input Manifests and planner-policy versions, semantic planning MUST
produce the same Semantic Plan content, canonical ordering, diagnostics, version, and identity.

Given the same Semantic Plan, Dispatch Request, operational-policy versions, resource classes, and
dispatch-admission facts, dispatch planning MUST produce the same Dispatch Plan content, canonical
ordering, diagnostics, version, and identity.

Actual mutable worker health or queue state MAY affect whether a Dispatch Plan succeeds, waits, or
is superseded. It MUST NOT mutate either plan or change semantics.

Equivalent Dispatch Plans MAY have different operational identities. They MUST satisfy the same
Semantic Plan obligations. Exact semantic, operational, and parallel equivalence criteria remain
governed by ADR-EPIP017-08 and ADR-EPIP017-14.

Filesystem order, registry enumeration, hash order, worker discovery, thread completion, cache
arrival, runtime duration, and telemetry MUST NOT affect Semantic Plan identity.

## Replay

### Semantic Replay

Semantic replay SHALL reconstruct or verify the original Semantic Plan from its complete Planning
Input Manifest and historical policy versions. It MUST preserve producer selection, dependency
graph, context projections, temporal boundaries, completeness, diagnostics, and identity.

### Dispatch Replay

Dispatch replay SHALL reconstruct or verify one original Dispatch Plan and its operational policy
inputs. It MUST NOT be required to reproduce physical thread interleaving, machine identity, or
elapsed timing unless ADR-EPIP017-11 explicitly defines operational reproduction evidence for
them.

### Equivalent Dispatch

A replay MAY use a different certified Dispatch Plan for the same Semantic Plan only when the
selected replay mode permits equivalent execution and assigns a distinct Dispatch Plan and
execution identity. It MUST NOT be described as exact operational reproduction.

### Equivalent Execution

Executions are semantically equivalent only when committed evidence and all semantic diagnostics,
metadata, completeness, provenance, temporal, and handoff obligations conform to the same Semantic
Plan. Matching terminal values alone is insufficient.

### Replay Authority

The replay authority SHALL select and declare the replay mode and permitted plan artifacts under
ADR-EPIP017-11. It MUST NOT modify either plan.

## Diagnostics

Diagnostics MUST identify the authority and phase that produced them and distinguish at minimum:

- planning-input failure;
- producer or capability resolution failure;
- dependency or temporal planning failure;
- semantic inconsistency;
- Semantic Plan validation or identity failure;
- dispatch-input failure;
- Execution Unit mapping failure;
- barrier or fence inconsistency;
- resource-admission failure;
- scheduler or worker-allocation failure;
- timeout, retry, cancellation, or cache-authorization failure;
- Dispatch Plan inconsistency;
- invocation execution failure;
- durable-result or commitment failure;
- semantic-versus-dispatch divergence;
- runtime mutation attempt.

Planning diagnostics MUST NOT recommend operational repair. Dispatch diagnostics MUST NOT
reinterpret Evidence, select a producer, or alter dependencies. Execution diagnostics MUST NOT be
misclassified as planning failures.

Every diagnostic MUST reference the relevant request, plan, graph node, Execution Unit, authority,
policy version, and immutable reason code.

## Audit

Audit MUST preserve:

- complete Planning Input Manifest and Planning Request;
- Semantic Plan content, identity, version, authority, certification, and rejected alternatives;
- complete Dispatch Request and dispatch-admission facts;
- every Dispatch Plan content, identity, version, authority, certification, and supersession;
- mapping from semantic graph nodes to Execution Intents and Execution Units;
- groups, barriers, stages, batches, windows, fences, resource classes, and policy references;
- all separated context identities and projections;
- Execution Ledger links without mutating plans;
- reasons for operational replanning;
- semantic and dispatch replay verdicts;
- evidence proving that dispatch never changed semantics.

Audit MUST distinguish intended semantics, authorized dispatch, and actual execution. It MUST NOT
collapse them into one retrospective plan.

## Migration

- Existing combined execution configurations MUST be inventoried and classified as semantic,
  dispatch, runtime-ledger, diagnostic, or prohibited hidden state.
- Producer selection, dependencies, timeframes, completeness, and context facts MUST move into the
  Semantic Plan contract conceptually before EPIP-017 certification.
- Workers, queues, batching, resources, retries, timeouts, cancellation, and cache lookups MUST
  remain dispatch concerns.
- Actual attempts, outcomes, timing, failures, and commitments MUST remain ledger concerns.
- Existing execution order MUST NOT be treated as semantic dependency without evidence under
  ADR-EPIP017-04.
- Existing operational availability MUST NOT select producers or optional dependencies.
- Shadow comparison MUST verify Semantic Plan equality separately from Dispatch Plan and execution
  behavior.
- Serial legacy behavior MAY serve as a reference Dispatch Plan only after semantic intent is
  independently reconstructed and certified.
- Migration divergence, rollback, and legacy retirement MUST follow ADR-EPIP017-16.

## Backward Compatibility

This ADR changes no production plan, scheduler, execution engine, producer, public API, EPIP-016
contract, Replay behavior, EventBus behavior, financial calculation, risk rule, portfolio behavior,
execution behavior, or serialization format.

Semantic Plan and Dispatch Plan are EPIP-017 architectural artifacts. They MUST NOT be inserted
into frozen EPIP-016 Decision contracts. The future handoff MAY reference the Semantic Plan's
evidence-set provenance through ADR-EPIP017-15 without exposing dispatch concerns.

Legacy execution MAY continue during governed migration. No legacy configuration is automatically
classified as a conforming plan.

Historical plan artifacts MUST remain interpretable under their original schema and policy
versions. New plan versions MUST NOT reinterpret prior identities.

## Forbidden Behaviours

EPIP-017 MUST NEVER permit:

1. Scheduler or worker behavior changing semantic intent.
2. Planner allocation of workers, threads, queues, batches, retries, cache entries, or resources.
3. Dispatch creation, removal, substitution, or reinterpretation of dependencies.
4. Dispatch modification or creation of Evidence semantics.
5. Dispatch change of producer or capability selection.
6. Dispatch modification of Semantic Context or temporal semantics.
7. Runtime semantic planning or semantic-plan mutation.
8. Dynamic dependency discovery.
9. Execution-driven producer or optional-dependency selection.
10. Cache hit or miss changing semantic meaning.
11. Resource failure causing semantic fallback without a new Semantic Plan.
12. Retry or timeout outcome written into a Semantic Plan.
13. Mutable worker or queue state written into a Dispatch Plan.
14. Operational groups or stages used as hidden semantic edges.
15. Barrier evaluation inventing a conditional dependency.
16. Runtime output reopening semantic resolution.
17. Operational telemetry becoming producer analytical input.
18. One universal plan containing both immutable intent and mutable runtime facts.
19. In-place plan amendment.
20. Retrospective rewriting of intended plans to match actual execution.
21. Decision, Candidate, Confidence, risk decision, or execution instruction added to either plan.

Any forbidden behavior SHALL be an architecture and certification failure and MUST fail closed.

## Alternatives Considered

### One mutable execution plan

One object contains semantics, scheduling, cache state, retries, workers, and runtime outcomes.

Rejected because operational volatility would mutate meaning and destroy deterministic replay and
audit.

### One immutable plan with all operational decisions frozen

One immutable artifact contains semantics, cache decisions, workers, retry counts, and resources.

Rejected because cache, worker, and failure state cannot be guaranteed to remain valid. The plan
would become stale or require undocumented side state.

### Runtime planner controlled by the scheduler

The scheduler adjusts producers, dependencies, and Evidence requirements in response to runtime
conditions.

Rejected because execution would become the semantic authority and could not be replayed or
certified independently.

### Semantic Plan plus mutable scheduler state only

Semantics are frozen, but operational authorization exists only as mutable scheduler internals.

Rejected because dispatch strategy, barriers, resources, retries, and fences would be unauditable
and unreproducible.

### Immutable Semantic Plan, immutable Dispatch Plan, append-only Execution Ledger

Meaning, authorized operational strategy, and actual runtime facts remain separate.

Accepted because each artifact has one authority, identity, lifecycle, replay meaning, and
certification boundary.

## Decision

EPIP SHALL adopt the Semantic Plan, Dispatch Plan, Execution Intent, Execution Unit, Group,
Barrier, Stage, Batch, Window, Fence, separated context, identity, versioning, certification,
determinism, replay, diagnostic, audit, migration, compatibility, and prohibition rules in this ADR
as the constitutional separation between meaning and execution.

No scheduler, worker, retry, timeout, cache, resource, or runtime outcome MAY change an accepted
Semantic Plan. No planner MAY decide worker topology or operational outcomes. Every actual runtime
fact SHALL remain outside both plans in the authoritative Execution Ledger.

## Consequences

### Positive

- Semantic intent remains stable across serial, parallel, cached, retried, and recovered execution.
- Cache or worker volatility cannot change producer selection or dependency meaning.
- Operational replanning remains auditable without semantic mutation.
- Replay can distinguish semantic reconstruction from dispatch reproduction.
- Context leakage between meaning, scheduling, operations, and diagnostics is prohibited.
- Planner, scheduler, result commitment, and audit receive precise authority boundaries.
- Future deployment changes do not require semantic-plan changes.

### Negative

- EPIP must retain and correlate more than one plan artifact plus a ledger.
- Operational policy changes create new Dispatch Plan identities.
- Implementations cannot hide scheduling decisions inside runtime state.
- Certification must test both plan kinds and their separation.
- Some failure recovery requires explicit operational replanning rather than mutation.

### Trade-offs

EPIP accepts additional artifacts and governance in exchange for preventing execution conditions
from silently redefining analytical meaning.

## Non-goals

This ADR does not define:

- implementation classes, APIs, interfaces, plan formats, schedulers, queues, workers, or stores;
- invocation state transitions, leases, attempt fencing implementation, or atomic result commit;
- producer analytical logic;
- detailed determinism profiles or digest algorithms;
- cache retention, lookup, reuse, or invalidation implementation;
- replay algorithms;
- retry, timeout, fallback, or recovery algorithms;
- parallel execution safety, fairness, backpressure, or worker topology;
- EPIP-016 handoff representation;
- trading, Decision, Candidate, Confidence, risk, portfolio, execution, or financial logic.

These exclusions MUST be resolved by their mandatory ADRs and MUST NOT be delegated to code.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 through ADR-EPIP017-05 and the frozen EPIP-016 and
H001–H007 architecture.

It creates or confirms mandatory dependencies on:

- ADR-EPIP017-07 for invocation lifecycle, Execution Ledger, attempt identity, leases, fences,
  cancellation, and atomic result commitment;
- ADR-EPIP017-08 for semantic, dispatch, output, replay, and operational determinism profiles;
- ADR-EPIP017-09 for Semantic Plan, Dispatch Plan, Execution Intent, context, fence, and ledger
  identities and digest hierarchy;
- ADR-EPIP017-10 for durable-result and cache lookup authorization without semantic mutation;
- ADR-EPIP017-11 for semantic replay, dispatch replay, equivalent dispatch, and operational
  reproduction;
- ADR-EPIP017-12 for immutable preservation and resumability of plan and ledger state;
- ADR-EPIP017-13 for retry, timeout, cancellation, failure, fallback, and operational replanning;
- ADR-EPIP017-14 for worker isolation, barriers, fairness, backpressure, and serial/parallel
  equivalence;
- ADR-EPIP017-15 for terminal evidence-set completeness and EPIP-016 handoff;
- ADR-EPIP017-16 for migration, plan divergence, rollback, and legacy retirement;
- ADR-EPIP017-17 for separated semantic, dispatch, execution, and
  diagnostic telemetry;
- ADR-EPIP017-18 for resource classes, plan limits,
  dispatch admission, and bounded graph expansion.

No new ADR family is introduced. This ADR makes the Execution Ledger dependency on ADR-07 explicit
and makes a complete context-projection model mandatory across ADR-06, ADR-07, ADR-09, and
ADR-EPIP017-17.

## Future Evolution

Future schedulers, worker models, distributed deployments, accelerators, queues, and resource
policies MAY create new Dispatch Plan schemas or policies without altering Semantic Plan meaning,
provided all equivalence and certification rules remain satisfied.

Future semantic planning capabilities MAY evolve through new immutable Semantic Plan schema and
policy versions. Historical plans MUST remain interpretable and MUST NOT be reclassified in place.

Adaptive scheduling MAY react to ledger facts only by selecting actions already authorized by the
current Dispatch Plan or by creating a new Dispatch Plan for the same unchanged Semantic Plan. It
MUST never become adaptive semantic planning.

Dynamic semantic graphs, iterative planning, streaming expansion, and execution-dependent
dependencies remain unsupported and require new ADRs.

## Approval Gate

Approval of this ADR resolves planning ambiguity and context leakage between semantic planning and
operational dispatch only.

It does not approve a planner, Dispatch Planner, scheduler, worker, queue, context object, plan
format, ledger, retry mechanism, cache, replay engine, or Programme A.

EPIP-017 implementation remains prohibited until the complete mandatory ADR set is accepted and
the remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
