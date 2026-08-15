# ADR-EPIP017-16 — Migration, Compatibility and Architectural Evolution Governance

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-15, ADR-EPIP017-17, and ADR-EPIP017-18 are approved, frozen,
and normative. Together, ADR-EPIP017-01 through ADR-EPIP017-18 constitute the complete mandatory
constitutional architecture of EPIP-017. This ADR MUST NOT weaken, reinterpret, replace, or
silently amend any frozen contract.

This ADR defines governance only. It authorizes no implementation, deployment, migration run,
release, manager, adapter, placeholder, or Programme A activity.

## Executive Summary

EPIP-017 SHALL evolve only through explicit, versioned, certified, and auditable contracts.
Migration SHALL occur within identified **Migration Epochs** and **Compatibility Epochs**, each
with closed scope, one authoritative path, immutable source and target identities, acceptance
criteria, divergence policy, rollback boundary, and retirement conditions.

Legacy and target paths MAY coexist for comparison, but only one SHALL be authoritative for any
request scope and epoch. Shadow outputs are non-authoritative and MUST NOT enter downstream
Evidence, cache authority, handoff, or EPIP-016 Decision input. Authority SHALL never transfer from
traffic percentage, deployment state, successful execution, operator convenience, or elapsed time.

Compatibility SHALL be explicit, directional, multidimensional, use-specific, version-bounded,
and certified. Schema or byte readability alone SHALL never imply semantic, temporal,
deterministic, authority, replay, recovery, concurrency, or handoff compatibility. Unknown
compatibility SHALL fail closed.

Rollback SHALL be a new, prospective, explicitly authorized activation decision. It SHALL preserve
all migrations, results, failures, handoffs, and authority history. It MUST NOT revive expired or
retired authority, erase target activity, retag historical artifacts, or create a second
authoritative EPIP-016 input.

Architectural evolution SHALL be additive or versioned. A change affecting a constitutional
invariant, authority boundary, semantic meaning, identity domain, determinism relation, or handoff
contract requires a new ADR and independent architecture review. Implementation convenience SHALL
never weaken the frozen architecture.

## Purpose

This ADR establishes institutional governance for Migration, Compatibility, Version Evolution,
Legacy Support, Deprecation, Retirement, Rollback, and Architectural Stability. It defines the
authorities, identities, lifecycles, invariants, diagnostics, audit, replay, and certification
needed to evolve EPIP without dual authority or historical rewriting.

## Problem Statement

Even a sound target architecture can fail during transition. Legacy code may remain authoritative
indefinitely, shadow results may leak into production, apparent equality may be treated as
compatibility, rollback may restore obsolete authority, or version aliases may rewrite which
contract governed historical execution.

Uncontrolled evolution creates:

- two competing producers or handoff paths for one obligation;
- silent semantic changes behind stable schemas or public APIs;
- incompatible temporal, identity, digest, replay, or recovery interpretations;
- incomplete lineage across migrated artifacts;
- legacy activation through fallback or configuration drift;
- retirement before replay, audit, retention, or rollback obligations end;
- “rollback” that deletes evidence of the failed release; and
- permanent undocumented coexistence with no exit criteria.

A frozen constitutional model must therefore govern not only target contracts but every interval
in which old and new contracts coexist.

## Architectural Context

ADR-EPIP017-01 requires exactly one authoritative path during migration. ADR-02 and ADR-03 require
explicit producer compatibility, trust, certification, lifecycle, and registry governance.
ADR-04 and ADR-05 require semantic and temporal migration without inferred meaning. ADR-06 and
ADR-07 preserve plan and execution identity. ADR-08 and ADR-09 govern determinism, versioned
profiles, identity, digests, and lineage. ADR-10 governs durable history and cache invalidation.
ADR-11 governs Migration Replay. ADR-12 through ADR-14 govern preserved state, recovery, and
parallel equivalence. ADR-15 prohibits dual Decision inputs and operational leakage at handoff.

This ADR coordinates those immutable contracts. It does not override their domain authorities.

## Definitions

### Migration

A governed transition of an identified scope from one authoritative versioned contract or path to
another while preserving meaning, identity lineage, historical authority, replay, audit, and
rollback evidence.

### Migration Scope

