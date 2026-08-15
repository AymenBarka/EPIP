# ADR-EPIP017-12 — Snapshot, Checkpoint and State Preservation

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-11 are approved, frozen, and normative. This ADR MUST NOT
modify their authority, identity, execution, storage, replay, determinism, or compatibility
contracts.

This ADR defines preserved-state architecture only. It authorizes no implementation, engine,
serialization format, persistence technology, placeholder, or Programme A activity.

## Executive Summary

EPIP-017 SHALL preserve two constitutionally distinct state artifacts. A **Snapshot** is an
immutable, point-in-boundary observation created for inspection, audit, replay, diagnosis, or
certification. It has no execution authority and MUST NOT resume execution. A **Checkpoint** is an
immutable, validated continuation package for one bounded execution lineage. It MAY authorize a
new execution attempt only after explicit recovery admission under ADR-EPIP017-13; it MUST NOT
become historical truth, a Commit, or a Durable Result.

Every preserved artifact SHALL bind a typed identity, preservation purpose, consistency boundary,
scope, lineage, authority, temporal facts, governing profiles, source artifact identities, and an
integrity digest under ADR-EPIP017-09. Publication SHALL make content immutable. Restoration SHALL
never be implicit. Observation, preservation, restoration, recovery, replay, commitment, caching,
and historical authority SHALL remain separate operations.

Historical preservation SHALL be append-only. Corrections, supersession, archival, retirement,
and permitted destruction SHALL create explicit lineage and audit facts; they SHALL NOT rewrite a
preserved artifact. Replay MAY consume preserved state according to ADR-EPIP017-11 but SHALL NOT
mutate or promote it. A Checkpoint MAY support continuation; only the normal fenced invocation and
atomic commit path of ADR-EPIP017-07 MAY create authoritative results.

## Purpose

This ADR establishes the constitutional state-preservation model for EPIP-017. It SHALL define:

- Snapshot and Checkpoint meaning, authority, identity, scope, completeness, and lineage;
- observation, continuation, historical, operational, diagnostic, and certification preservation;
- preservation and consistency boundaries;
- lifecycle, retention, visibility, admissibility, restoration, and reuse rules;
- compatibility with replay, recovery, determinism, audit, and migration; and
- prohibited overlap with Durable Results, Cache Entries, Execution Ledgers, and Commit Records.

## Problem Statement

Execution state is not a single concept. An immutable view suitable for audit cannot safely carry
continuation authority. A resumable package cannot become proof that an execution committed.
Without a normative distinction, EPIP-017 could:

- resume from a partial or temporally inconsistent observation;
- treat a Checkpoint as authoritative historical Evidence;
- rewrite execution history during restoration;
- confuse preservation identity with result, ledger, or cache identity;
- replay mutable runtime state or import present-day facts into historical analysis;
- publish stale work after lease or fence loss;
- make parallel scheduling and recovery nondeterministic;
- retain secrets, process handles, clocks, or external connections as executable state; or
- destroy artifacts required by lineage, audit, replay, certification, or legal hold.

A frozen architecture therefore requires explicit artifact types, consistency boundaries,
authority separation, lifecycle transitions, restoration admission, and certification rules before
any Snapshot Engine, Checkpoint Engine, Replay Engine, or Recovery Engine exists.

## Architectural Context

ADR-EPIP017-01 assigns orchestration authority and preserves the single authoritative path.
ADR-EPIP017-02 constrains producer capabilities and side effects. ADR-EPIP017-03 governs registry
snapshots, admission, trust, and certification. ADR-EPIP017-04 defines Evidence semantics and
dependencies. ADR-EPIP017-05 defines temporal availability, knowledge boundaries, and
cross-timeframe semantics. ADR-EPIP017-06 separates Semantic Plans from Dispatch Plans.

ADR-EPIP017-07 defines Invocation, Attempt, lease, fence, token, Commit, and append-only Execution
Ledger authority. ADR-EPIP017-08 defines determinism profiles. ADR-EPIP017-09 requires distinct
Snapshot and Checkpoint identity and digest domains. ADR-EPIP017-10 separates authoritative
Durable Results from disposable Cache Entries. ADR-EPIP017-11 makes replay read-only,
mode-specific, isolated, and non-authoritative.

This ADR specializes those frozen rules for preserved state. ADR-EPIP017-13 SHALL govern whether a
validated Checkpoint is eligible for recovery and whether a continuation attempt is admitted.
ADR-EPIP017-14 SHALL govern parallel quiescence and serial/parallel equivalence. This ADR does not
pre-approve either decision.

## Definitions

### Preserved State

A typed, immutable representation of admitted facts captured at one declared Preservation
Boundary for an explicit purpose. Preserved State is either observational state in a Snapshot or
restorable continuation state in a Checkpoint. The term SHALL NOT imply execution authority.

### Snapshot

An immutable observation of admitted state at one declared consistency boundary. A Snapshot MAY
support inspection, replay, audit, diagnosis, comparison, or certification. It MUST NOT resume,
continue, commit, cancel, retry, or otherwise control execution.

### Checkpoint

An immutable continuation package containing the admitted restorable state and restore contract
for one bounded execution lineage. A Checkpoint MAY be considered for explicit recovery admission.
It MUST NOT itself resume execution, own a lease, authorize a Commit, or establish historical
truth.

### Snapshot Identity

A domain-qualified, versioned identity under ADR-EPIP017-09 that binds Snapshot scope, purpose,
boundary, source identities, temporal facts, profiles, lineage, completeness declaration, and
Snapshot Digest. It SHALL never identify a Checkpoint.

