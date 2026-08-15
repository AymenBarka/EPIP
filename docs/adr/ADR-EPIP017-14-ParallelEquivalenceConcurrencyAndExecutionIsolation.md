# ADR-EPIP017-14 — Parallel Equivalence, Concurrency and Execution Isolation

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-13 are approved, frozen, and normative. This ADR MUST NOT
modify their authority, planning, execution, determinism, replay, preservation, or recovery
contracts. No implementation, scheduler, runtime, algorithm, or Programme A activity is authorized.

## Executive Summary

Parallelism in EPIP-017 SHALL be an operational optimization only. Work MAY execute concurrently
only when the frozen Semantic Plan and an authorized Dispatch Plan prove its independence, define
its isolation boundary, and place it within an identified Execution Group and Execution Window.
Absence of a declared dependency SHALL NOT alone prove independence.

Parallel and reference serial executions SHALL produce the same authoritative semantic outcome,
dependency satisfaction, failure disposition, and unique Commit under the applicable determinism
profile. Physical timing, placement, and interleaving MAY differ only where the selected
equivalence relation permits them. Scheduler observations SHALL never create semantics or
authority.

Every concurrent Attempt SHALL have isolated identity, context, mutable working state, lease,
fence, token, ledger stream, diagnostics, and cache interaction. Shared mutable analytical state
and ambient communication are forbidden. Downstream authority SHALL arise only after an explicit
Barrier Authority verifies committed inputs against a canonical barrier predicate.

Speculative execution MAY occur only under prior bounded authority. Its results remain candidates
until the normal fenced atomic Commit path accepts exactly one. Every race SHALL resolve at an
authoritative boundary, preserve all competing facts, and remain independent of thread arrival
order.

## Purpose

This ADR establishes the constitutional concurrency model governing serial, concurrent, parallel,
independent, dependent, speculative, retried, and recovered execution. It defines isolation,
groups, stages, barriers, windows, ordering, races, authority, equivalence, determinism, replay,
diagnostics, audit, migration, and certification.

## Problem Statement

Unconstrained concurrency can turn scheduling into hidden business logic. Thread completion order
can alter dependencies, select a result, hide a failure, release downstream work early, corrupt a
cache, reuse authority, or produce a parallel outcome different from the serial architecture.

The risks include hidden shared mutable state; false independence; duplicate or stale commits;
cancel-versus-commit ambiguity; barrier and window bypass; nondeterministic failure precedence;
cross-attempt diagnostics contamination; unsafe speculative results; and replay that cannot explain
the authoritative order. A frozen contract must define equivalence by architectural observation,
not by physical interleaving.

## Architectural Context

ADR-EPIP017-04 and ADR-EPIP017-05 define semantic and temporal dependencies. ADR-EPIP017-06
separates immutable Semantic Plans from operational Dispatch Plans and introduces groups, stages,
barriers, windows, and fences. ADR-EPIP017-07 governs Attempt isolation, leases, fences, tokens,
atomic Commit, and race authority. ADR-EPIP017-08 defines equivalence profiles; ADR-EPIP017-09
governs identity and canonical ordering. ADR-EPIP017-10 prevents cache authority. ADR-EPIP017-11
governs replay. ADR-EPIP017-12 governs concurrent preservation boundaries. ADR-EPIP017-13 governs
failure, Retry, and Recovery.

This ADR specializes concurrency without redefining those contracts. ADR-EPIP017-15 SHALL govern
handoff; ADR-EPIP017-16 SHALL govern migration and compatibility.

## Definitions

### Concurrency

The condition in which two or more execution lifetimes overlap or may advance without a total
physical order. Concurrency SHALL NOT imply independence or permission to run in parallel.

### Serial Execution

Execution under a declared canonical total order consistent with every semantic dependency,
barrier, authority, and temporal constraint. It SHALL serve as the reference execution where a
parallel-equivalence claim requires one.

### Parallel Execution

Authorized concurrent advancement of explicitly independent Execution Units. Parallel execution
SHALL preserve the applicable serial semantics.

### Independent Execution

