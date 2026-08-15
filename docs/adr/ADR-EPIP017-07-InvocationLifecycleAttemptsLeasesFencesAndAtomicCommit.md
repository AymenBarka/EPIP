# ADR-EPIP017-07 — Invocation Lifecycle, Execution Attempts, Leases, Fences and Atomic Commit

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-06 are approved, frozen, and normative. This ADR MUST NOT
modify their orchestration authority, producer contract, governance, Evidence semantics, temporal
model, plan separation, EPIP-016 boundary, or single-authoritative-path rule.

This ADR defines execution lifecycle architecture only. It authorizes no implementation,
scheduler, worker, lease service, commit engine, ledger, interface, placeholder, or Programme A
activity.

## Executive Summary

EPIP-017 SHALL distinguish an immutable **Invocation** from every operational **Execution
Attempt** made to satisfy it. An Invocation represents one frozen Execution Intent from one
Semantic Plan. It may have multiple attempts, but it may reach no more than one authoritative
terminal commit.

Every attempt SHALL require an explicit **Execution Lease**, **Execution Fence**, and unforgeable
**Execution Token** before producer execution begins. The lease grants temporary, non-transferable
operational ownership. The fence establishes a monotonic authority generation that prevents an
older, duplicated, cancelled, expired, or superseded attempt from committing. The token binds the
exact invocation, attempt, lease, fence, Dispatch Plan, owner, scope, and granted privileges.

An attempt's local completion is not authoritative completion. A submitted result becomes visible
as authoritative Evidence only through one atomic commit decision by the Commit Authority. Commit
validation SHALL verify plan identity, input identity, result integrity, lease and fence authority,
producer conformance, temporal validity, and absence of a prior authoritative outcome. Result
publication and the authoritative ledger commit fact SHALL form one indivisible logical commit.

The **Execution Ledger** SHALL be append-only. It SHALL preserve invocation admission, every
attempt, lease, fence, token, transition, result submission, failure, cancellation, abort,
rejection, commit, and archival fact. Corrections SHALL append superseding facts and MUST NOT alter
history.

Lease expiry, cancellation, or fence revocation SHALL terminate authority, not erase activity. A
worker that continues physically after authority ends is stale execution. Its outputs MUST be
rejected and quarantined; they MUST NOT become committed Evidence or trigger downstream work.

This lifecycle provides the atomicity and stale-work protection required for serial and future
parallel execution without defining scheduling, retry policy, or replay algorithms.

## Purpose

Establish the constitutional lifecycle by which EPIP-017 authorizes producer invocation, records
execution attempts, assigns temporary ownership, fences stale execution, validates completion,
atomically commits one authoritative outcome, and preserves immutable execution history.

This ADR defines:

- Invocation identity, scope, authority, context, visibility, and lifetime;
- attempt identity, lineage, ordering, ownership, result, failure, and completion;
- lease acquisition, validity, expiration, release, invalidation, and transfer prohibition;
- fence identity, scope, generation, verification, failure, and revocation;
- execution-token authority and least privilege;
- formal Invocation and Attempt state machines;
- commit, abort, rejection, cancellation, and archival semantics;
- Execution Ledger authority, atomicity, diagnostics, audit, and certification foundations.

## Problem Statement

A producer returning successfully does not prove that its result is still authorized. The worker
may have lost ownership, exceeded its lease, ignored cancellation, duplicated another attempt,
used obsolete inputs, or completed after another attempt committed.

Without an explicit lifecycle and atomic commit model, concurrent or recovered execution can
produce:

- two authoritative results for one Invocation;
- results committed after lease expiration or cancellation;
- stale attempts overwriting newer results;
- duplicate side effects or downstream publication;
- partial result visibility before ledger commitment;
- ambiguous ownership after worker failure;
- implicit retry through duplicate dispatch;
- deleted or rewritten attempt history;
- runtime mutation of Semantic or Dispatch Plans;
- snapshots that cannot determine authoritative state.

EPIP therefore requires immutable invocation identity, explicit attempt lineage, temporary leases,
monotonic fences, scoped tokens, append-only state transitions, and one atomic result-commit
authority.

## Architectural Context

ADR-EPIP017-01 establishes separate semantic planning, execution-ledger, durable-result, audit, and
handoff authorities.

ADR-EPIP017-02 establishes side-effect-free producer execution, immutable inputs, one terminal
result submission or structured failure, cooperative cancellation, and the distinction between
submission and authoritative completion.

ADR-EPIP017-03 establishes immutable governance and registry snapshots. Lifecycle revocation
cannot mutate an active run silently.

ADR-EPIP017-04 establishes explicit immutable dependencies and requires committed upstream results
before consumer eligibility.

ADR-EPIP017-05 establishes frozen Knowledge and temporal boundaries. Late output MUST NOT change
historical semantics.

ADR-EPIP017-06 establishes immutable Semantic and Dispatch Plans, Execution Intents, Units,
Barriers, Fences, separated contexts, and the append-only Execution Ledger as the authority for
actual runtime facts.