The closed set of producers, capabilities, Evidence types, subjects, tenants, requests, plans,
artifacts, stores, replay modes, handoff profiles, consumers, and compatibility dimensions covered
by one migration decision.

### Migration Epoch

An immutable, versioned interval during which one declared migration policy, source, target,
authority map, comparison contract, and exit criteria govern a scope.

### Migration Boundary

The authoritative logical cut separating source-governed work from target-governed work. Every
request SHALL bind exactly one side as authoritative before execution admission.

### Compatibility Epoch

An immutable interval in which a declared set of directional version combinations is certified for
specified uses. Compatibility SHALL not extend beyond its epoch implicitly.

### Compatibility Contract

The versioned, directional declaration of source, target, consumer, use, dimensions, transformations,
losses, invariants, exclusions, profiles, evidence, validity, and certification verdict.

### Compatibility Window

The bounded period or logical scope in which a Compatibility Contract may be used for admission.
It SHALL not imply coexistence authority or automatic migration.

### Version Identity

A domain-qualified identity binding artifact or contract family, semantic version, authority,
profiles, compatibility epoch, canonicalization, certification, and immutable lineage.

### Version Lineage

The immutable, typed, directional relations among predecessor, successor, compatible-with,
incompatible-with, migrates-from, supersedes, deprecates, retires, and rollback-target versions.

### Legacy Component

A producer, planner, runtime, store, cache, replay path, artifact, handoff path, adapter, or contract
that predates the target EPIP-017 authority and remains governed by its original legacy rules until
explicit migration.

### Shadow Execution

Non-authoritative execution of a comparison path against the same declared request scope. Shadow
outputs are diagnostic and certification evidence only.

### Deprecation

An authoritative notice that a version or component remains usable only within a bounded policy
while replacement and retirement obligations are active.

### Retirement

The authoritative prohibition of new use in a declared scope after eligibility and preservation
conditions are satisfied. Retirement SHALL not delete history.

### Rollback

A new prospective authority decision that changes the active path for future admitted work to an
eligible prior or alternative version. It SHALL not reverse historical execution.

### Evolution Authority

The authority permitted to approve architectural version introduction, compatibility epochs,
migration activation, deprecation, retirement, and rollback, subject to independent domain
authorities and certification. It SHALL not self-certify or rewrite domain facts.

### Migration Manifest

The immutable artifact binding Migration identity, scope, source, target, epoch, boundaries,
compatibility contracts, mappings, authority assignment, comparison policy, acceptance criteria,
rollback, retention, retirement, and certification evidence.

### Divergence

A typed difference between source and target observations under a declared comparison contract.
Divergence SHALL not be reduced to terminal value inequality.

## Migration Model

Every migration SHALL have one Migration Manifest and SHALL progress through inventory,
classification, compatibility assessment, shadow validation, certification, bounded activation,
verification, stabilization, and retirement eligibility. Skipped phases require an explicit ADR,
not an operational exception.

### Migration Scope and Boundary

Scope SHALL be finite, canonical, and non-overlapping with any concurrently authoritative migration
unless precedence is explicit and certified. Each request SHALL bind Migration Epoch, Compatibility
Epoch, authoritative path, profiles, and boundary before planning or execution.

Work admitted before a boundary SHALL complete under its original authority unless an existing
failure or cancellation contract explicitly terminates it. Work admitted after the boundary SHALL
use the newly authorized path. In-flight work MUST NOT change authority in place.

### Migration Eligibility

Migration MAY be eligible only when:

- source and target identities, contracts, authorities, and scopes are complete;
- every required compatibility dimension has an explicit verdict;
- historical ambiguity and unsupported artifacts are classified;
- deterministic Migration Replay and shadow comparison evidence exists;
- failure, recovery, concurrency, storage, replay, and handoff behavior is certified;
- no dual-authority or double-handoff path exists;
- rollback eligibility, scope, retention, and authority are defined;
- diagnostics and audit are complete; and
- retirement and exit criteria are measurable and governed.

Eligibility is necessary but not sufficient. Evolution Authority SHALL issue a separate activation
decision.

### Migration Validation

Validation SHALL cover architecture, semantics, temporal behavior, identity, digests, plans,
execution lifecycle, failures, caches, replay, preservation, recovery, parallel equivalence,
Terminal Evidence Set, and EPIP-016 behavioral equivalence. It SHALL include successful, empty,
partial, rejected, failed, cancelled, retried, recovered, concurrent, corrupted, and historical
cases.