### Checkpoint Identity

A domain-qualified, versioned identity under ADR-EPIP017-09 that binds continuation scope,
boundary, source Invocation and Attempt, restore contract, temporal facts, profiles, lineage,
eligibility constraints, and Checkpoint Digest. It SHALL never identify a Snapshot.

### Preservation Boundary

The declared logical cut at which included state is mutually interpretable. It binds captured
logical time, knowledge boundary, registry and plan versions, ledger frontier, committed-result
frontier, dependency frontier, in-flight-state treatment, and governing profiles.

### Consistency Boundary

The certified rules proving that all members of one preserved artifact describe the same declared
logical cut. Physical simultaneity is not required; causal consistency and an explicit frontier
are required.

### Snapshot Scope

The closed set of domains, identities, temporal intervals, timeframes, producers, plans,
Invocations, results, ledger facts, and projections observed by a Snapshot.

### Checkpoint Scope

The closed set of one continuation root and its admitted resumable state, dependencies, completed
frontier, pending frontier, authority prerequisites, and restore constraints. Scope MUST NOT span
independent authority domains merely for operational convenience.

### Snapshot Authority

The authority permitted to admit source facts, establish a consistency boundary, verify
completeness, publish a Snapshot, govern visibility and retention, and record lifecycle facts. It
SHALL have no execution, commit, result, replay-verdict, or recovery-admission authority.

### Checkpoint Authority

The authority permitted to admit restorable state, establish a continuation boundary, validate a
restore contract, publish a Checkpoint, govern visibility and lifetime, and record lifecycle facts.
It SHALL have no authority to admit a recovery attempt, acquire a lease, issue a token, commit a
result, or rewrite the source Invocation.

### Historical State

Preserved facts bound to their original Historical Time, Knowledge Boundary, authority, identity,
version, and availability. Historical State SHALL remain append-only and SHALL NOT be silently
reinterpreted under current facts.

### Restorable State

The deterministic, bounded data required to reconstruct an eligible continuation input without
preserving live runtime resources or authority. Restorable State becomes executable only through
explicit recovery admission and a new valid Attempt under ADR-EPIP017-07 and ADR-EPIP017-13.

### Preservation Manifest

The immutable manifest enumerating artifact type, identity, purpose, boundary, scope, source
identities and digests, omissions, completeness, profiles, authority, lineage, visibility,
retention class, integrity status, and lifecycle state.

### Restore Contract

The immutable Checkpoint declaration of the exact continuation point, required environment and
profiles, admitted state, excluded state, validation predicates, compatibility constraints,
expected dependency frontier, and authority prerequisites. It SHALL NOT grant restoration.

### Restoration

The explicit, audited construction of a new execution-attempt input from an admitted Checkpoint.
Restoration SHALL NOT mutate the Checkpoint or revive the original Attempt.

### Continuation Lineage

The immutable directional relationship from a source Invocation and Attempt through a Checkpoint
to a separately identified restoration and new Attempt. Lineage SHALL preserve every source and
supersession identity.

## Snapshot Model

### Snapshot Purpose and Scope

A Snapshot SHALL declare exactly one primary preservation purpose: historical, operational,
diagnostic, certification, migration, or governed composite observation. A composite observation
MUST enumerate each projection and MUST NOT gain the authority of any projected source.

Snapshot scope SHALL be closed and canonical. Unbounded expressions such as “current system
state,” “latest data,” or “all available Evidence” MUST NOT define scope. Scope SHALL identify all
included and intentionally excluded domains and the reason for every material omission.

### Snapshot Identity and Authority

Snapshot Identity SHALL be generated and verified in the Snapshot domain of ADR-EPIP017-09.
Snapshot Authority SHALL publish only after boundary consistency, source integrity, authority,
scope, and completeness have been evaluated. Publication SHALL NOT attest that every possible
system fact is included; it SHALL attest conformity to the declared scope and completeness class.

### Snapshot Completeness

Every Snapshot SHALL declare one completeness class:

- **Complete** — every fact required by the declared scope and boundary is present and verified;
- **Projection-complete** — every fact required by the named projection is present, while excluded
  domains are explicitly outside scope;
- **Partial** — one or more required facts are absent, inaccessible, corrupt, or unresolved; and
- **Indeterminate** — completeness cannot be established from preserved authority.

Partial and Indeterminate Snapshots MAY support diagnostics or explicitly tolerant replay. They
MUST NOT support certification requiring completeness and MUST NOT conceal missing facts with
current or inferred values.

### Snapshot Visibility

Snapshot visibility SHALL be explicit, least-privilege, purpose-bound, and independent of source
visibility. Inclusion SHALL NOT widen access. Redacted projections MUST preserve a binding to the
unredacted source identity, redaction authority, and excluded-field declaration without exposing
restricted content.

### Snapshot Retention

Retention SHALL be governed by purpose, lineage, audit, certification, legal hold, and source
retention obligations. Archival MAY change availability or representation but MUST preserve
identity, digest verifiability, authority, lineage, and interpretation. Destruction MAY occur only
when no governing retention, replay, certification, recovery, audit, or legal obligation remains.
It SHALL leave an immutable tombstone and destruction audit fact.

### Snapshot Lineage

Derivation, projection, redaction, correction, migration, and supersession SHALL create new
Snapshot identities and directional lineage. A later Snapshot SHALL NOT replace or mutate an
earlier Snapshot. Lineage SHALL state transformation authority, source identities, profile
versions, and whether semantic equivalence was certified.