This ADR completes the execution lifecycle and atomicity foundation. Retry eligibility remains in
ADR-EPIP017-13. Parallel scheduling and equivalence remain in ADR-EPIP017-14.

## Definitions

### Invocation

The immutable execution-plane representation of exactly one Execution Intent authorized by one
accepted Semantic Plan and one compatible Dispatch Plan lineage.

### Invocation Identity

The stable identity binding the run, Semantic Plan, semantic graph node, Execution Intent,
producer, capability, exact input manifest, expected result contract, temporal boundary, and
commit scope. It excludes attempts, workers, leases, fences, timings, and outcomes.

### Invocation Authority

The Execution Authority empowered to admit the Invocation, authorize attempts through valid
Dispatch Plans, and record lifecycle facts without changing semantic intent.

### Invocation Context

The immutable Execution Context from ADR-EPIP017-06 containing only the exact producer,
capability, configuration, inputs, temporal boundary, security scope, determinism profile, and
cancellation contract granted to all conforming attempts of the Invocation.

### Invocation Lifetime

The complete immutable history from Created through one terminal authoritative disposition and
Archived retention state. Lifetime is logical and MUST NOT be inferred solely from process
duration.

### Execution Attempt

One operational effort authorized to satisfy one Invocation under one Dispatch Plan, lease, fence,
token, owner, and attempt identity.

### Attempt Identity

The stable identity binding the Invocation, Dispatch Plan, attempt ordinal, predecessor or cause,
lease identity, fence generation, owner, and authorization epoch.

### Attempt Lineage

The immutable relation connecting an attempt to the initial attempt and any superseded, aborted,
cancelled, expired, or failed predecessor. Lineage MUST state authorization cause without implying
retry eligibility.

### Execution Lease

A time-bounded or logically bounded, exclusive grant of operational ownership over one attempt
scope. A lease permits execution only while valid and does not grant commit by itself.

### Execution Fence

A monotonic authority generation scoped to an Invocation or explicitly defined commit domain. Only
the currently valid fence generation may authorize result commitment.

### Execution Token

An immutable, verifiable, least-privilege authorization binding one attempt to its Invocation,
Dispatch Plan, lease, fence, owner, permitted producer, inputs, result submission scope, and
validity boundary.

### Attempt Result

The immutable producer result submitted by an attempt. It is non-authoritative until atomically
committed.

### Attempt Completion

The recorded fact that producer execution ended and submitted either a candidate result or a
structured failure. Completion is not Invocation completion or commit.

### Commit

The single atomic authoritative decision that accepts one eligible Attempt Result as the durable
result of the Invocation and makes its committed identity visible to dependent execution.

### Abort

An authoritative terminal disposition preventing an Invocation or Attempt from further authorized
progress because completion is impossible, prohibited, superseded, or explicitly abandoned.

### Cancellation

An authoritative request and resulting lifecycle disposition to stop work that remains in
progress. Cancellation terminates future authority according to its scope but does not erase work
already observed.

### Rejection

The authoritative refusal of an Invocation admission, attempt authorization, result submission, or
commit because a contract or validation rule is not satisfied.

### Stale Execution

Physical or logical work performed after lease expiry, fence supersession or revocation,
cancellation, abort, loss of ownership, or authoritative commit by another attempt.

### Commit Record

The immutable ledger fact binding one Invocation, one Attempt Result, one fence generation, one
durable-result identity, and one authoritative terminal commit.

## Invocation Model

An Invocation MUST be created only from an accepted Execution Intent. It MUST identify exactly one
semantic graph node and expected atomic result contract.

An Invocation MUST be immutable once Accepted. Its producer, capability, input manifest,
configuration, context, temporal boundary, expected outputs, completeness, determinism profile,
security scope, and commit scope MUST NOT change.

If any immutable Invocation fact changes, the Execution Authority MUST reject mutation and require
a new Semantic Plan and Invocation identity where semantics changed, or a new Dispatch Plan and
attempt where only operational strategy changed.

### Invocation Scope

Invocation scope SHALL include only:

- one run and Semantic Plan;
- one semantic graph node and Execution Intent;
- one selected producer and capability contract;
- one exact immutable input manifest;
- one atomic result group;
- one terminal authoritative outcome.

Multi-output capability results MAY share one Invocation only when ADR-EPIP017-02 declared them an
atomic semantic group. Unrelated outputs MUST NOT share commit scope.

### Invocation Visibility

The producer and worker MAY receive only the Invocation Context and minimal authorization facts.
They MUST NOT receive mutable lifecycle authority, alternative attempts, live registry state,
unrelated graph nodes, or commit mutation authority.

Dependent Invocations MAY observe only an authoritative committed-result reference or explicit
terminal dependency disposition. They MUST NOT observe Attempt Results, intermediate state, or
uncommitted completion.

## Execution Attempt Model

Multiple attempts MAY exist for one Invocation only when each attempt is explicitly authorized and
recorded. Duplicate physical execution without a distinct authorized Attempt identity is forbidden.

Attempt ordering MUST use a monotonically increasing logical ordinal within the Invocation. Wall
clock start order, worker observation order, or completion order MUST NOT define authority.

Every Attempt MUST identify:

- Invocation and Dispatch Plan identities;
- attempt ordinal and lineage;
- attempt owner;
- lease, fence, and token identities;
- authorization cause and policy reference;
- lifecycle transitions;
- immutable result or failure submission;
- final attempt disposition.

Attempt ownership MUST be exclusive for the lease scope. A worker MUST NOT execute the same
Attempt identity under multiple owners.

An Attempt Result MUST be immutable and isolated. It MUST NOT overwrite another attempt's result.
Multiple candidate results MAY be retained, but no more than one MAY become authoritative.

Attempt Failure MUST preserve producer, infrastructure, lease, fence, cancellation, authority, and
commit categories distinctly. It MUST NOT authorize a subsequent attempt. Retry authorization
belongs exclusively to ADR-EPIP017-13 and a new Dispatch Plan or existing immutable authorization.

## Lease Model

### Lease Acquisition

An Execution Lease MUST be granted by the Lease Authority only after:

- the Invocation is Accepted or Prepared;
- the Dispatch Plan authorizes the Execution Unit;
- required semantic results are committed;
- the proposed owner satisfies security, isolation, and operational eligibility;
- no conflicting valid lease exists for an exclusive scope;
- the current fence generation is established;
- lease duration or logical validity policy is explicit.

Lease acquisition MUST append an immutable ledger fact before execution authority begins.

### Lease Ownership

Every lease MUST have exactly one owner identity. Ownership MUST be least privilege and limited to
the named Invocation, Attempt, producer, input manifest, fence, and permitted actions.

### Lease Validity and Expiration

Lease validity MUST use one authoritative operational clock or logical lease boundary identified by
policy. Lease time is operational authority time and MUST NOT be interpreted as Evidence or
Knowledge Time.

After expiration, the owner MUST stop execution and MUST NOT submit or commit a result. Physical
work that continues is stale execution and SHALL be diagnosed, isolated, and denied authority.

Expiration MUST append a ledger fact or be deterministically derivable from immutable lease facts
and the authoritative lease-clock observation used by the Execution Authority. It MUST NOT rewrite
the lease grant.

### Lease Release

An owner MAY release a valid lease after completion, cancellation acknowledgement, or abandonment.
Release MUST be explicit and recorded. Release MUST NOT delete the attempt or imply successful
completion.

### Lease Invalidation

The Lease Authority MAY invalidate a lease for fence revocation, ownership loss, security action,
cancellation, abort, or authoritative commit. Invalidation MUST state scope, cause, authority, and
effective operational boundary.

### Lease Transfer

Lease transfer is forbidden. A different owner requires invalidation or release of the prior lease,
a new attempt identity where ownership changes, a new lease, a current fence, and a new token.

Lease renewal, if later permitted, MUST be an explicit immutable authorization fact preserving the
same owner and attempt. Renewal MUST NOT restore an expired lease, change semantic inputs, or avoid
fence verification. Detailed renewal policy belongs to operational governance.

## Fence Model

### Fence Identity and Scope

Every fence MUST identify its Invocation, commit scope, monotonic generation, issuing authority,
creation cause, and validity state.

The fence scope MUST cover every operation capable of making an Attempt Result authoritative. A
fence MAY additionally guard producer execution or durable-result submission when required by the
execution profile.

### Fence Authority

Only the Fence Authority MAY issue, advance, or revoke a fence generation. The worker, producer,
lease owner, scheduler, and Attempt MUST NOT modify it.

### Fence Lifetime

A fence generation begins when immutably issued and ends when superseded, revoked, or the
Invocation reaches an authoritative terminal disposition. End of a generation MUST NOT erase its
history.

### Fence Verification

Fence validity MUST be verified at minimum:

- before execution begins;
- before an Attempt Result is accepted for validation;
- immediately within the atomic commit decision;
- before authoritative downstream publication.

Verification MUST use authoritative fence state, not a worker's cached belief.

### Fence Failure

Missing, unverifiable, stale, superseded, mismatched, or revoked fence identity MUST reject
execution authority or result commitment. Fence failure MUST NOT be retried implicitly or treated
as producer failure.

### Fence Revocation

Fence revocation MUST immediately prevent new authoritative actions in its scope. It MAY be issued
for cancellation, abort, security action, ownership loss, duplicate execution, Dispatch Plan
supersession, or prior commit. Revocation MUST be append-only and audited.

Monotonic fence generations MUST never be reused, decremented, reset, or inferred from timestamps.

## Execution Token Model

An Execution Token MUST be immutable, authentic, bounded, non-transferable, and verifiable. It
MUST bind:

- Invocation and Attempt identities;
- Semantic and Dispatch Plan identities;
- owner identity;
- producer and capability identities;
- input-manifest and temporal-boundary identities;
- lease identity and validity boundary;
- fence identity and generation;
- permitted execution, diagnostic, submission, and cancellation operations;
- security and isolation profile;
- issuing authority and token-policy version.

A token MUST grant no registry, planner, scheduler, cache, unrelated result, EPIP-016, risk,
portfolio, execution, or administrative authority.