Execution Units proven not to consume one another's outputs, mutable state, authority, side
effects, ordering, temporal closure, failure disposition, or undeclared resource outcome.
Independence SHALL be a plan fact with evidence and scope.

### Dependent Execution

Execution whose admissibility or meaning depends on another unit's committed result, authoritative
absence, lifecycle fact, temporal closure, or barrier disposition. Dependent work MUST NOT receive
downstream authority before satisfaction.

### Speculative Execution

Bounded execution started before it is known which of several equivalent candidates will be
needed or commit-eligible. It carries no special result authority.

### Execution Isolation

The enforced separation of analytical state, authority, identity, ledger attribution, cache
interaction, diagnostics, and side effects between concurrent execution scopes.

### Concurrency Boundary

The closed set of units, dependencies, authority domains, shared immutable inputs, isolation
requirements, and observable outcomes within which concurrency is authorized.

### Execution Group

An immutable Dispatch Plan grouping of Execution Units sharing an explicit concurrency,
exclusion, speculation, resource, or failure-domain policy. Membership creates no semantic
dependency.

### Execution Stage

An operational partition whose units MAY become eligible under the same declared predecessor
barriers. Stage membership neither proves simultaneity nor creates global synchronization.

### Execution Barrier

An immutable, identified readiness predicate over committed results, authoritative absence,
terminal lifecycle facts, or governed operational conditions. A Barrier never creates Evidence
semantics.

### Execution Window

An identified operational admission interval expressed in governed logical time. It SHALL NOT be
Evidence Validity Time, Knowledge Time, or timeframe closure.

### Execution Dependency

An explicit semantic or operational ordering edge. Its type, source, target, predicate, authority,
and lineage SHALL be declared.

### Execution Ordering

The canonical partial order derived from dependencies, barriers, windows, lifecycle authority, and
Commit facts. Physical scheduling order SHALL not replace it.

### Execution Fence

The monotonic, scoped stale-authority exclusion contract frozen by ADR-EPIP017-07. This ADR does
not create a second fence concept.

### Parallel Authority

The authority permitted to admit an eligible Execution Group for concurrent execution under one
Dispatch Plan. It SHALL NOT create semantic independence, execution tokens, barrier completion, or
Commit authority.

### Execution Equivalence

The declared relation by which two executions preserve all required semantic, operational,
authority, diagnostic, and certification observations under ADR-EPIP017-08.

## Concurrency Model

Every concurrent scope SHALL declare its boundary, plan identities, units, independence proofs,
maximum authority scope, isolation class, barriers, windows, failure domain, equivalence profile,
and canonical observation order.

Only explicitly independent work MAY execute concurrently. Independence SHALL require proof that:

- no semantic or temporal dependency connects the units;
- each unit consumes only immutable, committed, or separately isolated inputs;
- neither unit observes the other's provisional result, progress, diagnostics, cache mutation, or
  mutable runtime state;
- authority, cancellation, Retry, and Recovery scopes cannot leak between units;
- external side effects are absent or separately governed and non-conflicting;
- numeric aggregation or reduction has a certified canonical rule; and
- failure of one unit has a deterministic declared effect on the other.

Unknown or incomplete independence SHALL require serial execution or an explicit barrier.
Resource coexistence, different producers, separate threads, or lack of a graph edge alone SHALL
NOT prove independence.

Dependent units MAY be physically prepared concurrently, but execution authority for dependency-
consuming work SHALL remain withheld until its barrier completes.

## Parallel Execution Model

Parallel admission SHALL require an accepted Semantic Plan, authorized Dispatch Plan, valid group
and window, satisfied predecessor barriers, eligible Invocations, available isolation, and a
declared equivalence profile. Each unit SHALL enter the ordinary Attempt lifecycle independently.

Parallel execution SHALL NOT change producer selection, Evidence requirements, context,
timeframes, absence semantics, dependency meaning, canonical result ordering, failure precedence,
or handoff obligations. A required reduction SHALL define canonical membership, ordering, numeric
profile, missing-member disposition, and failure behavior before execution.

Parallel capacity, fairness, and placement MAY affect start time but MUST NOT affect semantic
eligibility or authority. Starvation prevention policy SHALL be explicit and operational; it SHALL
not invent priority semantics.

