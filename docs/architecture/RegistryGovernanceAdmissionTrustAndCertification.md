# Registry Governance, Admission, Trust, and Certification

## Purpose

This document defines the frozen implementation architecture for EPIP-017 producer registry
governance. It specifies how complete immutable governance facts enter the public registry,
receive validation, undergo deterministic reduction, become an immutable registry snapshot, and
are published as the single authoritative governance state.

The architecture implements the constitutional responsibilities of
[ADR-EPIP017-03](../adr/ADR-EPIP017-03-RegistryGovernanceAdmissionTrustAndCertification.md)
without transferring authority to orchestration, storage, identity, or implementation mechanics.
It also preserves the boundaries established by ADR-01, ADR-02, ADR-08, ADR-09, ADR-11, ADR-16,
and ADR-17.

## Scope

This architecture governs:

- immutable producer-governance facts;
- admission, ownership, trust, certification, compatibility, lifecycle, and revocation validation;
- the complete immutable input for one governance operation;
- deterministic governance-state reduction;
- deterministic registry-snapshot construction;
- atomic publication of one authoritative registry snapshot;
- lifecycle-wide invariants;
- architectural conformance;
- compatibility and evolution of the frozen A03 contract.

It applies only to Programme A Work Package A03. It does not implement producer execution,
Evidence semantics, planning, scheduling, replay execution, durable persistence, recovery,
observability infrastructure, capacity control, or the EPIP-016 handoff.

## Relationship to ADR-03

ADR-EPIP017-03 is the constitutional authority for producer registry governance, admission,
ownership, trust, certification, compatibility, lifecycle, and governance evidence. This document
defines the implementation architecture that realizes those responsibilities.

This document does not amend ADR-03, create a new constitutional authority, or replace any rule in
ADR-01 through ADR-18. If this document and the constitutional corpus appear to conflict, the
constitutional corpus governs and the implementation fails closed pending governed correction.

The principal supporting ADRs are:

| ADR | Applied responsibility |
| --- | --- |
| ADR-EPIP017-01 | System boundary, authority separation, and prohibition of orchestration leakage |
| ADR-EPIP017-02 | Immutable producer declarations and producer-contract boundary |
| ADR-EPIP017-03 | Registry, admission, ownership, trust, certification, compatibility, and lifecycle governance |
| ADR-EPIP017-08 | Determinism profiles and reproducibility |
| ADR-EPIP017-09 | Identity domains, canonicalization, digest hierarchy, and lineage |
| ADR-EPIP017-11 | Historical interpretation and replay compatibility |
| ADR-EPIP017-16 | Compatibility, version evolution, and migration governance |
| ADR-EPIP017-17 | Governance diagnostics, audit, retention, and redaction boundary |

## Architectural Context

The producer contract established by A02 is immutable but is not self-admitting. A producer does
not become authoritative because it exists, can execute, or satisfies a structural protocol. Its
governance standing must be established through explicit immutable facts under ADR-03.

A03 therefore requires a closed governance path:

```text
GovernanceRegistry
    -> GovernanceCoordinator
        -> GovernanceReducer
            -> Governance validation layer
        -> SnapshotBuilder
        -> GovernanceStore
```

The public registry accepts one governance action, one complete immutable manifest, and one logical
governance epoch. It never retrieves missing governance facts from identifiers. Every fact required
to validate and reduce the operation travels in the manifest. The resulting snapshot becomes
authoritative only through atomic replacement in the store.

## Architectural Principles

The following principles govern every A03 component:

1. **Explicit authority.** Authority originates in validated governance facts, never in execution
   success, component location, object possession, or publication state. Governed by ADR-03.
2. **Complete immutable input.** One manifest contains every fact required to derive one governance
   operation. Governed by ADR-03 and ADR-09.
3. **One responsibility per layer.** Validation, reduction, construction, coordination, façade,
   and publication remain separate. Governed by ADR-01 and ADR-03.
4. **Fail closed.** Missing, ambiguous, unsupported, mutable, inconsistent, or rejected content
   produces no authoritative state change. Governed by ADR-03 and ADR-08.
