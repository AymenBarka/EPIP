# ADR-EPIP017-15 — EPIP-016 Handoff, Terminal Evidence Set and Decision Boundary

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-14 are approved, frozen, and normative. This ADR MUST NOT
modify them or the frozen EPIP-016 v1.5.17 Decision Framework. No implementation, transport, API,
serialization, adapter, engine, placeholder, or Programme A activity is authorized.

## Executive Summary

EPIP-017 SHALL terminate at one explicit constitutional boundary. It SHALL present exactly one
immutable **Handoff Manifest** referencing a closed **Terminal Evidence Set** composed only of
eligible, committed, immutable semantic Evidence. The manifest SHALL prove identity, integrity,
provenance, lineage, ordering, version compatibility, closure, and completeness under the frozen
Semantic Plan and handoff profile.

Before acceptance, EPIP-017 Handoff Authority owns presentation and validation responsibility;
EPIP-017 has no Decision authority. Acceptance SHALL be one atomic, immutable fact. After
acceptance, EPIP-017 SHALL lose all authority to replace, supplement, retract, or republish that
handoff identity, and EPIP-016 SHALL be the sole authority for evidence registration, inference,
candidates, confidence, Decision, explanation, and decision certification. Authority changes
exactly once and never returns.

Scheduler, planner, Dispatch Plan, runtime, Attempt, worker, lease, fence, token, Window, Barrier,
Ledger, Cache, Checkpoint, Retry, Recovery, speculation, and operational context state SHALL NOT
cross. Provenance MAY be represented only as immutable semantic references allowed by the frozen
EPIP-016 contract; it SHALL not expose reconstructable execution authority.

Incomplete, ambiguous, corrupted, incompatible, duplicated, late, or unauthorized handoffs SHALL
fail closed. Optional or partial Evidence MAY cross only when the frozen terminal contract
explicitly defines its admissibility and the resulting set is nevertheless closed and complete for
that declared profile.

## Purpose

This ADR defines the final EPIP-017 output, its validation, the single authority transition, and
the immutable Decision boundary. It establishes Terminal Evidence, Evidence Closure, Evidence
Completeness, Evidence Eligibility, Handoff Manifest, Handoff Authority, Transfer Eligibility,
Transfer Validation, failure behavior, replay, audit, migration, compatibility, and certification.

## Problem Statement

Without a narrow handoff, EPIP-016 could become coupled to orchestration internals, reconstruct
producer execution, accept provisional results, or receive different Evidence according to runtime
timing. EPIP-017 could accidentally generate Decision meaning, republish after acceptance, conceal
missing mandatory Evidence, or treat operational completion as semantic closure.

The boundary must answer conclusively: what crossed, why it was eligible, whether the requested
semantic obligation is complete, which versions govern it, who accepted it, and when authority
changed. Transport success, object readability, producer completion, Barrier release, or matching
digest alone is insufficient.

## Architectural Context

ADR-EPIP017-01 freezes EPIP-017 before Decision and assigns EPIP-016 all Decision Framework work.
ADR-EPIP017-04 defines Evidence semantics, eligibility, provenance, dependency resolution, and
completeness. ADR-EPIP017-05 governs temporal closure. ADR-EPIP017-06 requires the Semantic Plan to
terminate at a handoff requirement. ADR-EPIP017-07 permits only committed results to become
authoritative. ADR-EPIP017-08 and ADR-EPIP017-09 govern determinism, canonicalization, identity,
and digests. ADR-EPIP017-10 governs durable results. ADR-EPIP017-11 through ADR-EPIP017-14 govern
replay, preserved state, failure/recovery, and parallel equivalence without changing handoff
semantics.

This ADR specializes that boundary. ADR-EPIP017-16 SHALL govern migration and compatibility but
MUST NOT widen it.

## Definitions

### Terminal Evidence

Immutable semantic Evidence whose producing Invocation has an authoritative Commit, whose Durable
Result is integrity-valid, and whose semantic, temporal, provenance, lineage, compatibility,
certification, and handoff eligibility satisfy the terminal requirement.

### Terminal Evidence Set

The canonically ordered, immutable, closed collection of Terminal Evidence admitted for exactly
one handoff scope, Semantic Plan, subject, temporal boundary, completeness profile, and intended
EPIP-016 evidence-registration contract.

### Evidence Closure

The authoritative proof that every mandatory terminal requirement and every transitive semantic
dependency has one permitted terminal disposition, no unresolved or provisional dependency remains,
and no further EPIP-017 execution can alter the set under the same handoff identity.

