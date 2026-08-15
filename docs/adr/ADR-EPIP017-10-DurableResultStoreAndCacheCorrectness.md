# ADR-EPIP017-10 — Durable Result Store and Cache Correctness

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-09 are approved, frozen, and normative. This ADR MUST NOT
modify their orchestration authority, producer contract, governance, Evidence semantics, temporal
model, plan separation, execution lifecycle, determinism profiles, identity hierarchy, EPIP-016
boundary, or single-authoritative-path rule.

This ADR defines storage architecture only. It authorizes no implementation, database, filesystem,
object store, cache, eviction algorithm, persistence layer, interface, placeholder, or Programme A
activity.

## Executive Summary

EPIP-017 SHALL maintain one authoritative **Durable Result Store** for committed producer results.
Only an Attempt Result accepted through the atomic Commit defined by ADR-EPIP017-07 SHALL become a
Durable Result. The Durable Result Store is the authoritative historical source for result content,
identity, provenance, commitment, lifecycle, retention, and reuse eligibility.

A **Cache** SHALL be a disposable optimization containing non-authoritative Cache Entries that
reference or reproduce already committed Durable Results. Cache presence, absence, eviction,
latency, location, freshness, or corruption MUST NOT change Semantic Plan meaning, capability or
producer selection, dependency resolution, temporal interpretation, commit authority, or EPIP-016
handoff behavior.

A Cache Entry SHALL never replace the Durable Result identity or Commit Record. Every cache hit
MUST be verified against the authoritative Durable Result manifest, exact semantic and temporal
inputs, lineage, profiles, governance state, reuse policy, and integrity identities before reuse.
If authoritative verification is unavailable, reuse MUST fail closed as a cache miss or durable
lookup failure according to policy; the cache MUST NOT promote itself to authority.

Result reuse SHALL be permitted only when the cached or durably loaded result is semantically
equivalent to a fresh result required by the exact current Semantic Plan and when every identity
dimension capable of changing behavior matches or has an explicit certified compatibility
decision. Matching values, schemas, keys, or producer names SHALL be insufficient.

Invalidation SHALL be explicit, immutable, scoped, attributable, versioned, and epoch-based. It
MUST prevent future reuse within its scope without rewriting the Durable Result, prior Commit,
historical plans, or earlier valid reuse. Revision, dependency, authority, schema, profile,
expiration, corruption, and historical-policy changes SHALL create new invalidation facts.

Retention SHALL be independently governed for durable results, cache entries, ledgers, snapshots,
checkpoints, audits, and diagnostics. Cache eviction SHALL never imply durable deletion. Durable
destruction, if legally permitted, SHALL require explicit authority, proof that no retained lineage
or audit obligation depends on the result, and an immutable destruction record. Destruction MUST
never rewrite the fact that the result existed and was committed.

## Purpose

Establish the constitutional storage, visibility, reuse, invalidation, retention, historical
preservation, authority, determinism, replay, diagnostics, and audit model for every committed
EPIP-017 result.

This ADR defines:

- when an Attempt Result becomes committed and durable;
- the Durable Result Store's authority and non-responsibilities;
- the Cache's strictly non-authoritative role;
- exact cache and durable-result reuse eligibility;
- explicit invalidation causes and propagation boundaries;
- result and cache lifecycles;
- visibility, retention, archival, retirement, and destruction governance;
- equivalence and verification rules preserving semantic and historical correctness.

## Problem Statement

Cache reuse can silently corrupt analytical correctness while still returning structurally valid
data. A value may be stale because producer code, capability semantics, configuration, context,
dependency results, source revisions, timeframe boundaries, governance, certification, numeric
profile, or canonicalization changed. A simple time-to-live or matching key cannot prove semantic
equivalence.

The original EPIP-017 proposal treated cache decisions as part of an immutable execution plan but
did not define:

- an authoritative durable result source;
- atomic publication between Commit and storage;
- cache consistency or verification;
- result and cache identity separation;
- revision-aware lineage;
- invalidation epochs and propagation;
- corruption quarantine;
- retention and destruction authority;
- historical cache isolation;
- negative-result and failure caching;
- behavior when a cache entry exists but authority cannot be verified;
- equivalence between cached and freshly computed results.

Without these contracts, cache state becomes an undocumented semantic input and historical replay
may import future or revised results. EPIP therefore requires durable authority, disposable cache,
content and lineage verification, explicit invalidation, and immutable historical preservation.

## Architectural Context

ADR-EPIP017-01 separates durable-result authority from cache, planning, execution, replay, and
audit authorities.

ADR-EPIP017-02 prohibits producer-owned hidden caches and makes producer submission distinct from
authoritative completion.

ADR-EPIP017-03 requires frozen registry, trust, certification, compatibility, and governance state.

ADR-EPIP017-04 defines Evidence semantics, dependencies, completeness, provenance, and semantic
equivalence.

ADR-EPIP017-05 defines availability, knowledge, revision, expiration, historical visibility, and
cross-timeframe identities.

ADR-EPIP017-06 excludes cache state from Semantic Plans and permits only operational lookup
authorization in Dispatch Plans.

ADR-EPIP017-07 requires one atomic Commit binding the winning Attempt Result to an immutable
Durable Result identity before downstream visibility.

ADR-EPIP017-08 requires cached and fresh results to satisfy the selected equivalence profile.