5. **Deterministic derivation.** Canonically identical inputs and starting state produce canonically
   identical outcomes. Governed by ADR-08 and ADR-09.
6. **Append-only history.** New governance facts never erase or rewrite earlier authority,
   certification, compatibility, trust, lifecycle, or revocation evidence. Governed by ADR-03,
   ADR-09, and ADR-11.
7. **Single authoritative snapshot.** A candidate is non-authoritative until one atomic store
   replacement completes. Governed by ADR-03 and ADR-09.
8. **No hidden state.** Clocks, randomness, filesystem state, network state, process state, and
   mutable global state do not participate in governance outcomes. Governed by ADR-08.

## Alternative D Overview

The public governance operation is:

```text
GovernanceRegistry.apply(action, manifest, epoch)
```

The API remains unchanged. `GovernanceManifest` is the complete immutable governance derivation
input. It carries typed governance facts and immutable action-to-fact references. The action selects
the facts that participate in the operation; unrelated facts cannot acquire governance effect.

This design preserves the public façade while ensuring that the reducer never reconstructs typed
facts from identifiers and never relies on a lookup service, hidden repository, mutable payload, or
ambient context. Governed by ADR-03 and ADR-09.

## GovernanceManifest

### Completeness Boundary

One manifest represents exactly one governance operation and contains exactly one governance
action. It is complete when it contains every immutable fact required to:

- validate that action;
- reduce that action against the identified starting registry state;
- construct the resulting registry snapshot without external lookup or inference;
- reproduce the same candidate snapshot from the same starting state.

The manifest is not an epoch-wide inventory, registry dump, historical archive, batch, or transport
container for multiple operations. Historical state comes from the immutable starting snapshot.
Historical facts may be referenced only where the selected action requires them and the frozen
reference rules permit the relationship.

Facts unrelated to the selected action are prohibited. Multiple governance actions in one manifest
are prohibited. Non-selected actions and non-selected facts do not participate in governance,
identity derivation, reduction, or snapshot construction.

### Frozen Schema

`GovernanceManifest` has exactly these mandatory top-level fields, in this structural order:

1. `manifest_schema_version`
2. `identity_domain_version`
3. `canonicalization_profile_identity`
4. `canonicalization_profile_version`
5. `digest_profile_identity`
6. `digest_profile_version`
7. `manifest_identity`
8. `governance_epoch`
9. `actions`
10. `admission_requests`
11. `producer_contracts`
12. `proposed_registry_entries`
13. `certification_profiles`
14. `certification_records`
15. `compatibility_decisions`
16. `fact_references`
17. `policy_versions`
18. `authority_facts`

No optional top-level field exists. A collection with no members is represented by an explicit
empty immutable tuple. Additional, extension, opaque, catch-all, metadata, or implementation-private
fields are prohibited.

All fields except `manifest_identity` participate in manifest identity according to the frozen
identity and canonicalization profiles. `manifest_identity` is the resulting identity and does not
participate recursively in its own derivation. No field is validation-only or replay-only; every
field retains the participation assigned by the frozen schema and identity contract.

### Structural Invariants

The manifest must:

- use immutable values and immutable tuples exclusively;
- contain exactly one action;
- use valid versioned identity and profile declarations;
- contain no duplicate canonical member in any uniqueness-governed section;
- bind its action and facts to the same governance epoch;
- resolve every fact reference to exactly one contained fact;
- contain no orphan, ambiguous, or unrelated reference;
- match its declared canonical identity;
- require no external lookup, reconstruction, or inferred fact.

Intrinsic manifest validity establishes structure only. It does not establish governance acceptance.

## GovernanceFactReference

`GovernanceFactReference` is a first-class immutable value object representing one canonical
relationship between the selected governance action and one manifest-contained fact.

It contains exactly these mandatory fields:

1. `identity_domain`
2. `artifact_identity`
3. `artifact_version`
4. `fact_type`
5. `relationship_role`

It has no optional fields and no mutable content.