Token verification MUST occur before every privileged lifecycle action. An invalid, expired,
revoked, mismatched, duplicated, or transferred token MUST fail closed.

Token possession MUST NOT alone establish lease validity, fence freshness, result correctness, or
commit eligibility. All predicates remain independently verified.

## Execution Lifecycle

Invocation lifecycle and Attempt lifecycle SHALL be separate state machines.

### Invocation States

- **Created** — immutable identity is derived from an Execution Intent but not yet admitted.
- **Accepted** — authority and invariant validation succeeded; immutable Invocation begins.
- **Prepared** — required committed inputs, Dispatch Plan mapping, policy, and execution context are
  validated for attempt authorization.
- **Active** — at least one authorized Attempt exists and no authoritative terminal disposition
  exists.
- **Completed** — an eligible Attempt Result has been submitted and awaits commit decision; this is
  not authoritative success.
- **Committed** — exactly one Attempt Result is atomically authoritative.
- **Rejected** — Invocation admission or all presented completion claims failed contract
  validation and no commit exists.
- **Cancelled** — cancellation became authoritative before commit and no further attempt may be
  authorized under the cancelled scope.
- **Expired** — Invocation eligibility ended under an explicit logical policy before commit.
- **Aborted** — authoritative execution was terminated without commit for a governed non-recovery
  disposition.
- **Archived** — terminal history is retained under immutable archival policy.

### Legal Invocation Transitions

- Created SHALL transition only to Accepted or Rejected.
- Accepted SHALL transition only to Prepared, Cancelled, Expired, Aborted, or Rejected.
- Prepared SHALL transition only to Active, Cancelled, Expired, Aborted, or Rejected.
- Active MAY remain Active across explicitly authorized Attempts and SHALL transition only to
  Completed, Cancelled, Expired, Aborted, or Rejected.
- Completed SHALL transition only to Committed, Active when a presented result is rejected but an
  already authorized alternative remains, Rejected, Cancelled, Expired, or Aborted.
- Committed, Rejected, Cancelled, Expired, and Aborted SHALL transition only to Archived.
- Archived SHALL be terminal.

No transition may leave Committed for another semantic outcome. A correction to committed Evidence
requires new Evidence revision lineage and, where computation changes, a new Semantic Plan and
Invocation.

### Attempt States

- **Authorized** — attempt identity and lineage are accepted.
- **Leased** — valid exclusive lease, fence, and token are issued.
- **Executing** — producer execution began under valid authority.
- **Completed** — immutable result or structured failure was submitted.
- **CommitPending** — candidate result passed submission validation and awaits atomic commit.
- **Committed** — this attempt supplied the Invocation's sole authoritative result.
- **Rejected** — authorization, execution submission, validation, or commit was refused.
- **Cancelled** — cancellation ended attempt authority.
- **Expired** — lease or attempt validity ended.
- **Aborted** — execution ended without eligible completion under authoritative abort.
- **Superseded** — a newer fence or authorized attempt removed this attempt's future authority.
- **Archived** — terminal attempt history is retained.

### Legal Attempt Transitions

- Authorized SHALL transition only to Leased, Rejected, Cancelled, Expired, Aborted, or Superseded.
- Leased SHALL transition only to Executing, Aborted after explicit release, Cancelled, Expired,
  Rejected, or Superseded.
- Executing SHALL transition only to Completed, Cancelled, Expired, Aborted, Rejected, or
  Superseded.
- Completed SHALL transition only to CommitPending, Rejected, Cancelled, Expired, Aborted, or
  Superseded.
- CommitPending SHALL transition only to Committed, Rejected, Cancelled, Expired, Aborted, or
  Superseded.
- Committed, Rejected, Cancelled, Expired, Aborted, and Superseded SHALL transition only to
  Archived.
- Archived SHALL be terminal.

Every illegal, duplicate, skipped, or backward transition MUST be rejected and recorded as an
authority or lifecycle violation.

## Commit Model

### Commit Eligibility

An Attempt Result is eligible for commit only when all of the following are true atomically at the
commit decision:

- Invocation is accepted, non-terminal, and compatible with completion;
- Attempt is in CommitPending;
- exact Semantic and Dispatch Plan references are valid;
- producer, capability, implementation, configuration, and certification identities match;
- input manifest, dependencies, context, and temporal boundary match the Invocation;
- result is immutable, complete, schema-valid, semantically valid, and integrity-valid;
- lease was valid through the required submission boundary;
- current fence exactly matches the Attempt fence generation;
- token and owner authority remain valid for submission scope;
- cancellation, abort, expiry, security revocation, or supersession has not removed commit
  authority;
- no authoritative Commit Record exists for the Invocation;
- durable-result admission and provenance validation succeed.

### Commit Authority

Only the Commit Authority MAY decide and record authoritative commit. Producer, worker, lease
owner, scheduler, planner, cache, replay controller, and EPIP-016 MUST NOT self-commit a result.

### Atomicity

The Commit Authority SHALL make the following one indivisible logical transaction:

- verify every commit predicate against authoritative state;
- establish exactly one Commit Record for the Invocation;
- bind the immutable durable-result identity;
- transition the winning Attempt to Committed;
- transition the Invocation to Committed;
- revoke or supersede all competing commit authority;
- expose the committed-result reference to downstream barrier evaluation.

Either every authoritative effect occurs or none occurs. Partial visibility is forbidden.

### Commit Ordering

Competing commit requests MUST be serialized by authoritative Invocation identity and fence
generation. Arrival time, worker priority, completion order, or scheduler preference MUST NOT
override fence and atomic eligibility.

The first request that atomically satisfies all predicates MAY commit. Every later request MUST
observe the existing Commit Record and be rejected or superseded without altering it.

### Commit Rejection

Commit rejection MUST preserve the Attempt Result for the required audit or quarantine scope and
record every failed predicate. Rejection MUST NOT delete the result, mutate the plan, create retry
authority, or replace an existing commit.

### Commit Visibility and Permanence

No dependent Invocation, handoff, audit verdict, or durable reuse MAY treat a result as
authoritative before the Commit Record is visible.

After commit, the authoritative result and Commit Record MUST be immutable. Later correction,
withdrawal, revocation, or invalidation MUST create new facts and MUST NOT rewrite commit history.

## Abort Model

Abort MUST be an explicit authoritative disposition with scope, reason, issuing authority, policy,
and effective boundary.

Abort MAY apply to an Attempt or an uncommitted Invocation. It MUST revoke applicable leases,
fences, and tokens and prevent new commit in its scope.

Abort MUST NOT:

- erase execution history;
- fabricate successful completion;
- convert partial output into Evidence;
- mutate either plan;
- authorize a new attempt or fallback implicitly;
- reverse an authoritative commit.

Whether a new Invocation or attempt may later be authorized belongs to ADR-EPIP017-13.

## Cancellation Model

Cancellation SHALL have separate request, acknowledgement, authority-termination, and terminal
record facts. A request alone MUST NOT be mistaken for completed cancellation.

Cancellation scope MUST identify run, Invocation, Attempt, lease, fence, or dispatch lineage. It
MUST identify the issuing authority and policy.

When cancellation becomes authoritative before commit:

- applicable lease and token authority MUST end;
- applicable fence MUST be revoked or superseded;
- the producer MUST receive cooperative cancellation through its granted contract;
- further result submission and commit MUST be rejected;
- physical continuation MUST be classified as stale execution;
- all facts MUST remain in the ledger.

Commit and cancellation racing for the same Invocation MUST be resolved atomically by the same
authoritative state boundary. Exactly one terminal disposition MAY win. A cancellation recorded
after Commit MUST NOT reverse Commit; it MAY only record that cancellation arrived too late.

## Execution Authority

- The Invocation Authority SHALL create and accept immutable Invocations.
- The Dispatch Authority SHALL authorize Execution Units under one Dispatch Plan.
- The Lease Authority SHALL grant, expire, release, and invalidate leases.
- The Fence Authority SHALL issue, advance, verify, and revoke fence generations.
- The Token Authority SHALL issue and revoke scoped Execution Tokens.
- The Worker Authority SHALL perform only the actions granted by a valid token.
- The Commit Authority SHALL validate and atomically commit exactly one result.
- The Ledger Authority SHALL append and preserve authoritative lifecycle facts.
- The Durable Result Authority SHALL preserve committed result artifacts without deciding semantic
  planning.
- The Audit Authority SHALL verify conformance without changing state.

Authorities MAY be hosted together operationally only when their logical scopes, credentials,
separation, atomicity, and audit remain independently enforceable. Hosting convenience MUST NOT
collapse authority.

## Execution Ownership

An Invocation is owned institutionally by the Execution Authority and semantically by its frozen
Execution Intent. A worker never owns the Invocation.

An Attempt has exactly one operational owner while its lease is valid. Ownership MUST NOT be
shared, inherited, inferred from process location, or transferred.

The Attempt owner SHALL own only invocation-local resources and producer execution during the
lease. It MUST NOT own the plans, input artifacts, committed result, ledger, fence, or downstream
publication.

Loss of owner identity, isolation, health, or authority MUST invalidate or expire the lease and
MUST prevent commit until a separately authorized attempt exists.

## Execution Ledger Integration

The Execution Ledger SHALL be the sole authoritative history of execution lifecycle facts.

It MUST record immutable entries for:

- Invocation creation, acceptance, preparation, and every transition;
- Dispatch Plan authorization and supersession;
- Attempt authorization, identity, ordinal, lineage, and every transition;
- lease request, grant, renewal where permitted, release, expiration, and invalidation;
- fence issue, verification, advancement, supersession, and revocation;
- token issue, verification failure, and revocation;
- execution start and cancellation acknowledgement;
- result or failure submission and immutable artifact identity;
- validation, rejection, quarantine, abort, and stale-execution findings;
- commit request, atomic decision, Commit Record, and downstream visibility;
- late cancellation or duplicate commit attempts;
- archival and retention relationships;
- authority identities, policies, diagnostics, and audit references.

Ledger entries MUST be append-only, immutable, canonically attributable, ordered by authoritative
logical sequence within their scope, and linked causally. No entry MAY be updated or deleted.