## Isolation Model

Each concurrent Attempt SHALL have isolated:

- immutable Invocation and context projection;
- mutable working memory and producer instance state;
- Attempt identity, lease, fence, token, and ownership;
- provisional output and commit candidacy;
- ledger attribution and causal sequence;
- diagnostic, metric, and trace namespace;
- cache lookup and publication transaction; and
- cancellation, timeout, failure, Retry, and Recovery scope.

Concurrent units MAY share only immutable, identity-verified inputs or explicitly governed
read-only services. Hidden shared mutable state, process globals, mutable singletons, ambient
randomness, cross-attempt callbacks, and unrecorded communication are forbidden.

Cache hits SHALL return verified immutable result references. Concurrent cache population SHALL
not select authority, alter identity, or expose partial entries. Ledger facts MAY share physical
storage but SHALL retain isolated attribution and a canonical causal order. Diagnostics MAY be
aggregated only after preserving their originating identities and MUST NOT become communication
between Attempts.

Isolation failure SHALL revoke affected authority, quarantine provisional outputs, preserve facts,
and invoke ADR-EPIP017-13 disposition. It SHALL NOT be repaired by accepting apparent value
equivalence.

## Execution Groups

An Execution Group SHALL bind group identity, Dispatch Plan, members, group type, concurrency
limit, isolation class, barriers, window, failure policy, speculation policy, and equivalence
profile. Membership and policy SHALL be immutable.

Group types MAY express parallel-independent, serial-exclusive, bounded-concurrent, speculative-
equivalent, or recovery-isolated execution. A unit MAY belong to multiple descriptive groups only
when the effective intersection of constraints is explicit and deterministic.

Stages SHALL describe operational admission phases. A stage SHALL not wait for unrelated units
unless an explicit Barrier requires them. Group or stage completion MUST NOT substitute for
individual Commit or authoritative absence facts.

## Execution Barriers

### Creation and Authority

Every Barrier SHALL be created in an immutable Dispatch Plan and reference the Semantic Plan facts
it operationalizes. Barrier Authority alone MAY evaluate and publish barrier disposition. A
scheduler or worker SHALL NOT self-release a barrier.

### Completion

A Barrier SHALL complete only when its canonical predicate is satisfied by authoritative committed
references, governed absence, or explicitly permitted terminal facts. Provisional, cached-only,
physically completed, speculative, late, or uncommitted output SHALL NOT satisfy it.

Completion SHALL bind Barrier identity, input identities, predicate version, evaluation boundary,
logical time, authority, and digest. It SHALL be immutable. Re-evaluation after changed facts SHALL
create a new barrier disposition or new plan as governed; it SHALL NOT rewrite completion.

### Visibility and Failure

Downstream execution authority SHALL not exist before completion is authoritative and visible.
Visibility SHALL be atomic for all consumers of the same barrier scope.

Barrier failure SHALL identify unsatisfied members, causal failures, cancellations, expirations,
revocations, and policy disposition. It MAY cause isolation, fail-fast, fail-safe, Retry, Recovery,
or Replanning requests under ADR-EPIP017-13, but SHALL authorize none implicitly.

### Lineage

Barrier lineage SHALL preserve plan, dependency, group, input, evaluation, completion, failure,
supersession, replay, and migration identities. A new plan SHALL create new Barrier identity.

## Execution Windows

Every Window SHALL bind identity, Dispatch Plan, eligible units, logical opening and closing
predicates, authority, policy version, and visibility. Opening permits admission evaluation; it
does not grant Attempt authority. Closure prohibits new admission and SHALL define disposition of
already admitted work.

Window extension, reopening, narrowing, or policy change SHALL create a new immutable operational
fact and, where Dispatch semantics change, a new Dispatch Plan. Wall-clock drift or worker-local
time SHALL NOT redefine the Window.

Window visibility SHALL be consistent for all covered admission decisions. Work starting outside
its Window or continuing contrary to its closure policy SHALL be rejected, cancelled, expired, or
superseded according to authoritative policy and recorded as a Window violation.

## Speculative Execution