Canonical equality is equality of all five fields after application of the frozen canonicalization
profile. Canonical ordering uses the same fields in the listed order. Two canonically equal
references are duplicates and make the manifest invalid.

Every reference participates in manifest canonical serialization and manifest identity derivation.
It participates in snapshot identity through the frozen snapshot profile wherever its selected fact
affects snapshot content or governance provenance.

Resolution is local and exact. A reference must resolve to exactly one fact in the manifest with the
declared identity domain, artifact identity, version, and fact type. External lookup, identifier
reconstruction, transitive resolution, implicit version selection, and cross-domain identity
coercion are prohibited. Cross-domain relationships are allowed only when the relationship retains
both domains explicitly and satisfies the governing ADR contracts.

## Validation Architecture

Validation is ordered, exclusive, deterministic, and fail closed. Each validation activity has
exactly one owner. Delegation does not transfer validation ownership.

The normative order is:

1. intrinsic `GovernanceManifest` validation;
2. registry delegation without validation;
3. coordinator transfer without validation;
4. supported-action validation by `GovernanceReducer`;
5. deterministic applicable-validator selection by `GovernanceReducer`;
6. governance-semantic validation by the governance validation layer;
7. validator-completion confirmation by `GovernanceReducer`;
8. immutable reduction;
9. structural snapshot-construction checks by `SnapshotBuilder`;
10. candidate construction;
11. atomic store replacement.

No validation stage may be reordered, skipped, repeated, inferred, or executed speculatively.

### Intrinsic Manifest Validation

Intrinsic validation owns only facts decidable from the manifest itself:

- schema and mandatory-field conformance;
- prohibited-field absence;
- field types and deep immutability;
- tuple representation;
- intrinsic identity and version syntax;
- structural ordering and uniqueness;
- fact-reference uniqueness and exact local resolution;
- the one-operation completeness boundary;
- internal epoch and schema-version consistency;
- declared manifest-identity consistency.

It must not consult a registry snapshot, determine governance eligibility, decide authority,
validate lifecycle against prior state, reduce an action, construct a snapshot, or access an
external source.

### Governance Validation Layer

The existing stateless validators exclusively own governance-semantic validation against the
current snapshot and explicit manifest facts:

- admission eligibility and semantic declaration completeness;
- authoritative ownership uniqueness;
- authority authorization, scope, and separation;
- certification profile, scope, version, status, suspension, and revocation;
- compatibility direction, source, target, approval, and revocation;
- lifecycle transitions and terminal states;
- trust transitions, authority, scope, and evidence;
- revocation authority, scope, duplication, and prior state;
- action-to-fact semantic correspondence;
- consistency with current authoritative registry state;
- applicable governance-policy conditions.

Validators do not mutate, reduce, construct, coordinate, publish, repair, infer, or perform external
lookup. They return deterministic acceptance or an immutable `GovernanceRejection`.

### Structural Admission

`structural_admission_approved` is an explicit, immutable Registry Authority decision that one
proposed producer entry satisfies the structural-admission requirements of ADR-EPIP017-03. It is
not an admission request, an automatic consequence of a request, architectural-conformity approval
itself, certification, trust, compatibility approval, activation, publication, or a decision
inferred during reduction.

The existing governance validation layer exclusively owns semantic validation of this action. The
existing admission-validation path owns the structural-admission assertions below. The existing
authority-validation path retains general authority authorization, scope, and separation. No new
validator type, validation layer, or execution path is introduced.

Before reduction may begin, validation must establish all of the following against the exact
authoritative starting snapshot, selected action, complete manifest, and supplied governance epoch:

1. The selected action is exactly one `structural_admission_approved` action and selects exactly one
   proposed `RegistryEntry`.
2. The proposed entry corresponds canonically to the selected admission request, producer contract,
   and action-to-fact relationships.
3. Producer identity and version agree across the action, admission request, producer contract,
   proposed entry, and their canonical fact references.
4. The proposed entry contains the complete structurally admitted declaration represented by the
   selected immutable facts.