ADR-EPIP017-09 separates Durable Result, Cache Entry, Commit, storage locator, lineage, and other
identity domains.

This ADR supplies their storage constitution without selecting technology or algorithms.

## Definitions

### Attempt Result

An immutable producer result submitted by one Execution Attempt. It is non-authoritative and
non-durable until atomic Commit accepts it.

### Committed Result

An Attempt Result accepted by exactly one authoritative Commit Record for one Invocation.

### Durable Result

The immutable, integrity-verified, authoritatively retained representation of a Committed Result,
its result manifest, provenance, Commit Record reference, identity profiles, lifecycle, and storage
authority.

### Durable Result Manifest

The immutable canonical inventory binding Durable Result identity, content identity, Commit Record,
producer, capability, implementation, configuration, Semantic Plan, Invocation, input manifest,
dependency results, temporal boundary, profiles, schemas, diagnostics, provenance, retention, and
visibility.

### Durable Result Store

The authoritative persistence boundary responsible for preserving Durable Results and their
manifests, lifecycle facts, integrity, lineage, and governed retrieval.

### Fresh Result

A result produced by an authorized current Attempt and committed without satisfying the Invocation
through prior-result reuse. Fresh describes derivation path, not quality or correctness.

### Reused Result

A previously committed Durable Result accepted to satisfy a current Execution Intent after complete
reuse validation. Reuse MUST create its own execution and reuse ledger facts without creating a new
producer claim or rewriting the original Commit.

### Equivalent Result

A Durable Result proven to satisfy the semantic equivalence and all stricter profile obligations of
the current Execution Intent as if a fresh conforming execution had supplied the required Evidence.

### Historical Result

A Durable Result associated with a prior Knowledge Boundary, registry state, plan, revision, or run.
Historical status does not imply obsolete, invalid, archived, or reusable.

### Archived Result

A Durable Result moved to a governed lower-availability retention class while remaining immutable,
authoritative, addressable, and historically interpretable.

### Retired Result

A Durable Result prohibited from new reuse under a governed lifecycle decision while retained for
history, lineage, replay, audit, or legal obligations.

### Cache

A disposable, non-authoritative acceleration boundary that stores or indexes Cache Entries. It
MUST NOT own semantic, commit, governance, or historical authority.

### Cache Entry

A non-authoritative immutable copy, projection, reference, or retrieval aid for exactly one Durable
Result under one Cache Profile and cache scope.

### Cache Identity

The domain-qualified identity of one Cache Entry, distinct from Durable Result, Artifact, Commit,
Invocation, and storage-locator identities.

### Cache Scope

The explicit tenant, environment, execution profile, replay mode, governance epoch, temporal
boundary, security scope, and reuse-policy boundary within which a Cache Entry MAY be considered.

### Cache Freshness

The result of evaluating one Cache Entry against an explicit logical freshness policy and current
reuse manifest. Freshness is not authority, validity, or semantic equivalence.

### Cache Obsolescence

The governed state in which a Cache Entry is no longer preferred or eligible for future lookup due
to a newer result, policy, revision, invalidation, or retention decision. It MUST NOT mutate the
underlying Durable Result.

### Cache Invalidation Fact

An immutable, attributable, scoped fact that prevents a Cache Entry or Durable Result from future
reuse under specified plans, profiles, revisions, or governance epochs.

### Invalidation Epoch

A monotonic logical boundary under which reuse eligibility and invalidation facts are evaluated.
It MUST NOT be inferred from cache arrival or wall-clock execution order.

### Quarantine

A governed state isolating corrupted, mismatched, unauthenticated, or suspicious Cache Entries or
Durable Result representations from use while preserving evidence for diagnosis and audit.

### Storage Locator

An operational reference to physical storage. It MUST remain separate from Artifact Identity and
MUST NOT establish content, authority, or equality.

## Durable Result Model

### Commit and Durability

Only a result accepted through ADR-EPIP017-07 atomic Commit SHALL become a Durable Result.

The Commit Authority and Durable Result Authority MUST share one indivisible logical publication
boundary. Either the Durable Result Manifest, immutable content binding, Commit Record, Invocation
transition, and downstream visibility all become authoritative, or none does.

A producer return, Attempt completion, local file, message, temporary object, cache write, or
storage upload MUST NOT become a Durable Result without Commit.

### Result Identity

Durable Result identity MUST be domain-qualified under ADR-EPIP017-09 and MUST remain distinct from
Evidence, Attempt Result, Commit Record, Invocation, Cache Entry, and Storage Locator identities.

One Durable Result MAY contain one atomic group of Evidence outputs only when the capability and
Invocation contracts declare that group. Unrelated outputs MUST NOT share result authority.

### Result Authority

The Durable Result Authority SHALL own preservation, retrieval, integrity status, lifecycle, and
retention of committed results. It MUST NOT alter Evidence semantics, declare analytical truth,
select dependencies, authorize execution, issue certification, or decide EPIP-016 handoff.

### Result Visibility

A Durable Result becomes authoritative and visible only at successful Commit. Before that boundary,
no downstream Invocation, cache, snapshot, replay, handoff, or audit verdict MAY treat the Attempt
Result as committed.

Visibility MUST be role-scoped. Producers MUST NOT enumerate the store. Planners MAY receive only
governed reuse metadata, never mutable storage state as semantic input. Dispatch and execution MAY
request exact authorized lookups. Audit and replay MAY receive complete retained provenance under
their policies.

