# ADR-EPIP017-13 — Failure, Retry and Recovery Contract

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-12 are approved, frozen, and normative. This ADR MUST NOT
modify their system boundary, producer, Evidence, temporal, plan, execution, determinism,
identity, storage, replay, or preserved-state contracts.

This ADR defines failure, retry, recovery, compensation, and replanning architecture only. It
authorizes no implementation, algorithm, engine, placeholder, or Programme A activity.

## Executive Summary

EPIP-017 SHALL treat every unsuccessful execution condition as an immutable, typed, attributable
architectural fact. Failure SHALL NOT be inferred solely from missing output or wall-clock delay.
Cancellation, timeout, expiration, revocation, rejection, abort, and supersession SHALL remain
distinct dispositions with distinct authorities and causal records.

A **Retry** is an explicitly authorized new Execution Attempt for the same immutable Invocation,
Semantic Plan, Evidence obligations, temporal meaning, and semantic inputs. A Retry MUST acquire a
new Attempt identity, lease, fence, and token. It MUST NOT erase, replace, reopen, or mutate any
prior Attempt.

A **Recovery** is an explicitly authorized continuity process after disruption. It SHALL declare a
Recovery Boundary and MAY restore an admissible Checkpoint, reuse verified committed work, or
recompute governed state. Recovery SHALL create new operational identities and SHALL preserve the
original semantic authority. A Snapshot SHALL never be a recovery source. Only the standard
fenced, atomic Commit path MAY publish a recovered result.

**Replanning** is neither Retry nor Recovery. Any change to producer selection, Evidence
requirements, dependency semantics, temporal meaning, context, absence rules, or other semantic
intent SHALL create a new Semantic Plan and new lineage. **Compensation** is a new, visible,
authorized action addressing an external consequence; it SHALL NOT roll back history or fabricate
transactional reversal.

No retry, recovery, compensation, or replan SHALL be implicit. Policy may make a request
deterministically, but the competent authority SHALL record a separate authorization decision.

## Purpose

This ADR establishes the constitutional failure model for EPIP-017. It SHALL define:

- the meaning, classification, ownership, authority, and lifecycle of failure;
- the distinction between failure and cancellation, timeout, expiration, revocation, rejection,
  abort, and supersession;
- Retry eligibility, authority, identity, scope, lineage, limits, and exhaustion;
- Recovery source, boundary, admissibility, state, authority, and continuity;
- Compensation visibility and non-rewriting behavior;
- the boundary between retry, recovery, redispatch, and replanning;
- deterministic fail-fast, fail-safe, and isolation dispositions; and
- replay, diagnostic, audit, migration, compatibility, and certification obligations.

## Problem Statement

Failure is where architectural boundaries are most likely to collapse. Without a frozen contract,
an orchestrator could silently repeat producer work, reuse an expired lease, restore mutable
runtime state, substitute a new dependency, mutate a Semantic Plan, hide a failed Attempt, or
present compensation as if the original effect never occurred.

Ambiguous failure handling creates additional risks:

- duplicate or conflicting commits;
- retry storms and unbounded resource consumption;
- failure propagation dependent on completion timing;
- current-state substitution during historical recovery;
- cancellation races misclassified as execution failure;
- transient infrastructure faults changing Evidence semantics;
- invalid Checkpoints being restored because they are available;
- partial results leaking across dependency barriers;
- fallback producers silently changing semantic intent; and
- replay that cannot reproduce why execution stopped or continued.

EPIP-017 therefore requires separate facts for detection, classification, policy evaluation,
authorization, execution, resolution, and audit. Operational continuity SHALL never change
semantic authority.

## Architectural Context

ADR-EPIP017-01 owns orchestration boundaries and the single authoritative path.
ADR-EPIP017-02 constrains producer behavior, failures, timeouts, and side effects.
ADR-EPIP017-03 governs producer and capability eligibility, revocation, trust, and certification.
ADR-EPIP017-04 defines dependency satisfaction and Evidence semantics. ADR-EPIP017-05 governs
temporal availability, revision, knowledge boundaries, and cross-timeframe dependencies.

ADR-EPIP017-06 freezes Semantic and Dispatch Plans and requires a new plan when their respective
facts change. ADR-EPIP017-07 defines immutable Invocations, new Attempt identities, leases, fences,
tokens, cancellation, abort, atomic Commit, and the append-only Execution Ledger.
ADR-EPIP017-08 and ADR-EPIP017-09 govern determinism, identity, canonicalization, digest, and
lineage. ADR-EPIP017-10 separates Durable Results from Cache Entries. ADR-EPIP017-11 makes replay
read-only. ADR-EPIP017-12 permits only an admissible Checkpoint—not a Snapshot—to seed recovery.

This ADR allocates failure, Retry, Recovery, Compensation, and Replanning authority without
changing those contracts. ADR-EPIP017-14 SHALL govern concurrent failure observation, barrier
resolution, parallel equivalence, and race ordering. ADR-EPIP017-15 SHALL govern the EPIP-016
handoff. ADR-EPIP017-16 SHALL govern legacy compatibility and migration.

## Definitions

### Failure

An immutable, attributable fact that a declared obligation could not be satisfied under its
governing contract, scope, boundary, authority, and policy. Failure SHALL identify the failed
obligation and MUST NOT imply Retry eligibility, cancellation, or terminal Invocation disposition.

### Failure Event

The immutable occurrence recording detection of a suspected or confirmed failure condition. A
Failure Event SHALL preserve observed facts without deciding category, blame, retry, recovery, or
resolution.

### Failure Record

The authoritative, append-only record binding Failure identity, category, scope, causal facts,
classification authority, impacted identities, lifecycle, disposition, and lineage.

### Failure Category

A normative classification describing which architectural obligation failed. Categories SHALL be
orthogonal to severity, retryability, responsibility, and terminal disposition.

### Failure Authority

The authority permitted to validate and classify Failure Events, publish Failure Records, and
record lifecycle dispositions. Failure Authority SHALL NOT self-authorize Retry, Recovery,
Compensation, Replanning, cancellation, or Commit.

