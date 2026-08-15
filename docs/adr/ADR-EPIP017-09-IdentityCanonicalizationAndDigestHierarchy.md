# ADR-EPIP017-09 — Identity, Canonicalization and Digest Hierarchy

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-08 are approved, frozen, and normative. This ADR MUST NOT
modify their orchestration authority, producer contract, governance, Evidence semantics, temporal
model, plan separation, execution lifecycle, determinism profiles, EPIP-016 boundary, or
single-authoritative-path rule.

This ADR defines identity architecture only. It authorizes no implementation, serializer, digest
library, cryptographic primitive, signing service, identifier generator, interface, placeholder, or
Programme A activity.

## Executive Summary

EPIP-017 SHALL identify every authoritative artifact within an explicit, immutable, versioned
**Identity Domain**. Identity states what an artifact is and the authority scope in which it may be
interpreted. A digest is one integrity-bearing representation of canonical content; it is not the
artifact's semantic meaning, governance authority, trust, certification, or cross-domain identity.

Every digest-bearing artifact SHALL declare its Identity Domain, domain version, artifact schema
version, canonicalization profile, digest profile, and canonical content. Digest input SHALL be
domain-separated. Equal digest bytes from different domains, versions, or profiles SHALL have no
equality meaning.

EPIP SHALL not use one universal execution digest. Independent domains SHALL exist for Producer,
Capability, Registry Snapshot, Evidence, Evidence Dependency, Semantic Plan, Dispatch Plan,
Invocation, Execution Attempt, Lease, Fence, Token, Commit Record, Execution Ledger, Snapshot,
Checkpoint, Replay Session, Validation, Certification, and Diagnostic Report. Additional domains
MAY be governed later without reinterpreting existing domains.

Canonicalization SHALL be deterministic and profile-versioned. It SHALL define field presence,
type, ordering, numeric representation, temporal representation, identifiers, collections,
references, normalization boundaries, extension handling, and prohibited ambient values. Hidden
normalization is forbidden.

Digest hierarchy SHALL use explicit typed composition. A parent artifact MAY include child domain,
identity, digest-profile, and digest references, but MUST NOT reinterpret a child digest as its own
domain. Operational, semantic, ledger, diagnostic, validation, replay, and certification identities
SHALL remain separate.

Identity is immutable. Correction, replacement, supersession, deprecation, migration, withdrawal,
or recertification SHALL create new identities and explicit lineage. Historical identities and
canonicalization rules SHALL never be rewritten.

## Purpose

Establish the constitutional identity, canonicalization, digest-domain, hierarchy, lineage,
evolution, equality, certification, replay, migration, and audit model for every EPIP-017 artifact.

This ADR defines:

- what identity represents and does not represent;
- independent identity domains and their authorities;
- deterministic canonical representation and ordering;
- artifact, plan, registry, ledger, snapshot, validation, certification, and lineage digests;
- hierarchical typed composition and domain separation;
- immutable identity evolution and historical preservation;
- diagnostics and certification requirements for identity integrity.

## Problem Statement

A single digest cannot safely represent semantic meaning, operational execution, attempt history,
snapshot state, replay, validation, certification, and audit simultaneously. These artifacts have
different authorities, inputs, lifecycles, equivalence rules, and evolution rates.

Without explicit domain separation and canonicalization governance, EPIP could:

- interpret equal byte strings from unrelated domains as equal artifacts;
- reuse an Evidence digest as a Commit or Certification digest;
- let retry or elapsed timing change semantic identity;
- treat semantically equivalent but operationally distinct executions as identical;
- silently normalize timestamps, numbers, missing fields, or collection order;
- invalidate historical artifacts after serializer or hash evolution;
- identify producer behavior only through a self-declared version;
- construct circular digest dependencies;
- overwrite an identity during correction or migration;
- certify one canonical representation and execute another;
- conceal lineage by replacing rather than superseding an artifact.

EPIP therefore requires explicit identity domains, canonicalization profiles, digest profiles,
typed hierarchical composition, acyclic identity lineage, and immutable evolution.

## Architectural Context

ADR-EPIP017-01 separates registry, planning, execution, result, replay, audit, and handoff
authorities.

ADR-EPIP017-02 requires stable producer, capability, implementation, configuration, result, and
certification identities.

ADR-EPIP017-03 requires authentic immutable governance actions, certification records, and registry
snapshots.

ADR-EPIP017-04 separates Evidence semantic identity, artifact identity, dependency graph, and
provenance lineage.

ADR-EPIP017-05 requires temporal identity to preserve calendar, timeframe, availability, knowledge,
revision, and boundary meaning.

ADR-EPIP017-06 requires independent Semantic Plan, Dispatch Plan, Execution Intent, context, and
Execution Ledger identities.