## Checkpoint Model

### Checkpoint Purpose and Scope

A Checkpoint SHALL preserve only the state necessary for a declared continuation boundary. It
SHALL bind exactly one continuation root, source Invocation, source Attempt, Semantic Plan,
Dispatch Plan where relevant, registry snapshot, determinism profile, temporal contracts,
dependency frontier, and execution frontier.

A Checkpoint spanning multiple Invocations or dependency branches MUST declare one governed
atomic continuation group and prove a common consistency boundary. Otherwise, each continuation
root SHALL receive a distinct Checkpoint.

### Checkpoint Identity and Authority

Checkpoint Identity SHALL be generated and verified in the Checkpoint domain of
ADR-EPIP017-09. Checkpoint Authority SHALL validate the Restore Contract and publish the artifact.
It MUST NOT decide that restoration is currently safe, because eligibility can change after
publication through revocation, profile change, dependency change, lease state, or policy.

### Checkpoint Continuation

A Checkpoint SHALL specify:

- the exact completed, committed, pending, and excluded frontiers;
- which intermediate values are semantically restorable and which require recomputation;
- the original knowledge and temporal boundaries;
- required producer, capability, registry, plan, schema, canonicalization, and digest versions;
- external inputs that MUST be reacquired through governed authority;
- lease, fence, token, and Attempt facts that are historical only and MUST NOT be restored;
- validation and compatibility requirements; and
- the deterministic continuation entry point.

Restoration SHALL create a new restoration identity and a new Attempt identity. It SHALL acquire
new execution authority, lease, fence, and token. It MUST NOT revive the source Attempt or reuse
expired authority.

### Checkpoint Lifetime

Checkpoint lifetime SHALL be explicit and bounded by temporal validity, producer and capability
compatibility, registry governance, schema support, dependency validity, security policy,
retention, and recovery policy. Expiration SHALL remove continuation eligibility but SHALL NOT
rewrite the Checkpoint or erase historical lineage.

### Checkpoint Reuse

A Checkpoint MAY be restored more than once only when recovery policy explicitly permits it and
each restoration receives distinct identity, admission, Attempt, lease, fence, token, and audit
lineage. Multiple physical restorations MUST still obey ADR-EPIP017-07 single-authoritative-commit
rules. “Consumed” SHALL mean that a governed continuation was admitted; it SHALL NOT imply content
mutation or automatic destruction.

Published Checkpoints SHALL be immutable. Any changed continuation state, scope, constraint, or
profile SHALL require a new Checkpoint identity with explicit lineage.

## State Preservation Model

### State That MAY Be Preserved

Subject to scope, authority, policy, and canonicalization, preserved state MAY include:

- immutable Evidence, dependencies, plans, Durable Results, manifests, and Commit Records;
- registry snapshots, governance, trust, certification, and compatibility facts;
- temporal contracts, calendars, revisions, knowledge boundaries, and availability facts;
- append-only Execution Ledger frontiers and causally ordered lifecycle facts;
- immutable producer-declared intermediate state certified as restorable;
- dependency completion and pending frontiers;
- deterministic logical timers and timeout facts expressed under governed time semantics;
- diagnostics, metrics, audit references, and certification evidence;
- replay-local observations when explicitly scoped as non-authoritative; and
- source identities, qualified digests, profiles, lineage, omissions, and integrity status.

### State That MUST NOT Be Preserved as Restorable State

The following MUST NOT become executable Restorable State:

- live process, thread, coroutine, scheduler, stack, or instruction-pointer state;
- open files, sockets, database sessions, external connections, or mutable handles;
- wall-clock readings without governed logical-time meaning;
- active leases, fences, execution tokens, locks, credentials, secrets, or ambient authority;
- mutable shared memory, process-local caches, singleton state, or undeclared randomness;
- uncommitted side effects or claims that external effects occurred without authoritative records;
- current registry, context, calendar, market, or governance facts substituted for original facts;
- unserialized behavior, executable closures, producer instances, or environment-dependent objects;
- Cache Entries treated as authoritative source state; or
- ambiguous state whose type, authority, identity, scope, or lineage cannot be established.

Secrets MAY be referenced by governed identity where recovery policy permits reacquisition. Secret
material itself MUST NOT be embedded merely for restoration convenience.

### Historical Preservation

Historical preservation SHALL capture facts as known and authorized at the original Knowledge
Boundary. It SHALL be append-only. Later corrections, revisions, revocations, or discoveries SHALL
be separately preserved and linked; they MUST NOT alter the original preserved view.

### Operational Preservation

Operational preservation MAY capture an execution observation as a Snapshot or a continuation
boundary as a Checkpoint. The artifact type SHALL be declared before publication. Operational
urgency MUST NOT convert an observation into continuation authority.

### Diagnostic Preservation

Diagnostic preservation MAY capture partial or failed state as a Snapshot. A diagnostic artifact
MUST label uncertainty, corruption, missing facts, and non-authoritative observations. It MUST NOT
be restored unless a separately published valid Checkpoint independently contains the required
state.

### Certification Preservation

Certification preservation SHALL bind the exact inputs, profiles, plans, boundaries, results,
ledgers, comparisons, diagnostics, and verdict authority required to reproduce a certification.
Certification Snapshots MUST satisfy the certification completeness class. Certification alone
SHALL NOT make a Checkpoint recovery-eligible.

### Preservation Failure