### Failure Ownership

The architectural domain accountable for the failed obligation. Ownership is not human blame and
SHALL NOT be inferred from the component that observed the failure.

### Retry

An explicitly authorized new Attempt to satisfy the same immutable Invocation and Semantic Plan
after a prior Attempt did not commit. Retry SHALL preserve semantic inputs and obligations.

### Retry Request

A non-authoritative proposal to retry, binding the source failure or disposition, Invocation,
prior Attempts, policy, scope, eligibility evidence, and requested operational strategy.

### Retry Authorization

An immutable decision by Retry Authority permitting exactly one bounded new Attempt or explicitly
defined Attempt set. Authorization SHALL NOT itself execute, lease, or commit.

### Retry Eligibility

The deterministic predicate that a Retry Request satisfies all semantic, lifecycle, authority,
limit, temporal, governance, and operational preconditions. Eligibility is necessary but not
sufficient for authorization.

### Retry Identity

A domain-qualified identity binding the Retry Request, authorization decision, Invocation,
Semantic Plan, applicable Dispatch Plan, source failures, prior Attempt lineage, policy version,
limits, and scope.

### Retry Lineage

The immutable directional relation from failed or non-committed Attempts to Retry Authorization
and the newly created Attempt identities. It SHALL preserve every prior Attempt.

### Recovery

A governed continuity process that reconstructs an eligible execution path after disruption while
preserving the original semantic authority and immutable history.

### Recovery Request

A non-authoritative proposal binding the disruption, target scope, Recovery Boundary, candidate
sources, intended continuity, policy, and eligibility evidence.

### Recovery Authority

The authority permitted to admit or reject a Recovery Request and authorize a bounded recovery
operation. Recovery Authority SHALL NOT validate a Checkpoint on behalf of Checkpoint Authority,
mutate a plan, acquire execution authority, or commit a result.

### Recovery Boundary

The closed logical and causal boundary separating authoritative completed work, admissible
restorable state, work requiring recomputation, invalid or stale state, and pending obligations.

### Recovery Source

An explicitly identified authoritative or preserved artifact admitted to recovery. A source MAY be
an eligible Checkpoint, a verified committed Durable Result, an Execution Ledger frontier, or the
original immutable plan and input manifests. A Snapshot is observational and SHALL NOT be a
production Recovery Source.

### Recovery Admissibility

The deterministic verification that a proposed Recovery Boundary and every source satisfy
identity, authority, integrity, compatibility, temporal, semantic, lifecycle, and policy rules.

### Recovery State

The immutable record of the recovery process, including sources, boundary, validation, preparation,
new identities, execution, verification, disposition, and audit. It SHALL NOT be mutable runtime
state.

### Execution Continuity

Preservation of the same declared semantic obligation across separately identified operational
Attempts or recovery actions. Continuity SHALL NOT imply physical process continuity, Attempt
identity continuity, or authority continuity.

### Cancellation

An authoritative instruction that execution authority SHALL end within a declared scope.
Cancellation is intentional control, not proof that an obligation failed. Its races and terminal
effects remain governed by ADR-EPIP017-07.

### Timeout

An authoritative determination that a governed logical duration, deadline, or progress obligation
was exceeded. A clock signal or elapsed wall time alone SHALL NOT be a Timeout until the competent
authority validates it under the governing temporal and timeout policy.

### Expiration

The deterministic end of eligibility or authority at a declared boundary. Expiration MAY cause an
Attempt or Invocation to stop but SHALL NOT automatically classify the underlying work as failed.

### Revocation

An authoritative withdrawal of previously granted governance, trust, compatibility, lease, fence,
token, or other authority. Revocation is an authority fact and SHALL NOT be reduced to an
infrastructure failure.

### Compensation

A new, explicitly authorized and observable action intended to mitigate, counteract, or reconcile
an external consequence of an earlier action. Compensation SHALL NOT erase or reverse historical
facts.

### Replanning

The governed creation of a new Semantic Plan or Dispatch Plan because the corresponding immutable
planning facts or policy have changed. Replanning SHALL create new identity and lineage.

### Retry Limit

A policy-bound, immutable budget constraining Retry authorizations by scope, category, producer,
capability, Invocation, dependency branch, time boundary, or resource class. A limit SHALL NOT be
implemented as an unrecorded counter.

### Failure Isolation Boundary

The smallest declared dependency, Invocation, execution group, or orchestration scope within which
a failure disposition can be contained without violating semantic dependencies or authority.

## Failure Model

Failure processing SHALL separate:

1. observation of a condition;
2. validation that an obligation existed;
3. classification by Failure Authority;
4. ownership and impact determination;
5. append-only recording;
6. policy evaluation;
7. independent authorization of any response; and
8. resolution and archival.

A producer MAY report a structured failure but SHALL NOT authoritatively classify Retry,
Recovery, or Replanning. A scheduler MAY observe timeout or worker loss but SHALL NOT redefine
semantic failure. A planner MAY determine that a valid plan cannot be formed but SHALL NOT
self-authorize fallback execution.

Failure scope SHALL identify the exact producer, capability, Evidence requirement, dependency,
Invocation, Attempt, plan, temporal boundary, registry snapshot, and authority facts affected.
Propagation SHALL follow the frozen dependency graph and barrier semantics. A downstream node
SHALL NOT consume an uncommitted partial result merely because its upstream failure is classified
as recoverable.

### Failure Ownership and Responsibility

- Producer contract violations and declared analytical inability SHALL belong to the producer or
  capability obligation domain.
- Evidence incompatibility, ambiguity, and absence SHALL belong to semantic validation or
  dependency satisfaction, not infrastructure.
- Worker loss, transport failure, unavailable storage, and resource denial SHALL belong to the
  operational or infrastructure domain.
- Invalid authority, stale fence, revoked token, and unauthorized transition SHALL belong to the
  authority domain.
- Invalid plans, context, schemas, digests, temporal boundaries, and results SHALL belong to the
  validating authority for the failed predicate.
- Cancellation responsibility SHALL belong to the issuing and enforcing authority, not the
  producer merely receiving it.