Migration acceptance SHALL not require source and target physical traces to match. It SHALL require
the equivalence relation declared for every affected domain. Any unexplained divergence SHALL fail
closed.

### Migration Lifecycle

States SHALL be **Proposed**, **Inventoried**, **Classified**, **Validated**, **Shadowed**,
**Certified**, **Authorized**, **Active**, **Stabilized**, **Completed**, **Rejected**,
**RolledBack**, and **Archived**.

- Proposed SHALL transition only to Inventoried or Rejected.
- Inventoried SHALL transition only to Classified or Rejected.
- Classified SHALL transition only to Validated or Rejected.
- Validated SHALL transition only to Shadowed, Certified where shadowing is proven inapplicable, or
  Rejected.
- Shadowed SHALL transition only to Certified or Rejected.
- Certified SHALL transition only to Authorized or Rejected.
- Authorized SHALL transition only to Active, Rejected, or RolledBack before activation.
- Active SHALL transition only to Stabilized or RolledBack.
- Stabilized SHALL transition only to Completed or RolledBack.
- Completed, Rejected, and RolledBack SHALL transition only to Archived.
- Archived SHALL be terminal.

Rollback SHALL not move the lifecycle backward. It creates a terminal migration disposition and a
new activation lineage.

## Compatibility Model

Compatibility SHALL be explicit, directional, use-specific, epoch-bound, and independently
certified. It SHALL be assessed separately for:

- semantic meaning and Evidence obligations;
- schema and representation;
- temporal, calendar, availability, revision, and knowledge semantics;
- identity, canonicalization, digest, and lineage;
- producer capability, configuration, trust, and certification;
- Semantic and Dispatch Plans;
- Invocation, lifecycle, failure, Retry, Recovery, and Commit;
- Durable Results, Cache Entries, preservation, and retention;
- determinism, numeric behavior, serial/parallel equivalence, and replay;
- security, privacy, authority, and visibility; and
- Terminal Evidence Set, Manifest, and EPIP-016 behavior.

### Backward Compatibility

A target version is backward-compatible for a declared use only when it can consume or preserve
source-version artifacts and behavior without weakening any source guarantee or changing
historical interpretation.

### Forward Compatibility

A source version is forward-compatible for a declared use only when it can safely interpret a
target-version artifact through an explicit contract. Unknown fields, profiles, or semantics MUST
NOT be ignored unless the contract proves that omission is safe for that exact use.

### Cross-Version Compatibility

Cross-version compatibility SHALL name both versions, direction, consumer, operation, profiles,
transformations, losses, restrictions, and certification evidence. Transitivity SHALL NOT be
assumed. Compatibility between A and B and between B and C does not prove A and C compatibility.

### Compatibility Guarantees

Every guarantee SHALL state whether it preserves strict, semantic, operational, replay,
certification, migration, recovery, or handoff equivalence. A weaker guarantee SHALL not satisfy a
stronger consumer. Unknown, expired, revoked, ambiguous, or out-of-window compatibility SHALL fail
closed.

Transformations SHALL create new identities and lineage. Lossy transformation MAY be permitted for
diagnostic or observational use only when loss is explicit; it SHALL not gain authoritative
execution, recovery, certification, or handoff eligibility unless separately proven.

## Version Governance

Every architectural artifact, contract, profile, policy, manifest, and compatibility decision
SHALL have Version Identity and immutable lineage. Version aliases such as “latest,” “current,” or
“default” MUST NOT appear in authoritative historical manifests without resolving to an immutable
identity.

### Version Authority

Version Authority MAY issue a version identity after domain ownership, change classification,
compatibility impact, migration obligation, and certification requirements are established. It
SHALL not certify its own semantic or operational correctness.

### Version Certification and Activation

Certification SHALL bind exact artifact, environment, profiles, consumers, scope, evidence,
validity, and verdict. Successful certification does not activate a version. Evolution Authority
SHALL issue a separate activation fact with scope, epoch, boundary, predecessor, rollback target,
and authoritative-path assignment.

### Change Classification

- Representation-only change requires proof that canonical meaning and all qualified digests are
  preserved or explicitly versioned.