5. No authoritative entry for the same producer identity and version conflicts with the proposed
   entry.
6. The proposed entry introduces neither duplicate nor conflicting ownership, and identifies
   exactly one authoritative Producer Owner for the producer identity and version at the supplied
   epoch.
7. The required Architectural Authority conformity decision is explicit, selected, current for the
   operation, and applicable to the proposed entry's producer, contract, capability, version, and
   architectural scope.
8. The acting authority is the Registry Authority authorized to approve structural admission for
   the exact selected scope.
9. Producer Owner, Architectural Authority, and Registry Authority responsibilities remain
   distinct, and the Producer Owner does not approve its own structural admission.
10. Every applicable governance-policy identity and version is explicit in
    `GovernanceManifest.policy_versions` and has the identical identity and version in the
    authoritative starting `RegistrySnapshot.policy_versions`.
11. Every selected relationship has the correct identity domain, artifact identity, artifact
    version, fact type, relationship role, and governed subject.
12. No unrelated or non-selected fact participates in the decision.
13. The action effective epoch, manifest governance epoch, supplied governance epoch, and
    authoritative starting-state ordering are mutually consistent.

Missing, ambiguous, conflicting, incorrectly scoped, incorrectly role-labelled, substituted,
inferred, or reconstructed facts or policies cause deterministic immutable rejection. Absence of
rejection is not acceptance. `GovernanceAction.subject_references` does not replace canonical
validation through `GovernanceManifest.fact_references`.

The exact authoritative starting `RegistrySnapshot` determines prior identity and version state,
ownership consistency, applicable policy versions, governance-epoch ordering, and any existing
state that makes structural admission invalid. A later, alternate, reconstructed, or partially
derived snapshot must not be used. An acceptance remains valid only for the exact starting snapshot
to which it is bound.

Repository presence, contract validity, producer declaration, prior admission, or Registry
Authority action does not substitute for explicit Architectural Authority conformity. Manifest
policy declarations do not override the authoritative starting snapshot. Ownership uniqueness
remains exclusively governance-semantic validation and must not be repeated by the reducer.

### Structural Admission ValidationAcceptance

The resulting immutable `ValidationAcceptance` uses the existing admission-validation acceptance
identity `admission`. It binds without substitution or reconstruction:

- validator identity `admission`;
- the exact authoritative starting `RegistrySnapshot`;
- the exact selected `structural_admission_approved` action;
- the exact complete `GovernanceManifest`;
- the exact supplied `GovernanceEpoch`;
- the exact selected admission request, producer contract, and proposed `RegistryEntry`;
- their selected canonical `GovernanceFactReference` values;
- the explicit Architectural Authority conformity fact;
- the explicit Registry Authority authority fact;
- the applicable ownership facts;
- every applicable governance-policy identity and version;
- the canonical action-to-proposed-entry relationship.

The acceptance covers only facts selected for the single structural-admission operation. An
acceptance bound to different inputs does not satisfy validator-acceptance completion. The existing
authority-validation acceptance remains independently required by the applicable-validator set;
neither acceptance subsumes or substitutes for the other.

## GovernanceReducer

`GovernanceReducer` is internal, stateless, deterministic, and pure. It owns:

- supported-action validation;
- deterministic selection of the complete applicable validator set;
- confirmation that every applicable validator explicitly accepted;
- exactly one immutable state reduction after validation completion.

It consumes the exact immutable starting snapshot, selected action, complete manifest, governance
epoch, and applicable validation outcomes. It produces exactly one complete immutable reduction
result or one immutable rejection.

For `structural_admission_approved`, the reducer must consume explicit completion of every
applicable acceptance, including the structural-admission acceptance identified as `admission`,
before immutable reduction begins. A missing, mismatched, incomplete, or differently bound
acceptance terminates the operation with an immutable rejection and no reduction result.

The reducer must not create that acceptance, infer admission eligibility, validate ownership
uniqueness, validate Architectural Authority conformity, validate Registry Authority scope,
validate policy applicability, establish action-to-proposed-entry correspondence, reconstruct a
missing admission fact, or repeat or reinterpret any semantic assertion covered by the acceptance.