Responsibility for detection, classification, correction, Retry authorization, Recovery
authorization, and Commit SHALL remain separately attributable.

## Failure Categories

### Execution Failure

An authorized Attempt was unable to satisfy its execution contract before eligible completion.
Examples MAY include declared producer failure, unrecoverable local execution error, or invalid
Attempt completion. Execution Failure SHALL NOT include a successful but semantically rejected
result unless the failure concerns execution-contract conformance.

### Semantic Failure

Required semantic obligations cannot be satisfied under the immutable Semantic Plan. This MAY
include incompatible Evidence, forbidden ambiguity, unresolved required dependency, invalid
absence semantics, or result semantic validation failure. Semantic Failure SHALL normally make
same-plan Retry ineligible unless the failure arose from a nondeterministic defect explicitly
permitted and bounded by the determinism profile. A changed semantic obligation requires
Replanning.

### Operational Failure

The operational strategy could not execute while semantic intent remains valid. Examples MAY
include worker unavailability, dispatch admission failure, resource exhaustion, or queue failure.
Operational Failure MAY permit a new Dispatch Plan or Retry without changing the Semantic Plan.

### Infrastructure Failure

A required infrastructure service or substrate failed its declared availability, integrity, or
transport obligation. Infrastructure Failure SHALL identify whether authoritative state is known,
unknown, or potentially duplicated before Retry or Recovery is considered.

### Validation Failure

An artifact, transition, input, output, preservation source, or authority claim failed a normative
validation predicate. Validation Failure SHALL list every failed predicate available at the
decision boundary and SHALL fail closed where authority or integrity is uncertain.

### Authority Failure

An actor lacks, lost, exceeded, or presented stale authority. Invalid lease, fence, token,
ownership, lifecycle transition, registry eligibility, or Commit attempt SHALL be Authority
Failure. Authority Failure MUST NOT be retried under the same invalid authority.

### Dependency Failure

A required upstream obligation has an authoritative failure or terminal non-satisfaction that
prevents a barrier from opening. Dependency Failure SHALL preserve the originating failure and
propagation lineage rather than replacing it with a generic downstream error.

### Temporal Failure

Availability, Knowledge Boundary, timeframe, revision, deadline, calendar, or cross-timeframe
obligations cannot be satisfied under ADR-EPIP017-05. Current data SHALL NOT repair a historical
Temporal Failure implicitly.

### Storage or Integrity Failure

A committed result, ledger, Checkpoint, manifest, digest, or required artifact is unavailable,
corrupt, mismatched, or unverifiable. Cache miss alone is not Storage Failure. Recovery SHALL not
use an artifact whose integrity or authority cannot be proven.

### Policy or Governance Failure

Admission, certification, trust, compatibility, retention, security, or institutional policy
cannot be satisfied. Revocation SHALL retain its specific authority identity even when represented
within this category.

### Cancellation

Cancellation SHALL remain a non-failure terminal control disposition. Work that physically fails
after authoritative cancellation MAY record an execution observation, but the causal terminal
disposition SHALL remain cancellation where ADR-EPIP017-07 resolves it first.

### Timeout

Timeout SHALL be a distinct classified condition. Policy SHALL state whether timeout causes
cancellation, expiration, failure, abort, Retry evaluation, or Recovery evaluation. Timeout MUST
NOT imply any one of those outcomes automatically.

### Expiration

Expiration SHALL terminate eligibility in its declared scope. It MAY cause an Authority Failure if
stale work continues, but the expiration fact SHALL remain independently visible.

### Revocation

Revocation SHALL invalidate the exact governed authority from its effective boundary. Results
submitted after effective revocation SHALL fail authority validation. Revocation SHALL NOT rewrite
actions that were authoritative before its boundary.

### Multiple Categories

One incident MAY produce multiple typed Failure Records when distinct obligations fail. One
primary category SHALL identify the earliest authoritative failed obligation, and secondary
categories SHALL retain causal relationships. Classification order MUST NOT depend on observer or
thread arrival order.

## Failure Disposition Model

After recording, policy SHALL choose only among explicit requests for:

- no further action and terminal failure;
- bounded Retry under the same Semantic Plan;
- Recovery from an admissible boundary;
- operational redispatch through a new Dispatch Plan;
- Replanning through a new Semantic Plan;
- Compensation;
- cancellation, abort, quarantine, or escalation; or
- deterministic wait for a declared external authority fact.

Fail-fast SHALL mean deterministic termination or containment at a declared boundary when
continuation would violate a required invariant. Fail-safe SHALL mean a deterministic, explicitly
authorized degraded or isolated disposition whose semantics were already present in the Semantic
Plan. Fail-safe MUST NOT invent optionality, fallback, or absence semantics after failure.

Failure isolation SHALL stop propagation outside the smallest safe boundary. Isolation SHALL NOT
hide the failure from dependency diagnostics, audit, or plan-level completeness.

## Retry Model

### Retry Eligibility

A Retry MAY be eligible only when all of the following hold:

- the Invocation is uncommitted and its lifecycle permits another Attempt;
- authoritative cancellation, expiration, abort, or rejection has not closed the scope;
- the Semantic Plan, Evidence requirements, temporal boundary, and semantic inputs remain unchanged;
- the failure category and policy explicitly permit Retry;
- Retry limits and exhaustion rules permit one more authorization;
- producer, capability, registry, trust, certification, and compatibility remain eligible;
- no existing Attempt retains conflicting commit authority;
- prior lease, fence, and token authority is ended or superseded as required;
- input and committed dependency integrity remains verified;
- any required Dispatch Plan is valid or a newly identified equivalent Dispatch Plan is approved;
- determinism profile permits the proposed repeat; and
- Retry would not conceal a required Replan, Recovery, Compensation, or governance decision.

Eligibility evaluation SHALL be deterministic from an immutable manifest of governing facts.
Eligibility SHALL NOT itself create an Attempt.

### Retry Authority and Scope

Only Retry Authority MAY authorize a Retry. Authorization SHALL bind one Invocation, semantic
scope, failure lineage, policy version, limit budget, operational constraints, and validity
boundary. Broad “retry all failures” authority is forbidden.