ADR-EPIP017-07 requires immutable Invocation, Attempt, Lease, Fence, Token, Commit Record, result,
and ledger identities.

ADR-EPIP017-08 defines strict, semantic, operational, replay, and certification equivalence and
requires profile-scoped canonical artifacts.

This ADR supplies the identity and canonicalization constitution required by all of them. It does
not select cryptographic algorithms.

## Definitions

### Identity

An immutable, domain-scoped assertion that distinguishes one architectural artifact from every
other artifact under one versioned identity contract.

### Identity Domain

An immutable namespace and interpretation contract defining artifact kind, authority, canonical
content scope, equality meaning, lineage rules, and permitted references.

### Domain Version

The immutable version of an Identity Domain's interpretation rules. A domain-version change MUST
NOT reinterpret identities created under an earlier version.

### Artifact Identity

The complete domain-qualified identity of one immutable artifact, including domain, domain version,
identity-scheme version, and identifier value.

### Semantic Identity

An identity describing immutable semantic meaning independently from one material representation
or execution history.

### Operational Identity

An identity describing one operational authorization, lifecycle artifact, or execution fact
without claiming semantic equivalence.

### Canonical Representation

The unique, deterministic, versioned representation of one artifact's identity-bearing content
under one Canonicalization Profile.

### Canonicalization Profile

An immutable, versioned contract defining included and excluded fields, data types, field presence,
normalization, ordering, references, extension handling, and canonical encoding semantics.

### Canonical Equality

Equality of Identity Domain, domain version, artifact schema version, Canonicalization Profile, and
canonical representation. Canonical equality is stricter than semantic equivalence unless a
profile explicitly makes them identical.

### Digest

A domain-separated integrity value derived from one canonical representation under one Digest
Profile. A digest is not self-describing and MUST NOT be interpreted without its domain and profile.

### Digest Domain

The explicit domain-separation contract binding a digest to one Identity Domain, artifact purpose,
domain version, and Digest Profile.

### Digest Profile

An immutable, versioned contract identifying the governed digest construction class,
canonicalization dependency, domain-separation identifier, output representation, and migration
rules. It does not define an implementation in this ADR.

### Digest Authority

The authority permitted to attest that one digest was derived from one canonical artifact under the
declared profiles. It does not become semantic owner of the artifact.

### Canonical Ordering

The deterministic ordering contract for fields, entries, keys, references, graph nodes, graph
edges, diagnostics, transitions, and collections whose order participates in canonical content.

### Identity Lineage

The immutable, directed, typed, acyclic relationships connecting an artifact to predecessors,
sources, replacements, corrections, supersessions, migrations, validations, or certifications.

### Lineage Digest

The domain-separated digest of one canonical lineage manifest. It MUST NOT replace the identities
of lineage members.

### Identity Manifest

The immutable declaration of domain, versions, canonicalization, digest profile, canonical
references, authority, and lineage needed to interpret an artifact identity.

### Versioned Identity

An identity whose interpretation explicitly binds all domain, schema, canonicalization, digest,
and identity-scheme versions.

## Identity Model

Every authoritative EPIP-017 artifact MUST have exactly one primary Artifact Identity in exactly
one Identity Domain. It MAY reference identities in other domains only through explicit typed
references.

An identity MUST state or resolve:

- Identity Domain and Domain Version;
- artifact schema and identity-scheme versions;
- authoritative owner and issuing authority where applicable;
- canonicalization and digest profiles where digest-bearing;
- immutable subject and scope;
- lineage and supersession relationships;
- trust, validation, or certification references without incorporating their authority implicitly.

Identity MUST NOT be inferred from:

- memory address or runtime object identity;
- process, thread, worker, host, queue, or filesystem location;
- collection or discovery order;
- display name, path, module, class, package, or repository name alone;
- current time or random identifier without an approved deterministic identity contract;
- unqualified digest bytes;
- mutable database keys or storage locations;
- a version label lacking implementation or content identity.

Semantic identity, representation identity, operational identity, storage locator, and human-readable
label MUST remain distinct.

## Identity Domains

Each domain below SHALL be independent. No identity or digest SHALL be reused as the primary
identity of another domain.

### Producer Domain

Identifies one immutable producer behavior and implementation lineage under the producer contract.
It MUST distinguish producer name, version, implementation identity, owner, contract profile, and
certified configuration scope.

### Capability Domain

Identifies one immutable semantic capability contract independently from any implementing
producer.

### Registry Snapshot Domain

Identifies one immutable canonical registry view derived from one governance manifest and epoch.
It MUST remain distinct from individual Producer, Capability, Governance, and Certification
identities.

### Evidence Domain

Identifies one immutable Evidence artifact and binds semantic type, source, subject, scope,
temporal identity, content, provenance, validity, and completeness. Evidence semantic identity and
artifact identity MAY be separately referenced but MUST NOT be conflated.