- Operational change requires Dispatch, lifecycle, failure, concurrency, and replay assessment.
- Semantic change requires new semantic versions, plans, compatibility contracts, and handoff
  certification.
- Constitutional change affecting an invariant or authority boundary requires a new ADR and
  independent institutional review.

### Version Retirement

Retired versions SHALL remain identifiable and historically interpretable. Retirement SHALL not
reuse or erase their identifiers. New activation of a retired version requires a new version or an
explicit exceptional ADR; ordinary rollback authority is insufficient.

## Legacy Governance

Every Legacy Component SHALL have an owner, identity, original contract, authoritative scope,
dependencies, consumers, known gaps, isolation boundary, support state, migration disposition,
retention, and retirement criteria.

Legacy support SHALL be explicit and time- or condition-bounded. It SHALL not imply EPIP-017
registration, trust, certification, compatibility, or authority. Legacy components MAY remain
authoritative only within the exact pre-migration scope assigned by the active Migration Epoch.

### Legacy Isolation and Coexistence

Legacy and target paths MAY coexist only as:

- one authoritative path and one or more isolated shadow paths; or
- disjoint authoritative scopes whose partition is immutable, exhaustive, and deterministic.

For one request, Evidence obligation, and handoff scope, two paths MUST NOT be authoritative.
Shadow execution SHALL use separate identity, storage, cache namespace, ledger, diagnostics, and
handoff prohibition. Shadow results MUST NOT satisfy dependencies, populate authoritative caches,
trigger recovery, or enter EPIP-016.

### Legacy Replacement

Replacement SHALL require certified equivalence, explicit activation, bounded rollback, and
complete lineage. Target success SHALL not rewrite legacy results. Legacy divergence SHALL remain
visible after replacement.

Legacy MUST NEVER become authoritative through target failure, timeout, health check, routing
default, missing configuration, rollback script, or operator convenience. Any legacy fallback is a
new explicit authority decision governed as Rollback or a predeclared disjoint scope.

## Deprecation Model

A Deprecation Notice SHALL identify version or component, scope, authority, rationale, successor,
compatibility window, support guarantees, prohibited new uses, migration obligations, target
timeline or exit conditions, rollback implications, and retention requirements.

Deprecation lifecycle states SHALL be **Proposed**, **Announced**, **Effective**, **MigrationDue**,
**RetirementEligible**, **Withdrawn**, and **Archived**.

- Proposed SHALL transition to Announced, Withdrawn, or Archived.
- Announced SHALL transition to Effective, Withdrawn, or Archived.
- Effective SHALL transition to MigrationDue, RetirementEligible, or Withdrawn.
- MigrationDue SHALL transition to RetirementEligible or Withdrawn.
- RetirementEligible and Withdrawn SHALL transition only to Archived.
- Archived SHALL be terminal.

Withdrawal of deprecation SHALL be a new governance fact and SHALL not erase the notice. Timeline
changes require explicit authority and audit. Deprecation SHALL not itself transfer authority or
retire a component.

## Retirement Model

Retirement eligibility SHALL require:

- no new authoritative admissions in the declared scope;
- migration completion and stabilization evidence;
- target certification and compatibility obligations satisfied;
- rollback window closed or an alternative eligible rollback target established;
- all in-flight source work resolved under original authority;
- replay, audit, legal hold, retention, security, and historical interpretation preserved;
- caches invalidated or isolated without deleting durable history;
- documentation of unsupported consumers and disposition; and
- independent retirement validation.

Only Retirement Authority MAY retire. Retirement validation SHALL be separate from ownership and
operation. Retirement SHALL create an immutable fact, remove future eligibility, preserve identity
and lineage, and retain artifacts required for replay and audit.

Destruction is separate from retirement and SHALL follow each domain's retention contract. A
retired component's historical contract, binaries or reproducible references, profiles, manifests,
and interpretive evidence SHALL be retained as required for replay.

## Rollback Model

Rollback MAY be eligible only when:

- the target path has a classified failure, unacceptable divergence, certification loss, security
  event, or governance trigger;
- the rollback scope and prospective boundary are closed and explicit;
- the rollback target remains supported, certified, compatible, secure, and operationally eligible;
- no retired, revoked, expired, or historically ambiguous authority is revived;
- in-flight target work has an explicit completion, cancellation, isolation, or failure disposition;
- no duplicate Commit, Evidence publication, cache authority, handoff, or EPIP-016 Decision input
  can occur;
