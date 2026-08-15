# ADR-EPIP017-03 — Registry Governance, Admission, Trust and Certification

## Status

Approved and frozen.

ADR-EPIP017-01 and ADR-EPIP017-02 are approved, frozen, and normative. This ADR MUST NOT modify
their system boundaries, authority separation, producer execution contract, lifecycle semantics,
EPIP-016 boundary, or single-authoritative-path rule.

This ADR defines constitutional governance only. It authorizes no implementation, registry
component, interface, production code, placeholder, or Programme A activity.

## Executive Summary

EPIP-017 SHALL admit a producer only through explicit, attributable, independently certified, and
auditable governance decisions. Discovery, descriptor submission, registration, certification,
trust, enablement, and runtime availability SHALL remain distinct concepts. None SHALL imply
another.

Every producer identity and version MUST have exactly one authoritative **Producer Owner**. The
Producer Owner MAY request admission but MUST NOT approve registration, issue certification, grant
production trust, activate the producer, or suppress revocation for that producer.

EPIP-017 SHALL recognize separate institutional authorities for architecture, registry
administration, certification, security, operations, compatibility, and revocation. Their scopes
MUST be non-overlapping where final authority differs. For production admission, the Producer
Owner, Certification Authority, Security Authority, and Registry Authority MUST act through
independent authority identities.

The registry SHALL be an immutable, versioned, auditable governance catalog and capability index.
It SHALL publish deterministic snapshots for semantic planning. It MUST NOT discover at runtime,
execute producers, schedule work, inspect producer outputs, determine operational retries, mutate
an active run, or become a service locator for producers.

Trust, certification, and lifecycle SHALL be orthogonal axes. A producer can be registered but
uncertified, certified but disabled, trusted but deprecated, or legacy without being admitted to
EPIP-017. A producer is eligible for an authoritative plan only when the exact producer,
capability, contract, configuration, trust, compatibility, and certification combination is
Enabled in the frozen registry snapshot and satisfies the admitted policy profile.

Admission is never permanent. Certification MUST have explicit scope, version, validity,
expiration, revocation, and compatibility boundaries. Security or integrity revocation SHALL
prevent new authoritative use immediately through a new governance epoch while preserving the
immutable snapshots and evidence needed to interpret historical runs.

## Purpose

Define who may request, approve, certify, activate, suspend, revoke, deprecate, retire, and migrate
an EPIP-017 producer or capability; define how trust is granted and removed; and define the
registry's authority, invariants, visibility, determinism, and audit obligations.

This ADR SHALL be the constitutional governance contract for all EPIP-017 producers and
capabilities. Operational convenience MUST NOT override it.

## Problem Statement

Producer registration without institutional governance creates an uncontrolled plugin ecosystem.
Discovery alone cannot establish authenticity, analytical authority, security posture,
compatibility, determinism, replay safety, or fitness for authoritative execution.

The original architecture did not establish:

- who owns a producer;
- who may request or approve its admission;
- who independently certifies producer claims;
- who grants or revokes trust;
- whether registration implies execution eligibility;
- how capability versions are admitted and replaced;
- whether certification expires or survives producer changes;
- how emergency suspension differs from permanent revocation;
- how registry state is reconstructed for replay;
- how governance actions remain deterministic and auditable;
- how legacy or experimental producers are prevented from entering authoritative runs;
- how conflicts of interest and privilege escalation are prohibited.

Without these rules, a producer could self-register, self-certify, become implicitly trusted, and
silently alter future plan resolution. Such a system cannot support institutional certification or
ten-year maintainability.

## Architectural Context

ADR-EPIP017-01 assigns distinct authority to the registry, semantic planner, execution ledger,
durable result store, replay boundary, audit authority, and EPIP-016 handoff. The registry is a
governance authority, not an execution plane.

ADR-EPIP017-02 establishes that:

- registration, certification, and enablement are separate decisions;
- a producer MUST have one owner and immutable identity;
- a producer MUST NOT self-register, self-certify, or change its lifecycle;
- producer and capability versions are independent;
- capability conformance MUST be proven for exact version and profile combinations;
- registration-only integration applies only to conforming producers using approved architectural
  classes.

This ADR governs those decisions. It does not redefine producer execution behavior, capability
semantics, dependency resolution, temporal semantics, or runtime scheduling.

## Definitions

### Governance Action

An immutable, attributable decision by an authorized governance role that proposes or changes
ownership, registration, certification, trust, lifecycle, compatibility, suspension, revocation,
replacement, migration, or retirement.

### Governance Manifest

The complete immutable set of signed governance actions, referenced evidence, policy versions,
authority identities, and effective logical epochs used to derive one registry snapshot.

### Governance Epoch

A monotonically ordered logical boundary at which an accepted governance action becomes eligible
for inclusion in new registry snapshots. Wall-clock observation order MUST NOT define governance
precedence.

### Registry Entry