Corrections MUST append a new fact referencing the erroneous fact. A correction MUST NOT change an
authoritative committed outcome; semantic correction requires governed revision outside the
Invocation.

The ledger MUST distinguish proposed, observed, and authoritative facts. Worker telemetry MUST NOT
become an authoritative lifecycle transition without validation by the owning authority.

## Execution Invariants

1. Every Invocation represents exactly one immutable Execution Intent.
2. An accepted Invocation never changes semantic or dispatch facts in place.
3. Multiple Attempts MAY exist; no more than one authoritative Commit MAY exist.
4. Every Attempt has a unique identity, ordinal, lineage, and owner.
5. No Attempt executes without a valid lease, fence, and token.
6. Lease ownership is exclusive and non-transferable.
7. Lease expiry ends execution and submission authority.
8. Fence generations are monotonic and never reused.
9. A stale or revoked fence can never commit.
10. Token possession never replaces independent lease and fence verification.
11. Attempt completion is not Invocation completion.
12. Result submission is not authoritative commitment.
13. Commit is one indivisible logical transaction.
14. Only the Commit Authority creates a Commit Record.
15. Committed result visibility begins only with the Commit Record.
16. Commit never rewrites history.
17. Cancellation, abort, expiry, rejection, and supersession never erase history.
18. A terminal authoritative disposition cannot transition backward.
19. Execution never changes the Semantic Plan.
20. Execution never mutates the Dispatch Plan.
21. Runtime facts belong only to the append-only Execution Ledger.
22. Attempt history and rejected results remain auditable.
23. Illegal transitions fail closed and are recorded.
24. Downstream barriers consume committed references only.
25. Decision remains outside invocation and commit authority.

## Determinism

Given identical Invocation, Dispatch Plan, authoritative lifecycle facts, attempt authorizations,
lease facts, fence generations, tokens, submitted artifacts, commit-policy versions, and authority
decisions, lifecycle validation MUST produce identical:

- legal and illegal transition determinations;
- attempt ordering and lineage;
- lease, fence, and token validity determinations;
- commit eligibility predicates;
- winning authoritative disposition;
- rejection and stale-execution classifications;
- canonical ledger facts and identities;
- diagnostics and audit conclusions.

Physical start order, elapsed duration, worker location, thread interleaving, network arrival, or
storage enumeration MUST NOT determine semantic authority. Operational observations MAY determine
lease expiry or timeout only through explicit authoritative policy and recorded facts; they MUST
NOT alter Evidence semantics or historical Knowledge Time.

This ADR does not claim deterministic physical timing. Determinism profiles and operational
reproduction remain governed by ADR-EPIP017-08 and ADR-EPIP017-11.

## Diagnostics

Diagnostics MUST use stable, versioned reason codes and distinguish at minimum:

- Invocation identity, admission, preparation, or transition failure;
- Attempt identity, lineage, ordering, ownership, or transition failure;
- lease acquisition conflict, ownership mismatch, expiration, invalidation, or transfer attempt;
- missing, mismatched, stale, superseded, revoked, or reused fence;
- invalid, expired, revoked, mismatched, or over-privileged token;
- execution without authority;
- duplicate authorized or unauthorized execution;
- stale execution after expiry, cancellation, supersession, or commit;
- Attempt Result validation or completeness failure;
- commit predicate, ordering, atomicity, durable-result, or visibility failure;
- multiple-commit attempt;
- cancellation request, acknowledgement, race, or late arrival;
- abort, rejection, expiry, or archival failure;
- ledger ordering, causality, authority, immutability, or append failure;
- semantic or Dispatch Plan mutation attempt;
- authority-scope violation.

Diagnostics MUST identify Invocation, Attempt, lease, fence, token, owner, authority, plans,
transition, submitted artifact, policy, and ledger sequence where applicable. Diagnostics MUST NOT
authorize retry, mutate state, or select a replacement result.

## Audit

Audit MUST be able to establish:

- the immutable Invocation and Execution Intent;
- every Attempt identity, ordinal, cause, owner, and lineage;
- every lease, fence, token, validation, and authority decision;
- exact lifecycle transitions and rejected illegal transitions;
- producer start, completion, failure, cancellation, and stale-work facts;
- every submitted result and quarantine disposition;
- all commit predicates and the atomic Commit Record;
- proof that no second authoritative commit exists;
- cancellation and commit race resolution;
- Dispatch Plan supersession without Semantic Plan mutation;
- downstream visibility only after commit;
- complete append-only ledger continuity and causality;
- archival retention of unsuccessful and aborted work.

Audit MUST distinguish worker observations from authoritative transitions. It MUST NOT reconstruct a
clean history by deleting duplicate, stale, rejected, or failed attempts.

## Lifecycle Certification

Certification MUST verify at least:

1. Invocation identity, immutability, scope, and visibility.
2. Attempt identity, lineage, ordinal, ownership, and isolation.
3. Every legal transition and rejection of every illegal transition.
4. Exclusive lease acquisition, expiry, release, invalidation, and transfer prohibition.
5. Monotonic fence issue, verification, supersession, and revocation.
6. Token authenticity, scope, least privilege, expiry, mismatch, and revocation.
7. Rejection of execution without valid lease, fence, or token.
8. Rejection and quarantine of stale and duplicate execution.
9. Immutable result submission distinct from completion and commit.
10. Atomic all-or-nothing commitment and exactly-one authoritative outcome.
11. Competing commit, cancellation, expiry, abort, and supersession races.
12. Downstream invisibility before Commit Record publication.
13. Immutable committed result and correction-by-new-fact behavior.
14. Append-only ledger continuity, causality, attribution, and failure preservation.
15. Crash-boundary and partial-operation scenarios without partial commit.
16. No implicit retry, ownership transfer, plan mutation, or history rewriting.

Certification MUST include real concurrent race campaigns even though scheduling and parallel
equivalence are governed separately. Nominal sequential lifecycle tests are insufficient to prove
atomicity.

## Migration

- Existing execution calls MUST be inventoried for implicit Invocation, Attempt, ownership,
  timeout, cancellation, result publication, and completion semantics.
- Existing producer return values MUST NOT be treated as authoritative commit automatically.
- Existing duplicate dispatch, local retry, worker takeover, and timeout behavior MUST be exposed
  and classified before certification.
- Existing shared mutable execution state MUST be replaced conceptually by immutable Invocation
  facts and append-only ledger history before EPIP-017 adoption.
- Legacy worker ownership MUST NOT be inferred from threads, processes, callbacks, or object
  references.
- Existing result publication MUST be assessed for atomicity and downstream visibility.
- Shadow execution MUST test duplicate attempts, owner loss, lease expiry, cancellation, fence
  supersession, competing completion, commit races, and worker failure.
- Legacy authoritative execution MUST remain separate until lifecycle and commit equivalence are
  certified under ADR-EPIP017-16.
- Migration MUST preserve legacy attempt and failure history where available and MUST declare gaps
  rather than fabricate ledger facts.

## Backward Compatibility

This ADR changes no production execution path, public API, producer implementation, EPIP-016
contract, Replay behavior, EventBus behavior, financial calculation, risk rule, portfolio behavior,
execution behavior, or serialization format.

Invocation, Attempt, Lease, Fence, Token, Commit Record, and Execution Ledger are EPIP-017
architectural artifacts. They MUST NOT be inserted into frozen EPIP-016 Decision semantics.

Legacy execution MAY continue during governed migration. No legacy return, event, stored result, or
callback is automatically classified as a conforming atomic Commit.

Historical Invocation and Attempt artifacts MUST remain interpretable under their original schema,
policy, authority, and identity versions. New lifecycle versions MUST NOT reinterpret prior state
transitions.

## Forbidden Behaviours

EPIP-017 MUST NEVER permit:

1. More than one authoritative Commit for an Invocation.
2. Execution after lease expiration, invalidation, release, or ownership loss.
3. Execution or submission without a valid current fence.
4. Execution or privileged action without a valid scoped token.
5. Lease transfer or implicit ownership transfer.
6. Fence generation reuse, decrement, reset, or timestamp inference.
7. Result commit without complete atomic validation.
8. Partial commit or result visibility before Commit Record publication.
9. Worker, producer, scheduler, cache, or replay self-commit.
10. Attempt completion treated as authoritative Invocation completion.
11. Uncommitted result exposed to dependent execution or EPIP-016.
12. Implicit retry or duplicate attempt authorization.
13. Attempt deletion, result deletion to conceal failure, or history rewriting.
14. Ledger mutation, transition overwrite, or retrospective state cleanup.
15. Backward or illegal lifecycle transition.
16. Cancellation or abort reversing a prior Commit.
17. Stale execution overwriting or replacing a committed result.
18. Runtime mutation of Semantic or Dispatch Plans.
19. Operational ownership inferred from process, thread, queue, or object identity.
20. Authority expansion through token possession or successful execution.
21. Downstream publication based only on producer return or worker acknowledgement.
22. Decision, Candidate, Confidence, risk decision, or execution instruction created by commit.

Any forbidden behavior SHALL be an architecture and certification failure and MUST fail closed.

## Alternatives Considered

### Producer return is authoritative completion

The first successful producer return becomes the result.

Rejected because producer execution may be stale, duplicated, cancelled, or unauthorized.

### Lease without fencing

A lease grants ownership and its holder may commit while it believes the lease is valid.

Rejected because an expired or partitioned owner may continue and race a new owner. A monotonic
fence is required at commit.

### Fence without scoped token

A fence generation alone authorizes execution.

Rejected because it does not bind owner, producer, inputs, privilege, lease, or Dispatch Plan.

### Mutable invocation record

One record is updated in place as execution progresses.

Rejected because history, races, rejected transitions, and authority decisions become
unverifiable.

### Exactly-once physical execution

The runtime guarantees a producer is physically executed only once.

Rejected as an unsafe architectural assumption. EPIP instead permits explicitly authorized
multiple attempts while enforcing at most one authoritative atomic commit.

### Immutable Invocation, fenced attempts, atomic commit, append-only ledger