Speculation SHALL be admissible only when the Dispatch Plan identifies equivalent candidates,
bounds their number and resources, proves isolation, defines cancellation and discard policy,
declares selection predicates, and preserves one semantic obligation.

Each speculative Attempt SHALL have separate identity, lease, fence, token, result, diagnostics,
and ledger lineage. No candidate SHALL gain priority from physical completion alone unless that
rule is explicitly authorized and deterministic under the equivalence profile.

Only normal Commit Authority MAY accept a speculative result. After one Commit, every competing
candidate SHALL lose commit authority and become cancelled, superseded, rejected, or archived as
appropriate. Discard SHALL mean exclusion from authority and governed retention; it SHALL NOT erase
execution history or required diagnostics.

Speculation MUST NOT be used to try alternative semantic interpretations, producers, timeframes,
or dependencies unless those alternatives already exist in the same Semantic Plan with certified
equivalence.

## Execution Equivalence

Parallel execution MUST produce the same authoritative result as its equivalent canonical serial
execution under the selected profile. Matching terminal values alone is insufficient.

### Strict Equivalence

Strict equivalence SHALL require identical canonical semantic artifacts, result content, metadata,
diagnostics, ordering, dependency satisfaction, barrier dispositions, and digests. Physical trace
facts MAY differ only when explicitly excluded from the strict comparison domain.

### Semantic Equivalence

Semantic equivalence SHALL require identical Semantic Plan obligations, Evidence meaning and
values, provenance, temporal interpretation, completeness, semantic diagnostics, dependency
outcomes, canonical ordering, and handoff eligibility. Worker, Attempt, timing, and equivalent
Dispatch identities MAY differ.

### Operational Equivalence

Operational equivalence SHALL require the same authorized lifecycle semantics, failure categories,
Retry and Recovery dispositions, barrier outcomes, unique Commit, cancellation-race resolution,
and canonical ledger projection. Physical placement and permitted interleaving MAY differ.

### Certification Equivalence

Certification equivalence SHALL require identical certification-relevant facts and verdicts,
including isolation, race, barrier, Window, speculation, failure, recovery, replay, and digest
evidence. Semantically equal executions with forbidden operational variability SHALL fail
certification equivalence.

Every comparison SHALL identify reference serial order, complete input manifest, profiles,
observables, exclusions, and canonical comparison rules. Failed, cancelled, empty, degraded,
retried, recovered, and speculative outcomes SHALL participate.

## Race Conditions

All races SHALL resolve at an identified authoritative serialization boundary and preserve every
competing request and rejected fact.

- **Commit race:** ADR-EPIP017-07 Commit Authority SHALL accept at most one eligible result by
  Invocation identity and fence generation; arrival order alone has no authority.
- **Cancel versus Commit:** one atomic terminal boundary SHALL decide. Late cancellation cannot
  reverse Commit; late completion cannot bypass prior cancellation.
- **Retry versus Commit:** Retry authorization SHALL revalidate absence of Commit. A subsequent
  Commit SHALL revoke or supersede unused or competing commit authority as governed.
- **Lease expiration:** post-expiration work is stale. New ownership requires a higher fence and
  cannot validate the old result.
- **Duplicate completion:** duplicate submission SHALL be idempotently identified, rejected, or
  quarantined without creating a second lifecycle or Commit fact.
- **Late completion:** completion after cancellation, expiry, supersession, Window closure policy,
  or Commit SHALL remain visible but non-authoritative.
- **Barrier violation:** downstream work admitted before authoritative completion SHALL lose
  authority and its outputs SHALL be quarantined.
- **Window violation:** admission or continuation outside policy SHALL be rejected or terminated
  without changing semantic meaning.
- **Failure observation race:** category and causal precedence SHALL derive from authoritative
  logical facts, not observer arrival.

## Authority Model

- Planning Authority SHALL declare dependencies and independence; Parallel Authority SHALL not.
- Dispatch Authority SHALL define groups, stages, barriers, windows, and speculation policy.
- Parallel Authority SHALL admit eligible concurrent scopes without granting Attempt authority.
- Barrier Authority SHALL publish barrier disposition without creating source facts.
- Window Authority SHALL publish opening and closure facts without creating semantic time.
- Lease, Fence, Token, Cancellation, Retry, Recovery, and Commit Authorities retain their frozen
  responsibilities.