Failure to establish boundary consistency, identity, authority, integrity, scope, or required
completeness SHALL fail publication. A failed capture MAY produce a diagnostic record but MUST NOT
be presented as an Available Snapshot or Checkpoint.

## Snapshot Lifecycle

### Snapshot States

- **Created** — capture identity and proposed boundary exist; the artifact is not trusted.
- **Verified** — sources, scope, boundary, integrity, authority, and completeness were evaluated.
- **Committed** — Snapshot Authority atomically published the immutable manifest and content.
- **Available** — the committed Snapshot is accessible under visibility and retention policy.
- **Archived** — preserved but not ordinarily available; identity and verification remain intact.
- **Retired** — prohibited from new operational use while retained for history or audit.
- **Destroyed** — permitted content destruction completed and an immutable tombstone remains.
- **Rejected** — verification or publication failed; the candidate has no Snapshot authority.

### Legal Snapshot Transitions

Legal transitions SHALL be:

- Created to Verified or Rejected;
- Verified to Committed or Rejected;
- Committed to Available, Archived, or Retired;
- Available to Archived or Retired;
- Archived to Available, Retired, or Destroyed;
- Retired to Archived or Destroyed; and
- Rejected and Destroyed are terminal.

Reactivation from Archived SHALL restore availability, not mutate content or identity. Retirement
SHALL be reversible only through a new explicit governance fact and the Archived state; a Retired
Snapshot MUST NOT transition directly to Available. Destruction SHALL satisfy all retention gates.

## Checkpoint Lifecycle

### Checkpoint States

- **Created** — a candidate continuation package exists without restore authority.
- **Validated** — identity, boundary, state, Restore Contract, and integrity are valid.
- **Available** — published and eligible to be evaluated for recovery admission.
- **Consumed** — at least one explicit restoration was admitted and linked.
- **Expired** — continuation eligibility ended; historical retention MAY continue.
- **Archived** — retained outside ordinary recovery availability.
- **Retired** — administratively prohibited from future continuation.
- **Destroyed** — permitted content destruction completed and a tombstone remains.
- **Rejected** — validation failed and the candidate has no Checkpoint authority.

### Legal Checkpoint Transitions

Legal transitions SHALL be:

- Created to Validated or Rejected;
- Validated to Available, Archived, Retired, or Rejected;
- Available to Consumed, Expired, Archived, or Retired;
- Consumed to Available, Expired, Archived, or Retired only when reuse policy permits;
- Expired to Archived, Retired, or Destroyed;
- Archived to Available only after renewed validation and an explicit governance fact, or to
  Expired, Retired, or Destroyed;
- Retired to Archived or Destroyed; and
- Rejected and Destroyed are terminal.

Renewed validation SHALL NOT change content, identity, or original boundary. If compatibility or
state must change, a new Checkpoint SHALL be created. A lifecycle transition MUST NOT itself admit
restoration.

## Preservation Boundary

Every preserved artifact SHALL bind:

1. one logical capture boundary and its governing clock or causal frontier;
2. Historical Time, Knowledge Boundary, availability, revision, and calendar facts;
3. Registry Snapshot and governance epoch;
4. Semantic Plan and, where relevant, Dispatch Plan identities;
5. Execution Ledger frontier and Commit frontier;
6. included dependency and cross-timeframe frontiers;
7. treatment of in-flight Invocations and Attempts;
8. Durable Result identities and integrity states;
9. canonicalization, digest, determinism, and compatibility profiles;
10. scope, omissions, completeness, visibility, and retention; and
11. preservation authority and capture audit identity.

An artifact MUST NOT combine states from different boundaries unless the manifest defines a
causally consistent composite boundary and independently identifies each component frontier.
Physical capture order SHALL NOT redefine logical order.

For a Snapshot, in-flight state MAY be observed and labeled incomplete or transitional. For a
Checkpoint, every in-flight element MUST be classified as safely restorable, completed and
verifiable, pending and recomputable, or excluded. Ambiguity SHALL reject the Checkpoint.

## Boundary Separation

The following concepts SHALL remain non-overlapping:

| Concept | Constitutional meaning | Authority it MAY carry | Authority it MUST NOT carry |
| --- | --- | --- | --- |
| Snapshot | Immutable observation at a consistency boundary | Observation, audit, replay input | Execution continuation or Commit |
| Checkpoint | Immutable continuation package | Candidate recovery input | Historical truth, lease, token, or Commit |
| Replay | Read-only evaluation of admitted preserved facts | Replay observation and comparison | Production mutation or result authority |
| Durable Result | Authoritative preservation of an atomically committed result | Committed-result retrieval | Continuation or mutable cache state |
| Cache Entry | Disposable verified acceleration reference | Conditional reuse under cache policy | Historical or durable authority |
| Execution Ledger | Append-only lifecycle and authority facts | Execution history and causal record | Result content or resumable runtime state |
| Commit Record | Atomic authoritative outcome fact | Binding Attempt to committed result | General observation or continuation package |

A preserved artifact MAY reference these concepts. Reference SHALL NOT copy, merge, or inherit
their authority. The same bytes in two domains SHALL retain distinct qualified identities and
meanings.

## State Identity

Snapshot and Checkpoint identities SHALL be domain-separated and non-interchangeable. Each
identity SHALL include or bind:

- artifact and domain version;
- preservation purpose and authority;
- closed scope and consistency boundary;
- source identities and qualified digests;
- temporal and knowledge-boundary identity;
- registry, plan, ledger, result, producer, and capability versions as applicable;
- canonicalization, digest, determinism, schema, and compatibility profiles;
- completeness or Restore Contract identity;
- lineage, supersession, and migration facts; and
- content or manifest digest.

Identity SHALL be stable after publication. Relocation, replication, archival, or access-control
change MUST NOT alter semantic identity. Projection, redaction, content change, boundary change,
restore-contract change, or migration SHALL create a new identity and lineage.

A Snapshot Digest SHALL bind observational projection and completeness. A Checkpoint Digest SHALL
bind restorable state and Restore Contract. One SHALL NOT substitute for the other.

## Authority Model

Authority SHALL be separated as follows:

- source authorities SHALL remain authoritative for their original facts;
- Snapshot Authority SHALL admit and publish observations without acquiring source authority;
- Checkpoint Authority SHALL validate and publish continuation packages without admitting recovery;
- Preservation Authority SHALL govern capture policy, retention, visibility, archival, and
  destruction without altering source facts;
- Replay Authority SHALL admit read-only replay use under ADR-EPIP017-11;
- Recovery Authority under ADR-EPIP017-13 SHALL decide whether a Checkpoint may seed a new Attempt;
- Execution Authority under ADR-EPIP017-07 SHALL govern new Attempt, lease, fence, token, and Commit;
- Durable Result Authority under ADR-EPIP017-10 SHALL govern committed result preservation; and
- Audit and Certification Authorities SHALL record and assess compliance without mutating artifacts.

No authority SHALL infer another authority from storage possession, artifact accessibility,
identity verification, successful replay, lifecycle state, or technical ability to deserialize.

## Replay Compatibility

Replay SHALL consume preserved state without mutation and under one declared mode from
ADR-EPIP017-11. Admissibility SHALL be explicit:

| Replay mode | Snapshot admissibility | Checkpoint admissibility |
| --- | --- | --- |
| Historical | Historical Snapshot at the original Knowledge Boundary; partial only with explicit inconclusive semantics | Checkpoint MAY be observed as a historical artifact; it MUST NOT be restored |
| Certification | Complete certification Snapshot with verified profiles and authority | Checkpoint MAY be inspected and restoration logic evaluated in isolation; it MUST NOT authorize production continuation |
| Operational | Operational Snapshot or preserved ledger projection at the original boundary | Checkpoint MAY reproduce restoration decisions in an isolated replay domain; no live authority is restored |
| Diagnostic | Complete, Partial, or Indeterminate diagnostic Snapshot with limitations visible | Checkpoint MAY be inspected for inconsistency; mutation and production restoration are forbidden |
| Simulation | Explicit simulation projection derived from admissible Snapshot state | Checkpoint MAY seed isolated simulation only after conversion to a separately identified simulation input |
| Regression | Versioned comparison Snapshot with stable baseline identity | Checkpoint MAY test restore compatibility in isolation; outputs remain non-authoritative |
| Explainability | Snapshot containing or referencing preserved provenance and reasoning artifacts | Checkpoint is admissible only as provenance about continuation; it MUST NOT invent explanation |
| Migration | Pre-migration and post-migration Snapshots with separate identities and lineage | Checkpoints MAY be compatibility-tested or migrated into a new separately identified Checkpoint; original state remains unchanged |

“Checkpoint replay” SHALL mean read-only evaluation or isolated reproduction of restoration
semantics. It SHALL NOT mean production restoration. A Snapshot SHALL never be converted in place
to a Checkpoint. Any governed derivation SHALL create a new Checkpoint identity and independently
satisfy every Checkpoint validation rule; source observation alone is insufficient.

## Recovery Compatibility

Only an Available or reuse-permitted Consumed Checkpoint MAY be considered for production
continuation. Consideration SHALL additionally require:

- verified identity, digest, boundary, scope, lineage, and Restore Contract;
- supported producer, capability, registry, plan, schema, canonicalization, digest, and determinism
  profiles;
- satisfied temporal, security, dependency, governance, and retention constraints;
- no revocation, corruption, expiration, retirement, or incompatible migration;
- explicit Recovery Authority admission under ADR-EPIP017-13; and
- creation of a new Attempt with new lease, fence, token, and ledger facts under ADR-EPIP017-07.

Snapshots MAY only be observed. Historical, diagnostic, certification, replay-local, migration,
partial, indeterminate, archived-without-readmission, retired, rejected, expired, or destroyed
preserved states MUST NEVER resume production.

A recovery decision SHALL state which preserved values are reused and which are recomputed.
Recomputation SHALL use the original Semantic Plan and knowledge constraints unless a separately
governed migration or new Invocation explicitly establishes different semantics.

## Determinism

Preservation SHALL conform to ADR-EPIP017-08 and ADR-EPIP017-09. For identical admitted source
facts, boundary, scope, profiles, ordering, and authority, preservation SHALL produce canonically
equivalent manifests and digests.

Determinism requires:

- canonical membership and ordering;
- logical or causal capture boundaries independent of wall-clock race;
- explicit treatment of in-flight, missing, partial, and corrupt state;
- preserved original temporal, revision, registry, plan, producer, and capability facts;
- domain-separated Snapshot and Checkpoint identities;
- stable qualified digests and canonicalization profiles;
- deterministic completeness and restore-validation verdicts;
- no ambient environment, mutable cache, undeclared randomness, or current-state substitution; and
- equivalent results across certified serial and parallel capture under ADR-EPIP017-14.