### Evidence Dependency Domain

Identifies one immutable Evidence requirement or resolved dependency edge, including consumer,
provider, compatibility, cardinality, temporal mapping, and semantic-plan scope.

### Semantic Plan Domain

Identifies one immutable semantic intent, complete dependency graph, frozen context, temporal
boundary, selections, policies, and terminal Evidence requirements.

### Dispatch Plan Domain

Identifies one immutable operational strategy for one Semantic Plan, including Execution Units,
barriers, fences, resource classes, and authorizations. It MUST NOT share Semantic Plan identity.

### Invocation Domain

Identifies one immutable Execution Intent instance for one semantic graph node and result scope.

### Execution Attempt Domain

Identifies one authorized operational attempt, lineage ordinal, Dispatch Plan, lease, fence, token,
and owner scope. Attempt identity MUST NOT become Invocation identity.

### Execution Lease Domain

Identifies one immutable lease grant and validity scope. Renewal, invalidation, release, or expiry
MUST be separate lineage facts and MUST NOT mutate lease identity.

### Execution Fence Domain

Identifies one monotonic fence generation and commit scope. Fence generations MUST have distinct
identities.

### Execution Token Domain

Identifies one scoped authorization credential manifest without exposing or equating secret token
material with public identity. Token identity MUST remain distinct from token proof or credential
storage.

### Commit Record Domain

Identifies one immutable atomic authoritative commitment binding Invocation, Attempt Result, fence,
durable result, transition, and visibility scope.

### Execution Ledger Domain

Identifies one append-only ledger lineage and its canonical authoritative projection. Individual
ledger-entry identities MUST remain distinct from the ledger-lineage identity and any ledger
checkpoint.

### Snapshot Domain

Identifies one immutable audit-state projection at a declared consistency boundary. It MUST remain
distinct from a resumable Checkpoint.

### Checkpoint Domain

Identifies one immutable resumable execution-state artifact and its restore contract. It MUST not be
treated as a Snapshot merely because content overlaps.

### Replay Session Domain

Identifies one governed replay purpose, mode, input boundary, original artifacts, policy, and
execution lineage. It MUST remain distinct from the replayed run and original run.

### Validation Domain

Identifies one immutable validation subject, ruleset, evidence set, findings, and verdict. Validation
identity MUST remain distinct from Certification identity.

### Certification Domain

Identifies one immutable institutional attestation, scope, Certification Profile, authority,
evidence, verdict, validity, and revocation lineage.

### Diagnostic Report Domain

Identifies one immutable diagnostic projection, audience, source authority, schema, stable findings,
and redaction profile. It MUST remain distinct from the artifacts diagnosed.

Additional mandatory domains SHALL exist for Governance Action, Registry Entry, Evidence Type,
Temporal Contract, Configuration, Input Manifest, Execution Intent, Attempt Result, Durable Result,
Audit Record, and Handoff Manifest when those artifacts require independent authority. They MUST
follow this ADR without collapsing into the listed domains.

## Canonicalization Model

Every digest-bearing artifact MUST select exactly one Canonicalization Profile compatible with its
Identity Domain and artifact schema version.

The profile MUST define:

- canonical field set and field-order semantics;
- required, optional, absent, null, empty, default, and unknown-field distinctions;
- primitive type and value representation;
- text normalization boundaries and prohibited lossy normalization;
- numeric type, precision, sign, rounding, exceptional-value, and scale representation;
- canonical instant, interval, timezone basis, precision, calendar, timeframe, and temporal-version
  representation;
- binary and opaque-value representation;
- enum, reason-code, and identifier representation;
- map, set, sequence, multiset, graph, and reference ordering;
- duplicate handling and canonical rejection rules;
- extension namespace and unknown-extension treatment;
- inclusion or exclusion of diagnostics, telemetry, signatures, and derived display fields;
- child artifact reference form and domain qualification;
- cycle detection and maximum canonical graph scope;
- canonical equality and validation rules.

Canonicalization MUST be pure with respect to the declared artifact. It MUST NOT read ambient time,
locale, timezone, environment, registry, filesystem, network, storage order, process state, or
mutable external data.

Canonicalization MUST preserve every distinction that can affect semantic meaning, authority,
validity, provenance, temporal interpretation, lifecycle, or certification. It MUST NOT normalize
away meaningful differences.

Fields excluded from one domain's canonical representation MAY remain authoritative in another
domain. Exclusion MUST be explicit and versioned.

## Canonical Ordering

Canonical ordering MUST use domain-defined immutable keys and MUST NOT rely on runtime comparison
or insertion order.

At minimum:

- record fields SHALL follow the Canonicalization Profile's declared order;
- maps SHALL order by canonical key representation and MUST reject canonically duplicate keys;
- sets SHALL order by domain-qualified canonical member identity and MUST reject duplicates;
- sequences SHALL preserve semantic sequence when order is meaningful;
- order-insensitive collections SHALL be normalized by an explicit canonical member order;
- multisets SHALL preserve multiplicity explicitly;
- graph nodes and edges SHALL use explicit domain-qualified identities and canonical tie-breakers;
- diagnostics SHALL order by severity only when severity is semantically relevant, followed by
  stable code, subject identity, scope, and causal order as declared;
- lifecycle facts SHALL preserve authoritative logical sequence and causal relationships;
- operational telemetry SHALL remain outside semantic canonical ordering unless its own domain
  defines an observational order.

Canonical ordering rules MUST be versioned. An ordering change creates a new Canonicalization
Profile and MUST NOT alter historical identity.

## Representation Invariants

1. One Canonicalization Profile yields exactly one representation for one valid artifact.
2. Canonical representation is deterministic for identical complete content.
3. Canonical representation is independent of runtime, storage, locale, machine, and process.
4. Required, absent, null, empty, and default values remain distinguishable where contracts do.
5. Semantic sequence and order-insensitive collection remain distinguishable.
6. Unknown or duplicate canonical fields fail according to explicit profile rules.
7. Invalid artifacts MUST NOT receive an authoritative digest.
8. Human-readable display representation MUST NOT substitute for canonical representation.
9. Canonical equality applies only within the same domain and complete version set.
10. Semantic equivalence MAY exist without canonical equality and MUST be represented separately.

## Digest Model

Every digest MUST be interpreted as the tuple of:

- Identity Domain;
- Domain Version;
- artifact schema version;
- Canonicalization Profile identity and version;
- Digest Domain identity;
- Digest Profile identity and version;
- digest value.

Unqualified digest values MUST NOT be used for equality, lookup, authority, or audit.

Digest Authority MUST validate canonical artifact conformance before attesting a digest. Digest
issuance MUST NOT grant semantic correctness, trust, certification, ownership, validity, or commit
authority.

Digest mismatch MUST fail integrity validation. It MUST NOT be repaired through silent
recanonicalization, profile substitution, or digest replacement.

Digest profiles MUST define algorithm agility, profile retirement, collision-response governance,
and multi-profile migration obligations without specifying cryptographic implementations in this
ADR.

## Digest Hierarchy

EPIP SHALL use typed hierarchical composition rather than one universal digest.

### Artifact Digest

Every immutable authoritative artifact requiring integrity MUST have a domain-specific Artifact
Digest over its canonical content and typed references.

### Evidence and Dependency Digests

Evidence Digest and Evidence Dependency Digest MUST remain distinct. Evidence provenance MAY
include dependency domain-qualified references without absorbing dependency interpretation.

### Plan Digests

Semantic Plan Digest MUST compose semantic inputs, registry reference, capabilities, producers,
Evidence requirements, dependency graph, temporal identities, contexts, policies, and terminal
requirements.

Dispatch Plan Digest MUST compose the Semantic Plan reference and operational strategy artifacts.
It MUST NOT be interpreted as a Semantic Plan Digest.

### Registry Digest

Registry Snapshot Digest MUST compose the canonical eligible and governance view of one immutable
snapshot. It MUST not replace individual governance, certification, producer, or capability
identities.

### Ledger Digest

Execution Ledger SHALL have independent digests for immutable ledger entries, canonical
authoritative projection, and ledger lineage or segment composition as governed by its profile.
Raw observational telemetry MUST NOT contaminate a semantic or authoritative ledger digest.

### Commit Digest

Commit Record Digest MUST bind the Invocation, winning Attempt Result, fence generation, durable
result, authoritative transition, and visibility scope. It MUST not be reused as the result digest.

### Snapshot Digest

Snapshot Digest MUST bind the exact audit-state projection, consistency boundary, plan, ledger,
results, governance, temporal state, and profile declared by ADR-EPIP017-12.

### Checkpoint Digest

Checkpoint Digest MUST bind resumable operational state and restore contract. It MUST remain
distinct from Snapshot Digest even when referencing the same plans and results.

### Replay Digest

Replay Session and replay-verdict digests MUST bind replay mode, original artifacts, replay inputs,
policies, comparison scope, and outcomes under ADR-EPIP017-11. They MUST not become original-run
identities.

### Validation Digest

Validation Digest MUST bind exact subject identities, ruleset, input evidence, findings, and
verdict. It MUST remain distinct from certification.

### Certification Digest

Certification Digest MUST bind certification subject, profile, evidence, environment, authority,
verdict, validity, and lineage. It MUST not be interpreted as proof of artifact content without its
referenced validation and Artifact Digests.

### Diagnostic Report Digest

Diagnostic Report Digest MUST bind stable findings, subjects, schema, audience, and redaction
profile. Variable operational measurements MAY require a separate observational digest domain.