- Scheduler and workers SHALL execute authorized work but MUST NOT define semantics, equivalence,
  readiness, or authoritative race winners.
- Audit and Certification Authorities SHALL verify without mutating execution.

Technical ownership, resource allocation, data possession, or first observation SHALL not imply
authority. Shared authority state SHALL be immutable or accessed only through its competent
authoritative boundary; mutable authority replication without a certified consistency contract is
forbidden.

## Concurrency Invariants

1. Parallelism is an operational optimization and never changes architectural meaning.
2. Only explicitly proven independent work executes concurrently.
3. Absence of a dependency edge alone never proves independence.
4. Parallel execution preserves applicable serial equivalence.
5. Scheduling never creates semantics or authority.
6. Concurrent Attempts share no hidden mutable state.
7. Identity, authority, provisional output, ledger, cache, and diagnostics remain isolated.
8. Downstream authority never precedes authoritative Barrier completion.
9. Barriers consume committed or otherwise authoritative facts only.
10. Window opening does not itself grant execution authority.
11. Commit remains unique across serial, parallel, speculative, retried, and recovered execution.
12. Execution history is immutable and parallelism never rewrites it.
13. Speculative execution never bypasses normal Commit.
14. Physical completion order never determines semantic ordering.
15. Late or duplicate output never gains authority accidentally.
16. Failure propagation and isolation are deterministic.
17. Parallel reduction uses certified canonical semantics.
18. Replay observes concurrency without activating it.
19. Recovery reacquires isolated authority and preserves equivalence.
20. Unknown equivalence requires serial execution or rejection.

## Determinism

Concurrency decisions SHALL derive from immutable plans, manifests, policies, profiles, logical
time, and authoritative facts. Enumeration order, hash order, thread scheduling, network latency,
worker discovery, queue order, cache arrival, or physical completion SHALL NOT affect semantic or
authority outcomes.

Canonical ordering SHALL govern dependency readiness, barrier inputs, failure precedence,
reductions, diagnostics, ledger projection, and comparison. Permitted variability SHALL be named
by ADR-EPIP017-08 profile and excluded only from the appropriate equivalence domain.

If an operation is not associative, commutative, numerically stable, or otherwise parallel-safe
under its profile, it SHALL use a canonical serial order or a certified deterministic reduction.
Unproven numeric equivalence SHALL fail closed.

## Replay Compatibility

Replay SHALL preserve plans, groups, stages, barriers, windows, Attempts, leases, fences, tokens,
race requests, canonical authority order, failures, diagnostics, and Commit facts. Operational
Replay MAY reproduce recorded concurrency decisions but MUST NOT require identical physical
interleaving unless its profile expressly includes it.

Historical Replay SHALL use original policies and knowledge boundaries. Certification Replay SHALL
compare serial and parallel campaigns. Diagnostic Replay MAY explore alternative interleavings as
counterfactual non-authoritative observations. Replay SHALL NOT open a Window, release a production
Barrier, acquire authority, mutate ledgers, or Commit.

## Recovery Compatibility

Recovery SHALL establish a new concurrency boundary, revalidate independence and barriers, and
acquire new Attempts, leases, fences, and tokens. A Checkpoint MAY preserve group and frontier
facts but SHALL not restore active concurrency, scheduler state, locks, barriers as newly complete,
or authority.

Committed work MAY satisfy recovered barriers only after identity and integrity verification.
Ambiguous in-flight work SHALL be recomputed, rejected, or isolated under ADR-EPIP017-13. Recovery
MUST preserve the same semantic and operational equivalence obligations; changed semantics require
Replanning.

## Diagnostics

Diagnostics SHALL distinguish parallel divergence, false independence, unexpected dependency,
isolation breach, shared-state access, authority leakage, ledger contamination, cache contamination,
diagnostic contamination, barrier violation, premature release, Window violation, execution race,
duplicate execution, duplicate or late completion, stale-fence execution, equivalence failure,
speculation rejection, nondeterministic reduction, and serial-reference mismatch.