Checkpoint restoration SHALL be deterministic with respect to its admitted Checkpoint, Restore
Contract, recovery decision, new execution authority, and declared determinism profile. This does
not require physical Attempt identity or timing equality. Any permitted nondeterminism SHALL be
declared by profile and MUST NOT weaken authority or historical consistency.

## State Invariants

1. Snapshots are immutable observations.
2. Checkpoints are immutable continuation packages.
3. Snapshots never resume execution.
4. Checkpoints never rewrite history or establish committed-result authority.
5. Publication freezes content, boundary, scope, identity, and manifest.
6. Historical preservation is append-only.
7. Replay consumes preserved state but never mutates it.
8. Restoration is explicit, separately identified, admitted, and audited.
9. Restoration creates a new Attempt and new execution authority.
10. Active leases, fences, tokens, locks, and ambient authority are never restored.
11. Snapshot Identity and Checkpoint Identity are never interchangeable.
12. Artifact storage does not grant preservation, replay, recovery, execution, or result authority.
13. Partial or indeterminate state never silently becomes complete.
14. A Checkpoint with ambiguous in-flight state is rejected.
15. Source authority remains with the source domain.
16. Corrections, projections, migrations, and supersession create new identity and lineage.
17. Cache state is never historical or continuation authority.
18. Destruction never occurs while a governing retention obligation remains.
19. Every observation and restoration preserves original temporal and knowledge boundaries.
20. Only ADR-EPIP017-07 atomic commit can create an authoritative execution result.

## Diagnostics

Diagnostics SHALL be typed, stable, attributable, and non-authoritative. They SHALL distinguish at
minimum:

- **snapshot inconsistency** — members do not satisfy the declared consistency boundary;
- **snapshot incompleteness** — required scope facts are absent or unresolved;
- **checkpoint inconsistency** — continuation members do not share a valid boundary;
- **checkpoint non-restorability** — the Restore Contract cannot deterministically reconstruct the
  declared continuation input;
- **preservation corruption** — content or manifest integrity verification fails;
- **identity mismatch** — domain, version, manifest, content, or digest identity disagrees;
- **scope mismatch** — actual content lies outside or fails to satisfy declared scope;
- **lineage inconsistency** — source, derivation, supersession, migration, or restoration lineage is
  missing, cyclic, or contradictory;
- **unexpected restoration** — restoration occurred without eligible state or explicit admission;
- **authority mismatch** — an actor performed an operation outside its authority;
- **profile incompatibility** — required schema, digest, canonicalization, determinism, or
  compatibility profile is unavailable or unsupported;
- **temporal mismatch** — Historical Time, Knowledge Boundary, availability, or revision facts are
  incompatible;
- **frontier mismatch** — ledger, Commit, dependency, completed, or pending frontier disagrees;
- **forbidden-state capture** — live resources, credentials, locks, tokens, or ambient state appear;
- **retention violation** — archival, retirement, or destruction contradicts governing policy; and
- **replay mutation attempt** — replay attempted to alter preserved or authoritative state.

Diagnostics MUST preserve artifact identity, lifecycle state, boundary, scope, authority,
detected facts, expected facts, profile versions, severity, disposition, and audit identity. A
diagnostic MUST NOT repair, reclassify, restore, retire, or destroy an artifact automatically.

## Audit

The preservation audit SHALL be append-only and SHALL preserve:

- capture request, purpose, authority, and policy;
- source identities, qualified digests, visibility, and integrity states;
- boundary construction, logical ordering, scope, omissions, and completeness evidence;
- manifest, Snapshot or Checkpoint identity, and publication decision;
- every lifecycle transition, actor, authority, reason, and logical time;
- access, projection, redaction, replication, relocation, and archival facts as governed;
- validation, corruption, quarantine, retirement, destruction, and tombstone facts;
- lineage across derivation, supersession, migration, replay use, and restoration;
- every recovery evaluation, admission, rejection, and new Attempt identity;
- profiles, compatibility verdicts, diagnostics, and certification references; and
- legal hold and retention decisions.

Audit SHALL distinguish observation from continuation, availability from eligibility, validation
from admission, and restoration from Commit. Audit records SHALL NOT mutate preserved artifacts or
inherit their authority.

## Certification Rules

Architectural and future executable certification SHALL prove at minimum:

1. Snapshot and Checkpoint identities and digests are domain-separated.
2. Equivalent captures under one boundary and profile are deterministic.
3. Snapshot publication proves declared scope and completeness.
4. Checkpoint publication proves boundary consistency and Restore Contract validity.
5. Snapshot restoration is impossible through every supported authority path.
6. Checkpoint restoration requires explicit recovery admission and a new Attempt.
7. No lease, fence, token, credential, lock, or ambient authority is restored.
8. Restoration cannot produce multiple authoritative commits.
9. Partial, corrupt, expired, retired, rejected, and incompatible artifacts are denied as required.
10. Replay is read-only for every admissible preserved-state class.
11. Historical facts remain unchanged after correction, migration, replay, or recovery.
12. Projection, redaction, supersession, and migration preserve lineage.
13. Serial and parallel preservation are equivalent under ADR-EPIP017-14.
14. Retention, archival, legal hold, and destruction preserve required authority and tombstones.
15. Diagnostics distinguish every mandatory failure class.
16. Legacy ambiguous artifacts cannot enter authoritative recovery without explicit migration.

Certification failure SHALL prohibit the affected artifact class, profile, migration path, or
recovery path from institutional use. It SHALL NOT be downgraded to an operational warning.