The immutable association between one exact producer identity and version, one descriptor, one
owner, declared capabilities, trust standing, certification records, compatibility decisions,
lifecycle standing, and governance provenance.

### Registry Snapshot

An immutable, canonically ordered, content-identified view of all registry entries and governance
facts effective at one governance epoch. A semantic plan MUST reference exactly one registry
snapshot.

### Admission

The governed acceptance of a producer or capability declaration into the registry lineage.
Admission makes the declaration institutionally known. It does not grant certification, trust,
enablement, selection, or runtime execution.

### Activation

The Registry Authority's governed transition of an eligible certified producer version into
Enabled lifecycle state for specified capabilities and policy profiles.

### Suspension

A reversible governance action that prevents new authoritative selection while investigation,
remediation, recertification, or operational review occurs. Suspension SHALL map to Disabled
lifecycle standing without deleting history.

### Revocation

An authoritative withdrawal of trust, certification, compatibility, or admission eligibility for
future use. Revocation MUST preserve historical records and MUST identify its scope and reason.

### Trust Standing

The governed security and institutional confidence assigned to one exact producer version and
scope. Trust is not analytical confidence and MUST NOT appear as EPIP-016 Confidence.

### Certification Record

An immutable attestation by the sole institutional Certification Authority that a precise producer
and capability combination satisfied one versioned certification profile using identified
evidence.

### Compatibility Decision

An immutable, directional, scoped determination that one exact version combination may satisfy a
specified consumer or migration contract. Similar schemas or names do not constitute a
compatibility decision.

## Governance Model

EPIP-017 SHALL use a constitutional governance model with separation of request, evaluation,
certification, security approval, activation, operation, and audit.

Governance SHALL operate on immutable versioned facts. No governance authority MAY mutate a prior
action, registry entry, certification record, trust decision, compatibility decision, or registry
snapshot. Corrections and reversals MUST be new actions at a later governance epoch.

For production admission, the following decisions MUST all exist and remain valid:

1. A Producer Owner submits an admission request and accepts accountability.
2. The Architectural Authority confirms that the producer uses approved capability and execution
   classes or records the prerequisite architectural decision.
3. The Registry Authority validates identity, descriptor completeness, ownership, and governance
   prerequisites.
4. The Certification Authority independently certifies the exact producer and capability profile.
5. The Security Authority grants the required trust standing and privilege scope.
6. The Compatibility Authority approves every compatibility claim required by intended consumers.
7. The Registry Authority activates only the approved scope in a new registry snapshot.

No missing decision MAY be inferred from another decision. Operational readiness MAY further
restrict availability but MUST NOT grant semantic admission, certification, or trust.

## Admission Model

### Admission Request

Only the authoritative Producer Owner or an explicitly delegated Maintainer acting on behalf of
that owner MAY request admission. The request MUST identify:

- producer identity, owner, maintainer set, and producer version;
- producer contract version and implementation identity;
- every capability identity and version requested;
- configuration, input, output, context, temporal, failure, and diagnostic schemas;
- execution, resource, side-effect, isolation, determinism, and replay profiles;
- security classification, requested privileges, and external boundaries;
- compatibility claims, replacement claims, and migration intent;
- certification profile requested;
- deprecation or retirement relationships to existing entries;
- immutable evidence supporting every claim.

### Admission Approval

The Registry Authority SHALL approve or reject structural admission only after the Architectural
Authority confirms architectural conformity. Approval MUST be deterministic for the same complete
admission manifest, policy versions, and authority facts.

Admission approval MUST NOT imply certification, trust, activation, availability, or selection.

### Certification of Admission

The Certification Authority SHALL certify only the exact scope declared in the certification
record. Certification MUST be independent of the Producer Owner, Maintainer, Operational Owner,
and Registry Authority for that producer.

### Activation

Only the Registry Authority MAY activate a producer entry. Activation MUST require valid
certification, sufficient trust, approved compatibility, unexpired governance evidence, and no
active suspension or revocation.

Activation MUST identify the exact producer capabilities and policy profiles enabled. Admission
of one capability MUST NOT activate another capability exposed by the same producer.

### Suspension

The Security Authority SHALL have immediate authority to suspend new authoritative use for a
security, authenticity, integrity, or privilege concern. The Certification Authority SHALL have
authority to suspend the certification scope when certification evidence becomes unreliable. The
Operational Authority MAY request an operational suspension, but the Registry Authority MUST
record the resulting Disabled state.

Suspension MUST NOT terminate or mutate an active run implicitly. The disposition of already
planned or executing invocations MUST follow the frozen run policy and ADR-EPIP017-07,
ADR-EPIP017-13, and ADR-EPIP017-16. Emergency action MUST be explicit, attributable, and audited.

### Revocation

Trust revocation belongs to the Security Authority. Certification revocation belongs to the sole
Certification Authority. Compatibility revocation belongs to the Compatibility Authority.
Registry-entry revocation and lifecycle enforcement belong to the Registry Authority after the
authoritative scoped revocation fact exists.