### Historical Result

Historical Results MUST retain original Semantic Plan, registry, producer, capability, temporal,
revision, profile, Commit, and lineage identities. Later correction, withdrawal, invalidation,
revocation, migration, or replacement MUST append new facts and MUST NOT alter original content or
historical visibility.

### Archived and Retired Results

Archival MAY change physical availability and operational retrieval expectations. It MUST NOT
change identity, semantic meaning, Commit authority, or historical validity.

Retirement MUST prevent new reuse in its scope but MUST preserve historical interpretation and
retention obligations.

## Durable Store Model

The Durable Result Store SHALL:

- preserve immutable committed content and Durable Result Manifests;
- validate qualified identities, canonical representations, and digests;
- bind every result to exactly one authoritative Commit Record;
- preserve complete provenance and lineage;
- expose role-scoped retrieval and reuse verification;
- record lifecycle, integrity, quarantine, archival, retirement, and destruction facts;
- preserve historical versions and invalidation epochs;
- support independent audit and replay verification;
- separate physical locators, replicas, and retention classes from identity.

The Durable Result Store MUST NOT:

- accept uncommitted producer results as authoritative;
- rewrite content or manifests;
- create Evidence semantics;
- select producers or dependencies;
- mutate Semantic or Dispatch Plans;
- decide retry, fallback, recovery, or handoff;
- treat a replica or Cache Entry as authority;
- infer freshness, validity, or compatibility from access time or storage location;
- delete history without governed retention and destruction authority.

Replication, relocation, compaction, and archival MUST preserve qualified identity and canonical
content. Physical divergence MUST fail integrity validation and trigger quarantine.

## Cache Model

Every Cache Entry MUST reference exactly one Durable Result and MUST identify:

- Cache Entry and Cache Profile identities;
- authoritative Durable Result and Commit Record identities;
- content and manifest identities;
- cache scope and security scope;
- reuse-policy and invalidation-epoch identities;
- creation source and owner;
- logical freshness and expiration facts;
- integrity-verification status;
- cache lifecycle and retention class.

A Cache Entry MUST be immutable. Refresh, relocation, revalidation, scope change, or profile change
MUST create a new Cache Entry identity or new immutable validation fact according to the governed
profile.

Cache ownership belongs to the Cache Authority for operational retention and lookup only. Cache
ownership MUST NOT transfer result, producer, Evidence, Commit, or semantic authority.

Cache visibility MUST be restricted to exact authorized lookup. Producers MUST NOT access or
populate a hidden cache. Semantic planning MUST NOT inspect live cache state. A Dispatch Plan MAY
authorize lookup without assuming a hit.

Cache lifetime MAY end through eviction, expiration, invalidation, corruption, quarantine,
retirement, or administrative removal. Ending cache lifetime MUST NOT affect Durable Result
existence or historical Commit.

Negative execution outcomes, failures, timeouts, cancellations, rejected results, and cache misses
MUST NOT be cached as Evidence or Durable Results. An operational system MAY retain separately
identified diagnostic or admission facts, but they MUST remain outside the result cache and MUST
NOT satisfy Evidence requirements.

## Cache Correctness

A Cache Entry is correct for one lookup only when all of the following are verified:

- it references an existing authoritative Durable Result and Commit Record;
- qualified identities, canonicalization profiles, digests, and content match;
- the Durable Result is not quarantined, corrupted, withdrawn, retired, or ineligible for the
  requested scope;
- exact producer, implementation, capability, contract, configuration, schema, numeric,
  determinism, and certification identities match or have explicit certified compatibility;
- exact Semantic Plan requirements, Evidence semantics, completeness, provenance, and independence
  constraints are satisfied;
- exact input-manifest and dependency-result identities match the current Execution Intent;
- context projection and every semantic input match;
- temporal boundary, availability, Knowledge Time, timeframe, calendar, watermark, revision, and
  expiration rules match;
- governance, trust, compatibility, and profile requirements remain eligible for reuse;
- no applicable invalidation fact exists at the current Invalidation Epoch;
- reuse is permitted by the Execution and Cache Profiles;
- security scope and visibility permit disclosure;
- semantic equivalence with a fresh result is certified under ADR-EPIP017-08.

All predicates MUST be true. Unknown or unverifiable predicates MUST fail closed.

A Cache Entry MAY be fresh but semantically incompatible, valid but unauthorized, unexpired but
invalidated, or intact but historically unavailable. These states MUST remain distinct.

Cached-result reuse MUST create immutable lookup, validation, reuse, and current-run ledger facts.
It MUST preserve the original producer claim and Commit rather than claiming the current run
recomputed the result.

## Cache Eligibility

### Results That MAY Be Cached

Only immutable Durable Results MAY be cached when:

- the exact Cache Profile permits the result class;
- result content and manifest are integrity-verifiable;
- producer and capability contracts declare reuse-safe semantics;
- security and retention policies permit duplication;
- temporal and revision identities are complete;
- deterministic and semantic-equivalence certification is valid;
- result size, sensitivity, and lifecycle permit the cache scope;
- no applicable prohibition or invalidation exists.

### Results That MUST NEVER Be Cached as Results

The following MUST NOT enter the result cache:

- uncommitted Attempt Results;
- partial or intermediate producer state;
- rejected, failed, cancelled, expired, aborted, superseded, or stale Attempt outputs;
- results lacking complete identity, provenance, temporal, or Commit binding;
- corrupted, quarantined, unauthenticated, withdrawn, or retired-for-reuse results;
- secret credential material or unauthorized sensitive projections;
- mutable producer state;
- runtime telemetry, failure records, negative results, or cache misses represented as Evidence;
- artifacts prohibited by legal, security, certification, or profile policy.

Valid Empty Evidence MAY be cached only when it is part of a committed Durable Result and its
capability defines exact boundary, revision, freshness, and reuse semantics. Absence MUST NOT be
cached as valid empty output.

### Results That MAY Be Recomputed

A result MAY be recomputed only through a new authorized Invocation or Attempt lineage under the
current Semantic and Dispatch Plans. Cache miss, expiry, invalidation, or eviction MUST NOT itself
authorize recomputation or retry.

Recomputation creates new execution and Commit facts. If canonical Evidence is strictly equal, the
Evidence identity MAY be equal only under its domain contract; Commit, Invocation, Attempt, and
run identities remain distinct.

### Results That MUST Be Revalidated

Every Cache Entry MUST be revalidated at every authoritative reuse decision against current
identity, integrity, invalidation, temporal, governance, security, and profile predicates.

Long-lived Durable Results MUST be revalidated for new reuse whenever certification, trust,
compatibility, revision, schema, profile, or authority state may have changed. Revalidation creates
a new validation fact and MUST NOT mutate the Durable Result.

### Results That MUST Be Reloaded

Institutional, Certification, Historical, and authoritative Replay profiles MUST establish
Durable Result authority from the authoritative manifest or a certified immutable authoritative
replica before reuse. A Cache Entry alone MUST never satisfy this requirement.

Where policy requires complete content verification, the content MUST be loaded or independently
verified against the authoritative content identity. Cache metadata alone is insufficient.

## Cache Invalidation

Invalidation MUST be an explicit immutable fact. It MUST identify:

- invalidation identity, authority, reason, and policy;
- affected Durable Result, Cache Entries, Evidence types, dependencies, producers, capabilities,
  schemas, profiles, temporal boundaries, or scopes;
- effective Invalidation Epoch;
- future-reuse impact;
- historical-use interpretation;
- propagation and closure evidence;
- remediation, revalidation, or retirement requirements.

### Explicit Invalidation

An authorized governance or operational action MAY invalidate an exact entry or governed scope.
The action MUST be attributable and MUST NOT silently broaden scope.

### Revision Invalidation

A correction, replacement, withdrawal, late arrival, watermark change, or source-data revision
MUST invalidate future reuse for every affected temporal and transitive dependency scope according
to ADR-EPIP017-05 and the frozen dependency lineage.

### Expiration Invalidation

Expiration MUST use an explicit logical boundary and policy. Wall-clock observation MUST NOT
silently mutate eligibility inside an accepted Semantic Plan.

### Dependency Invalidation

A changed, withdrawn, invalidated, or incompatible dependency result MUST invalidate future reuse
of every result whose certified lineage materially depends on it. Propagation MUST use explicit
lineage and MUST be bounded, deterministic, and auditable.

### Authority Invalidation

Trust, certification, compatibility, ownership, security, legal, or commit-integrity revocation MAY
invalidate future reuse in its exact governed scope. It MUST NOT rewrite prior Commit history.

### Schema Invalidation

An incompatible Evidence, capability, input, output, configuration, canonicalization, or manifest
schema change MUST invalidate reuse unless explicit directional compatibility is certified.

### Profile Invalidation

Changed Determinism, Execution, Replay, Cache, numeric, security, or certification profiles MUST
invalidate reuse when the prior result is not explicitly compatible.

### Historical Invalidation

Historical invalidation SHALL mean that a result is no longer accepted for a specified historical
analysis or replay interpretation. It MUST preserve the original artifact, original eligibility,
and prior uses. Historical invalidation MUST NOT rewrite what was knowable or committed at the
original boundary.

### Invalidation Atomicity

A new reuse decision MUST evaluate one complete immutable invalidation view at one Invalidation
Epoch. It MUST NOT combine partial epochs or race a mutable invalidation set.

Invalidation failure MUST fail closed for authoritative reuse. Cache eviction MAY proceed
independently because eviction removes optimization state and cannot create eligibility.

## Retention Model

Retention classes and authorities MUST remain independent.

### Durable Result Retention

The Durable Result Retention Authority SHALL define minimum retention from replay, lineage, audit,
certification, legal, operational, and EPIP-016 obligations. A retained dependent artifact MUST
prevent destruction of required authoritative lineage unless an approved preservation substitute
exists.

### Cache Retention

The Cache Authority MAY evict Cache Entries according to capacity and policy without semantic
effect. Cache retention MUST NOT exceed security or legal scope and MUST NOT be relied upon for
historical preservation.

### Ledger Retention

Execution Ledger retention MUST preserve Commit, attempt, lease, fence, cancellation, failure, and
reuse evidence required to interpret every retained Durable Result.

### Audit and Certification Retention

Audit, validation, and certification evidence MUST remain available for the validity and historical
interpretation of retained results.

### Diagnostic Retention

Stable semantic and authority diagnostics required for result interpretation MUST follow Durable
Result or audit retention. Variable operational telemetry MAY use a separate bounded retention
policy.

### Destruction

Destruction MAY be permitted only by an explicit Retention Authority decision after proving that no
retained result, lineage, replay, checkpoint, snapshot, audit, certification, legal hold, or handoff
requires the artifact.