## Migration

Migration SHALL classify each legacy artifact as Snapshot, Checkpoint, Durable Result, Cache
Entry, Execution Ledger projection, Commit Record, diagnostic artifact, or ambiguous. Classification
MUST be based on meaning and authority, not filename, storage location, shape, or historical label.

Legacy artifacts lacking a provable boundary, source identity, authority, integrity, scope, or
lineage SHALL be quarantined or admitted only as explicitly Partial or Indeterminate diagnostic
Snapshots. They MUST NOT become recovery-eligible Checkpoints.

A migrated Snapshot or Checkpoint SHALL receive a new versioned identity in the correct domain and
immutable lineage to the legacy identity. Migration SHALL preserve original bytes or an approved
digest reference, original interpretation, known omissions, uncertainty, and migration authority.
It SHALL NOT backfill unknown historical facts or manufacture restore eligibility.

Checkpoint migration SHALL require deterministic compatibility evidence for the Restore Contract,
producer and capability versions, plans, schema, temporal model, profiles, and dependency frontier.
If those requirements cannot be proven, the artifact SHALL remain observational only.

Migration Replay under ADR-EPIP017-11 MAY compare old and new representations. A successful replay
SHALL not itself authorize production restoration. ADR-EPIP017-16 SHALL govern compatibility
epochs, transition policy, deprecation, rollback, and institutional migration certification.

## Backward Compatibility

This ADR SHALL NOT modify EPIP-016, its Decision Framework, Kernel, Replay, EventBus, financial
engines, execution, serialization, public APIs, or released behavior. EPIP-016 SHALL neither
consume a Checkpoint nor receive replay-local or restored intermediate state.

Existing EPIP-017 contracts remain unchanged:

- producer and Evidence semantics remain governed by ADR-02 and ADR-04;
- temporal meaning remains governed by ADR-05;
- plan identity remains governed by ADR-06;
- execution and Commit authority remain governed by ADR-07;
- determinism and digest identity remain governed by ADR-08 and ADR-09;
- Durable Result and Cache authority remain governed by ADR-10; and
- replay remains isolated and non-authoritative under ADR-11.

Compatibility SHALL be additive through explicit preserved-state domains. No legacy object SHALL
gain Snapshot or Checkpoint meaning implicitly. Unsupported consumers SHALL continue without
preservation integration. Removal or reinterpretation of a preserved-state contract SHALL require
governed versioning, migration, compatibility evidence, and ADR approval.

## Forbidden Behaviours

The following are constitutionally forbidden:

1. Snapshot becoming execution or continuation authority.
2. Checkpoint becoming historical, Evidence, result, or Commit authority.
3. Mutation of a published Snapshot or Checkpoint.
4. History rewriting, silent correction, or in-place migration.
5. Implicit, automatic, or unaudited restoration.
6. Reusing the source Attempt, lease, fence, token, lock, or credential.
7. Mixed, shared, inferred, or interchangeable Snapshot and Checkpoint identity.
8. Replay mutating, consuming, retiring, or promoting preserved state.
9. Cache Entry treated as preserved authoritative state.
10. Snapshot used as a Checkpoint because its content appears sufficient.
11. Checkpoint treated as a Commit because execution later succeeds.
12. Present-day facts substituted into historical preservation.
13. Partial or ambiguous state labeled Complete or restorable.
14. Cross-boundary state aggregation without a certified composite boundary.
15. Publication before scope, identity, authority, integrity, and boundary verification.
16. Restoration based solely on possession, availability, or successful deserialization.
17. Restoration from expired, corrupt, retired, rejected, destroyed, or incompatible state.
18. Destruction while retention, lineage, replay, recovery, audit, certification, or legal hold
    requires preservation.
19. Diagnostic or certification observation resuming production.
20. Preservation implementation bypassing the single authoritative execution and Commit path.

## Alternatives Considered

### One Universal Preserved-State Artifact

Rejected. A universal artifact collapses observation and continuation authority, makes identity
ambiguous, and permits accidental restoration of audit material.

### Snapshot as Both Observation and Resume Point

Rejected. Resumability requires a closed Restore Contract, stricter consistency, explicit
eligibility, and recovery admission. Assigning it to every Snapshot creates hidden execution
authority.

### Checkpoint as Authoritative Historical Record

Rejected. A Checkpoint records continuation state, not whether an outcome committed or what was
authoritatively visible. Execution Ledger, Commit Record, and Durable Result retain those roles.

### Mutable Checkpoints Updated In Place

Rejected. Mutation destroys deterministic identity, lineage, replay evidence, concurrent safety,
and the ability to prove what state was restored.

### Physical Runtime Image Preservation

Rejected. Process memory, handles, locks, clocks, credentials, and scheduler state carry ambient
authority and environment coupling that cannot satisfy institutional determinism or portability.

### Implicit Latest Checkpoint Recovery

Rejected. “Latest” is not a semantic or authority rule. It can select stale, incompatible,
revoked, or causally invalid state and makes recovery nondeterministic.

### Separate Immutable Snapshot and Checkpoint Domains

Accepted. This preserves constitutional authority separation, typed identity, deterministic
boundaries, replay safety, recovery governance, auditability, and long-term evolution.

## Decision

EPIP-017 SHALL adopt separate immutable Snapshot and Checkpoint domains.

A Snapshot SHALL preserve observation only. A Checkpoint SHALL preserve a candidate continuation
package only. Neither artifact SHALL inherit authority from referenced sources or storage.
Checkpoint restoration SHALL require explicit recovery admission and the normal new-Attempt,
lease, fence, token, ledger, and atomic-Commit path.