### Lineage Digest

Lineage Digest MUST bind typed directed relationships and member references. It MUST not collapse
member identities or imply semantic equivalence.

## Hierarchical Composition

Parent canonical content MAY reference child artifacts only through a typed reference containing
the child's Identity Domain, Domain Version, Artifact Identity, Canonicalization Profile, Digest
Profile, and digest where required.

Composition MUST be acyclic within one identity derivation. If two artifacts require mutual
association, one authority MUST establish identities independently and a third lineage or binding
artifact MUST relate them. Circular digest construction is forbidden.

Embedded child content and referenced child identity MUST have explicit, non-interchangeable
semantics. A profile MUST state whether content is embedded, referenced, or both for validation.

Changing a child reference that participates in parent canonical content MUST create a new parent
identity. Changing an excluded observational child MUST NOT change a semantic parent identity.

## Domain Separation

Every Digest Domain MUST have an immutable domain-separation identifier unique to artifact purpose
and Domain Version. No digest input MAY rely only on untyped serialized bytes.

The following separations are mandatory:

- **semantic separation** — Evidence, dependencies, capabilities, contexts, and Semantic Plans;
- **operational separation** — Dispatch Plans, Invocations, Attempts, Leases, Fences, Tokens, and
  Attempt Results;
- **ledger separation** — ledger entries, authoritative ledger projections, and ledger lineage;
- **diagnostic separation** — semantic, operational, audit, and redacted Diagnostic Reports;
- **validation separation** — validation subjects, findings, and verdicts;
- **replay separation** — Replay Sessions, replay outputs, comparisons, and original artifacts;
- **certification separation** — certification evidence, attestation, validity, and revocation;
- **governance separation** — governance actions, registry entries, snapshots, and authority facts;
- **storage separation** — durable results, cache entries, storage manifests, and content locators;
- **handoff separation** — committed Evidence set and EPIP-016 handoff manifest.

Cross-domain digest equality MUST have no architectural interpretation. A component MUST compare
complete qualified identities, never naked digest bytes.

## Identity Lineage

Lineage relationships MUST be typed, immutable, attributable, directional, and acyclic. Supported
relationship classes MUST include at minimum:

- derived-from;
- depends-on;
- produced-by;
- validates;
- certifies;
- commits;
- included-in;
- snapshots;
- checkpoints;
- replays;
- corrects;
- replaces;
- supersedes;
- withdraws;
- deprecates;
- migrates-from;
- equivalent-under-profile;
- incompatible-with.

Lineage MUST preserve every original identity and version. It MUST NOT imply ownership transfer,
semantic equivalence, trust, validity, or certification unless the relationship contract explicitly
states and governs that meaning.

Conflicting lineage, missing predecessor, cycle, domain mismatch, or ambiguous supersession MUST
fail validation and be diagnosed.

## Identity Evolution

### Stability

An Artifact Identity MUST remain stable for the lifetime of its immutable content and contract. It
MUST NOT change because of relocation, replication, caching, archival, display, owner tooling, or
newer profile availability.

### Version Evolution

Domain, schema, identity-scheme, canonicalization, and digest-profile versions MUST evolve
independently. Every artifact MUST bind the exact versions used.

A new version MUST create a new identity when canonical content or interpretation changes. Prior
versions MUST remain resolvable for the governed retention period.

### Replacement and Supersession

Replacement and supersession MUST create new artifacts and typed lineage. They MUST NOT reuse or
overwrite predecessor identity. Replacement MUST state scope and compatibility and MUST NOT imply
canonical equality.

### Deprecation

Deprecation MUST append governance lineage and MUST NOT alter identity or historical validity.
Deprecated identities MUST remain interpretable.

### Migration

Migration to a new domain, schema, canonicalization, or digest profile MUST produce a new Artifact
Identity and a migration manifest linking old and new identities. A migration MUST state whether
semantic equivalence, canonical equality, or no equivalence is certified.

### Historical Preservation

Historical artifacts MUST retain their original canonical representation or sufficient immutable
inputs and profile definitions to reconstruct it exactly. New software MUST NOT recanonicalize
historical artifacts under current profiles and present the result as the original identity.

### Digest Profile Retirement

Retirement of a Digest Profile MUST preserve old qualified digests. A new digest MAY be added for
the same immutable artifact through an explicit multi-profile binding record. The old digest MUST
NOT be silently replaced.

## Identity Invariants