- state and data written by the target are directionally compatible or isolated;
- replay and audit preservation are complete; and
- a forward-recovery or re-migration path is declared.

Only Rollback Authority MAY authorize rollback. Rollback Authority SHALL be distinct from the
target runtime and SHALL not infer eligibility from health checks alone.

Rollback SHALL create a new Rollback identity, activation fact, Compatibility Epoch, and Migration
lineage. It applies only to work admitted after its boundary. Historical source and target activity
remain under their original authority. Rollback MUST NOT delete, retag, overwrite, or reclassify
past artifacts.

Rollback lifecycle states SHALL be **Requested**, **Validated**, **Authorized**, **Activated**,
**Verified**, **Completed**, **Rejected**, **Failed**, and **Archived**. Every transition SHALL be
forward-only, explicit, and audited. Completion does not erase the failed migration.

## Authority Model

- Evolution Authority SHALL approve architectural evolution and epoch activation without
  redefining domain truth.
- Migration Authority SHALL govern Migration Manifests, boundaries, and lifecycle.
- Compatibility Authority SHALL issue directional Compatibility Contracts.
- Version Authority SHALL issue identities and lineage.
- Certification Authority SHALL independently assess exact versions and scopes.
- Legacy Authority SHALL maintain only assigned legacy scope.
- Deprecation and Retirement Authorities SHALL govern their separate lifecycle decisions.
- Rollback Authority SHALL authorize prospective reactivation without rewriting history.
- Domain authorities from ADR-01 through ADR-15 retain semantic, temporal, execution, replay,
  storage, recovery, concurrency, and handoff decisions.
- Audit Authority SHALL preserve and verify facts without activating anything.

No authority SHALL self-approve all stages. Separation of proposal, compatibility assessment,
certification, activation, rollback, and retirement SHALL be demonstrable. Technical deployment,
configuration access, ownership, majority traffic, or storage possession SHALL not grant authority.

## Evolution Invariants

1. Frozen architectural contracts never weaken implicitly.
2. Migration never rewrites history.
3. Compatibility is explicit, directional, multidimensional, scoped, versioned, and certified.
4. Unknown compatibility fails closed.
5. Every request has exactly one authoritative path.
6. Shadow execution is always non-authoritative and isolated.
7. Legacy never gains or regains authority silently.
8. Version lineage is immutable, typed, and complete.
9. In-flight work never changes authority in place.
10. Activation and certification are separate decisions.
11. Deprecation and retirement are separate decisions.
12. Retirement preserves replay, audit, and historical interpretation.
13. Rollback is prospective and never restores historical authority.
14. Rollback never creates duplicate Commit, handoff, or Decision input.
15. Version aliases never replace immutable identities in authority records.
16. Migration transformations create new identities and lineage.
17. Compatibility transitivity is never assumed.
18. Divergence remains visible and cannot be averaged away.
19. Constitutional change requires a new ADR and independent review.
20. Replay remains reproducible across migration, deprecation, retirement, and rollback.

## Determinism

Given identical Migration Manifest, scope, authoritative facts, versions, profiles, policies,
logical boundary, and certification evidence, migration eligibility, routing, comparison,
activation, rollback, and retirement verdicts SHALL be identical.

Traffic arrival, host topology, deployment order, health-check timing, operator identity, cache
state, filesystem order, or wall-clock race SHALL not determine authority. Request routing SHALL
derive from immutable scope and epoch facts. Comparison SHALL use canonical membership, ordering,
equivalence profiles, and divergence taxonomy.

## Replay Compatibility

Migration Replay SHALL preserve source and target identities, original authorities, contracts,
inputs, outputs, profiles, divergences, epochs, activation, rollback, deprecation, retirement, and
audit facts. Historical Replay SHALL interpret each artifact under its original epoch and SHALL
not apply current compatibility retroactively.

Replay MAY reproduce migration validation, compatibility verdicts, shadow comparisons, handoff
projections, and rollback decisions. It SHALL not activate versions, transfer authority, repopulate
production caches, restore retired components, or generate a production handoff.

Retirement SHALL retain sufficient artifacts or certified reproducible references for every
required Replay Mode. Missing evidence SHALL remain explicit and may make replay inconclusive; it
SHALL not be reconstructed from current state.