Each diagnostic SHALL bind plan, group, unit, Attempt, barrier, Window, profiles, expected and
observed facts, canonical order, authority, scope, severity, and disposition. Diagnostics SHALL not
release barriers, cancel work, select winners, retry, recover, or Commit automatically.

## Audit

Audit SHALL preserve concurrency admission; independence evidence; groups, stages, barriers, and
windows; isolation declarations and violations; every Attempt and authority; scheduling
observations; canonical causal order; provisional and committed outcomes; races and losing facts;
speculation and discard; failures, retries, recovery, cancellation, and late work; equivalence
comparisons; diagnostics; policies; profiles; migrations; and certification evidence.

Audit SHALL distinguish physical order from authoritative order, eligibility from admission,
completion from Commit, and discard from erasure. It SHALL explain why different interleavings are
equivalent or why equal terminal values are not.

## Certification Rules

Certification SHALL prove at minimum:

1. Independence is explicit, closed, and complete.
2. Hidden shared mutable state and authority communication are absent.
3. Serial and parallel executions satisfy every claimed equivalence relation.
4. Barriers never release from provisional or uncommitted state.
5. Window boundaries are authoritative and deterministic.
6. Parallel reductions preserve certified canonical results.
7. Commit remains unique in real race campaigns.
8. Cancel/Commit, Retry/Commit, expiration, duplicate, late, and barrier races resolve correctly.
9. Speculative Attempts never gain exceptional authority.
10. Cache, ledger, and diagnostics remain isolated.
11. Failure and Recovery preserve serial/parallel equivalence.
12. Replay reproduces authoritative concurrency without production mutation.
13. Distributed or multi-worker execution does not weaken fences or visibility.
14. Migration does not infer independence or equivalence.

Certification SHALL include repeated adversarial stress campaigns with varied interleavings,
failures, delays, duplicates, partitions, cancellation, Retry, and Recovery. Nominal parallel tests
alone are insufficient. Failure SHALL prohibit the affected concurrency mode or profile.

## Migration

Legacy execution SHALL be classified as serial, explicitly parallel, incidentally concurrent,
speculative, or ambiguous. Migration SHALL preserve original traces and authority facts and SHALL
not infer independence from apparent success or different worker identity.

Parallel legacy paths require evidence of isolation, barriers, windows, unique Commit, failure
ordering, and serial equivalence. Missing evidence SHALL restrict the path to serial execution,
diagnostic replay, or quarantine. Migrated groups, barriers, windows, and profiles SHALL receive
new identities and lineage; history SHALL not be rewritten.

ADR-EPIP017-16 SHALL govern compatibility epochs, transition, rollback, deprecation, and migration
certification.

## Backward Compatibility

This ADR SHALL NOT modify EPIP-016, its Decision Framework, Kernel, Replay, EventBus, financial
engines, execution, serialization, public APIs, or released behavior. EPIP-016 SHALL observe only
the certified handoff artifact defined by ADR-EPIP017-15, never parallel intermediate state.

Serial EPIP-017 execution remains valid and SHALL be the safe fallback when parallel admissibility
or equivalence cannot be proven. Existing contracts remain unchanged; concurrency support is
additive and MUST pass the same semantic and authority path.

## Forbidden Behaviours

The following are forbidden:

1. Scheduler-defined semantics, dependency, readiness, or winner selection.
2. Shared mutable analytical or authority state.
3. Parallel history rewriting or deletion of losing Attempts.
4. Implicit dependency or independence creation.
5. Parallel Commit replacement or more than one authoritative Commit.
6. Speculative authority outside the normal Attempt and Commit path.
7. Barrier or Window bypass.
8. Execution without declared isolation.
9. Downstream consumption of provisional, cached-only, or physically completed output.
10. Completion order defining semantic order or failure precedence.
11. Cross-attempt lease, fence, token, context, cache, ledger, or diagnostic reuse.
12. Treating equal terminal values as sufficient equivalence.
13. Hiding late, duplicate, rejected, cancelled, or speculative execution.
14. Restoring active concurrency or authority from a Checkpoint.
15. Claiming parallel safety for an uncertified reduction.

## Alternatives Considered

### Scheduler Determines Safe Parallelism Dynamically