No Producer Owner or Maintainer MAY revoke, erase, or rewrite institutional evidence. They MAY
request withdrawal, disablement, deprecation, or retirement.

### Permanence

Admission, certification, trust, activation, and compatibility MUST NOT be permanent. Every
governance grant MUST define its scope, governing policy version, effective epoch, review or expiry
condition, and revocation authority.

Historical admission facts remain permanent records even after future eligibility ends.

## Ownership Model

### Producer Owner

Every producer identity and version MUST have exactly one authoritative Producer Owner at any
governance epoch. The Producer Owner is accountable for analytical intent, descriptor accuracy,
versioning, maintained certification evidence, vulnerability response, deprecation planning, and
retirement obligations.

Joint, ambiguous, inherited, anonymous, or multiple authoritative ownership is prohibited.

### Maintainer

One or more Maintainers MAY perform delegated maintenance and submit governance requests. A
Maintainer MUST NOT become an authoritative owner through activity, repository access, authorship,
or operational control.

### Architectural Owner

The Architectural Authority owns the EPIP-017 constitutional contracts and determines whether a
new capability, trust, temporal, resource, execution, or extension class requires an ADR. It MUST
NOT certify a producer implementation or activate a registry entry.

### Operational Owner

The Operational Authority owns runtime readiness, capacity, availability, incident response, and
operational suspension requests. Operational readiness MUST NOT grant semantic trust,
certification, compatibility, or registration.

### Certification Owner

EPIP SHALL have exactly one institutional Certification Authority for EPIP-017. It owns
certification profiles, evidence requirements, verdicts, expiration, and certification revocation.
It MAY use independently identified reviewers or facilities, but delegated work MUST produce one
verdict under the single Certification Authority and MUST NOT create competing certification
authorities.

### Security Owner

The Security Authority owns trust policy, privilege classification, authenticity requirements,
security review, emergency suspension, and trust revocation. It MUST NOT alter analytical
capability semantics or certification evidence.

### Ownership Transfer

Ownership transfer MUST be a new governance action approved by the outgoing owner where available,
the incoming owner, the Registry Authority, and the Security Authority. It MUST trigger review of
trust, maintenance obligations, credentials, certification responsibility, and operational
contacts. It MUST NOT rewrite prior ownership history.

If no valid owner exists, the producer MUST be Disabled for new authoritative use until ownership
is re-established. Owner absence MUST NOT default to platform or registry ownership.

## Authority Model

### Administrative Authority

The Registry Authority SHALL be the sole administrative authority for registry admission,
activation, lifecycle recording, snapshot publication, disablement enforcement, and retirement
recording.

### Operational Authority

The Operational Authority SHALL determine runtime readiness and operational constraints. It MUST
NOT alter producer identity, capability semantics, certification, trust, compatibility, or frozen
registry snapshots.

### Certification Authority

The sole Certification Authority SHALL issue, expire, suspend, and revoke certification records.
It MUST NOT own the producer being certified, activate it, or modify its descriptor.

### Revocation Authority

Revocation authority SHALL be scoped:

- Security Authority for trust and privilege;
- Certification Authority for certification validity;
- Compatibility Authority for compatibility determinations;
- Registry Authority for administrative eligibility and lifecycle enforcement.

Where multiple scoped revocations apply, any single authoritative revocation sufficient to make a
required eligibility predicate false SHALL prevent new authoritative selection. No authority may
override another authority's valid revocation outside a new governed review by that same scope.

### Compatibility Authority

The Compatibility Authority SHALL issue directional, versioned compatibility decisions based on
approved evidence. It MUST NOT infer semantic compatibility from schema compatibility or producer
replacement claims.

### Audit Authority

The Audit Authority SHALL independently verify governance history, authority separation,
attestations, snapshot derivation, and policy compliance. It MUST NOT register, certify, trust,
activate, or revoke producers.

## Trust Model

Trust, certification, and administrative lifecycle SHALL remain independent axes.

### Trust Standings

- **Untrusted** — no institutional trust has been granted. The producer MUST NOT enter an
  authoritative plan.
- **Experimental** — limited trust permits isolated non-authoritative evaluation only. Outputs
  MUST NOT reach EPIP-016 or mix with authoritative evidence.
- **Trusted** — the Security Authority has approved the exact producer version, capability scope,
  privilege profile, and trust policy version for eligible authoritative use.
- **Revoked** — trust has been withdrawn. The exact revoked scope MUST NOT be used for new
  authoritative or experimental execution unless a new producer version or explicitly governed
  trust review creates a new admissible scope.

### Named Producer Classifications

- A **Trusted Producer** has Trusted standing but MAY still be uncertified, disabled, deprecated,
  incompatible, or operationally unavailable.