1. Every authoritative artifact has one primary domain-qualified identity.
2. Identity is immutable.
3. Identity Domain and Domain Version are mandatory.
4. Every digest is qualified by domain, canonicalization, and Digest Profile.
5. Naked digest equality has no architectural meaning.
6. Canonical representation is deterministic.
7. Canonical ordering never depends on runtime or storage order.
8. Canonical equality applies only within identical complete profile scope.
9. Semantic equivalence does not automatically imply canonical equality.
10. Digest domains never overlap or reuse identity purpose.
11. Cross-domain digest interpretation is prohibited.
12. Parent-child digest composition is typed and acyclic.
13. Operational variability never changes semantic identity.
14. Invalid artifacts receive no authoritative digest.
15. Identity lineage is immutable, typed, directional, and preserved.
16. Correction, replacement, supersession, withdrawal, and migration never rewrite identity.
17. Historical canonicalization profiles remain interpretable.
18. Digest-profile evolution never silently replaces prior digests.
19. Storage location and cache presence never define artifact identity.
20. Certification identity remains distinct from validation and subject identity.
21. Replay identity remains distinct from original run and result identities.
22. Snapshot identity remains distinct from Checkpoint identity.
23. Token identity remains distinct from secret credential material.
24. Decision identity remains outside EPIP-017 identity authority.

## Certification

Identity certification MUST verify at least:

1. Domain ownership, uniqueness, and version interpretation.
2. Complete Identity Manifest and qualified references.
3. Deterministic canonical representation from identical valid content.
4. Field, collection, graph, diagnostic, temporal, and lifecycle ordering.
5. Missing, null, empty, default, duplicate, unknown, numeric, textual, binary, and temporal
   representation rules.
6. Independence from machine, locale, timezone, environment, process, thread, memory, filesystem,
   storage, and discovery order.
7. Domain separation for every digest-bearing artifact.
8. Rejection of cross-domain equality and unqualified digests.
9. Typed acyclic hierarchical composition.
10. Identity and digest stability under relocation, replication, cache, and archival.
11. New identity and lineage for correction, replacement, supersession, migration, and profile
    evolution.
12. Historical reconstruction under original versions.
13. Digest mismatch, collision-response, and multi-profile migration governance.
14. Separation of semantic, operational, ledger, diagnostic, validation, replay, certification,
    governance, storage, and handoff domains.
15. Strict and semantic equivalence handling under ADR-EPIP017-08.

Certification MUST use adversarial ordering, omitted fields, duplicates, version mismatches,
cross-domain equal byte values, environment changes, and historical migration cases. Nominal
serialization round trips are insufficient.

## Determinism

Given identical valid artifact content, Identity Domain, Domain Version, artifact schema,
Canonicalization Profile, Digest Profile, identity-scheme version, and child references, EPIP-017
MUST produce identical:

- canonical representation;
- canonical ordering;
- qualified Artifact Identity where content-derived by contract;
- qualified digest;
- lineage representation;
- validation findings and diagnostics.

Environment, implementation language, machine, worker, process, thread, locale, timezone,
filesystem, database, insertion order, memory address, and wall clock MUST NOT affect canonical
content.

This ADR does not require semantically equivalent but canonically different artifacts to share an
identity. Their equivalence MUST be an explicit separately identified relation under
ADR-EPIP017-08.

## Replay Compatibility

Replay MUST preserve or reconstruct using the original:

- Identity Domains and Domain Versions;
- artifact schemas and identity-scheme versions;
- Canonicalization and Digest Profiles;
- qualified artifact and child references;
- canonical ordering;
- lineage, migration, replacement, and supersession facts;
- original validation and certification identities;
- original plan, registry, temporal, ledger, snapshot, and result identities.

Replay MUST NOT recanonicalize an original artifact under the latest profile and call it identical.
If migration is required, replay MUST produce a separately identified migrated artifact and lineage.

Replay comparison MUST name strict, semantic, operational, replay, or certification equivalence and
MUST compare identities appropriate to that profile. Replay modes remain governed by
ADR-EPIP017-11.

## Diagnostics

Diagnostics MUST use stable, versioned codes and distinguish at minimum:

- missing, malformed, duplicate, ambiguous, or conflicting identity;
- Identity Domain or Domain Version mismatch;
- identity-authority or ownership conflict;
- Canonicalization Profile absence, incompatibility, or violation;
- field, collection, graph, temporal, numeric, or diagnostic ordering conflict;
- hidden, lossy, environment-dependent, or runtime-dependent normalization;
- canonical equality conflict;
- digest mismatch, unqualified digest, profile mismatch, or domain violation;
- cross-domain equality attempt or digest reuse;
- parent-child composition mismatch or identity cycle;
- lineage inconsistency, missing predecessor, or ambiguous supersession;
- unexpected equivalence or unexpected divergence;
- migration inconsistency or implicit migration;
- historical reconstruction failure;
- silent digest replacement or profile retirement violation;
- validation or certification identity confusion.

Diagnostics MUST identify artifact, domain, complete versions, profiles, authority, expected and
observed canonical facts, lineage, and comparison relation. Diagnostics MUST NOT silently normalize,
migrate, replace, or recalculate an authoritative identity.