Authorization MAY cover an explicitly bounded set of equivalent Attempts only when the Dispatch
Plan and concurrency contract permit speculative or parallel Attempts. Each Attempt SHALL still
have unique identity and authority. ADR-EPIP017-14 SHALL govern their equivalence and races.

### Retry Identity and Lineage

Every Retry Request and Authorization SHALL have immutable identity under ADR-EPIP017-09. Every
new Attempt SHALL reference the Retry Authorization and all causal prior Attempt and Failure
identities. The retry ordinal MAY be recorded for observation but SHALL NOT be the sole identity.

Prior Attempts, results, failures, diagnostics, leases, fences, and tokens SHALL remain unchanged
and visible. Retry SHALL never replace historical Attempts.

### Retry Limits

Retry policy SHALL declare finite limits or a finite external decision boundary. Limits SHALL be
scoped and versioned and MAY include authorization count, cumulative logical budget, category,
producer, capability, Invocation, dependency branch, or resource class. Limit evaluation SHALL use
authoritative ledger facts, not process-local counters.

Exhaustion SHALL create an immutable Retry Exhaustion fact. It SHALL NOT silently replan, recover,
compensate, cancel, or increase the limit. Any policy exception SHALL be a new explicit authority
fact with distinct identity and audit.

### Retry Execution

An authorized Retry SHALL create a new Attempt under ADR-EPIP017-07. It SHALL obtain a new lease,
new or advanced fence, and new token. It MAY reference the same Semantic Plan and an eligible
Dispatch Plan. It MUST NOT reuse active or expired execution authority.

Only the atomic Commit Authority MAY select an authoritative result. Successful physical execution
does not erase earlier failures or guarantee Commit.

## Recovery Model

### Recovery Sources

Recovery MAY use only explicitly admitted sources:

- an Available or reuse-permitted Consumed Checkpoint under ADR-EPIP017-12;
- verified committed Durable Results and Commit Records;
- an authoritative Execution Ledger frontier;
- original immutable Semantic and Dispatch Plans and input manifests; and
- recomputation from authoritative source inputs under the original Knowledge Boundary.

Snapshots, Cache Entries, mutable runtime state, replay outputs, diagnostics, uncommitted Attempt
Results, active leases, fences, tokens, locks, and credentials SHALL NOT be production Recovery
Sources.

### Recovery Boundary

Every Recovery Request SHALL partition state into:

- authoritative completed and reusable work;
- admissible Checkpoint state;
- state requiring deterministic recomputation;
- invalid, stale, revoked, corrupt, or quarantined state;
- cancelled, expired, aborted, rejected, or superseded authority;
- pending semantic obligations; and
- external consequences requiring independent reconciliation or Compensation.

The boundary SHALL bind the original Invocation, plans, temporal and Knowledge Boundaries,
registry snapshot, dependency frontier, Commit frontier, ledger frontier, preservation profiles,
and governing recovery policy.

### Recovery Admissibility

Recovery MAY be admitted only when:

- the target semantic obligation remains valid and uncommitted;
- no authoritative terminal disposition forbids continuation;
- every source identity, digest, authority, integrity, compatibility, and lineage is valid;
- the Checkpoint satisfies ADR-EPIP017-12 and has not expired, retired, been destroyed, or revoked;
- the boundary contains no ambiguous in-flight or external-effect state;
- producer, capability, registry, temporal, schema, canonicalization, digest, and determinism
  profiles remain supported;
- recovery preserves the original Semantic Plan and knowledge constraints;
- any operational change receives a new Dispatch Plan identity where required;
- a new Attempt, lease, fence, token, and ledger lineage will be created; and
- policy limits, security, retention, and audit obligations are satisfied.

Admissibility is necessary but not sufficient. Recovery Authority SHALL issue a separate immutable
authorization or rejection.

### Recovery Execution and Verification

Recovery SHALL create a Recovery identity and Restoration identity. It SHALL restore only the
state enumerated by the admitted Restore Contract and SHALL reacquire every external input and
authority explicitly required by policy. It SHALL NOT revive the source Attempt.

Recovered execution SHALL enter the normal ADR-EPIP017-07 path. Verification SHALL compare the
actual reconstructed boundary, inputs, plans, profiles, dependency frontier, and new authority to
the authorization. Any mismatch SHALL fail closed and be recorded as Recovery Failure.

Completion of recovery SHALL mean the authorized continuity operation reached its declared
verified disposition. It SHALL NOT mean that the Invocation committed unless a separate atomic
Commit Record exists.

### Deterministic Recovery

Given identical authoritative sources, Recovery Boundary, profiles, policy, and authorization,
Recovery SHALL produce canonically equivalent restoration manifests and equivalent continuation
obligations. Physical worker, Attempt identity, and elapsed timing MAY differ where the declared
profile permits, but semantic results and authority decisions SHALL satisfy the applicable
equivalence contract.

If deterministic recovery cannot be established, Recovery SHALL be rejected, isolated for
diagnosis, or performed only in a non-authoritative replay or simulation mode.

## Compensation Model

Compensation SHALL be used only for an external consequence that cannot be removed by terminating
or invalidating internal execution authority. It SHALL be a new governed intent with distinct
identity, scope, authority, inputs, expected effect, failure policy, and audit lineage.

Compensation Authority SHALL be separate from Failure, Retry, Recovery, producer, scheduler, and
Commit Authorities. An actor MAY hold multiple roles only through explicit grants and SHALL record
which authority was exercised.

Compensation SHALL be visible as a new action. It SHALL preserve:

- the original action and outcome facts;
- the consequence being addressed;
- the compensation authorization and rationale;
- observed external state and uncertainty;
- execution, result, failure, and retry facts for the compensation itself; and
- causal lineage without claiming erasure or rollback.

Compensation success SHALL NOT change the historical authority of the original action. A failed
Compensation SHALL produce its own Failure Record and SHALL NOT recursively retry without explicit
authorization and limits.

EPIP-017 Evidence producers remain subject to the side-effect restrictions of ADR-EPIP017-02.
This model does not authorize producer side effects, trading actions, risk actions, or execution
actions.