## Diagnostics

Diagnostics SHALL distinguish migration failure, incomplete inventory, eligibility rejection,
compatibility violation, unknown compatibility, version conflict, lineage gap, epoch mismatch,
dual authority, shadow leakage, undocumented coexistence, unexplained divergence, legacy
activation, deprecation violation, retirement violation, replay-retention failure, rollback
rejection, rollback failure, contract mismatch, in-flight boundary violation, duplicate handoff,
and unauthorized evolution.

Each diagnostic SHALL bind scope, request, source and target versions, epochs, contracts,
authorities, profiles, expected and observed facts, severity, and disposition. Diagnostics SHALL
not migrate, activate, rollback, deprecate, retire, or transfer authority automatically.

## Audit

Audit SHALL preserve every inventory, classification, Migration Manifest, Compatibility Contract,
version identity, lineage relation, shadow run, comparison, divergence, certification, authority
decision, boundary, request routing, activation, deprecation, retirement, rollback, exception,
diagnostic, retention decision, and historical interpretation.

Audit SHALL prove one authoritative path per scope, absence of shadow leakage, exact authority at
every epoch, preservation of in-flight work, all EPIP-016 handoffs, and every rejected alternative.
It SHALL remain append-only across rollback and retirement.

## Certification Rules

Institutional certification SHALL prove at minimum:

1. Inventory and classification cover the complete migration scope.
2. Compatibility is directional and certified across every affected dimension.
3. Unknown or expired compatibility fails closed.
4. Each request resolves to exactly one authoritative path.
5. Shadow state cannot enter dependencies, caches, recovery, handoff, or EPIP-016.
6. Source and target comparisons cover all terminal and failure outcomes.
7. Identity, digest, temporal, replay, recovery, concurrency, and handoff contracts remain intact.
8. Activation occurs only after independent certification and authority.
9. In-flight work preserves original authority at boundaries.
10. Rollback is prospective, preserves history, and creates no duplicate authority.
11. Retirement removes future admission while preserving replay and audit.
12. Legacy cannot reactivate from failure, configuration drift, or operator convenience.
13. Constitutional changes cannot bypass ADR review.
14. EPIP-016 remains behaviorally unchanged and receives exactly one authoritative handoff.

Certification SHALL include real shadow, divergence, failure, rollback, replay, and retirement
campaigns. Nominal success comparison is insufficient. Failure SHALL block the affected version,
scope, epoch, adapter, migration, rollback, or retirement.

## Backward Compatibility

EPIP-016 v1.5.17 and all frozen EPIP-017 ADR contracts remain unchanged. Existing public APIs,
Kernel, Replay, EventBus, financial engines, execution, serialization, and Decision Framework
behavior SHALL not be modified by migration governance.

Legacy paths MAY remain authoritative only within explicitly assigned pre-migration scopes. They
SHALL not be wrapped and relabeled as EPIP-017 without full contract conformance. Compatibility
adapters MAY translate representation only under certified contracts and MUST NOT fabricate
identity, authority, semantics, completeness, determinism, or provenance.

Backward compatibility SHALL not mean permanent legacy support. Its window, guarantee, consumer,
exceptions, and retirement conditions SHALL be explicit. Where equivalence cannot be proven, the
legacy path SHALL remain isolated, be retired without migration, or require a new architectural
decision.

## Forbidden Behaviours

The following are constitutionally forbidden:

1. Implicit migration or undocumented scope expansion.
2. Silent, inferred, transitive, or schema-only compatibility.
3. Hidden rollback or rollback by configuration drift.
4. Automatic authority transfer from deployment, traffic, success, or timeout.
5. Legacy reactivation after retirement or outside assigned scope.
6. Weakening a frozen contract through implementation or compatibility policy.
7. Rewriting, deleting, retagging, or reclassifying history.
8. Undocumented legacy and target coexistence.
9. Dual authoritative execution, Evidence publication, cache population, handoff, or Decision input.
10. Shadow output satisfying production dependencies or barriers.
11. Version alias used as immutable historical identity.
12. Activation based solely on certification, and certification inferred from activation.
13. Retirement before replay, audit, retention, rollback, or in-flight obligations are resolved.
14. Rollback reviving expired, revoked, incompatible, or retired authority.
15. Compatibility transformation mutating source artifacts in place.
16. Divergence suppression, averaging, or acceptance without declared policy.
17. Constitutional change without a new ADR and independent review.