## Audit

Audit MUST preserve:

- every Identity Manifest and issuing authority;
- domain, schema, identity-scheme, canonicalization, and Digest Profile versions;
- canonical representations or sufficient immutable reconstruction inputs;
- qualified digests and domain-separation identifiers;
- parent-child typed composition and lineage manifests;
- all corrections, replacements, supersessions, withdrawals, deprecations, and migrations;
- multi-profile digest bindings and retirement actions;
- validation and certification evidence;
- identity conflicts, mismatches, collision responses, and diagnostics;
- proof that historical identities were not rewritten;
- equivalence relation used for every comparison.

Audit MUST be able to distinguish artifact equality, canonical equality, semantic equivalence,
operational equivalence, and mere equal digest bytes. It MUST NOT infer authority or trust from a
digest.

## Migration

- Every legacy identifier MUST be inventoried by actual domain and authority. Names, database keys,
  paths, UUIDs, hashes, and timestamps MUST NOT be assumed equivalent.
- Legacy artifacts lacking domain qualification MUST receive migration manifests rather than silent
  reinterpretation.
- Existing serialization order, defaults, null handling, numeric representation, timezone,
  collections, and normalization MUST be documented before equivalence claims.
- Existing producer versions MUST be supplemented by immutable implementation identity before
  EPIP-017 certification.
- Existing universal execution digests MUST be decomposed into domain-specific identities and
  digests.
- Historical digests MUST be retained with their original interpretation, even when weak or
  incomplete.
- Migration MUST create new identities and typed migrates-from lineage.
- Cross-domain digest reuse MUST be eliminated.
- Shadow validation MUST compare canonical artifacts under exact profiles and separately assess
  semantic equivalence.
- Identity gaps or historical reconstruction failures MUST be diagnosed and MUST NOT be fabricated.
- Legacy rollback and retirement MUST follow ADR-EPIP017-16.

## Backward Compatibility

This ADR changes no production identifier, digest, serialization format, public API, producer,
EPIP-016 contract, Replay behavior, EventBus behavior, financial calculation, risk rule, portfolio
behavior, or execution behavior.

Existing identities and digests remain governed by their original contracts until migrated. They
MUST NOT be relabeled as EPIP-017-qualified identities without a migration manifest and
certification.

EPIP-016 identity and canonical serialization remain frozen. ADR-EPIP017-15 MUST map committed
Evidence and handoff provenance without changing EPIP-016 Decision identity or interpreting an
EPIP-017 operational digest as a Decision digest.

Historical EPIP-017 identities MUST remain interpretable after new profiles, domains, schemas, or
digest constructions are introduced.

## Forbidden Behaviours

EPIP-017 MUST NEVER permit:

1. Identity mutation or in-place reinterpretation.
2. Digest reuse as the primary identity of another domain.
3. Cross-domain equality based on digest bytes.
4. Runtime canonicalization-profile changes.
5. Environment-, machine-, locale-, timezone-, storage-, or order-dependent canonicalization.
6. Hidden, lossy, or undocumented normalization.
7. Silent digest replacement or digest-profile migration.
8. Implicit identity migration.
9. Historical recanonicalization presented as original identity.
10. Unqualified digest storage, comparison, lookup, or audit interpretation.
11. One universal digest for semantic, operational, ledger, replay, validation, and certification
    purposes.
12. Invalid artifacts receiving authoritative digests.
13. Circular digest composition.
14. Storage locator, memory address, process, thread, worker, or queue identity used as artifact
    identity.
15. Version label used as sufficient producer implementation identity.
16. Matching schema or representation treated as semantic equivalence.
17. Canonical equality claimed across different profiles or domain versions.
18. Lineage deletion, cycle, mutation, or predecessor replacement.
19. Certification digest treated as self-contained proof without its evidence.
20. Token secret or credential material exposed through identity.
21. Replay Session identity replacing original artifact identity.
22. Snapshot and Checkpoint identity conflation.
23. Decision identity created or reinterpreted by EPIP-017.

Any forbidden behavior SHALL be an architecture and certification failure and MUST fail closed.

## Alternatives Considered

### One universal content hash

Every artifact uses the same unqualified content hash and equal values imply equality.

Rejected because domain, interpretation, authority, canonicalization, and lifecycle differ.

### Runtime-generated opaque identifiers only

Artifacts use random or storage-generated identifiers without canonical content identity.

Rejected because identity would not establish reproducibility, lineage integrity, or independent
verification.

### Semantic identity only

Semantically equivalent artifacts share one identity regardless of producer, representation,
execution, or provenance.

Rejected because provenance, authority, representation, validation, and operational history would
be lost.

### Digest identity only

An artifact is identified solely by digest bytes.

Rejected because a digest is not self-describing and cannot establish domain, profile, trust,
meaning, or authority.