### Evidence Completeness

Conformance of the closed set to the cardinality, optionality, absence, validity, timeframe,
conflict, provenance, and certification rules of its declared terminal completeness profile.

### Evidence Eligibility

The deterministic predicate that Evidence is committed, immutable, valid, temporally admissible,
identity-verified, integrity-valid, compatible, trusted, certified as required, within scope, and
permitted by the handoff profile.

### Mandatory Evidence

Evidence whose terminal requirement MUST be satisfied by eligible Evidence or by an explicitly
declared authoritative absence disposition permitted by the Semantic Plan.

### Optional Evidence

Evidence whose omission behavior, presence rules, and effect on completeness were frozen in the
Semantic Plan. Runtime availability SHALL NOT redefine optionality.

### Partial Evidence

Evidence explicitly marked incomplete in its own semantic domain. It MAY cross only when the
terminal profile explicitly permits that exact partiality and remains complete for its declared
contract. Otherwise it is ineligible.

### Missing Evidence

An unsatisfied terminal requirement with no eligible Evidence and no permitted authoritative
absence disposition. It SHALL make closure or completeness fail.

### Rejected Evidence

Evidence denied by semantic, temporal, authority, integrity, compatibility, trust, certification,
or handoff validation. It SHALL not enter the Terminal Evidence Set.

### Handoff Manifest

The immutable constitutional transfer artifact that binds the complete Terminal Evidence Set and
all evidence necessary to validate its authority and meaning without transferring execution state.

### Handoff Identity

A domain-qualified identity binding request scope, Semantic Plan, terminal profile, Evidence Set,
manifest version, EPIP-016 compatibility contract, authorities, canonical representation, and
qualified digest.

### Handoff Authority

The EPIP-017 authority permitted to assemble, validate, and present one eligible Manifest. It SHALL
not create Evidence, waive completeness, invoke Decision work, or accept on behalf of EPIP-016.

### Boundary Acceptance Authority

The authority at the EPIP-016 boundary permitted to validate the frozen admission contract and
atomically accept or reject one Manifest. It SHALL not reconstruct EPIP-017 execution or modify
Evidence.

### Decision Boundary

The one-way constitutional boundary after which EPIP-016 alone owns evidence registration and all
Decision Framework responsibilities. It is not an execution graph node or Evidence producer.

### Transfer Eligibility

The deterministic predicate that the Manifest, set, authorities, versions, completeness, closure,
and Evidence satisfy every handoff rule.

### Transfer Acceptance Record

The immutable atomic fact binding Handoff Identity, manifest digest, accepting authority, target
contract, validation verdict, logical boundary, and accepted status. It SHALL exist at most once
for one Handoff Identity.

## Terminal Evidence Model

Only a closed Terminal Evidence Set MAY cross. Each member SHALL bind Evidence identity, type,
schema, semantic meaning, subject and scope, canonical content digest, validity, completeness,
temporal and Knowledge Boundaries, provenance, derivation lineage, producer and capability
identity, registry snapshot, Commit Record, Durable Result, and required certification.

The set SHALL contain no Attempt Result lacking Commit, no provisional output, no cache-only
artifact, and no operational projection. Reference to Commit and provenance establishes
validation lineage; it SHALL NOT transfer the underlying Ledger or execution authority.

### Evidence Closure

Closure SHALL require:

- every terminal requirement has a canonical disposition;
- all required semantic and cross-timeframe dependencies are committed or have a permitted
  authoritative absence;
- all relevant temporal watermarks and closure facts are satisfied;
- conflicts, redundancy, cardinality, compatibility, and revision selection are resolved under the
  frozen Semantic Plan;
- every required Barrier is authoritatively complete, while Barrier state itself remains internal;
- no eligible Retry, Recovery, speculative candidate, or in-flight Attempt can alter the selected
  set under this identity; and
- the membership and canonical ordering are frozen.

Operational quiescence alone SHALL not prove closure. Closure is use-specific and SHALL not claim
global completion of all possible Evidence.

### Provenance, Lineage, and Integrity

Provenance and lineage SHALL be sufficient to verify source, derivation, versions, dependencies,
temporal interpretation, Commit authority, and transformations. They SHALL cross only as semantic
metadata or immutable references compatible with EPIP-016. Worker, scheduling, Retry, Recovery,
and runtime details SHALL remain behind the boundary.

Integrity SHALL require qualified Evidence, content, lineage, set, and manifest digests under
ADR-EPIP017-09. Digest validity proves integrity, not semantic eligibility or authority.