## Alternatives Considered

### Big-Bang Replacement

Rejected. It removes comparison evidence, makes rollback unsafe, and concentrates authority risk.

### Permanent Dual Authority

Rejected. Competing results, caches, handoffs, and Decisions become unavoidable and history cannot
identify the authoritative path.

### Compatibility by API and Schema Stability

Rejected. Stable shapes do not preserve semantics, time, identity, determinism, recovery, or
Decision behavior.

### Automatic Fallback to Legacy

Rejected. Failure would silently transfer authority and could duplicate execution or handoff.

### In-Place Upgrade with Mutable Version Labels

Rejected. Historical interpretation, replay, lineage, and certification would become unstable.

### Epoch-Governed Migration with One Authoritative Path

Accepted. It supports comparison, bounded rollout, explicit rollback, retirement, and evolution
without weakening architectural contracts.

## Decision

EPIP-017 SHALL govern evolution through immutable Migration Manifests, Migration Epochs,
Compatibility Epochs, directional Compatibility Contracts, version lineage, independent
certification, explicit activation, isolated shadow execution, prospective rollback, and governed
retirement.

Exactly one path SHALL be authoritative for each request scope and epoch. Legacy and target may
coexist only without overlapping authority. Unknown compatibility, unexplained divergence, missing
lineage, or ambiguous authority SHALL fail closed.

Frozen constitutional contracts SHALL never be weakened by migration or implementation. Material
constitutional evolution requires a new ADR and independent review.

## Consequences

### Positive

- Migration cannot create dual authority.
- Compatibility claims become precise and certifiable.
- Legacy coexistence has explicit isolation and exit conditions.
- Rollback preserves history and avoids duplicate Decision inputs.
- Retirement preserves replay and audit.
- Future architectural change remains governed over ten-year horizons.

### Negative

- Inventory, shadow execution, certification, retention, and audit are expensive.
- Some legacy components will remain isolated or be retired without automatic migration.
- Activation and rollback require explicit institutional decisions.
- Compatibility matrices and version lineage will grow over time.
- Strict failure closure can delay release.

### Trade-offs

EPIP accepts slower evolution and greater governance cost to prevent silent semantic drift,
permanent legacy ambiguity, double authority, unreproducible history, and unsafe rollback.

## Compatibility

This ADR is the governing meta-contract for compatibility claims; it does not declare any concrete
version pair compatible. Every such claim SHALL exist in a separate immutable Compatibility
Contract with exact scope and evidence.

## Non-goals

This ADR does not define deployment procedures, rollout percentages, feature-flag mechanisms,
database migrations, packaging, CI/CD, release automation, implementation strategies, transport,
APIs, or production code. It defines no producer, trading, financial, Decision, risk, portfolio,
or execution logic.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 through ADR-EPIP017-15, ADR-EPIP017-17,
ADR-EPIP017-18, and frozen EPIP-016 v1.5.17. The complete ADR-EPIP017-01 through ADR-EPIP017-18
corpus has no remaining blocking ADR dependency for constitutional completeness.

Future ADRs MAY specialize concrete migrations, version families, capacity, security, privacy,
distributed consistency, or deployment governance. They MUST conform to all sixteen frozen ADRs.

## Future Evolution

New producer families, distributed runtimes, storage formats, replay profiles, identity algorithms,
handoff consumers, security domains, or governance automation MAY evolve only through versioned
contracts, compatibility evidence, certification, and authority decisions.

Automated governance MAY prepare evidence or execute a narrowly pre-authorized decision, but it
SHALL emit the same identities, boundaries, lifecycle facts, and audit as a human authority. It
MUST NOT infer compatibility, activate a version, rollback, or retire outside an explicit grant.

## Approval Gate

Approval of ADR-EPIP017-01 through ADR-EPIP017-18 completes the mandatory constitutional ADR set
for EPIP-017. It does not approve implementation or certify the combined architecture
automatically.

Before Programme A, the complete ADR-EPIP017-01 through ADR-EPIP017-18 set SHALL undergo a final
independent cross-ADR architecture review. Implementation remains prohibited until that review
issues **APPROVED AS FROZEN ARCHITECTURE** with no blocking finding.