- A **Certified Producer** has a valid certification record but MAY still be untrusted, disabled,
  deprecated, or unavailable.
- An **Experimental Producer** has Experimental standing and MUST remain outside authoritative
  evidence and EPIP-016 handoff.
- A **Deprecated Producer** is in Deprecated administrative lifecycle state; it MAY remain trusted
  and certified for explicitly pinned compatibility use.
- A **Disabled Producer** is administratively barred from new selection regardless of trust or
  certification.
- A **Revoked Producer** has a revoked required trust, certification, compatibility, or admission
  scope and MUST fail the affected eligibility predicate.
- A **Legacy Producer** operates only through the governed legacy path and is not an EPIP-017
  producer unless separately admitted, certified, trusted, and enabled.
- An **Untrusted Producer** has Untrusted standing and MUST NOT enter authoritative execution.

These classifications MUST NOT be collapsed into one ambiguous status label.

### Trust Transitions

- Untrusted MAY transition to Experimental or Trusted only through Security Authority approval.
- Experimental MAY transition to Trusted only after required certification and security evidence
  exist; it MAY transition to Untrusted or Revoked.
- Trusted MAY transition to Untrusted through governed reassessment, or to Revoked for a scoped
  trust breach.
- Revoked SHALL be terminal for the revoked producer-version and trust scope. Restoration MUST
  require a new governed version or a new scope that does not rewrite the revocation.

Trust transition MUST create a new immutable governance action and registry snapshot. A producer
MUST NOT transition its own trust.

## Certification Model

### Prerequisites

Certification MUST require:

- a structurally Registered producer descriptor;
- verified producer ownership and authenticity;
- an accepted producer contract version;
- admitted capability versions;
- frozen schemas, configuration profiles, execution properties, and implementation identity;
- an approved determinism, replay, security, isolation, and resource profile;
- complete certification evidence from real execution where required by ADR-EPIP017-02;
- no unresolved architectural exception.

### Scope

Certification MUST bind the exact combination of producer identity and version, implementation
identity, producer contract version, capability identity and version, configuration profile,
input/output/context/diagnostic schemas, temporal profile, determinism profile, replay profile,
execution and isolation profile, privilege scope, certification profile, and certification-suite
version.

Certification of one scope MUST NOT imply certification of another.

### Certification Profile and Version

Every certification profile MUST be immutable and versioned. It MUST define required evidence,
test classes, repeat counts where applicable, environmental constraints, acceptance criteria,
failure criteria, expiry rules, and recertification triggers.

### Validity and Expiration

A certification record MUST state its effective governance epoch and an explicit expiration or
review condition. Certification MUST expire when its declared validity ends or when a bound
identity, version, policy, trust boundary, or certification prerequisite changes.

Expiration MUST prevent new eligibility after the effective expiration epoch. It MUST NOT erase
historical certification.

### Certification Revocation

The Certification Authority MUST revoke or suspend certification when evidence is false,
incomplete, corrupted, irreproducible, superseded by a critical contract change, or invalidated by
a discovered defect. Revocation MUST state scope, cause, effective epoch, affected compatibility,
and required remediation.

### Certification Compatibility

Certification evidence MAY be reused only when the certification profile explicitly proves that
the changed dimension is outside the certified semantic and operational scope. Reuse MUST be an
explicit Certification Authority decision. Similarity or unchanged source files MUST NOT imply
continued validity.

## Capability Governance

Capability identity and version admission MUST precede producer certification for that capability.

The Architectural Authority SHALL determine whether a proposed capability:

- conforms to an existing approved capability category;
- changes evidence semantics or dependency meaning;
- introduces a new temporal, resource, trust, side-effect, state, or execution class;
- requires a new or amended ADR;
- conflicts with EPIP-016 or another authoritative domain.

The Registry Authority SHALL register an admitted capability contract only after architectural
approval. Capability admission MUST NOT activate any producer.

Capability replacement and deprecation MUST:

- identify exact predecessor and successor versions;
- preserve historical identity;
- state compatibility direction and known semantic differences;
- prohibit implicit redirection of existing pipelines;
- define migration and retirement conditions;
- require independent certification for each producer implementation.

Capability authenticity MUST be established through attributable architectural approval and
content identity. Display names and producer claims are insufficient.

## Registry Governance

### Registry Responsibilities

The registry SHALL:

- maintain immutable producer, capability, ownership, trust, certification, compatibility,
  lifecycle, deprecation, replacement, suspension, revocation, and retirement records;
- validate governance prerequisites for each administrative transition;
- publish canonically ordered immutable registry snapshots;
- expose only governed views appropriate to each authority;
- preserve historical snapshots required for audit and replay;
- produce stable provenance and identity under ADR-EPIP017-09;
- prevent conflicting active ownership and duplicate identity claims;
- prevent ineligible entries from appearing as selectable in new snapshots.

### Registry Non-responsibilities

The registry MUST NOT:

- execute or instantiate a producer;
- schedule an invocation;
- resolve a runtime dependency;
- inspect or transform evidence outputs;
- determine retry, timeout, fallback, cache, recovery, or handoff behavior;
- expose mutable state to producers;
- serve as a producer service locator;
- change an active run's frozen snapshot;
- infer operational availability from process discovery;
- become an EPIP-016 evidence source.

### Registry Invariants

1. Every producer identity and version has exactly one owner at an epoch.
2. Every governance mutation is a new immutable action.
3. Every snapshot references one complete governance manifest.
4. Snapshot ordering and identity are canonical.
5. A snapshot is immutable after publication.
6. A run references exactly one registry snapshot.
7. Registration does not imply certification, trust, enablement, or availability.
8. Certification does not imply trust or enablement.
9. Trust does not imply certification or enablement.
10. Enablement requires all governed predicates but does not guarantee operational readiness.
11. Revocation never deletes historical facts.
12. Experimental and legacy entries never appear as eligible for authoritative planning.
13. Secrets and mutable runtime state never enter a registry snapshot.
14. Registry iteration order never affects semantic resolution.

### Registry Visibility

- Producers MAY receive only the stable snapshot identity explicitly granted by their invocation.
- The semantic planner MAY receive the immutable eligible-planning view required by the admitted
  policy.
- Governance authorities MAY receive role-scoped administrative views.
- Audit MAY receive complete immutable governance provenance subject to redaction policy.
- Operational systems MAY receive eligibility and operational-reference data but MUST NOT mutate
  governance state.
- Public or documentation views MUST exclude secrets, sensitive evidence, credentials, and
  unnecessary personal data.

### Registry Retirement

Retirement MUST remove an entry from future selectable views while retaining descriptor,
ownership, capability, certification, trust, compatibility, lifecycle, and audit history for the
required retention period. A retired entry MUST NOT be physically erased while any retained run,
result, replay record, checkpoint, audit, or release requires its interpretation.

## Lifecycle Governance

ADR-EPIP017-02 lifecycle states remain normative:

Declared, Registered, Certified, Enabled, Deprecated, Disabled, and Retired.

Lifecycle governance SHALL enforce these rules:

- only the Registry Authority MAY record a lifecycle transition;
- every transition MUST satisfy the legal transition table from ADR-EPIP017-02;
- certification status MUST be derived from valid Certification Authority records;
- Enabled MUST require Trusted standing and valid certification for the exact enabled scope;
- Deprecated MUST prohibit new implicit adoption;
- Disabled MUST prohibit new planning selection;
- Retired MUST remain terminal for the producer identity and version;
- operational availability SHALL remain a derived condition and MUST NOT rewrite lifecycle;
- Executing and Completed SHALL remain invocation states governed by ADR-EPIP017-07.

Lifecycle policy MUST NOT merge trust, certification, compatibility, and operational readiness into
one state.

## Compatibility Governance

The Compatibility Authority SHALL govern explicit compatibility decisions for producer contract,
capability, input schema, output schema, configuration, context, temporal semantics, determinism,
replay, execution, isolation, and handoff.

Every compatibility decision MUST be:

- directional;
- scoped to exact versions and profiles;
- supported by immutable evidence;
- attributable to one authority identity;
- effective at a defined governance epoch;
- versioned and reviewable;
- revocable without rewriting history.

Schema readability, matching field names, successful import, common capability category,
replacement declaration, or prior certification MUST NOT establish compatibility.

Unknown, ambiguous, expired, or revoked compatibility MUST fail closed for authoritative planning.

## Revocation Model

Revocation MUST identify:

- revocation authority and scope;
- affected producer, capability, certification, trust, compatibility, or admission identity;
- immutable reason code and evidence reference;
- effective governance epoch;
- whether emergency suspension preceded final revocation;
- impact on new plans, queued work, active runs, replay, historical interpretation, and handoff;
- remediation and recertification requirements where allowed.

New semantic plans produced from a snapshot effective after revocation MUST exclude the revoked
scope. Previously frozen runs MUST follow their recorded policy for continuation, cancellation, or
quarantine; they MUST NOT silently adopt a later registry snapshot.

A severe security or integrity revocation MAY require explicit cancellation or quarantine of active
work. That action MUST be issued through the execution and failure authorities and MUST be audited;
the registry itself MUST NOT execute cancellation.

Revocation MUST NOT delete producer identity, prior results, certification history, registry
snapshots, or audit evidence. Historical replay MUST expose the governance state that originally
applied and separately report any later revocation relevant to interpretation.

## Audit Model

Every governance action MUST be represented by an immutable audit fact containing:

- action identity and type;
- authority identity and role;
- subject identities and exact scope;
- prior and resulting governance standing;
- governing policy and contract versions;
- effective governance epoch;
- reason code;
- evidence references;
- approvals and required separation-of-duty attestations;
- resulting registry snapshot identity where applicable;
- supersession, suspension, expiry, or revocation relationships.