## Handoff Manifest

The Manifest SHALL bind:

- Handoff Identity, manifest domain and version;
- source Semantic Plan and terminal requirement identities;
- intended frozen EPIP-016 contract and compatibility profile;
- subject, scope, temporal boundary, Knowledge Boundary, and registry snapshot reference;
- canonically ordered Terminal Evidence identities and qualified digests;
- each member's semantic metadata, provenance, lineage, Commit and Durable Result references;
- mandatory, optional, partial, valid-empty, absent, rejected, and excluded dispositions;
- closure and completeness profile, evidence, and verdict;
- conflicts, revisions, conversions, redactions, and assumptions;
- canonicalization, digest, determinism, schema, and certification profiles;
- Handoff Authority, validation authority, logical creation boundary, and expiry if governed;
- complete diagnostic references affecting interpretation; and
- Manifest Digest.

Manifest Authority SHALL arise only from successful validation and authorized publication. A
Manifest MUST NOT incorporate runtime state merely to make validation convenient. Version change,
membership change, corrected Evidence, profile change, or target-contract change SHALL create a new
Handoff Identity and lineage; published manifests are immutable.

## Completeness Model

Every Manifest SHALL name exactly one terminal completeness profile frozen by the Semantic Plan
and compatible with EPIP-016. Completeness SHALL be evaluated over requirements, not merely present
items.

- Mandatory Evidence SHALL be eligible or have an expressly permitted absence disposition.
- Optional Evidence MAY be omitted only according to its predeclared semantics.
- Partial Evidence SHALL be rejected unless the profile names its admissible dimensions and effect.
- Valid-empty Evidence SHALL remain distinct from Missing Evidence.
- Rejected Evidence SHALL remain visible in diagnostics but outside membership.
- Conflicting or ambiguous Evidence SHALL fail unless the frozen plan contains a deterministic
  resolution whose result is itself eligible.

An **Incomplete Transfer** exists when any closure or completeness predicate is unsatisfied,
unknown, contradictory, or unverifiable. It SHALL fail closed. A degraded handoff is permitted only
when “degraded” is an explicit complete terminal profile established before execution; it SHALL not
be invented after failure.

## Authority Transfer

Authority SHALL change through these phases:

1. EPIP-017 authorities produce, commit, validate, close, and present the Manifest. EPIP-017 owns
   no Decision authority.
2. Boundary Acceptance Authority validates the presented immutable artifact without acquiring
   producer execution authority.
3. One atomic acceptance creates the Transfer Acceptance Record and establishes EPIP-016 as the
   sole downstream Decision Framework authority for that Handoff Identity.
4. EPIP-017 loses authority to modify, supplement, replace, retract, or republish the accepted
   transfer. It retains immutable historical and audit responsibilities only.

Rejection transfers no authority. Presentation, transport receipt, validation start, or durable
storage SHALL not constitute acceptance. Acceptance and rejection SHALL be mutually exclusive and
terminal for the presented Handoff Identity.

EPIP-016 SHALL not receive EPIP-017 execution authority. “Authority transfers” means responsibility
for downstream interpretation begins exactly once; it does not move leases, producers, or
orchestration ownership. EPIP-016 SHALL not request mutation of an accepted set. New or corrected
Evidence requires a new EPIP-017 request, Semantic Plan, execution lineage, Manifest, and distinct
handoff.

## Validation Model

Transfer validation SHALL independently verify:

1. Manifest structure, domain, version, canonical representation, and digest;
2. Handoff, Evidence, content, provenance, lineage, Commit, and result identities;
3. Handoff and acceptance authorities, scopes, validity, and non-revocation;
4. target EPIP-016 contract and compatibility profile;
5. set membership, canonical ordering, duplication, and scope;
6. every member's Commit, durability, integrity, semantic validity, temporal eligibility, trust,
   and certification;
7. closure across terminal requirements and dependencies;
8. completeness, optionality, partiality, absence, cardinality, conflict, and revision rules;
9. absence of forbidden operational artifacts or reconstructable authority;
10. uniqueness and timeliness of the handoff identity; and
11. consistency between Manifest Digest and referenced qualified digests.

Validation SHALL use immutable authoritative facts. Cache presence, runtime availability, producer
claims, transport metadata, or current versions SHALL not substitute. Every failed predicate SHALL
be recorded; no validator MAY repair, infer, or waive a failure.

## Boundary Conditions