## Replanning Model

Retry, Recovery, and Replanning SHALL remain distinct:

| Operation | Semantic Plan | Dispatch Plan | Execution identity | Permitted purpose |
| --- | --- | --- | --- | --- |
| Retry | Same immutable plan | Same or new equivalent plan | New Attempt | Repeat the same semantic obligation |
| Recovery | Same immutable plan unless recovery terminates and a separate Replan begins | Same or new compatible plan | New Recovery, Restoration, and Attempt | Continue the same semantic obligation from a governed boundary |
| Operational redispatch | Same immutable plan | New Dispatch Plan | New operational lineage and Attempt as authorized | Change operational strategy only |
| Replanning | New Semantic Plan when semantic facts change | New Dispatch Plan derived from it | New Invocation lineage | Establish changed semantic intention |

Replanning SHALL be required when any producer requirement, capability selection semantics,
Evidence dependency, absence rule, context projection, temporal boundary, revision policy,
cross-timeframe meaning, completeness obligation, or analytical policy changes.

A Replanning Request MAY arise from failure diagnosis, but it SHALL NOT be automatically
authorized by Failure, Retry Exhaustion, Recovery Failure, or Compensation Failure. Planning
Authority SHALL create and validate a new Semantic Plan with explicit derivation and supersession
lineage. The prior plan and all execution history SHALL remain immutable.

If only workers, resource classes, batching, queueing, timeout allocation, or other operational
strategy changes, Dispatch Replanning MAY create a new Dispatch Plan referencing the same Semantic
Plan. It SHALL NOT change semantic inputs or obligations.

Fallback to a different producer or Evidence interpretation is semantic Replanning unless the
original Semantic Plan already declared the alternative, its equivalence, ordering, and absence
semantics. No failure handler MAY invent fallback.

## Failure Lifecycle

### Failure States

- **Detected** — a Failure Event exists but category and authority are not yet established.
- **Classified** — Failure Authority assigned category, scope, ownership, and causal lineage.
- **Recorded** — the authoritative Failure Record is append-only and visible.
- **Audited** — required integrity, authority, chronology, and policy evidence was assessed.
- **Resolved** — an explicit disposition completed or the obligation became terminal.
- **Archived** — terminal failure history is retained.
- **Rejected** — the suspected event was not a valid Failure under the claimed contract.
- **Cancelled** — classification work was authoritatively stopped without deleting observed facts.

### Legal Failure Transitions

- Detected SHALL transition only to Classified, Rejected, or Cancelled.
- Classified SHALL transition only to Recorded, Rejected, or Cancelled.
- Recorded SHALL transition only to Audited, Resolved, or Archived under an explicit terminal
  disposition.
- Audited SHALL transition only to Resolved or Archived.
- Resolved SHALL transition only to Archived.
- Rejected, Cancelled, and Archived SHALL be terminal.

Resolution SHALL NOT mean historical removal. A Retry, Recovery, Replan, Compensation, escalation,
or terminal decision MAY resolve response obligations while the Failure remains permanently true.

## Retry Lifecycle

### Retry States

- **Requested** — a Retry proposal exists without authority.
- **Eligible** — deterministic eligibility predicates passed.
- **Authorized** — Retry Authority granted a bounded authorization.
- **Scheduled** — a new Attempt was admitted to an eligible Dispatch Plan.
- **Executed** — the new Attempt reached a terminal or submitted disposition.
- **Completed** — Retry processing reached its declared disposition; Commit remains separately
  authoritative.
- **Rejected** — eligibility or authorization was denied.
- **Cancelled** — Retry authority ended before a new Attempt could continue.
- **Exhausted** — applicable Retry limits prohibit further authorization.
- **Archived** — terminal Retry history is retained.

### Legal Retry Transitions

- Requested SHALL transition only to Eligible, Rejected, Cancelled, or Exhausted.
- Eligible SHALL transition only to Authorized, Rejected, Cancelled, or Exhausted.
- Authorized SHALL transition only to Scheduled, Cancelled, Rejected, or Exhausted.
- Scheduled SHALL transition only to Executed or Cancelled.
- Executed SHALL transition only to Completed, Cancelled, or Exhausted.
- Completed, Rejected, Cancelled, and Exhausted SHALL transition only to Archived.
- Archived SHALL be terminal.

Authorization expiry or invalidation before scheduling SHALL produce Rejected, Cancelled, or
Exhausted according to its authoritative cause. Retry completion MUST NOT be equated with Attempt
Commit.

## Recovery Lifecycle

### Recovery States

- **Requested** — continuity is proposed without recovery authority.
- **Validated** — boundary, sources, integrity, compatibility, semantics, and policy were evaluated.
- **Authorized** — Recovery Authority admitted the bounded operation.
- **Prepared** — restoration manifest, new identities, and execution prerequisites are verified.
- **Executed** — authorized restoration and continuation were attempted.
- **Verified** — reconstructed state and execution lineage satisfy the Recovery authorization.
- **Completed** — Recovery reached its declared disposition; this is not a Commit claim.
- **Rejected** — validation or authorization denied Recovery.
- **Failed** — an authorized Recovery could not satisfy its contract.
- **Cancelled** — Recovery authority ended before completion.
- **Archived** — terminal Recovery history is retained.

### Legal Recovery Transitions

- Requested SHALL transition only to Validated, Rejected, or Cancelled.
- Validated SHALL transition only to Authorized, Rejected, or Cancelled.
- Authorized SHALL transition only to Prepared, Rejected, or Cancelled.
- Prepared SHALL transition only to Executed, Failed, or Cancelled.
- Executed SHALL transition only to Verified, Failed, or Cancelled.
- Verified SHALL transition only to Completed or Failed.
- Completed, Rejected, Failed, and Cancelled SHALL transition only to Archived.
- Archived SHALL be terminal.

A failed Recovery SHALL require a new request for any subsequent Recovery, Retry, Compensation, or
Replanning. Backward, skipped, hidden, or in-place transitions are forbidden.

## Authority Model