Auditable actions MUST include at minimum:

- admission request and decision;
- producer and capability registration;
- certification issuance, expiration, suspension, and revocation;
- trust grant, reassessment, suspension, and revocation;
- activation, deprecation, disablement, and retirement;
- compatibility approval and revocation;
- migration and legacy classification changes;
- ownership and maintainer transfer;
- privilege-scope changes;
- emergency governance actions;
- registry snapshot publication.

Audit facts MUST be append-only, canonically attributable, tamper-evident under the future digest
and audit ADRs, and retained sufficiently to interpret every retained run. The Audit Authority MUST
be independent of the action authority being audited.

## Security Model

### Least Privilege

Every authority, registry view, producer entry, capability, and execution profile MUST receive only
the minimum privileges required for its approved scope. Trust MUST be capability-specific and
profile-specific, not a blanket property of a producer name.

### Identity Verification

Producer Owner, Maintainer, governance authority, producer descriptor, producer implementation,
capability contract, certification record, and registry snapshot authenticity MUST be verifiable.
Unverified identity MUST fail closed.

### Producer Authenticity

The admitted implementation identity MUST match the certified implementation identity under
ADR-EPIP017-09. A matching version string, repository path, package name, or owner claim is
insufficient.

### Capability Authenticity

Only a capability contract admitted by the Architectural and Registry Authorities MAY be claimed.
A producer MUST NOT create or alter capability identity through self-description.

### Administrative Separation

For production activation, the Producer Owner, Certification Authority, Security Authority, and
Registry Authority MUST be distinct authority identities for the subject producer. No single
authority identity MAY request, certify, trust, and activate the same producer scope.

Emergency suspension MAY be performed by its scoped authority without prior approval, but MUST be
audited and reviewed after the action. Emergency power MUST NOT grant activation or expanded
privilege.

### Forbidden Privilege Escalation

Runtime state, operational health, successful execution, test success, ownership, repository
access, or prior trust MUST NOT increase privileges dynamically. Privilege expansion requires a
new governance action, security approval, certification impact assessment, and registry snapshot.

Registry records MUST NOT contain credentials or secret material. Governance evidence access MUST
follow retention and redaction rules established by the mandatory audit ADR.

## Determinism Impact

Governance SHALL NOT introduce runtime nondeterminism.

Human or institutional judgement MAY create an explicit governance action, but that judgement MUST
become an immutable input fact before registry derivation. Given the same governance manifest,
policy versions, authority facts, effective epoch, and canonicalization rules, registry admission,
eligibility, lifecycle derivation, and snapshot identity MUST be identical.

Governance timing, database row order, filesystem discovery, network arrival, reviewer order,
process identity, or registry enumeration order MUST NOT determine snapshot content or semantic
producer selection.

An active run MUST use its frozen registry snapshot. Later admission, certification, activation,
suspension, revocation, expiration, or retirement MUST NOT mutate that snapshot.

Certification procedures claiming deterministic verdicts MUST define identical evidence inputs,
profile versions, environmental constraints, and acceptance criteria. Discretionary exceptions
MUST be explicit governance facts and MUST NOT masquerade as deterministic certification results.

## Replay Impact

Every replay MUST identify the registry snapshot and governance epoch applicable to the original or
recomputed run.

Historical recomputation SHALL evaluate producer eligibility using the replay policy defined by
ADR-EPIP017-11. Operational reproduction SHALL preserve the original registry snapshot and
governance facts.

Later revocation MUST NOT rewrite historical registry state. Replay and audit MUST nevertheless be
able to report that an originally eligible producer was later revoked, expired, deprecated,
disabled, or retired.

Experimental, untrusted, or legacy outputs MUST NOT become authoritative during replay merely
because they are historically available. Replay MUST preserve the original authoritative path and
trust scope.

Registry snapshot retention and producer-artifact availability MUST be sufficient to interpret
retained replay records. The registry MUST NOT itself perform replay.

## Migration Rules

- Existing producers SHALL remain Legacy until independently admitted under this ADR.
- Legacy classification MUST NOT imply Untrusted, Experimental, Certified, Trusted, or Enabled
  EPIP-017 standing.
- A migration request MUST identify the legacy owner, authoritative legacy behavior, intended
  capabilities, compatibility claims, and rollback scope.
- Every migrated producer MUST pass the same admission, trust, certification, and activation gates
  as a new producer.
- Prior production use MUST NOT substitute for EPIP-017 certification.
- Shadow evaluation MUST use Experimental standing unless the producer is separately Trusted and
  Certified; shadow outputs MUST remain non-authoritative.
- Migration MUST NOT silently redirect existing pipelines.
- Ownership gaps, hidden dependencies, unknown implementation identity, or unavailable
  certification evidence MUST block admission.
- Legacy retirement MUST follow ADR-EPIP017-16 and MUST preserve historical interpretability.