The reducer does not own registry state, snapshot construction, publication, persistence,
coordination, identity profiles, clocks, randomness, or external services.

## SnapshotBuilder

`SnapshotBuilder` is internal, stateless, deterministic, and pure. It consumes:

- one complete immutable reduction result;
- the corresponding validated manifest;
- the corresponding governance epoch;
- the frozen snapshot identity, canonicalization, schema, and digest profiles.

It produces exactly one complete immutable candidate `RegistrySnapshot` or one immutable rejection.
It performs only the structural construction checks assigned to it. It does not validate governance
semantics, reinterpret reduction, infer facts, reconstruct omitted state, decide authority, publish
state, or modify a previous snapshot.

## GovernanceStore

`GovernanceStore` is the in-memory owner of the current authoritative `RegistrySnapshot`. An
initialized store exposes exactly one current authoritative snapshot.

The store:

- exposes read-only access to the current immutable snapshot;
- accepts only one complete admitted candidate for a governance operation;
- replaces the current snapshot atomically;
- preserves the previous snapshot until replacement succeeds;
- exposes exactly one authoritative snapshot at every observable point.

It does not validate governance, reduce actions, construct snapshots, derive identity, canonicalize,
reinterpret facts, infer authority, persist externally, schedule work, or execute producers.

## GovernanceCoordinator

`GovernanceCoordinator` is internal and orchestrates exactly one governance operation at a time. It:

1. reads the current immutable snapshot from `GovernanceStore`;
2. invokes `GovernanceReducer` with the exact action, manifest, epoch, and starting snapshot;
3. stops immediately on rejection;
4. invokes `SnapshotBuilder` with the successful reduction result and corresponding inputs;
5. stops immediately on construction failure;
6. requests exactly one atomic store replacement;
7. returns the resulting authoritative snapshot.

The coordinator contains no governance rule, validation rule, reduction rule, construction rule,
identity rule, persistence logic, scheduling, retry, recovery, or producer execution.

## GovernanceRegistry

`GovernanceRegistry` is the sole public A03 governance façade. Its public operation remains:

```text
apply(action, manifest, epoch)
```

It owns one `GovernanceStore`, delegates exactly one operation to `GovernanceCoordinator`, exposes
read-only current-snapshot access, and propagates immutable rejection unchanged.

It performs no validation, reduction, construction, authority decision, persistence, scheduling,
retry, recovery, publication transformation, or fact reconstruction. It introduces no alternate
governance path.

## Complete Governance Lifecycle

The lifecycle has one exclusive sequence:

| Phase | Admission condition | Successful output |
| --- | --- | --- |
| Manifest validation | Complete immutable manifest constructed | Intrinsically valid manifest |
| Governance validation | Exact snapshot, action, manifest, and epoch bound | Explicit acceptance from every applicable validator |
| Immutable reduction | Validation completion established | One complete immutable reduction result |
| Snapshot construction | Successful complete reduction result admitted | One complete immutable candidate snapshot |
| Store replacement | Complete candidate admitted | One authoritative immutable snapshot |

A governance operation has exactly one of two outcomes:

- successful atomic publication of the complete candidate; or
- terminal failure with the previously authoritative snapshot unchanged.

No intermediate value is authoritative. No phase may be retried, repeated, reordered, bypassed, or
replaced by an alternative path within the same operation.

## Component Responsibility Matrix

| Component | Owns | Explicitly does not own |
| --- | --- | --- |
| `GovernanceManifest` | Complete immutable operation input and intrinsic structural validity | Governance acceptance, reduction, construction, publication |
| Governance validation layer | Governance-semantic validation | Mutation, reduction, construction, coordination, publication |
| `GovernanceReducer` | Validator dispatch/completion and immutable state reduction | Registry state, snapshot construction, publication, persistence |
| `SnapshotBuilder` | Structural candidate-snapshot construction and frozen identity derivation | Governance semantics, reduction, authority, publication |
| `GovernanceStore` | Single authoritative snapshot and atomic replacement | Validation, reduction, construction, governance interpretation |
| `GovernanceCoordinator` | Ordered single-operation orchestration | Governance rules, validation rules, state derivation, persistence |
| `GovernanceRegistry` | Public delegation and read-only state access | Every internal governance-processing responsibility |