### Domain-qualified identities with versioned canonicalization and typed digest hierarchy

Accepted because meaning, representation, execution, validation, replay, and certification remain
independently identifiable and evolvable.

## Decision

EPIP SHALL adopt the identity, domain, canonicalization, ordering, digest, hierarchy, composition,
domain separation, lineage, evolution, certification, determinism, replay, diagnostic, audit,
migration, compatibility, and prohibition rules in this ADR as the constitutional identity model
for EPIP-017.

No artifact MAY be compared, trusted, committed, replayed, validated, certified, migrated, cached,
or audited using an unqualified identity or digest. No implementation MAY collapse domains for
convenience.

## Consequences

### Positive

- Semantic, operational, ledger, replay, validation, and certification identities cannot be
  confused.
- Historical artifacts remain interpretable across canonicalization and digest evolution.
- Hidden normalization and runtime ordering cannot change identity.
- Producer implementation behavior receives stronger identity than version labels.
- Typed hierarchical composition supports independent verification without universal digests.
- Migration and replacement preserve complete lineage.
- Replay, cache, snapshot, audit, and certification receive stable identity foundations.

### Negative

- Every authoritative artifact requires explicit domain and profile metadata.
- More identities and digests must be retained and correlated.
- Canonicalization evolution requires governed migration rather than transparent upgrades.
- Cross-domain comparisons become deliberately more restrictive.
- Historical reconstruction requires long-term profile and schema retention.

### Trade-offs

EPIP accepts a richer identity system and explicit migration cost in exchange for eliminating
ambiguous equality, digest misuse, silent identity drift, and historical reinterpretation.

## Non-goals

This ADR does not define:

- cryptographic algorithms, key lengths, libraries, protocols, encodings, or implementations;
- signature issuance, key custody, certificate infrastructure, or secret storage;
- implementation classes, APIs, serializers, digest engines, stores, or interfaces;
- durable-result store, cache, eviction, reuse, or invalidation behavior;
- replay modes or replay algorithms;
- snapshot or checkpoint content and consistency rules;
- retry, failure, recovery, or parallel execution algorithms;
- EPIP-016 handoff representation;
- analytical formulas, trading, Decision, Candidate, Confidence, risk, portfolio, execution, or
  financial logic.

These exclusions MUST be resolved by their mandatory ADRs and MUST NOT be delegated to code.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 through ADR-EPIP017-08 and the frozen EPIP-016 and
H001–H007 architecture.

It creates or confirms mandatory dependencies on:

- ADR-EPIP017-10 for Durable Result, cache-entry, content-locator, invalidation, and reuse identity
  domains;
- ADR-EPIP017-11 for Replay Session, replay result, comparison, divergence, and original-artifact
  identity relations;
- ADR-EPIP017-12 for Snapshot, Checkpoint, consistency-boundary, and restore identity domains;
- ADR-EPIP017-13 for failure, retry authorization, recovery, fallback, and supersession lineage;
- ADR-EPIP017-14 for parallel-attempt, barrier, execution-group, and equivalence identities;
- ADR-EPIP017-15 for Evidence-set and Handoff Manifest identity without EPIP-016 identity
  modification;
- ADR-EPIP017-16 for migration manifests, compatibility lineage, rollback, and retirement;
- ADR-EPIP017-17 for Audit Record, telemetry projection,
  redaction, attestation, and Diagnostic Report identity;
- ADR-EPIP017-18 for resource, environment, and
  operational-policy identity.

This ADR introduces the Identity Domain Authority, Canonicalization Profile Authority, and Digest
Profile Authority as explicit governance roles. They MUST use ADR-EPIP017-03 ownership,
separation, authenticity, lifecycle, and audit rules. Cryptographic signing and key governance MAY
require a future security ADR if not fully governed by existing H007 contracts; no implementation
assumption is authorized here.

## Future Evolution

New Identity Domains, canonicalization profiles, digest profiles, representations, and lineage
relationships MAY be introduced through immutable versioned governance. Existing identities MUST
NOT be reinterpreted.

Algorithm agility, multiple concurrent digest profiles, stronger integrity mechanisms, signatures,
and external attestation MAY evolve through governed profiles and binding records while preserving
old qualified digests.

Cross-system identity federation MAY be introduced only with explicit domain mapping, authority,
trust, collision, migration, replay, and certification rules. External identifiers MUST NOT become
EPIP identities implicitly.

## Approval Gate

Approval of this ADR resolves EPIP-017 identity, canonicalization, digest hierarchy, domain
separation, lineage, and deterministic identity evolution only.

It does not approve a serializer, digest algorithm, signature service, key system, identifier
generator, cache, replay engine, snapshot engine, audit engine, or Programme A.

EPIP-017 implementation remains prohibited until the complete mandatory ADR set is accepted and
the remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