## Backward Compatibility

This ADR changes no production behavior, public API, producer implementation, EPIP-016 contract,
Replay behavior, EventBus behavior, financial calculation, risk rule, portfolio behavior,
execution behavior, or serialization format.

Existing analytical producers MAY continue through the legacy path during the governed migration
window. EPIP-017 governance MUST NOT modify their legacy runtime authority implicitly.

Historical registry snapshots, producer identities, capability contracts, certification records,
trust decisions, ownership records, and compatibility decisions MUST remain interpretable after
new versions or policies are introduced.

A governance-policy change MUST create a new policy version and governance epoch. It MUST NOT
reinterpret prior admission or certification facts in place.

## Forbidden Behaviours

EPIP-017 governance MUST NEVER permit:

1. Producer self-registration.
2. Producer self-certification.
3. Producer self-activation, self-deprecation, self-disablement, self-revocation, or
   self-retirement.
4. Implicit admission through discovery, import, deployment, repository presence, or successful
   execution.
5. Implicit trust through ownership, authorship, certification, legacy use, or operational health.
6. Implicit certification through registration, tests, schema compatibility, or prior versions.
7. Implicit capability activation.
8. More than one authoritative Producer Owner for one producer identity and version at an epoch.
9. Competing institutional Certification Authorities.
10. One authority identity requesting, certifying, trusting, and activating the same production
    producer scope.
11. Runtime authority changes inside an active run.
12. Mutation of a frozen registry snapshot.
13. Dynamic privilege escalation.
14. Registration-order or discovery-order selection semantics.
15. Registry execution, scheduling, retry, cache, recovery, or evidence transformation.
16. Deletion or rewriting of historical governance actions.
17. Silent redirection to a replacement producer or capability.
18. Treating schema compatibility as semantic compatibility.
19. Treating Experimental, Legacy, Untrusted, Disabled, Deprecated, or Revoked standing as
    authoritative eligibility without the exact required governed exceptions.
20. Governance exceptions outside immutable, attributable, reviewed actions.

Any forbidden governance behavior SHALL constitute an institutional architecture and certification
failure. It MUST fail closed.

## Alternatives Considered

### Open plugin registration

Any discoverable producer registers and becomes available automatically.

Rejected because discovery cannot establish identity, ownership, semantic authority, trust,
certification, compatibility, or security.

### Owner-controlled admission and certification

The Producer Owner registers, certifies, and activates its own producer.

Rejected because it eliminates separation of duties and makes certification a self-attestation.

### One combined producer status

Trusted, certified, enabled, deprecated, disabled, and retired are represented by one state.

Rejected because trust, certification, lifecycle, compatibility, and operational readiness have
different authorities, transition rules, and historical meanings.

### Mutable central registry

The registry exposes current mutable state and active runs query it continuously.

Rejected because runtime governance changes would alter plan semantics and destroy deterministic
replay.

### Permanent certification and trust

Certification and trust remain valid for the producer identity indefinitely.

Rejected because implementation, dependencies, threats, contracts, and certification profiles
evolve independently.

### Multiple independent certification authorities

Different teams issue equally authoritative EPIP-017 certifications.

Rejected because conflicting verdicts would make eligibility ambiguous. EPIP uses one
institutional Certification Authority with independently attributable reviewers and evidence.

### Immutable governance actions and deterministic snapshots

Governance decisions become immutable facts; one authority-scoped model derives canonical
snapshots for planning.

Accepted because it preserves accountability, historical interpretation, deterministic planning,
and clear separation of duties.

## Decision

EPIP SHALL adopt the governance, admission, ownership, authority, trust, certification, capability,
registry, lifecycle, compatibility, revocation, audit, security, determinism, replay, migration,
and compatibility rules in this ADR as the constitutional governance model for EPIP-017.

No producer or capability SHALL become eligible for authoritative planning unless every required
governance predicate is explicitly satisfied in the exact frozen registry snapshot used by the
run.

No implementation MAY weaken these rules through default configuration, administrative override,
runtime discovery, operator convenience, or legacy precedent.

## Consequences

### Positive

- Producer admission becomes explicit, attributable, reproducible, and auditable.
- Ownership and separation of duties prevent self-certification and privilege concentration.
- Trust, certification, lifecycle, compatibility, and availability remain precise.
- Registry snapshots provide stable governance input for deterministic planning and replay.
- Security revocation can stop new authoritative use without destroying historical evidence.
- Experimental and legacy producers cannot contaminate authoritative EPIP-016 evidence.
- Capability replacement cannot silently change existing pipelines.
- Governance remains stable across deployment and storage changes.

### Negative

- Admission and activation require multiple independent authorities.
- Certification and trust require continued maintenance and periodic review.
- Emergency suspension and historical replay require careful scope reporting.
- Registry snapshots and governance evidence require durable retention.
- Small producer changes may require recertification or new compatibility decisions.
- Existing producers may remain Legacy for a significant period.