## Validation Responsibility Matrix

The matrix is normative. `OWNER` identifies the sole validation owner; a blank cell means the
component must not perform that validation.

```text
Validation activity                                      Sole owner
Schema, mandatory fields, types, and immutability        Manifest
Structural ordering and section uniqueness               Manifest
Fact-reference uniqueness and local resolution           Manifest
One-operation manifest completeness                      Manifest
Manifest identity consistency                            Manifest
Admission eligibility                                    Validation layer
Ownership and authority scope                            Validation layer
Structural-admission semantics                           Validation layer
Architectural-conformity dependency                      Validation layer
Structural-admission policy consistency                  Validation layer
Action-to-proposed-entry correspondence                  Validation layer
Certification semantics                                  Validation layer
Compatibility semantics                                  Validation layer
Lifecycle and trust transitions                          Validation layer
Revocation semantics                                     Validation layer
Action-to-fact semantic correspondence                   Validation layer
Supported-action validation                              Reducer
Applicable-validator-set completeness                    Reducer
Validator-acceptance completion                          Reducer
Candidate input immutability and identity uniqueness     Builder
Candidate epoch and manifest structural consistency      Builder
Candidate identity derivability and reproducibility      Builder
```

Each activity has exactly one owner. Duplicated, skipped, hidden, or unassigned validation is
prohibited.

## Reduction Semantics

Reduction begins only after explicit acceptance from every applicable validator. Absence of a
rejection is not acceptance.

The reducer applies exactly one frozen transformation using only facts selected by the action's
validated references. It must:

- preserve the complete prior governed state;
- preserve every unaffected `RegistryEntry` by canonical value;
- preserve all prior governance history;
- append every accepted selected fact exactly once;
- create new immutable authoritative representations where the action requires a state change;
- retain prior representations as historical evidence;
- preserve canonical ordering;
- produce all state required by `SnapshotBuilder` without lookup or inference.

It must not mutate the starting snapshot, delete or rewrite history, process unrelated manifest
facts, invent authority, infer decisions, reconstruct facts, or choose an alternative reduction
path.

Canonically identical validated inputs produce canonically identical reduction results. If a
complete immutable result cannot be produced, reduction fails and no construction is admitted.

## Snapshot Construction Semantics

The frozen `RegistrySnapshot` structure contains:

1. `snapshot_identity`
2. `manifest_reference`
3. `governance_epoch`
4. `entries`
5. `governance_action_references`
6. `policy_versions`

The builder preserves the complete post-reduction entries, action-reference history, policy state,
authority attribution, lineage, and governance meaning. It creates a new deeply immutable candidate
and never mutates its inputs.

Snapshot identity is derived from all and only the identity-participating values established by
ADR-09 and the frozen profiles, including the domain and profile versions, manifest identity,
governance epoch, canonical entries, action-reference history, policy versions, and governed
authority facts where the profile designates them. The identity does not derive from itself.

Identity must not depend on clock time, randomness, process or thread identity, memory allocation,
input iteration order where different from canonical order, mutable cache, filesystem, network,
locale, or platform behaviour.

Construction is complete only when every field and the final identity are present and deeply
immutable. Lazy materialization, deferred identity, post-construction canonicalization, and partial
candidates are prohibited.

## Authoritative Publication Semantics

A candidate remains non-authoritative until atomic replacement succeeds. Before the publication
boundary, every current-state read returns the previous complete snapshot. After the boundary,
every subsequent current-state read returns the new complete snapshot until another independently
completed replacement.

At no observable point may the store expose:

- zero authoritative snapshots;
- two current authoritative snapshots;
- a partially published candidate;
- a mixture of old and candidate fields;
- mutable authoritative state;
- a reduction result as authoritative state.