Destruction MUST append an immutable tombstone containing identity, authority, reason, scope,
policy, and prior lineage references without retaining prohibited content. Destroyed content MUST
not be silently recreated under the same Durable Result identity.

## Visibility Rules

- Uncommitted Attempt Results SHALL be visible only to authorized validation, quarantine, and audit
  boundaries.
- Committed Durable Results SHALL become visible atomically with their Commit Record.
- Producers SHALL receive only dependency content explicitly granted in their Invocation Context;
  they MUST NOT enumerate stores or caches.
- Semantic planning SHALL use immutable result metadata and lineage authorized by policy; it MUST
  NOT make semantic selection depend on live cache presence.
- Dispatch MAY request exact lookup under one Cache Profile; a miss MUST NOT alter the Semantic
  Plan.
- Downstream barriers SHALL accept only committed and reuse-validated result references.
- Replay SHALL see only results permitted by its original or declared historical Knowledge and
  governance boundaries.
- Audit SHALL see sufficient immutable history subject to security and redaction policy.
- EPIP-016 handoff SHALL receive only committed, valid, complete, authorized Evidence under
  ADR-EPIP017-15.

Physical replica visibility, cache locality, storage latency, and archive class MUST NOT change
semantic visibility.

## Result Lifecycle

Result lifecycle and Cache Entry lifecycle SHALL remain separate.

### Durable Result States

- **Created** — immutable Attempt Result exists but has no authoritative Commit.
- **Committed** — atomic Commit accepted the result and bound its Durable Result identity.
- **Durable** — authoritative preservation and manifest verification are established within the
  same logical commit boundary.
- **Available** — role-scoped retrieval is currently permitted under policy.
- **Obsolete** — a later result or policy is preferred for future use; historical authority remains.
- **Quarantined** — integrity, authenticity, or policy concern blocks use pending disposition.
- **Archived** — authoritative retention continues in a lower-availability class.
- **Retired** — future reuse is prohibited while historical retention continues.
- **Destroyed** — content was removed under explicit authority and only governed tombstone and
  permitted lineage remain.

Committed and Durable MUST be one atomic authority boundary even when recorded as distinct
conceptual states. No externally observable state may exist in which Commit is authoritative but
the Durable Result binding is absent.

### Legal Durable Result Transitions

- Created SHALL transition only through atomic Commit to Committed and Durable, or remain an
  uncommitted Attempt Result outside durable lifecycle.
- Durable SHALL transition to Available, Obsolete, Quarantined, Archived, or Retired.
- Available MAY transition to Obsolete, Quarantined, Archived, or Retired.
- Obsolete MAY transition to Available only through explicit revalidation; otherwise to Archived,
  Retired, or Quarantined.
- Quarantined MAY transition to Available or Obsolete only after authoritative integrity and policy
  revalidation; otherwise to Archived, Retired, or Destroyed where permitted.
- Archived MAY transition to Available through governed restoration, or to Retired or Destroyed.
- Retired MAY transition only to Archived or Destroyed; it MUST NOT return to future reuse.
- Destroyed SHALL be terminal for content and MUST preserve its tombstone.

No transition may mutate result content, identity, Commit, or historical uses.

### Cache Entry States

- **Created** — non-authoritative entry is derived from one Durable Result.
- **Verified** — exact integrity and authority binding were validated.
- **Eligible** — one current lookup satisfies every reuse predicate.
- **Hit** — an eligible entry was selected for governed reuse validation.
- **Stale** — freshness requirement failed.
- **Invalidated** — an applicable invalidation fact prohibits reuse.
- **Corrupted** — content or identity integrity failed.
- **Quarantined** — entry is isolated from lookup.
- **Obsolete** — entry is no longer preferred or eligible under policy.
- **Evicted** — cache retention ended; no semantic effect occurred.

Cache Hit is an observational lookup fact, not a durable lifecycle promotion or authority grant.
Every transition MUST be immutable in cache operational history where required by audit.

## Authority Model

- The Commit Authority SHALL establish the sole authoritative result through ADR-EPIP017-07.
- The Durable Result Authority SHALL preserve content, manifest, lineage, integrity, and retrieval.
- The Cache Authority SHALL own Cache Entry creation, verification, retention, eviction,
  quarantine, and operational lookup.
- The Reuse Validation Authority SHALL decide exact current lookup eligibility under frozen plans,
  profiles, authority, temporal facts, and invalidation view.
- The Invalidation Authority SHALL issue scoped invalidation facts. Domain-specific source,
  governance, security, certification, compatibility, temporal, and retention authorities MAY
  originate causes within their frozen scopes.
- The Retention Authority SHALL govern archival, retirement, legal hold, and destruction.
- The Replay Authority SHALL select historical visibility without rewriting store state.
- The Audit Authority SHALL verify authority and history without altering results.
- The Handoff Authority SHALL consume only committed, eligible Evidence and SHALL NOT use cache
  state as authority.

No producer, planner, scheduler, worker, Cache Entry, storage replica, or EPIP-016 consumer MAY
grant Durable Result authority.

## Store Invariants