Authority SHALL be separated as follows:

- Observation Authority MAY emit Failure Events but SHALL NOT classify or respond.
- Failure Authority SHALL classify and record failures without authorizing remediation.
- Cancellation Authority SHALL request and establish cancellation under ADR-EPIP017-07.
- Timeout Authority SHALL validate governed timeout conditions without self-authorizing Retry.
- Retry Authority SHALL authorize bounded new Attempts without executing or committing.
- Recovery Authority SHALL admit bounded continuity without validating source artifacts on behalf
  of their authorities.
- Checkpoint Authority SHALL validate Checkpoints without admitting Recovery.
- Replanning Authority SHALL create new plans under ADR-EPIP017-06.
- Compensation Authority SHALL authorize new compensating actions without rewriting history.
- Execution, Lease, Fence, Token, and Commit Authorities retain ADR-EPIP017-07 responsibilities.
- Audit and Certification Authorities SHALL assess compliance without mutating decisions.

Policy SHALL constrain authority but SHALL NOT replace it. Possession of a Checkpoint, error
message, Retry token, scheduler role, producer role, or administrative access SHALL not imply
Failure, Retry, Recovery, Replanning, Compensation, or Commit authority.

## Failure Invariants

1. Failure is immutable, typed, scoped, attributable, and observable.
2. Failure never rewrites execution history.
3. Cancellation differs from Failure.
4. Timeout, expiration, revocation, rejection, abort, and supersession remain distinct facts.
5. Retry always creates a new Attempt identity.
6. Retry preserves the same Semantic Plan and semantic obligation.
7. Retry never replaces, deletes, or reopens a prior Attempt.
8. Retry requires explicit eligibility and authority.
9. Retry limits are finite or externally bounded and ledger-derived.
10. Recovery preserves semantic and historical authority.
11. Recovery uses only explicitly admitted sources and boundaries.
12. Snapshot never resumes production execution.
13. Recovery never revives leases, fences, tokens, locks, credentials, or the source Attempt.
14. Recovery creates new operational identity and authority.
15. Compensation is a new visible action and never changes historical authority.
16. Replanning never mutates an existing Semantic or Dispatch Plan.
17. Changed semantic intent always creates a new Semantic Plan and Invocation lineage.
18. Fail-safe behavior must already be authorized by semantic intent.
19. Failure classification never depends on thread arrival or enumeration order.
20. Only atomic Commit creates an authoritative execution result.

## Determinism

Failure classification, eligibility, limits, propagation, isolation, and dispositions SHALL be
deterministic for identical authoritative facts, policies, profiles, and logical ordering.

Determinism requires:

- canonical category precedence and causal classification for multi-failure incidents;
- authoritative logical deadlines and timeout policies rather than local elapsed timing;
- immutable policy, scope, input, lineage, and authority manifests;
- stable Retry, Recovery, Compensation, and Replanning identities;
- deterministic limit evaluation from the Execution Ledger;
- no random jitter, queue ordering, worker discovery, thread completion, or observer arrival in
  semantic or authority decisions;
- original temporal and Knowledge Boundaries during recovery and replay;
- explicit treatment of unknown outcome and potentially duplicated external effects; and
- serial and parallel equivalence under ADR-EPIP017-14.

Operational backoff, placement, or timing MAY vary only within a frozen Dispatch policy and MUST
NOT alter eligibility, semantic intent, failure classification, attempt limits, or outcome
authority. Any randomized operational choice SHALL use a declared determinism profile and seed and
SHALL remain outside semantic identity.

## Replay Compatibility

Replay under ADR-EPIP017-11 SHALL preserve and reproduce, according to mode:

- original Failure Events, categories, ownership, authority, and lifecycle;
- cancellation, timeout, expiration, revocation, rejection, abort, and supersession distinctions;
- Retry Requests, eligibility facts, limits, authorizations, rejections, exhaustion, and lineage;
- Recovery Requests, boundaries, sources, compatibility, authorizations, restoration identities,
  verification, and dispositions;
- Compensation and Replanning requests, authorities, results, and lineage;
- original plans, policies, profiles, clocks, registry snapshots, Checkpoints, ledgers, and results;
- concurrent ordering and atomic terminal dispositions where recorded; and
- diagnostics, audit, and certification evidence.

Historical Replay SHALL use facts and policy available at the original Knowledge Boundary.
Operational Replay MAY reproduce the recorded authority decisions; it MUST NOT recalculate timeout
from current machine speed. Certification Replay SHALL test policy and equivalence without granting
live authority. Diagnostic Replay MAY explore alternatives but SHALL label them counterfactual and
non-authoritative.

Replay MUST NOT execute production Retry, Recovery, Compensation, cancellation, Replanning, or
Commit. It MUST NOT mutate limits, ledgers, Checkpoints, plans, results, or historical disposition.

## Diagnostics

Diagnostics SHALL distinguish at minimum:

- execution failure;
- semantic failure;
- operational failure;
- infrastructure failure;
- validation failure;
- authority failure;
- dependency and temporal failure;
- cancellation, timeout, expiration, and revocation;
- retry ineligibility and retry rejection;
- retry exhaustion and limit inconsistency;
- recovery-source rejection and boundary inconsistency;
- restoration mismatch and recovery failure;
- compensation request and compensation failure;
- replanning request and unauthorized semantic change;
- unexpected, implicit, duplicate, or stale Retry;
- hidden or unauthorized Recovery;
- failure-propagation and isolation violations; and
- Commit versus cancellation race disposition.

Each diagnostic SHALL bind affected identities, observed and expected facts, category, causal
lineage, authority, policy and profile versions, scope, logical time, severity, and disposition.
Diagnostics SHALL be non-authoritative: they MUST NOT Retry, Recover, Compensate, Replan, cancel,
abort, quarantine, or commit automatically.

## Audit

Audit SHALL be append-only and SHALL preserve:

- every observed Failure Event and authoritative Failure Record;
- classification inputs, category precedence, ownership, authority, and causal graph;
- cancellation, timeout, expiration, revocation, rejection, abort, and supersession facts;
- failed obligations, impacted dependencies, barriers, and isolation decisions;
- Retry Requests, eligibility manifests, limits, authorizations, Attempts, and exhaustion;
- Recovery Requests, boundaries, sources, Checkpoint validation, admissions, restorations, new
  Attempts, verification, completion, rejection, and failure;
- Compensation and Replanning requests, authorizations, plans, actions, outcomes, and lineage;
- policies, exceptions, profiles, migrations, diagnostics, and certification evidence;
- all competing authority decisions and their canonical ordering; and
- every terminal disposition and archival transition.

Audit SHALL distinguish requested from authorized, eligible from admitted, scheduled from
executed, executed from committed, recovered from successful, and compensated from reversed.

## Certification Rules

Institutional certification SHALL prove at minimum:

1. Every mandatory failure category is classified deterministically and remains distinguishable.
2. Cancellation, timeout, expiration, revocation, rejection, abort, and supersession do not collapse.
3. Retry is impossible without explicit eligibility and authorization.
4. Every Retry creates a new Attempt, lease, fence, token, identity, and lineage.
5. Prior Attempts and failures remain immutable and replayable.
6. Retry limits and exhaustion are deterministic and cannot be bypassed silently.
7. Semantic Failure cannot be repaired by hidden operational retry or fallback.
8. Recovery admits only eligible sources and never restores a Snapshot or ambient authority.
9. Recovery creates new identities and uses the atomic Commit path.
10. Recovery preserves Semantic Plan, temporal meaning, and Knowledge Boundary.
11. Compensation is visible, separately authorized, and non-rewriting.
12. Semantic Replanning creates a new Semantic Plan and Invocation lineage.
13. Failure propagation and isolation respect dependency and barrier semantics.
14. Fail-fast and fail-safe dispositions are deterministic and pre-authorized.
15. Replay cannot activate any production remediation authority.
16. Serial and parallel failure outcomes are equivalent under ADR-EPIP017-14.
17. Migration does not manufacture Retry or Recovery eligibility.
18. No remediation path can produce more than one authoritative Commit.

Certification failure SHALL prohibit the affected policy, profile, producer class, recovery path,
Retry class, compensation class, migration path, or concurrency mode from institutional use. It
SHALL NOT be downgraded to a warning.

## Migration

Migration SHALL classify legacy unsuccessful outcomes as Execution Failure, Semantic Failure,
Operational Failure, Infrastructure Failure, Validation Failure, Authority Failure, Dependency
Failure, Temporal Failure, Storage or Integrity Failure, Policy or Governance Failure,
Cancellation, Timeout, Expiration, Revocation, Rejection, Abort, Supersession, or ambiguous.

Legacy retries SHALL be assigned distinct Attempt identities and reconstructed lineage only where
authoritative evidence exists. Missing Retry authority, limits, policy, or causal facts SHALL be
recorded as gaps; they MUST NOT be invented. Legacy repeated executions MUST NOT be presumed to be
valid retries.

Legacy recovery state SHALL be admitted only if it satisfies ADR-EPIP017-12 Checkpoint and this
ADR's Recovery Boundary requirements. Otherwise it MAY remain an observational migration Snapshot
or diagnostic artifact and SHALL NOT resume production.

Legacy plan mutation SHALL be represented as separate plan versions where provenance can be
proven. Ambiguous semantic changes SHALL be quarantined and MUST NOT be certified as same-plan
Retry or Recovery. Compensation history SHALL preserve original actions and SHALL NOT be rewritten
as rollback.

Migration Replay MAY compare legacy and new dispositions without granting authority. ADR-EPIP017-16
SHALL govern compatibility epochs, transition policy, exceptions, rollback, and final migration
certification.

## Backward Compatibility

This ADR SHALL NOT modify EPIP-016, its Decision Framework, Kernel, Replay, EventBus, financial
engines, execution, serialization, public APIs, or released behavior. EPIP-016 SHALL not request or
authorize producer Retry, Recovery, Compensation, or Replanning inside EPIP-017.

Existing EPIP-017 authority remains unchanged. Failure response is additive and SHALL operate only
through the frozen Invocation, Attempt, plan, identity, storage, replay, and preservation contracts.
No existing success, Commit, cancellation, or historical fact SHALL be reclassified in place.

Legacy callers that do not use the new failure contract MAY continue only where their behavior is
provably equivalent and does not rely on implicit retry, mutable plans, hidden fallback, or
restoration. Compatibility wrappers SHALL emit explicit identities and audit facts and SHALL not
manufacture authority.

## Forbidden Behaviours

The following are constitutionally forbidden:

1. Implicit or unrecorded Retry.
2. Hidden, automatic, or unaudited Recovery.
3. Automatic semantic Replanning after failure.
4. Failure, Retry, Recovery, Compensation, or Replanning rewriting history.
5. Retry replacing, reopening, deleting, or mutating historical Attempts.
6. Recovery mutating committed results, Commit Records, plans, ledgers, Snapshots, or Checkpoints.
7. Semantic mutation after failure under the same Semantic Plan identity.
8. Retry without deterministic eligibility, explicit authority, or limit evaluation.
9. Retry using the same Attempt, lease, fence, token, or stale authority.
10. Recovery from a Snapshot, Cache Entry, replay output, diagnostic, or mutable runtime state.
11. Recovery restoring locks, credentials, connections, leases, fences, tokens, or process state.
12. Compensation presented as erasure, rollback, or reversal of historical authority.
13. Retry exhaustion silently increasing limits or selecting fallback.
14. Timeout inferred solely from local elapsed wall time.
15. Cancellation classified as failure merely because no result committed.
16. Operational failure changing Evidence meaning or producer semantics.
17. Fallback producer selection not declared by the Semantic Plan.
18. Failure handlers self-committing partial or recovered results.
19. Reusing current facts to repair historical Recovery or Replay.
20. Diagnostics or policy engines exercising remediation authority implicitly.

## Alternatives Considered

### Automatic Retry on Every Exception

Rejected. Exceptions do not establish category, eligibility, semantic stability, authority, or
safe duplication. Automatic retry can create storms, stale commits, and hidden semantic changes.