Publication exposes the exact candidate unchanged. If replacement fails, the previous snapshot
remains authoritative and the candidate remains non-authoritative. No rollback transition is
required because no authoritative change occurred.

## Lifecycle-Wide Architectural Invariants

The following invariants remain true from operation admission through publication or terminal
failure:

### Authority

- Every authority-bearing fact is explicit and validated.
- No component invents, infers, transfers, broadens, narrows, or reconstructs authority.
- Execution mechanics and publication status create no governance decision.

### Immutability

- Inputs, validation outcomes, reduction results, candidates, entries, and snapshots are deeply
  immutable.
- The current authoritative snapshot is never mutated in place.
- No mutable or deferred reference crosses a lifecycle boundary.

### Determinism

- The lifecycle order is fixed.
- Canonically identical inputs and starting state produce canonically identical outcomes.
- Hidden environment state does not influence validation, reduction, identity, construction, or
  publication.

### Identity

- Frozen identity domains and profiles remain authoritative.
- Identity remains stable while canonical identity-participating content remains unchanged.
- Every identity describes the exact immutable content it identifies.

### History

- Governance history is append-only.
- Successful operations append accepted facts exactly once.
- Failed operations append no authoritative history.

### Validation

- Every validation has exactly one owner.
- Complete explicit acceptance binds only the exact validated inputs.
- Later phases do not repeat or reinterpret validation.

### Reduction and Construction

- One completed validation admits at most one reduction.
- One successful reduction admits at most one construction.
- Reduction and construction preserve governance meaning and unaffected state.

### Publication

- One candidate admits at most one replacement request.
- Exactly one authoritative snapshot exists at every observable point.
- Failure at any phase preserves the previous authoritative snapshot.

### Responsibility Separation

- No hidden validation, authority, reduction, construction, publication, inference, reconstruction,
  persistence, or state transition exists.
- No component duplicates or acquires another component's responsibility.

### Traceability

Every new authoritative fact remains traceable through the selected action, immutable fact
reference, manifest fact, validation acceptance, reduction result, candidate snapshot, and
published authoritative snapshot.

## Conformance Model

The architecture is one indivisible conformance contract. Complete conformance exists only when
objective evidence demonstrates every obligation and prohibition in this document.

Each obligation receives one result:

- `PASS`: complete objective evidence demonstrates the obligation;
- `FAIL`: objective evidence demonstrates a violation;
- `NOT DEMONSTRATED`: evidence is missing, incomplete, indeterminate, or unrelated.

Only `PASS` satisfies an obligation. Any `FAIL` or `NOT DEMONSTRATED` result makes overall
architectural conformance incomplete. Partial conformance may be recorded diagnostically but is not
architectural conformance.

Required evidence categories are technology-neutral:

- structure and immutable representation;
- requirement traceability;
- exclusive responsibility ownership;
- lifecycle sequencing;
- state preservation and publication;
- immutability;
- deterministic equivalence;
- identity stability and reproducibility;
- append-only history;
- fail-closed behaviour;
- negative architectural boundaries;
- complete obligation coverage;
- exact evaluated-configuration identity.

Conformance cannot be established through architectural intent, documentation claims without
implementation evidence, selected successful scenarios, implementation-specific equivalence, or
one component performing another component's responsibility.

For the same frozen specification, evaluated configuration, evidence, and obligation matrix, the
conformance result must be identical.

## Compatibility and Evolution Contract

Architectural compatibility preserves both observable outcomes and the responsibility allocation
that produces them.

### Backward Compatibility

Artifacts valid under the frozen contract retain their representation, governance meaning,
authority, lifecycle interpretation, canonical identity, deterministic outcomes, and failure
semantics under their original versions and profiles.

### Forward-Safe Behaviour

A frozen implementation is not required to process an unsupported future version. It must identify
the version as unsupported, reject it deterministically, preserve the authoritative snapshot, and
avoid partial interpretation or implicit migration.

### Compatibility Classes