The following MUST NOT cross, whether embedded, referenced for consumption, or reconstructable:

- Scheduler or worker state and identity;
- mutable runtime or producer instance state;
- Checkpoint, Snapshot-as-runtime, lease, fence, token, lock, or credential;
- Invocation, Attempt, Retry, Recovery, Compensation, or speculative-execution state;
- Execution Window, Execution Barrier, Dispatch Plan, Execution Group, or operational dependency;
- Operational Context, queue, placement, timeout allocation, or resource state;
- Execution Ledger or replay ledger;
- Cache Entry, invalidation state, or cache freshness;
- provisional, rejected, late, duplicate, stale, or uncommitted output; and
- planner internals, registry discovery state, diagnostics control state, or execution trace.

Semantic Plan identity MAY cross only as immutable provenance and contract identity, not as planner
state or instruction to EPIP-016. Commit Record identity MAY cross only as an integrity and
authority reference, not as an Execution Ledger projection. Only terminal semantic Evidence and
the validating Manifest cross constitutionally.

## Failure Handling

- **Rejected handoff:** validation failed; no authority transfers. A new presentation requires a
  new or explicitly revalidated identity according to the failed predicate.
- **Incomplete handoff:** closure or completeness failed; it SHALL not be partially accepted.
- **Duplicate handoff:** an existing acceptance or terminal presentation exists for the identity;
  duplicate processing SHALL be idempotently rejected or recognized without a second transfer.
- **Late handoff:** its validity, request, temporal, or authority boundary expired; it is rejected.
- **Corrupted handoff:** any canonical content or digest cannot be verified; it is quarantined.
- **Version mismatch:** Manifest, Evidence, schema, profile, or EPIP-016 contract is unsupported;
  it is rejected, never silently converted.
- **Digest mismatch:** the affected artifact and entire transfer are rejected.
- **Identity mismatch:** domain, lineage, membership, or target identity disagrees; it is rejected.
- **Authority mismatch:** presenter or accepter lacks exact scope; it is rejected and audited.
- **Boundary violation:** forbidden operational state is present; it is rejected and quarantined.

Failure SHALL follow ADR-EPIP017-13. Retry of transport or validation MUST NOT become duplicate
semantic publication. Replanning, Recovery, or Evidence correction SHALL create appropriate new
lineage and never mutate the rejected Manifest.

## Handoff Lifecycle

States SHALL be **Assembled**, **Validated**, **Presented**, **Accepted**, **Rejected**, **Expired**,
and **Archived**.

- Assembled SHALL transition only to Validated, Rejected, or Expired.
- Validated SHALL transition only to Presented, Rejected, or Expired.
- Presented SHALL transition atomically only to Accepted, Rejected, or Expired.
- Accepted, Rejected, and Expired SHALL transition only to Archived.
- Archived SHALL be terminal.

Accepted SHALL exist at most once per Handoff Identity. No transition may return to an earlier
state or change membership.

## Handoff Invariants

1. EPIP-017 ends and EPIP-016 begins at one explicit boundary.
2. EPIP-017 never creates Decision, Candidate, Confidence, or inference authority.
3. EPIP-016 never reconstructs producer execution or generates EPIP-017 Evidence.
4. Only immutable terminal semantic Evidence crosses.
5. Only closed Evidence Sets may cross.
6. Completeness is profile-specific, explicit, and validated over requirements.
7. Every Evidence member is committed and durable.
8. Execution and runtime state never cross.
9. Authority changes exactly once on atomic acceptance.
10. Rejection transfers no authority.
11. Accepted handoff identity and membership are immutable.
12. Transfer never rewrites execution or Decision history.
13. Replay never recreates execution or acceptance authority.
14. Optionality and degraded behavior are declared before execution.
15. Valid-empty, missing, partial, and rejected Evidence remain distinct.
16. Runtime order cannot affect membership or canonical ordering.
17. Duplicate or late handoff cannot create a second Decision input.
18. Digest validity never substitutes for semantic or authority validation.
19. EPIP-016 receives no Dispatch Plan, Checkpoint, Retry, Recovery, Cache, or Ledger.
20. Corrections require a new request and handoff lineage.

## Determinism

Identical terminal requirements, authoritative committed Evidence, temporal facts, profiles,
versions, and authorities SHALL yield the same closure, completeness, membership, canonical order,
Manifest representation, identity, digest, and validation verdict.