All preserved artifacts SHALL use closed scopes, explicit consistency boundaries, typed identities,
qualified digests, immutable manifests, append-only lineage, governed lifecycles, deterministic
profiles, least-privilege visibility, explicit retention, and auditable authority.

No runtime convenience, replay mode, migration, certification result, storage mechanism, or future
engine MAY weaken these distinctions.

## Consequences

### Positive

- Observation and continuation authority cannot be confused.
- Replay receives stable, immutable, mode-admissible inputs.
- Recovery receives explicit, validated candidate state without bypassing execution authority.
- Historical facts survive correction, supersession, migration, and restoration.
- Identity, lineage, retention, diagnostics, and certification become testable contracts.
- Partial and failed captures remain visible without gaining false authority.
- Future storage and serialization technologies can evolve behind stable semantics.

### Negative

- Two artifact domains, authorities, lifecycles, identities, and certification suites are required.
- Checkpoint creation is stricter and more expensive than observational capture.
- Long-lived replay, audit, and recovery obligations increase retention and governance cost.
- Some legacy state will remain observational and cannot be made resumable.
- Recovery must reacquire authority and may recompute state rather than resume transparently.

### Trade-offs

EPIP accepts additional storage, validation, governance, and operational complexity to prevent
history rewriting, stale authority restoration, nondeterministic continuation, and false audit
evidence. Convenience is subordinate to institutional correctness.

## Compatibility

Compatibility is governed by qualified identity and explicit profiles. Byte readability SHALL NOT
equal semantic, replay, or restoration compatibility. A consumer SHALL support the artifact domain,
manifest version, canonicalization profile, digest profile, schema, temporal contract, producer and
capability versions, plan versions, and declared preservation purpose.

Snapshot compatibility MAY permit read-only projection with explicit loss declarations.
Checkpoint compatibility SHALL be stricter: any uncertainty affecting continuation semantics,
dependency frontier, temporal meaning, authority prerequisites, or deterministic state SHALL deny
restoration. Compatibility adapters SHALL create new artifacts and lineage; they MUST NOT mutate
published state.

## Non-goals

This ADR does not define:

- serialization, wire formats, database schemas, object stores, or persistence vendors;
- compression, replication, backup, transport, or storage implementation;
- capture algorithms, checkpoint frequency, scheduler policy, or performance tuning;
- failure classification, retry limits, fallback, or recovery admission policy;
- parallel capture algorithms or distributed consensus;
- Replay Engine, Recovery Engine, Snapshot Engine, Checkpoint Engine, or Migration Engine;
- producer, financial, trading, risk, Decision, or execution logic; or
- any Programme A implementation.

## ADR Dependencies

This ADR depends normatively on:

- ADR-EPIP017-01 for system boundary and orchestration authority;
- ADR-EPIP017-02 for producer execution and side-effect constraints;
- ADR-EPIP017-03 for Registry Snapshot, governance, trust, and certification;
- ADR-EPIP017-04 for Evidence and dependency semantics;
- ADR-EPIP017-05 for temporal, availability, and cross-timeframe boundaries;
- ADR-EPIP017-06 for Semantic Plan and Dispatch Plan identities;
- ADR-EPIP017-07 for Invocation, Attempt, lease, fence, token, Ledger, and Commit authority;
- ADR-EPIP017-08 for determinism profiles;
- ADR-EPIP017-09 for identity, canonicalization, digest, and lineage domains;
- ADR-EPIP017-10 for Durable Result, Cache, retention, and storage authority; and
- ADR-EPIP017-11 for replay modes, isolation, inputs, and equivalence.

The remaining architecture SHALL specialize this ADR through:

- ADR-EPIP017-13 for failure classification, retry, recovery admission, restoration disposition,
  and deterministic recovery;
- ADR-EPIP017-14 for capture quiescence, concurrent boundaries, parallel equivalence, and barriers;
- ADR-EPIP017-15 for the EPIP-016 handoff prohibition on preserved intermediate state; and
- ADR-EPIP017-16 for migration, compatibility epochs, deprecation, and rollback governance.

No circular dependency is authorized. ADR-13 MAY determine whether a Checkpoint is eligible; it
MUST NOT redefine Checkpoint content, identity, or authority. ADR-14 MAY define how a valid boundary
is established concurrently; it MUST NOT merge Snapshot and Checkpoint semantics.

## Future Evolution

Incremental Snapshots, differential Checkpoints, content-addressed deduplication, remote
attestation, encrypted preservation, jurisdictional retention, tiered archival, distributed
capture, and profile negotiation MAY evolve through versioned contracts and additional ADRs.

Such evolution SHALL preserve immutable publication, domain-separated identity, complete lineage,
explicit boundaries, historical interpretation, replay isolation, recovery admission, and the
single authoritative Commit path. Optimization MUST NOT make a delta independently authoritative;
its complete reconstruction chain SHALL remain verifiable and retention-safe.

## Approval Gate

Approval of this ADR resolves Snapshot, Checkpoint, Preservation Boundary, State Identity,
preserved-state authority, lifecycle, replay admissibility, and recovery-foundation architecture
only.

It does not approve restoration policy, retry or recovery behavior, concurrency mechanisms,
serialization, persistence, any preservation engine, or Programme A.

EPIP-017 implementation remains prohibited until the complete mandatory ADR set is accepted and
the remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