| Class | Required condition |
| --- | --- |
| Compatible | Every applicable frozen obligation remains satisfied without changed meaning, identity, responsibility, sequence, or failure behaviour |
| Conditionally compatible | The complete frozen contract remains unchanged behind its existing boundary and new behaviour is isolated by an explicit version or profile boundary |
| Incompatible | Any frozen obligation is violated, reinterpreted, weakened, silently superseded, or no longer demonstrably conformant |

A change receives exactly one classification for each affected compatibility boundary. Missing or
indeterminate evidence cannot establish compatibility.

Future revisions are cumulative. A frozen obligation is superseded only when a governed revision
identifies the exact obligation, originating contract, replacement, affected version boundary, and
compatibility classification. Silence, omission, implementation convenience, a new version number,
or apparent behavioural similarity does not supersede a frozen rule.

Compatibility claims require objective evidence for representation, responsibility, determinism,
identity, sequencing, state, failure behaviour, conformance, version boundaries, and any explicit
supersession. Governed by ADR-09 and ADR-16.

## Repository Traceability

The repository implementation maps to this architecture as follows:

| Architectural element | Repository artifact | Governing ADRs |
| --- | --- | --- |
| Immutable governance models and manifest | `epip/governance/model.py` | ADR-02, ADR-03, ADR-08, ADR-09 |
| Governance validation layer | `epip/governance/validation.py` | ADR-03, ADR-08 |
| Immutable reduction | `epip/governance/reduction.py` | ADR-03, ADR-08, ADR-09 |
| Snapshot construction and identity | `epip/governance/snapshot.py` | ADR-03, ADR-09 |
| Authoritative in-memory state | `epip/governance/store.py` | ADR-03, ADR-09 |
| Lifecycle orchestration | `epip/governance/coordinator.py` | ADR-01, ADR-03 |
| Public governance façade | `epip/governance/registry.py` | ADR-01, ADR-03 |
| Public immutable exports | `epip/governance/__init__.py` | ADR-02, ADR-03 |
| Component and integration evidence | `tests/governance/` | ADR-03, ADR-08, ADR-09, ADR-16 |

Every exported symbol must identify A03 ownership and all governing ADRs. Internal symbols must
remain internal. Tests must demonstrate both required behaviour and prohibited responsibility
leakage.

## Implementation Boundary

The implementation may change only the existing A03 model, validator, reducer, builder, store,
coordinator, registry, package-export, test, and architecture-document artifacts required to
realize this specification.

It must preserve:

- the A01-F orchestration boundary;
- the A02 producer contract;
- the public `GovernanceRegistry.apply(action, manifest, epoch)` operation;
- all ADR-01 through ADR-18 authority and responsibility boundaries.

It must not create another registry path, validator layer, reducer, snapshot authority, store
authority, public operation, lookup service, hidden repository, persistence adapter, or mutable
payload.

## Explicit Non-Goals

This architecture does not define or implement:

- producer discovery or runtime execution;
- Evidence dependency resolution;
- semantic or dispatch planning;
- scheduling or parallel execution;
- invocation attempts, leases, fences, or atomic result commit;
- durable-result persistence or cache authority;
- replay execution;
- snapshot checkpoints or recovery;
- migration execution;
- observability, retention, or redaction infrastructure;
- capacity admission or operational scheduling;
- EPIP-016 handoff;
- trading, market analysis, risk, portfolio, or execution logic;
- external services, network protocols, transport APIs, or deployment mechanisms.

## Summary

A03 provides one closed, deterministic governance path. One public registry operation receives one
action, one complete immutable manifest, and one logical epoch. Intrinsic and semantic validation
remain exclusively owned. Successful validation admits one immutable reduction, which admits one
deterministic snapshot construction, which admits one atomic store replacement.

No component invents facts or authority. No intermediate state is authoritative. Governance
history is append-only. Failure at any boundary preserves the previous authoritative snapshot.
Compatibility, conformance, and evolution remain explicit, versioned, deterministic, and governed
by the frozen EPIP-017 corpus.