1. Only an atomically Committed Result becomes Durable.
2. Durable Results and manifests are immutable.
3. Every Durable Result binds exactly one Commit Record.
4. Durable Result identity remains distinct from Evidence, Cache Entry, Commit, and locator.
5. The Durable Result Store is the authoritative historical result source.
6. Cache never owns result, semantic, commit, or historical authority.
7. Cache presence or absence never changes a Semantic Plan.
8. Every Cache Entry references exactly one authoritative Durable Result.
9. Every authoritative reuse decision revalidates complete eligibility.
10. Fresh and reused results satisfy the required semantic equivalence.
11. Cache invalidation is explicit, immutable, scoped, and epoch-bound.
12. Invalidation prevents future reuse and never rewrites history.
13. Revision and dependency invalidation propagate through explicit lineage only.
14. Unknown reuse eligibility fails closed.
15. Cache eviction never deletes or invalidates a Durable Result.
16. Durable storage relocation and replication never change identity.
17. Corrupted content is quarantined and never silently repaired.
18. Historical results preserve original governance, temporal, plan, and revision state.
19. Uncommitted, failed, partial, stale, or cancelled output never enters the result cache.
20. Valid empty Evidence remains distinct from cached absence.
21. Retention classes remain independent and governed.
22. Destruction never erases the historical fact of Commit.
23. Operational storage behavior never changes Evidence semantics.
24. Decision remains outside result-store and cache authority.

## Determinism

Given identical Durable Result Manifests, Semantic and Dispatch Plans, input and dependency
identities, temporal and governance facts, Cache Profiles, invalidation view and epoch, retention
facts, identity profiles, and reuse policies, EPIP-017 MUST derive identical:

- result authority and visibility;
- Cache Entry identity and verification status;
- cache eligibility, freshness, staleness, obsolescence, and invalidation decisions;
- durable-versus-cached lookup disposition;
- semantic-equivalence verdict;
- invalidation propagation closure;
- lifecycle transitions;
- diagnostics and audit facts.

Cache eviction order, physical location, machine, process, worker, latency, storage tier, replica,
memory pressure, and wall-clock access MUST NOT change semantic behavior or authority.

Equivalent cached and fresh execution MAY have different Dispatch, Invocation, Attempt, reuse, and
ledger identities. They MUST preserve the semantic equivalence required by ADR-EPIP017-08.

## Replay Compatibility

This ADR does not define replay modes. Every replay mode MUST nevertheless preserve:

- original Durable Result, Commit, Evidence, plan, registry, producer, capability, profile,
  temporal, revision, and lineage identities;
- the historical availability and invalidation view applicable to the original Knowledge Boundary;
- distinction between original durable authority and later Cache Entries;
- original reuse versus fresh-computation facts;
- later invalidation, corruption, withdrawal, retirement, or destruction as separate facts;
- cache scope isolation between live, simulation, historical, certification, and replay contexts.

A replay MUST NOT consume a Cache Entry produced from future knowledge, a later revision, a newer
registry snapshot, or an incompatible profile. Cache reuse in replay MUST reference an eligible
Durable Result and satisfy the replay mode selected by ADR-EPIP017-11.

Loss or eviction of a Cache Entry MUST NOT prevent replay when the required Durable Result and
retained authoritative artifacts exist. Loss of required Durable Result content MUST produce an
explicit historical reconstruction failure, not silent cache substitution.

## Diagnostics

Diagnostics MUST use stable, versioned codes and distinguish at minimum:

- cache miss;
- verified cache hit;
- cache hit rejected by reuse validation;
- stale, expired, obsolete, invalidated, retired, unauthorized, or incompatible cache entry;
- corrupted, quarantined, unauthenticated, or mismatched cache content;
- Durable Result lookup, availability, archive restoration, or content-verification failure;
- missing or mismatched Commit Record;
- result, cache, manifest, locator, domain, or digest identity mismatch;
- authority, security-scope, trust, certification, or compatibility mismatch;
- Semantic Plan, dependency, context, temporal, revision, schema, or profile mismatch;
- invalidation-view or epoch inconsistency;
- invalidation propagation or lineage failure;
- cached-versus-fresh semantic divergence;
- illegal lifecycle transition;
- retention, legal-hold, archival, retirement, or destruction conflict;
- cache-driven planning or hidden refresh attempt;
- unexpected result visibility or history mutation.

Diagnostics MUST identify Durable Result, Cache Entry, Commit, plans, dependencies, temporal facts,
profiles, invalidation epoch, authority, lifecycle, and reason. Diagnostics MUST NOT refresh,
recompute, retry, correct, invalidate, delete, or promote a result automatically.

## Audit

Audit MUST preserve:

- Attempt Result submission and atomic Commit boundary;
- Durable Result content and manifest identities;
- every storage locator, replica, verification, relocation, and archival lineage required for
  authority;
- every Cache Entry, scope, profile, verification, hit, miss, rejection, invalidation,
  quarantine, obsolescence, and eviction fact required by policy;
- all reuse predicates and exact verdict;
- original and current governance, temporal, revision, dependency, schema, and profile facts;
- every invalidation cause, epoch, scope, propagation edge, and closure;
- cached-versus-fresh equivalence evidence and divergence;
- lifecycle transitions, retention, legal holds, retirement, and destruction tombstones;
- proof that cache never became authority and history was never rewritten.

Audit MUST distinguish result authority, physical storage, cache optimization, validation,
invalidation, and historical interpretation. It MUST NOT infer successful recomputation from cache
reuse.

## Storage Certification

Certification MUST verify at least:

1. Only atomically committed results become durable and visible.
2. Durable Result and Commit Record remain bound and immutable.
3. Replication, relocation, archival, and restoration preserve identity and content.
4. Cache Entry identity remains separate and references one Durable Result.
5. Cache loss, miss, eviction, or corruption never changes semantics or authority.
6. Complete reuse eligibility across producer, capability, implementation, configuration, input,
   dependency, context, temporal, revision, governance, schema, profile, security, and invalidation
   dimensions.
7. Fresh and cached semantic equivalence across success and valid-empty outcomes.
8. Rejection of uncommitted, failed, partial, stale, cancelled, corrupted, unauthorized, or hidden
   cache content.
9. Explicit invalidation for revision, expiration, dependency, authority, schema, profile, and
   historical scopes.
10. Deterministic and bounded transitive invalidation using lineage.
11. Atomic invalidation views and race handling.
12. Historical preservation after correction, withdrawal, revocation, retirement, and destruction.
13. Replay isolation from future or incompatible cache state.
14. Retention-class independence and legal destruction governance.
15. No cache-driven planning, hidden refresh, implicit recomputation, or semantic correction.
16. Durable lookup and cache failures produce precise fail-closed diagnostics.

Certification MUST include corruption, partial storage failure, replica divergence, cache poisoning,
eviction, concurrent invalidation, late revision, governance revocation, archive restoration, and
historical replay campaigns. Nominal hit/miss tests are insufficient.

## Migration

- Existing stored outputs MUST be classified as uncommitted, committed, durable, cached,
  diagnostic, snapshot, checkpoint, or legacy-ambiguous.
- No existing cache or database row SHALL be assumed authoritative without Commit, identity,
  provenance, temporal, and integrity evidence.
- Existing hidden producer caches, module caches, memoization, files, and local stores MUST be
  inventoried and removed from authoritative semantics.
- Legacy cache keys MUST be decomposed into complete identity dimensions; matching symbol and
  timeframe is insufficient.
- Existing TTL, refresh, overwrite, upsert, latest-value, and garbage-collection behavior MUST be
  assessed for history rewriting.
- Historical results lacking required manifests MUST be declared legacy-ambiguous and MUST NOT be
  promoted silently.
- Migration MUST create new qualified identities and lineage without rewriting legacy identities.
- Shadow validation MUST compare fresh and reused Evidence, diagnostics, provenance, temporal
  visibility, invalidation, and handoff.
- Cache state MUST be excluded from semantic divergence decisions except as an operational path.
- Rollback, dual-run authority, acceptance criteria, and legacy retirement MUST follow
  ADR-EPIP017-16.

## Backward Compatibility

This ADR changes no production storage, cache, serialization, public API, producer, EPIP-016
contract, Replay behavior, EventBus behavior, financial calculation, risk rule, portfolio behavior,
or execution behavior.

Existing stores and caches remain governed by legacy contracts until migrated. They MUST NOT be
described as the EPIP-017 Durable Result Store or compliant Cache without certification.

EPIP-016 SHALL receive only committed Evidence through ADR-EPIP017-15. It SHALL NOT observe whether
Evidence was freshly computed or reused unless compatible provenance explicitly exposes that fact
without changing Decision semantics.

Historical Durable Results, Cache Entries, invalidation facts, retention decisions, and tombstones
MUST remain interpretable under their original identity and policy versions.

## Forbidden Behaviours

EPIP-017 MUST NEVER permit:

1. Cache becoming authoritative.
2. Cache identity replacing Durable Result, Evidence, Commit, or Invocation identity.
3. Uncommitted or rejected Attempt Results entering authoritative durable storage or result cache.
4. Implicit cache mutation, refresh, overwrite, or upsert of immutable entries.
5. Hidden producer, planner, scheduler, worker, or adapter caches affecting semantics.
6. Cache-driven producer, capability, dependency, optionality, temporal, or Semantic Plan selection.
7. Cache hit accepted without Durable Result and Commit authority verification.
8. Matching value, schema, symbol, timeframe, or key treated as sufficient reuse equivalence.
9. Automatic semantic correction or revision through cache refresh.
10. History rewriting after correction, invalidation, withdrawal, revocation, or replacement.
11. Implicit invalidation or invalidation inferred solely from cache eviction.
12. Wall-clock TTL changing an accepted Semantic Plan.
13. Environment-, machine-, storage-, locality-, or latency-dependent semantic cache behavior.
14. Cache miss authorizing implicit retry or recomputation.
15. Failure, timeout, cancellation, rejected output, or absence cached as successful Evidence.
16. Corrupted content silently repaired under the same Cache Entry or Durable Result identity.
17. Future, revised, or incompatible cache content entering historical replay.
18. Durable deletion because cache exists.
19. Cache eviction treated as historical invalidation.
20. Destruction without authority, dependency closure, legal review, and tombstone.
21. Storage locator interpreted as content identity or authority.
22. Decision, Candidate, Confidence, risk decision, or execution instruction created by result reuse.

Any forbidden behavior SHALL be an architecture and certification failure and MUST fail closed.

## Alternatives Considered

### Cache as source of truth

The fastest available cached value becomes authoritative.

Rejected because eviction, corruption, locality, and refresh would change semantics and history.

### One storage layer without authority distinction

Committed, temporary, cached, archived, and failed outputs share one undifferentiated store.

Rejected because visibility, retention, lifecycle, identity, and historical meaning become
ambiguous.