Worker identity, scheduling, parallel interleaving, cache outcome, Retry count, Recovery path,
physical timing, storage locator, and transport segmentation MUST NOT cross or affect the result.
Serial, parallel, fresh, cached, retried, and recovered execution SHALL yield equivalent handoffs
when they satisfy the same Semantic Plan and profile.

## Replay Compatibility

Replay MAY reproduce or verify the Terminal Evidence Set, canonical Manifest, validation inputs,
closure, completeness, acceptance/rejection verdict, and exact EPIP-016 Decision input projection.
It SHALL preserve the original versions, policies, temporal facts, knowledge boundary, authorities,
and Transfer Acceptance Record.

Replay SHALL NOT recreate producer execution authority, reopen barriers, restore Checkpoints,
republish Evidence, create a second acceptance, invoke production EPIP-016, or modify the accepted
Decision input. A replayed handoff SHALL remain non-authoritative and separately identified.

## Diagnostics

Diagnostics SHALL distinguish missing mandatory Evidence, invalid optionality, inadmissible partial
Evidence, duplicate member, duplicate transfer, late transfer, authority violation, Manifest
corruption, digest mismatch, identity mismatch, version mismatch, target-contract mismatch,
boundary violation, incomplete closure, completeness failure, provenance or lineage gap, temporal
ineligibility, uncommitted Evidence, and forbidden runtime leakage.

Each diagnostic SHALL bind Handoff Identity, affected Evidence, expected and observed facts,
profile and version, authority, logical boundary, severity, and disposition. Diagnostics SHALL not
repair, complete, accept, republish, or launch Decision.

## Audit

Audit SHALL preserve assembly inputs, terminal requirements, membership decisions, exclusions,
closure and completeness evidence, canonical ordering, manifests and digests, all validation
predicates, authorities, lifecycle transitions, presentations, acceptance or rejection, duplicate
and late attempts, boundary violations, EPIP-016 target contract, replay, migration, diagnostics,
and certification evidence.

Audit SHALL prove exactly one acceptance, the exact Decision input, and that no execution state or
Decision work crossed in the wrong direction.

## Certification Rules

Certification SHALL prove at minimum:

1. Every member is eligible, committed, durable, immutable, and integrity-valid.
2. Closure covers all terminal and transitive requirements.
3. Completeness correctly distinguishes mandatory, optional, partial, empty, missing, and rejected.
4. Canonical membership, ordering, identity, representation, and digest are deterministic.
5. Every forbidden operational artifact is rejected.
6. Acceptance is atomic, unique, and irreversible.
7. Rejected, incomplete, duplicate, late, corrupt, incompatible, and unauthorized cases fail closed.
8. EPIP-017 cannot create Decision work and EPIP-016 cannot reconstruct execution.
9. Serial, parallel, cached, retried, and recovered paths produce equivalent handoffs.
10. Replay reproduces validation without recreating authority.
11. Version migration preserves meaning and cannot widen the boundary.
12. EPIP-016 behavior remains equivalent to its frozen public contract.

Failure SHALL prohibit the affected handoff profile, manifest version, adapter, migration path, or
consumer contract from institutional use.

## Migration

Legacy transfers SHALL be classified as terminal Evidence handoff, direct producer publication,
runtime-coupled transfer, partial transfer, Decision-coupled transfer, or ambiguous. Only transfers
with provable committed Evidence, closure, completeness, identity, authority, and compatibility MAY
be migrated to an eligible Manifest.

Missing historical facts SHALL not be invented. Runtime-coupled or ambiguous transfers SHALL be
quarantined, retained for diagnostic replay, or routed through the legacy path until retired. A
migrated Manifest SHALL have new identity and immutable lineage to the legacy artifact.

ADR-EPIP017-16 SHALL govern compatibility epochs, comparison, dual-run validation, rollback, and
legacy retirement. Migration SHALL not cause two authoritative Decision inputs.

## Backward Compatibility

EPIP-016 v1.5.17 remains unchanged. This ADR SHALL not modify its Kernel, Replay, EventBus,
financial engines, execution, serialization, public APIs, Evidence semantics, inference, graph,
candidate, confidence, Decision, explanation, or certification behavior.

Any handoff adapter MAY translate representation only when semantic and behavioral equivalence is
certified. It SHALL not add dependencies, fabricate Evidence, weaken completeness, expose
orchestration state, or require EPIP-016 to understand EPIP-017 artifacts. Until certified, the
legacy EPIP-016 input path SHALL remain authoritative under ADR-16 governance.

## Forbidden Behaviours

The following are forbidden:

1. Runtime, execution, planner, scheduler, cache, Checkpoint, Retry, or Recovery leakage.
2. Dispatch Plan, Barrier, Window, Attempt, lease, fence, token, worker, or Ledger transfer.
3. EPIP-016 execution reconstruction.
4. Decision, Candidate, Confidence, inference, or recommendation generation inside EPIP-017.
5. EPIP-017 Evidence generation, producer orchestration, or dependency resolution inside EPIP-016.
6. Transfer of provisional, uncommitted, rejected, stale, late, or speculative output.
7. Partial acceptance of an incomplete set.
8. Runtime invention of optionality, degraded mode, or absence semantics.
9. Acceptance based only on transport success, readability, or digest match.
10. Duplicate acceptance, authority return, or mutation after acceptance.
11. Silent version conversion or Manifest repair.
12. Replay creating production acceptance or Decision input.
13. Correction or supplementation of an accepted Manifest in place.
14. Producer publication directly to EPIP-016.

## Alternatives Considered

### Stream Evidence Directly as Producers Finish

Rejected. Physical completion order would define Decision input and completeness could not be
proven.

### Transfer the Execution Ledger for EPIP-016 to Reconstruct Evidence

Rejected. It leaks orchestration, duplicates semantic authority, and couples EPIP-016 to runtime.

### Permit Partial Handoff and Let EPIP-016 Decide Sufficiency

Rejected. It transfers EPIP-017 completeness responsibility and changes frozen EPIP-016 behavior.

### Shared Mutable Evidence Registry

Rejected. Authority would not change once, history could mutate, and replay would be ambiguous.

### Immutable Closed Terminal Evidence Set and Manifest

Accepted. It creates a narrow, deterministic, auditable, backward-compatible, one-way boundary.

## Decision

EPIP-017 SHALL terminate by presenting one immutable Handoff Manifest for one closed Terminal
Evidence Set. Only committed, durable, eligible semantic Evidence SHALL cross. Atomic acceptance
SHALL change downstream authority exactly once; thereafter EPIP-016 alone owns all Decision
Framework responsibilities.

No execution artifact, operational context, mutable state, or orchestration authority SHALL cross.
Any uncertainty in identity, authority, integrity, compatibility, closure, or completeness SHALL
fail closed.

## Consequences

### Positive

- EPIP-016 remains frozen and isolated from orchestration.
- Decision input is complete, immutable, deterministic, and replayable.
- Authority transition is singular and auditable.
- Runtime variability cannot affect boundary semantics.
- Failures and partiality cannot leak as accidental Decision inputs.

### Negative

- Handoff waits for full profile-specific closure.
- Manifest and compatibility certification add governance cost.
- Corrected Evidence requires a new request and lineage.
- Some legacy direct-publication paths cannot migrate automatically.

### Trade-offs

EPIP accepts boundary latency and strict rejection to prevent semantic coupling, duplicate Decision
inputs, incomplete Evidence, and irreversible contamination of a frozen institutional framework.

## Compatibility

Compatibility SHALL cover Evidence contracts, schema, semantic meaning, temporal interpretation,
canonicalization, digest, manifest, completeness profile, provenance projection, and EPIP-016
behavior. Readability or API shape alone is insufficient. Material change requires a new version,
lineage, certification, and ADR-16 governance.

## Non-goals

This ADR does not define transport, API, serialization, adapter implementation, storage, launch
mechanism, EPIP-016 internals, Decision logic, producer logic, trading, risk, execution, or any
Programme A implementation.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 through ADR-EPIP017-14 and frozen EPIP-016 v1.5.17.
ADR-EPIP017-16 SHALL govern rollout and compatibility without widening this boundary, changing
acceptance semantics, or permitting dual authority.

No new blocking ADR dependency is introduced.

## Future Evolution

Additional consumers, signed manifests, remote attestation, privacy-preserving provenance,
federated handoff, and new completeness profiles MAY evolve only through versioned contracts and
ADRs. They SHALL preserve closed semantic Evidence, one-way authority, immutable acceptance,
consumer isolation, and zero operational leakage.

## Approval Gate

Approval resolves the EPIP-016 handoff, Terminal Evidence Set, completeness, closure, Manifest,
validation, and Decision boundary architecture only. It approves no adapter, validator, transfer,
launcher, pipeline terminator, or Programme A.

EPIP-017 implementation remains prohibited until the complete ADR-EPIP017-01 through
ADR-EPIP017-18 corpus is accepted and an independent review grants
**APPROVED AS FROZEN ARCHITECTURE**.