Accepted because duplicate or stale physical work cannot create multiple authoritative outcomes
and every decision remains auditable.

## Decision

EPIP SHALL adopt the Invocation, Attempt, Lease, Fence, Execution Token, lifecycle, commit, abort,
cancellation, authority, ownership, ledger, determinism, diagnostic, audit, certification,
migration, compatibility, and prohibition rules in this ADR as the constitutional execution
lifecycle for EPIP-017.

Execution SHALL become authoritative only through one atomic Commit Record. No runtime component,
failure path, operational convenience, or recovery mechanism MAY bypass lease, fence, token,
validation, or ledger authority.

## Consequences

### Positive

- Exactly one authoritative outcome exists per Invocation.
- Duplicate and stale execution cannot overwrite committed Evidence.
- Worker failure and ownership loss have explicit dispositions.
- Result visibility and downstream readiness become atomic.
- Cancellation and commit races have one authoritative resolution boundary.
- All attempts, failures, and rejected results remain auditable.
- Serial and parallel runtimes share the same lifecycle foundation.
- Semantic and Dispatch Plans remain immutable during execution.

### Negative

- EPIP must maintain leases, fences, tokens, atomic commit state, and an append-only ledger.
- Physical execution may occur without producing an authoritative result.
- Operational failures require explicit lifecycle facts rather than local cleanup.
- Retention requirements increase because unsuccessful attempts remain auditable.
- Recovery cannot reuse ownership implicitly and may require new attempts and Dispatch Plans.

### Trade-offs

EPIP accepts additional execution authority and history artifacts in exchange for eliminating
multiple commits, stale-result publication, hidden takeover, and unverifiable recovery.

## Non-goals

This ADR does not define:

- implementation classes, APIs, interfaces, databases, consensus algorithms, locks, or protocols;
- worker-selection, queueing, batching, scheduling, fairness, or backpressure algorithms;
- retry eligibility, retry count, backoff, fallback, or recovery policy;
- replay modes or replay algorithms;
- cache, durable-result, or invalidation implementation;
- physical timeout mechanisms or producer-specific deadline policy;
- distributed topology or failure detector;
- canonical serialization or digest algorithms;
- snapshot or checkpoint representation;
- EPIP-016 handoff representation;
- producer analytical logic;
- trading, Decision, Candidate, Confidence, risk, portfolio, execution, or financial logic.

These exclusions MUST be resolved by their mandatory ADRs and MUST NOT be delegated to code.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 through ADR-EPIP017-06 and the frozen EPIP-016 and
H001–H007 architecture.

It creates or confirms mandatory dependencies on:

- ADR-EPIP017-08 for lifecycle, authority, timing, result, and operational determinism profiles;
- ADR-EPIP017-09 for Invocation, Attempt, Lease, Fence, Token, Commit Record, result, and ledger
  identities and digest hierarchy;
- ADR-EPIP017-10 for durable-result admission, atomic storage boundary, quarantine, cache lookup,
  and committed-result reuse;
- ADR-EPIP017-11 for lifecycle and ledger reproduction without rewriting original authority;
- ADR-EPIP017-12 for consistent audit snapshots, resumable checkpoints, in-flight attempts, leases,
  fences, and restore admission;
- ADR-EPIP017-13 for retry authorization, timeout disposition, cancellation policy, fallback,
  recovery, and new-attempt governance;
- ADR-EPIP017-14 for concurrent lease acquisition, worker isolation, fairness, duplicate
  suppression, barrier release, and serial/parallel equivalence;
- ADR-EPIP017-15 for committed-result-only completeness and EPIP-016 handoff;
- ADR-EPIP017-16 for lifecycle migration, rollback, divergence, and legacy retirement;
- ADR-EPIP017-17 for ledger retention, redaction, attestation,
  causality, and telemetry separation;
- ADR-EPIP017-18 for lease policy, execution
  admission, owner health, resource bounds, and archival retention.

No new ADR family is introduced. This ADR makes authoritative operational clock governance for
leases explicit; it SHALL be covered by ADR-EPIP017-08 and ADR-EPIP017-18
without changing the semantic temporal model of ADR-EPIP017-05.

## Future Evolution

Future distributed workers, lease-renewal profiles, replicated commit authorities, or consensus
mechanisms MAY evolve behind this lifecycle only when they preserve exclusive ownership,
monotonic fencing, atomic commit, append-only history, and exactly one authoritative outcome.

New Invocation or Attempt states require a versioned lifecycle ADR amendment. Existing historical
transitions MUST remain interpretable and MUST NOT be reclassified in place.

Future streaming or multi-commit capabilities are incompatible with the one-Invocation,
one-authoritative-commit invariant and require a new architectural model rather than an exception
in implementation.

## Approval Gate

Approval of this ADR resolves Invocation lifecycle, execution authority, leases, fences, tokens,
atomic commit, and immutable execution history only.

It does not approve a scheduler, worker runtime, ledger, lease service, fence service, token
service, commit engine, retry mechanism, replay engine, storage system, or Programme A.

EPIP-017 implementation remains prohibited until the complete mandatory ADR set is accepted and
the remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