### Time-to-live validity

A result is reusable until a wall-clock TTL expires.

Rejected because semantic validity depends on explicit temporal, revision, dependency, governance,
schema, and profile facts.

### Recompute on every request

No cache or durable reuse is permitted.

Rejected as a permanent architecture because deterministic immutable results may be safely reused
when complete equivalence and authority are proven. Fresh-only execution MAY remain a profile.

### Authoritative durable results with disposable verified cache

Only atomic Commit creates Durable Results; cache entries reference and revalidate them under
complete reuse manifests.

Accepted because it preserves correctness, historical authority, replay, and optimization
independence.

## Decision

EPIP SHALL adopt the Durable Result, Durable Result Store, Cache, Cache Entry, reuse, invalidation,
retention, visibility, lifecycle, authority, determinism, replay, diagnostic, audit, certification,
migration, compatibility, and prohibition rules in this ADR as the constitutional storage model for
EPIP-017.

Only committed results SHALL become durable. Cache SHALL remain a disposable optimization. No
result reuse SHALL occur unless complete current eligibility and semantic equivalence are proven
against authoritative identities and one immutable invalidation view.

## Consequences

### Positive

- Cache cannot become a hidden source of truth.
- Fresh and reused execution preserve semantic behavior.
- Revision, dependency, governance, schema, and profile changes invalidate reuse explicitly.
- Historical results and prior Commit facts remain immutable.
- Replay remains isolated from future cache content.
- Corruption and cache poisoning fail closed through quarantine.
- Physical storage and retention can evolve without changing identity.
- Audit can explain every reuse and invalidation decision.

### Negative

- Reuse validation requires substantial identity, lineage, temporal, and governance metadata.
- Durable retention and historical preservation increase storage obligations.
- Cache hits may be rejected when any predicate is unknown.
- Invalidation propagation requires complete explicit lineage.
- Destruction becomes a governed exceptional action.
- Existing cache systems may not qualify for migration.

### Trade-offs

EPIP accepts higher metadata, verification, and retention cost in exchange for preventing silent
stale Evidence, cache-driven semantics, history rewriting, and replay contamination.

## Non-goals

This ADR does not define:

- storage, database, filesystem, object-store, replication, cache, or eviction technologies;
- implementation classes, APIs, indexes, protocols, consistency algorithms, or interfaces;
- cache replacement, admission, prefetch, warming, compression, or capacity algorithms;
- cryptographic digest algorithms;
- replay modes or replay algorithms;
- snapshot or checkpoint consistency and restore rules;
- retry, fallback, recovery, or scheduler algorithms;
- parallel execution and invalidation implementation;
- EPIP-016 handoff representation;
- analytical formulas, trading, Decision, Candidate, Confidence, risk, portfolio, execution, or
  financial logic.

These exclusions MUST be resolved by their mandatory ADRs and MUST NOT be delegated to code.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 through ADR-EPIP017-09 and the frozen EPIP-016 and
H001–H007 architecture.

It creates or confirms mandatory dependencies on:

- ADR-EPIP017-11 for replay-mode-specific durable reuse, original-versus-revised history, cache
  isolation, and reconstruction failure;
- ADR-EPIP017-12 for Snapshot and Checkpoint references, retention, restore validation, and
  authoritative Durable Result dependencies;
- ADR-EPIP017-13 for cache-miss disposition, recomputation authorization, corruption recovery,
  timeout, retry, fallback, and invalidation-triggered recovery;
- ADR-EPIP017-14 for concurrent lookup, invalidation epochs, duplicate computation, result races,
  and fresh/cached parallel equivalence;
- ADR-EPIP017-15 for committed-result-only Evidence completeness and EPIP-016 handoff;
- ADR-EPIP017-16 for store migration, historical ambiguity, dual-run divergence, rollback, and
  legacy retirement;
- ADR-EPIP017-17 for storage telemetry, cache diagnostics,
  invalidation audit, retention, redaction, and quarantine evidence;
- ADR-EPIP017-18 for storage capacity, cache budgets,
  retention classes, archival service levels, legal holds, and destruction approval.

This ADR introduces the Durable Result Retention Authority, Cache Authority, Reuse Validation
Authority, Invalidation Authority, and Retention Authority as explicit governance roles. They MUST
use ADR-EPIP017-03 ownership, separation, authenticity, lifecycle, and audit rules. No separate
governance model is required.

## Future Evolution

Future storage technologies, replicas, archives, content-distribution layers, cache tiers, and
retention classes MAY evolve behind these authority and identity contracts. They MUST preserve
atomic Commit, immutable Durable Results, explicit invalidation, cache non-authority, and historical
lineage.

New Cache Profiles or reuse dimensions MAY be introduced through immutable versioned governance.
Existing reuse decisions and historical results MUST NOT be reinterpreted.

Derived indexes, projections, summaries, or materialized views MAY be added only as independently
identified non-authoritative artifacts or committed producer capabilities. They MUST NOT silently
replace Durable Results.

## Approval Gate

Approval of this ADR resolves EPIP-017 Durable Result authority, cache correctness, result reuse,
invalidation, historical preservation, visibility, and retention architecture only.

It does not approve a database, result store, cache, persistence layer, invalidation engine,
retention service, replay engine, recovery engine, or Programme A.

EPIP-017 implementation remains prohibited until the complete mandatory ADR set is accepted and
the remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