Rejected. Runtime observation cannot create semantic independence and makes behavior dependent on
mutable topology and timing.

### Shared Mutable Context with Locks

Rejected. Locks serialize access but do not prove semantic isolation, deterministic ordering, or
authority separation.

### First Completion Wins

Rejected. Arrival order is not semantic authority and is unstable across execution environments.

### Terminal Value Equality Defines Equivalence

Rejected. It ignores provenance, diagnostics, failures, ordering, authority, barriers, and handoff.

### Disable All Parallelism

Rejected as the institutional target. Serial execution is safe but cannot meet future scale needs;
explicit independence and certification permit optimization without semantic change.

### Plan-Proven Parallelism with Isolated Attempts and Authoritative Barriers

Accepted. It makes parallelism optional, auditable, replayable, deterministic, and equivalent to
the canonical serial architecture.

## Decision

EPIP-017 SHALL authorize parallel execution only for explicitly proven independent work described
by immutable plans and bounded by identified groups, barriers, windows, isolation, and equivalence
profiles.

Every concurrent unit SHALL retain separate execution authority and state. Barrier completion and
atomic Commit SHALL remain the only authoritative publication boundaries. Physical scheduling and
interleaving SHALL never change architectural meaning.

Unproven independence, isolation, ordering, or equivalence SHALL require serial execution or
rejection. No future scheduler, worker runtime, distributed executor, recovery mechanism, or
optimization MAY weaken this rule.

## Consequences

### Positive

- CF-02 receives a testable constitutional resolution.
- Serial execution remains a stable reference and safe fallback.
- Parallel speed cannot change Evidence semantics or Commit authority.
- Races, barriers, windows, speculation, and failures become auditable.
- Hidden communication and provisional-result leakage are forbidden.
- Local and distributed runtimes can share one equivalence contract.

### Negative

- Independence proofs, isolation, canonical reductions, and stress certification are costly.
- Some apparently parallel work must remain serial.
- Ledger, diagnostic, and race evidence retention increases operational volume.
- Barrier authority may add latency.
- Distributed implementations require stronger consistency evidence.

### Trade-offs

EPIP accepts lower maximum opportunistic concurrency and higher certification cost to preserve
determinism, unique authority, replayability, and ten-year maintainability.

## Compatibility

Concurrency compatibility SHALL name group, barrier, Window, isolation, failure, reduction,
Dispatch, determinism, and equivalence profile versions. Runtime or schema compatibility alone is
insufficient. A change affecting independence, ordering, readiness, winner selection, or observable
equivalence SHALL create new versioned policy and require recertification.

## Non-goals

This ADR does not define thread pools, processes, queues, workers, scheduler algorithms, fairness
algorithms, backpressure mechanisms, distributed consensus, lock implementations, transport,
resource sizing, performance targets, or production code. It defines no producer, trading,
financial, risk, Decision, or execution logic.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 through ADR-EPIP017-13. ADR-EPIP017-15 SHALL consume
only barrier-complete committed Evidence and MUST NOT redefine concurrency. ADR-EPIP017-16 SHALL
govern concurrency-profile migration and MUST NOT infer missing independence or equivalence.

No new blocking ADR dependency is introduced. ADR-EPIP017-18 governs capacity and resource
admission. Future distributed-consistency ADRs MAY specialize deployment but SHALL preserve this
contract.

## Future Evolution

Distributed execution, deterministic partitioning, content-addressed work sharing, hardware
acceleration, adaptive bounded concurrency, remote attestation, and multi-region barriers MAY
evolve through versioned profiles and additional ADRs. They SHALL preserve plan-proven independence,
isolated authority, canonical ordering, unique Commit, immutable history, and certified serial
equivalence.

## Approval Gate

Approval of this ADR resolves CF-02, Parallel Execution, Concurrency, Parallel Equivalence,
Execution Isolation, barriers, windows, speculation, and architectural race treatment only.

It does not approve a scheduler, runtime, distributed system, handoff, migration governance, or
Programme A. EPIP-017 implementation remains prohibited until all mandatory ADRs are accepted and
an independent review grants **APPROVED AS FROZEN ARCHITECTURE**.