### Trade-offs

EPIP accepts slower admission and higher governance cost to prevent untrusted, ambiguous,
uncertified, or silently substituted producers from entering an institutional decision pipeline.

## Invariants

1. Every producer identity and version has exactly one authoritative Producer Owner at an epoch.
2. No producer self-registers, self-certifies, self-trusts, or self-activates.
3. EPIP has exactly one institutional Certification Authority for EPIP-017.
4. Production request, certification, trust, and activation use independent authority identities.
5. Registration, certification, trust, lifecycle, compatibility, and availability are distinct.
6. Admission never implies activation.
7. Certification never implies trust or activation.
8. Trust never implies certification or activation.
9. Enabled eligibility requires every exact governed predicate.
10. Experimental outputs never enter authoritative handoff.
11. Legacy status never implies EPIP-017 admission.
12. Every governance action is immutable, attributable, scoped, and audited.
13. Every registry snapshot is immutable, canonical, and bound to one governance epoch.
14. Every run references exactly one registry snapshot.
15. Later governance action never mutates an active run's snapshot.
16. The registry never executes or schedules producers.
17. The registry never becomes a producer service locator.
18. Unknown identity, trust, certification, compatibility, or ownership fails closed.
19. Revocation prevents new affected eligibility and preserves historical records.
20. Retirement preserves historical interpretability.
21. Capability replacement never silently redirects existing pipelines.
22. Runtime success never grants privilege or trust.
23. Governance state is reproducible from its immutable manifest.
24. Decision and EPIP-016 remain outside registry authority.

## Non-goals

This ADR does not define:

- implementation classes, APIs, storage engines, databases, files, services, or interfaces;
- producer execution behavior already governed by ADR-EPIP017-02;
- capability semantic resolution algorithms;
- dependency graphs or planning algorithms;
- temporal calendars, watermarks, or timeframe rules;
- semantic-plan or dispatch-plan representation;
- invocation state machines or result commitment;
- digest algorithms, signatures, or canonical formats;
- durable result stores or caches;
- replay execution algorithms;
- retry, fallback, or recovery algorithms;
- parallel execution or worker topology;
- EPIP-016 handoff representation;
- organizational names, individual appointments, or staffing decisions;
- trading, market analysis, Decision, Candidate, Confidence, risk, portfolio, execution, or
  financial logic.

These exclusions do not permit implementation teams to invent missing architecture.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 and ADR-EPIP017-02 and on the frozen EPIP-016 and
H001–H007 architecture.

It creates or confirms mandatory dependencies on:

- ADR-EPIP017-04 for evidence semantics, capability resolution, selection stability, and
  dependency compatibility;
- ADR-EPIP017-06 for the registry snapshot's role in semantic plans and dispatch plans;
- ADR-EPIP017-08 for deterministic certification profiles and allowed environmental variation;
- ADR-EPIP017-09 for governance-action, producer-implementation, registry-snapshot, signature, and
  digest identities;
- ADR-EPIP017-11 for historical governance state in replay modes;
- ADR-EPIP017-13 for the operational disposition of work affected by suspension or revocation;
- ADR-EPIP017-14 for isolation and privilege enforcement during concurrent execution;
- ADR-EPIP017-15 for trust and certification provenance at EPIP-016 handoff;
- ADR-EPIP017-16 for legacy migration, shadow governance, rollback, and retirement;
- ADR-EPIP017-17 for attestation, chain of custody, retention,
  redaction, and governance-event visibility;
- ADR-EPIP017-18 for operational readiness and
  resource admission without semantic privilege escalation.

This ADR makes one additional architectural requirement explicit: the future digest and audit ADRs
MUST define authenticity and tamper evidence for governance actions and registry snapshots. This
is a scope clarification, not a new implementation dependency.

## Future Evolution

Governance roles MAY be delegated, federated, or supported by additional review facilities only if
one final authority remains unambiguous for every scope and the separation-of-duty invariants are
preserved.

New producer categories, trust classes, certification profiles, privilege classes, or compatibility
dimensions MUST be introduced through versioned governance policy and, where architectural meaning
changes, a new or amended ADR.

Governance automation MAY evaluate immutable manifests and publish deterministic recommendations,
but it MUST NOT bypass required institutional authorities or convert operational success into
trust. A future automated authority requires an explicit ADR defining accountability, failure,
security, and appeal.

Historical governance records MUST remain interpretable across policy, authority, identity,
signature, canonicalization, and storage evolution.

## Approval Gate

Approval of this ADR resolves the EPIP-017 governance, admission, trust, certification, ownership,
revocation, and registry-authority blocker only.

It does not approve a registry implementation, producer, interface, planner, scheduler, adapter,
storage mechanism, or Programme A.

EPIP-017 implementation remains prohibited until the complete mandatory ADR set is accepted and
the remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