### Mutable Attempt with an Incrementing Retry Counter

Rejected. It erases execution lineage, reuses authority, prevents causal audit, and cannot safely
resolve competing results.

### Recovery as Process Resumption

Rejected. Physical process state carries ambient authority, live resources, nondeterministic
timing, and unverifiable external effects. Recovery SHALL reconstruct a new governed Attempt.

### Failure Handler May Select a Fallback Producer

Rejected. Producer selection and Evidence meaning are semantic planning decisions. Undeclared
fallback silently mutates intent.

### Compensation as Transaction Rollback

Rejected. External consequences may not be reversible. Claiming rollback rewrites history and
hides uncertainty.

### One Authority for Classification and Remediation

Rejected. Combining Failure, Retry, Recovery, Replanning, Compensation, execution, and Commit
authority removes institutional checks and permits self-justifying recovery.

### Typed Failure Facts with Separately Authorized Responses

Accepted. This preserves history, authority separation, deterministic policy, bounded retries,
safe continuity, replayability, and semantic immutability.

## Decision

EPIP-017 SHALL adopt typed immutable Failure Records and separately governed Retry, Recovery,
Compensation, and Replanning contracts.

Failure SHALL be recorded before response. Retry SHALL create a new Attempt for the same Semantic
Plan. Recovery SHALL use an explicit Recovery Boundary and admissible sources, create new
operational identities, and enter the normal fenced atomic-Commit path. Compensation SHALL be a new
visible action. Any semantic change SHALL create a new Semantic Plan and Invocation lineage.

No policy, scheduler, producer, planner, administrator, migration, replay, or implementation
convenience MAY bypass explicit authority, limits, identity, lifecycle, diagnostics, or audit.

## Consequences

### Positive

- Every unsuccessful condition remains explainable and replayable.
- Cancellation and authority events cannot be hidden as generic failures.
- Retries are bounded, attributable, and protected from stale authority.
- Recovery preserves semantic intent and historical truth.
- Compensation remains honest about external consequences.
- Replanning cannot silently alter immutable plans.
- Failure isolation and propagation become certifiable.
- Future execution engines share one institutional contract.

### Negative

- Separate records, authorities, state machines, identities, and policy manifests increase
  governance cost.
- Recovery may require recomputation and new resource admission instead of transparent resume.
- Some transient errors will terminate rather than retry when eligibility cannot be proven.
- Legacy retry and recovery behavior may be quarantined.
- Compensation cannot offer the fiction of atomic rollback across external systems.

### Trade-offs

EPIP accepts higher operational latency, explicit decision overhead, retention obligations, and
implementation complexity to prevent duplicate authority, hidden retries, semantic drift,
nondeterministic recovery, and historical falsification.

## Compatibility

Compatibility SHALL be proven separately for Failure classification, Retry policy, Recovery
sources, Checkpoint Restore Contracts, Dispatch Plans, Compensation contracts, and Replanning
lineage. Byte or schema readability SHALL NOT imply behavioral or authority equivalence.

A changed failure taxonomy, category precedence, Retry eligibility rule, limit policy, recovery
admissibility rule, timeout meaning, compensation contract, or semantic fallback SHALL require a
new versioned policy and compatibility assessment. Material semantic change SHALL require a new
Semantic Plan, never a compatibility assertion.

## Non-goals

This ADR does not define:

- retry algorithms, backoff formulae, queue policies, scheduling heuristics, or worker placement;
- recovery implementation, checkpoint format, process restoration, or persistence technology;
- distributed consensus, concurrency primitives, or parallel race algorithms;
- producer analytical behavior or financial, trading, risk, Decision, or execution logic;
- external transaction protocols or authorization for producer side effects;
- monitoring products, alert routing, or operator interfaces; or
- any Programme A implementation.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 through ADR-EPIP017-12, especially:

- ADR-06 for immutable Semantic and Dispatch Plans and Replanning boundaries;
- ADR-07 for Invocation, Attempt, lease, fence, token, cancellation, abort, Commit, and Ledger;
- ADR-08 and ADR-09 for determinism, identity, digest, canonicalization, and lineage;
- ADR-10 for Durable Result, Cache, corruption, and recomputation boundaries;
- ADR-11 for historical and operational reproduction of failure decisions; and
- ADR-12 for Checkpoint admissibility, restoration, and preserved-state authority.

The remaining architecture SHALL specialize this ADR through:

- ADR-EPIP017-14 for concurrent detection, failure ordering, speculative Attempts, cancellation and
  Commit races, barrier disposition, and serial/parallel equivalence;
- ADR-EPIP017-15 for EPIP-016 handoff behavior when required Evidence is failed, absent, degraded,
  recovered, or incomplete; and
- ADR-EPIP017-16 for taxonomy, policy, Retry, Recovery, Compensation, and Replanning migration and
  compatibility governance.

No circular dependency is authorized. ADR-14 MAY govern ordering and equivalence but MUST NOT
redefine Failure categories or remediation authority. ADR-15 MAY govern handoff admission but MUST
NOT authorize Retry or Recovery. ADR-16 MAY govern migration but MUST NOT manufacture historical
eligibility.

## Future Evolution

Adaptive retry budgets, failure-domain health models, distributed recovery, replicated
Checkpoints, predictive isolation, automated operator proposals, multi-region continuity, and
externally attested compensation MAY evolve through versioned policies and additional ADRs.

Automation MAY propose and, where an explicit pre-authorized authority grant permits, issue a
bounded decision. It SHALL still produce the same identities, manifests, lifecycle facts, limits,
diagnostics, and audit as any other authority. No future optimization MAY introduce hidden retry,
implicit restoration, mutable planning, or historical rewriting.

## Approval Gate

Approval of this ADR resolves Failure, Retry, Recovery, Execution Continuity, Compensation, and
Replanning authority architecture only.

It does not approve concurrency behavior, handoff policy, migration governance, retry algorithms,
recovery mechanisms, any engine, or Programme A.

EPIP-017 implementation remains prohibited until the complete mandatory ADR set is accepted and
the remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
