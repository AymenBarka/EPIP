# ADR-EPIP017-02 — Producer Capability and Execution Contract

## Status

Approved and frozen.

ADR-EPIP017-01 is approved and normative. This ADR MUST NOT modify its system boundary,
orchestration authority, control-plane and execution-plane separation, producer isolation,
EPIP-016 boundary, or single-authoritative-path rule.

This ADR is architecture only. It authorizes no implementation, production code, interface,
placeholder, or Programme A activity.

## Executive Summary

An **Evidence Producer** is an admitted analytical authority that transforms an explicitly granted,
immutable input manifest into an immutable producer result under one or more certified capability
contracts. It owns only its declared analytical transformation. It does not own discovery,
dependency resolution, scheduling, retry, caching, replay control, result commitment, orchestration,
or decision formation.

Every producer MUST declare its identity, implementation version, contract version, capabilities,
configuration schema, context projection, dependency requirements, determinism profile, execution
properties, resource requirements, failure vocabulary, output schemas, trust classification, and
certification record before it can be enabled.

A producer MUST be isolated from undeclared inputs and mutable shared state. It MUST NOT call
another producer, discover dependencies at runtime, modify orchestration artifacts, use ambient
time or uncontrolled randomness, create a hidden cache, perform retries, or create Decision,
Candidate, Confidence, or execution instructions.

Producer lifecycle governance is distinct from invocation execution state. Registration,
certification, enablement, deprecation, disablement, and retirement describe the producer's
administrative status. Execution attempts are authorized and recorded by the execution plane under
ADR-EPIP017-07; a producer never transitions itself into an orchestration state.

This contract resolves CF-01 by making producer behavior explicit, bounded, certifiable, and
independent of implementation language or deployment topology.

## Purpose

Establish the single institutional contract governing every Evidence Producer admitted to
EPIP-017. The contract defines what a producer is, which authority it owns, which capabilities it
may expose, which inputs it may observe, which outputs it may produce, which state it may retain,
and which behaviors are prohibited.

The contract MUST remain sufficient to assess producer conformance without relying on production
code or informal implementation conventions.

## Problem Statement

The initial EPIP-017 architecture required stable producer identity, deterministic behavior,
replay compatibility, caching, retries, and parallel execution without defining the execution
semantics that make those guarantees credible.

In particular, it did not establish whether producers could:

- retain mutable state between invocations;
- access clocks, randomness, files, networks, environment variables, or global registries;
- invoke other producers or discover runtime dependencies;
- publish partial results before failure;
- execute retries internally;
- share instances concurrently;
- emit side effects;
- create multiple outputs atomically;
- distinguish valid empty output from failure;
- use a declared version that did not identify the actual analytical behavior.

Without a normative producer contract, the orchestrator cannot certify determinism, replay,
parallel equivalence, cache validity, failure isolation, or backward compatibility. Producer
declarations would be unverified claims rather than enforceable architectural obligations.

## Architectural Context

ADR-EPIP017-01 freezes the following authority model:

- EPIP-017 is the sole semantic orchestration authority for an admitted EPIP-017 run;
- the control plane owns semantic resolution and planning;
- the execution plane owns authorized operational coordination only;
- producers never discover, schedule, or invoke other producers;
- durable results, cache, replay, audit, and handoff remain separate authorities;
- EPIP-016 remains outside EPIP-017 and begins only after an evidence-set handoff is accepted;
- Decision is not an EPIP-017 producer or analytical graph node;
- exactly one execution path is authoritative for a run.

This ADR refines only the producer boundary. Registry admission and trust governance are completed
by ADR-EPIP017-03. Evidence semantics and dependency resolution are completed by
ADR-EPIP017-04. Invocation lifecycle and atomic result commitment are completed by
ADR-EPIP017-07. Determinism profiles are completed by ADR-EPIP017-08. Concurrency and parallel
equivalence are completed by ADR-EPIP017-14.

## Definitions

### Producer

A versioned analytical authority admitted by the EPIP-017 registry to perform one declared
transformation for an authorized invocation.

### Producer Descriptor

The immutable administrative declaration of producer identity, ownership, versions,
capabilities, execution properties, schemas, policies, trust classification, and certification
references.

### Capability

An immutable, versioned architectural contract describing one evidence-producing semantic service
that eligible producers may satisfy.

### Invocation

One execution-plane authorization to apply one producer version and one selected capability set to
one immutable input manifest. An invocation belongs to a run and semantic plan. It is not owned by
the producer.

### Input Manifest

The complete immutable inventory of every semantic input visible to an invocation, including
dependency results, context projection, timeframe boundary, configuration, registry snapshot
reference, plan reference, and replay boundary where applicable.

### Producer Result

The producer-authored immutable analytical outcome submitted for validation and atomic commitment.
Submission does not make the result authoritative; authority begins only after the result-commit
boundary accepts it under ADR-EPIP017-07.

### Semantic Diagnostic

A stable, deterministic producer-authored finding about input validity, analytical execution, or
output meaning. It is part of the producer result.

### Operational Telemetry

Measurements about runtime behavior, such as elapsed duration, queue delay, process identity, or
resource use. Operational telemetry is observed by the execution plane and MUST NOT affect
producer semantics, result identity, or producer-authored diagnostics.

### Side Effect

Any externally observable mutation other than submission of the producer result through the
authorized result boundary. This includes files, network writes, events, databases, caches,
registries, portfolios, orders, global state, and external services.

### Valid Empty Result

A successful, schema-valid outcome explicitly stating that no evidence exists for the authorized
input boundary. It is not absence, skip, timeout, cancellation, or failure.

## Producer Definition

A conforming Evidence Producer MUST:

- own exactly the analytical transformations declared by its certified capabilities;
- operate only after receiving an authorized invocation;
- consume only the immutable inputs listed in that invocation's input manifest;
- produce only declared evidence outputs, semantic metadata, and semantic diagnostics;
- expose no orchestration or decision authority;
- be independently identifiable, versioned, auditable, replaceable, and retireable;
- declare every required execution property before admission;
- satisfy the certification profile required by each enabled capability.

A producer is not:

- a scheduler;
- a dependency resolver;
- a registry;
- a cache or durable result store;
- a retry, fallback, or recovery coordinator;
- a replay controller;
- a decision, candidate, confidence, risk, portfolio, or execution engine;
- an audit authority;
- an owner of the orchestration run.

## Capability Definition

### Capability Identity

Every capability MUST have a globally stable identity independent of producer identity,
registration order, module path, display name, or runtime location.

Capability identity denotes semantic purpose, not implementation. Two producers MAY claim the same
capability only when registry governance certifies that both satisfy the same semantic contract.

### Capability Version

Every capability MUST have an immutable semantic version. A version MUST define:

- accepted input evidence semantics;
- produced evidence semantics;
- required and optional dependency roles;
- context fields and temporal semantics required;
- output completeness and valid-empty semantics;
- compatibility promises;
- certification obligations.

Changing any of those meanings MUST create a new capability version. Existing versions MUST NOT
be mutated in place.

### Capability Category

Every capability MUST belong to a governed category describing its architectural role. Categories
MUST be semantic and MUST NOT encode deployment, scheduling, or vendor details. Category creation
or modification requires registry-governance approval under ADR-EPIP017-03.

### Multiple Capabilities

A producer MAY expose one or more capabilities. Each capability MUST remain independently
identifiable and certifiable.

When one invocation produces outputs for multiple capabilities, the producer descriptor MUST
declare whether those outputs form one atomic semantic group. Undeclared atomic grouping is
prohibited. Atomic commitment semantics are governed by ADR-EPIP017-07.

### Capability Compatibility

Compatibility MUST be explicit, directional, versioned, and certified. Similar names, identical
schemas, common output types, or successful deserialization MUST NOT imply semantic compatibility.

An existing pipeline MUST NOT silently resolve to a newly registered producer merely because it
claims a compatible capability. Selection stability and certified selection profiles are governed
by ADR-EPIP017-04.

### Capability Evolution

Backward-compatible clarification MAY retain a capability version only when it changes neither
accepted inputs, produced meaning, completeness, temporal interpretation, nor certification
behavior. Every other evolution MUST create a new version.

### Capability Replacement

A replacement MUST declare which capability versions it replaces, the compatibility direction,
known semantic differences, migration conditions, and certification evidence. Replacement does
not automatically redirect existing pipelines.

### Capability Deprecation

Deprecation MUST preserve identity and historical interpretability. It MUST prohibit new implicit
adoption while allowing explicitly governed compatibility and replay use until retirement rules
are satisfied.

### Capability Certification

Capability certification MUST bind the capability version, producer version, producer contract
version, configuration schema, determinism profile, replay profile, execution profile, and
certification-suite version. Certification of one combination MUST NOT be generalized to another.

## Execution Contract

For every authorized invocation, a producer:

- MUST validate that the granted manifest matches its declared contract before analysis;
- MUST treat every granted input as immutable;
- MUST execute exactly the selected capability transformation;
- MUST produce one terminal producer result submission or one structured producer failure;
- MUST NOT publish a semantically usable partial output before terminal submission;
- MUST distinguish success, valid empty result, validation failure, execution failure, unsupported
  capability, invalid context, and dependency unavailability;
- MUST submit outputs as one declared atomic semantic group when atomic grouping applies;
- MUST cooperate with an execution-plane cancellation request according to its certified execution
  profile;
- MUST release producer-owned invocation resources when execution terminates;
- MUST NOT decide whether an invocation is retried, recovered, cached, skipped, or committed.

An invocation MUST freeze all semantic inputs for its lifetime. A retry, when authorized by the
execution plane, is a distinct attempt against the same frozen semantic inputs unless recovery
requires a new semantic plan. The producer MUST NOT mutate inputs between attempts.

The producer MUST NOT equate local return or output submission with authoritative completion.
Authoritative invocation completion and result commitment belong to ADR-EPIP017-07.

## Input Contract

The complete producer-visible input set MUST be represented by an immutable input manifest.

### Permitted Visibility

A producer MAY observe only:

- its producer and capability identities;
- its immutable certified configuration;
- the context projection explicitly declared for the selected capability;
- dependency results explicitly resolved in the semantic plan;
- the exact symbol, timeframe, temporal boundary, and data revision granted to the invocation;
- the logical clock or replay boundary explicitly granted by policy;
- bounded execution-control signals explicitly authorized by its execution profile.

### Registry Visibility

A producer MAY receive the stable identity of the registry snapshot that authorized it when needed
for provenance. It MUST NOT enumerate the registry, inspect other producer descriptors, query
available alternatives, or change selection based on registry contents.

### Dependency Visibility

A producer MUST see only resolved dependency results granted in its input manifest. It MUST NOT
discover, query, invoke, wait for, or substitute another producer. Missing required dependencies
MUST be reported before analytical execution. Optional dependencies MUST have explicit absence
semantics defined by the selected capability contract.

### Context Visibility

Context visibility MUST use the narrowest declared projection. A producer MUST NOT receive an
undifferentiated shared context. It MUST NOT infer authority from fields outside its declared
projection. Context decomposition is completed by the context architecture governed through
ADR-EPIP017-05 and ADR-EPIP017-06 dependencies.

### Configuration Visibility

Configuration MUST be immutable, schema-versioned, canonicalizable, and included in producer
identity and certification rules as required by ADR-EPIP017-09. Ambient configuration is
prohibited.

### Prohibited Access

Unless a future capability class is separately approved by ADR, a producer MUST NOT access:

- mutable global or shared state;
- the live registry or planner;
- the dependency graph beyond its granted dependency references;
- the mutable execution ledger;
- caches or durable result stores directly;
- system time or an ambient clock;
- uncontrolled randomness or entropy;
- environment variables as semantic inputs;
- files, databases, networks, external services, or EventBus as undeclared semantic inputs;
- portfolio, risk, execution, account, credential, or decision state not explicitly granted by an
  approved capability contract.

Any authorized external read capability MUST be explicitly modeled as a trust, input, temporal,
and replay boundary in later ADRs. It MUST NOT be introduced as an implementation convenience.

## Output Contract

A producer result MAY contain only:

- evidence outputs conforming to declared evidence schemas and capability semantics;
- immutable provenance metadata;
- explicit completeness and valid-empty declarations;
- deterministic semantic diagnostics;
- deterministic semantic statistics declared by the capability;
- deterministic producer trace facts required to explain the analytical transformation;
- references to the exact input manifest, producer, capability, configuration, and schema versions.

Producer-authored metrics or trace facts that participate in the result MUST be semantic,
canonical, and deterministic. Runtime duration, machine identity, memory consumption, scheduling
order, thread identity, and similar operational observations MUST be generated outside the
producer result by the execution plane.

A producer result MUST NOT contain or create:

- a Decision;
- a Candidate;
- a Confidence assessment owned by EPIP-016;
- a recommendation or execution instruction;
- a mutation of the semantic plan, dispatch plan, dependency graph, context, registry, cache,
  durable result store, execution ledger, or upstream result;
- an undeclared evidence type;
- a hidden downstream invocation request.

Output submission MUST NOT directly publish to EPIP-016. Only the governed handoff authority from
ADR-EPIP017-15 may deliver committed evidence.

## Failure Contract

A producer MUST report failures through a stable, versioned producer-failure vocabulary. It MUST
preserve the root cause category without claiming scheduler or infrastructure authority.

At minimum, producer-visible outcomes MUST distinguish:

- input validation failure;
- unsupported producer contract or capability version;
- invalid configuration;
- invalid context projection;
- dependency unavailable;
- dependency semantically invalid;
- unsupported timeframe or temporal boundary;
- analytical execution failure;
- deterministic contract violation detected by the producer;
- cooperative cancellation observed by the producer.

A timeout is classified by the execution authority because a producer MUST NOT read ambient time
or decide that its own execution exceeded an operational limit. If the execution plane declares a
timeout, any later producer submission MUST NOT become authoritative without the fencing and
commit rules of ADR-EPIP017-07.

A producer MUST emit deterministic semantic diagnostics for every producer-detectable failure. It
MUST NOT:

- retry automatically;
- select a fallback producer;
- degrade a required dependency unless the capability contract explicitly defines the resulting
  semantic outcome;
- convert failure into a valid empty result;
- publish partial evidence as successful evidence;
- suppress a contract violation;
- decide pipeline fail-fast or fail-safe behavior.

Failure propagation, retry eligibility, fallback, recovery, and pipeline disposition belong to
ADR-EPIP017-13.

## Dependency Contract

Every semantic dependency MUST be declared by capability version before registration and resolved
before invocation.

A producer:

- MUST consume dependencies only by stable references granted in the input manifest;
- MUST validate required dependency presence and declared compatibility;
- MUST preserve dependency provenance in its result;
- MUST apply only the absence semantics defined for optional dependencies;
- MUST NOT perform runtime discovery;
- MUST NOT invoke another producer;
- MUST NOT recursively execute a producer;
- MUST NOT add, remove, replace, or reorder graph dependencies;
- MUST NOT read a hidden dependency through shared state, ambient services, or global caches;
- MUST NOT make output semantics depend on the availability of an undeclared producer.

Conditional or alternative dependencies require explicit architecture under ADR-EPIP017-04. They
MUST NOT be invented during producer execution.

## Context Contract

The producer context MUST be an immutable, capability-specific projection. It MUST identify its
schema version and source authority. It MUST contain only fields declared by the selected
capability.

A producer MUST NOT:

- mutate context;
- retain a mutable reference to context after invocation;
- add context fields;
- treat producer-generated evidence as ambient context;
- use context as a service locator;
- discover dependencies, stores, producers, or orchestration services through context;
- access undeclared portfolio, risk, execution, or decision information.

Any context field that represents an analytical result MUST instead be modeled as an evidence
dependency unless a later ADR explicitly certifies it as an authoritative external input.

## Replay Contract

A producer MUST NOT control replay. It MAY participate only under a declared replay profile.

For replay-eligible execution, a producer:

- MUST consume only the replay boundary and historical inputs granted in its manifest;
- MUST NOT access future data or live mutable state;
- MUST NOT use ambient current time;
- MUST NOT reuse hidden cache state;
- MUST produce the same semantic result, metadata, diagnostics, trace facts, and digest when the
  determinism profile requires identical output for identical complete inputs;
- MUST preserve explicit valid-empty and failure semantics;
- MUST declare any external input class that prevents historical recomputation.

Historical recomputation and operational execution reproduction remain distinct replay modes under
ADR-EPIP017-11. Certification in one replay mode MUST NOT imply certification in the other.

## Certification Contract

No producer MAY enter Enabled state without certification for every enabled combination of:

- producer identity and version;
- producer contract version;
- capability identity and version;
- configuration schema and certified configuration profile;
- input and output schema versions;
- determinism profile;
- replay profile;
- execution and isolation profile;
- supported timeframe and context profile;
- certification-suite version.

Certification MUST test real analytical execution. Declaration inspection alone is insufficient.
Certification evidence MUST be immutable, attributable, reproducible where the profile requires,
and governed by ADR-EPIP017-03.

Certification MUST NOT be inferred from registration, successful import, schema compatibility,
unit-test presence, prior producer versions, or another producer implementing the same capability.

## Registration Contract

Registration is an administrative act performed by the registry authority, never by the producer
during execution.

A producer descriptor submitted for registration MUST declare:

- producer identity, owner, version, and contract version;
- implementation or build identity as governed by ADR-EPIP017-09;
- capability identities and versions;
- configuration schema and compatibility;
- input, output, diagnostic, and failure schemas;
- context and dependency declarations;
- timeframe and temporal requirements;
- execution, resource, isolation, cancellation, and concurrency properties;
- statefulness, side-effect, idempotency, determinism, and replay classifications;
- security and trust classification;
- certification requirements and evidence references;
- deprecation, replacement, and retirement metadata where applicable.

Registration makes a producer known. It MUST NOT make it certified, enabled, selected, or
authoritative. Admission, duplicate handling, signatures, trust, approval, and registry snapshots
belong to ADR-EPIP017-03.

## Versioning Contract

Four independent versions are mandatory.

### Producer Version

Identifies one analytical behavior and implementation lineage. Any change capable of altering
semantic output, diagnostics, dependency use, failure classification, state behavior, or resource
behavior MUST create a new producer version and require recertification.

### Capability Version

Identifies one immutable semantic service contract. It evolves independently of producer version.

### Producer Contract Version

Identifies the EPIP-017 producer-execution contract under which the descriptor and execution are
interpreted. A producer MUST declare exactly one supported contract version per certified
registration entry.

### Certification Version

Identifies the certification profile and suite used to establish conformance. Certification
evidence MUST state every version and profile it covers.

Version strings alone MUST NOT establish executable identity. The digest hierarchy and build
identity are governed by ADR-EPIP017-09.

## Compatibility Contract

Compatibility MUST be declared separately for:

- producer contract interpretation;
- capability semantics;
- input schema;
- output schema;
- configuration schema;
- context projection;
- temporal semantics;
- determinism profile;
- replay profile;
- execution and isolation profile.

Compatibility MUST be directional. A compatible serialization format MUST NOT imply compatible
analytical meaning. A compatible capability MUST NOT imply identical producer outputs. A new
producer registration MUST NOT redirect an existing pipeline without a compatible, approved
selection policy.

Any compatibility claim MUST be certified for the exact version combination. Unknown
compatibility MUST fail closed for institutional execution.

## Lifecycle

Producer administrative lifecycle and invocation execution lifecycle MUST remain separate.

### Administrative States

- **Declared** — a descriptor exists but has not been admitted to a registry.
- **Registered** — the descriptor has passed structural admission and is present in a governed
  registry lineage.
- **Certified** — the exact declared version and profile combination has valid certification
  evidence.
- **Enabled** — governance permits selection for new authoritative plans.
- **Deprecated** — existing pinned use may continue under policy, but new implicit adoption is
  prohibited.
- **Disabled** — selection and new execution are prohibited; historical interpretation remains.
- **Retired** — production selection is permanently prohibited; records remain resolvable for
  audit and replay according to retention policy.

**Available** is a derived eligibility condition, not a persistent lifecycle state. A producer is
available for a request only when it is Enabled, certified for the requested profiles, compatible,
trusted, and operationally admissible. Operational availability MUST NOT mutate administrative
identity.

**Executing** and **Completed** are invocation states, not producer administrative states. Their
authoritative state machine belongs to ADR-EPIP017-07.

## Producer State Machine

The following administrative transitions are legal:

- Declared SHALL transition only to Registered or remain Declared.
- Registered SHALL transition to Certified, Disabled, or remain Registered.
- Certified SHALL transition to Enabled, Disabled, or require recertification.
- Enabled SHALL transition to Deprecated or Disabled.
- Deprecated MAY transition to Enabled only through explicit recertification and governance
  approval; otherwise it SHALL transition to Disabled or Retired.
- Disabled MAY transition to Registered or Certified only through explicit remediation,
  revalidation, and governance approval; it MAY transition to Retired.
- Retired SHALL be terminal for that producer identity and version.

No producer may transition itself. Every transition MUST be authorized, recorded, attributable,
and reflected in a new immutable registry snapshot where registry eligibility changes.

Certification expiry, revocation, trust revocation, or contract incompatibility MUST remove
availability immediately under registry policy without rewriting historical lifecycle records.

## Authority Rules

1. The producer SHALL be authoritative only for the analytical meaning of its declared output
   before result commitment.
2. The registry SHALL remain authoritative for admission and administrative lifecycle.
3. The control plane SHALL remain authoritative for capability selection and semantic planning.
4. The execution plane SHALL remain authoritative for dispatch, timeout classification,
   cancellation coordination, and attempt recording.
5. The result-commit authority SHALL remain authoritative for accepted durable results.
6. The replay authority SHALL remain authoritative for replay boundaries.
7. The handoff authority SHALL remain authoritative for EPIP-016 evidence-set eligibility.
8. The audit authority SHALL evaluate conformance and SHALL NOT rewrite producer or execution
   facts.
9. A producer MUST NOT assume or delegate any authority not explicitly granted here.

## Ownership Rules

- The producer owner MUST be institutionally identifiable.
- The producer owner SHALL own analytical correctness, declared schemas, configuration semantics,
  resource declarations, failure vocabulary, and certification maintenance.
- The producer SHALL own invocation-local resources only for the duration authorized by the
  execution profile.
- Mutable producer instance state MUST NOT cross invocation boundaries.
- Persistent analytical state MUST be modeled as an explicit immutable input or authoritative
  dependency, never hidden inside a producer instance.
- The producer MUST NOT own upstream results, context, registry records, plans, graphs, caches,
  checkpoints, ledgers, or downstream committed evidence.
- Resource ownership transfer MUST be explicit and governed by H005; implicit transfer is
  prohibited.

## Determinism Rules

Under an output-deterministic producer profile, the same complete input manifest—including the
same producer version, capability version, contract version, configuration, context projection,
registry snapshot reference, semantic plan reference, dependencies, temporal boundary, replay
boundary, and authorized logical clock—MUST produce:

- the same evidence outputs;
- the same semantic metadata;
- the same semantic diagnostics;
- the same semantic trace facts;
- the same valid-empty or failure classification;
- the same canonical representation;
- the same producer-result digest.

Operational telemetry is excluded because it is not producer-authored semantic output.

A producer MUST NOT use:

- ambient system time;
- uncontrolled randomness;
- random identifiers;
- hash, set, memory, discovery, registration, thread, or completion order as semantic order;
- mutable global state;
- undeclared external state;
- floating-point behavior outside its certified numeric profile.

Exact determinism levels, environmental manifests, numeric policies, and divergence tolerances are
governed by ADR-EPIP017-08.

## Immutability Rules

- Producer descriptors and capability versions MUST be immutable.
- Input manifests and every referenced semantic input MUST be immutable for an invocation.
- Producer results, evidence outputs, semantic metadata, diagnostics, and trace facts MUST be
  immutable after submission.
- A producer MUST NOT mutate upstream results, context, configuration, plans, graphs, registry
  snapshots, or execution records.
- Any semantic change MUST create a new artifact and identity.
- Mutable invocation-local working state MAY exist conceptually only within the producer's isolated
  execution ownership and MUST NOT escape, be shared, or become authoritative.

## Replay Rules

- Replay eligibility MUST be declared per producer, capability, and profile combination.
- Replay execution MUST use the exact authorized historical or recorded input boundary.
- Live mutable data MUST NOT enter replay execution.
- Hidden producer caches and retained mutable state MUST NOT influence replay.
- A producer MUST NOT decide replay time, progression, failure reproduction, or cache reuse.
- Historical recomputation and operational reproduction MUST remain distinct.
- A replay-ineligible producer MUST cause planning or handoff rejection when the pipeline requires
  replay certification.
- Replay conformance MUST be recertified when producer behavior, capability semantics, temporal
  semantics, or determinism profile changes.

## Audit Rules

Every producer participation record MUST be attributable to:

- producer identity and owner;
- producer, capability, contract, configuration, schema, and certification versions;
- implementation or build identity;
- registry snapshot and semantic plan;
- input manifest and dependency-result identities;
- invocation and attempt identities;
- submitted result or failure identity;
- lifecycle and trust state applicable at plan admission;
- deterministic diagnostics and relevant operational observations.

The producer MAY supply deterministic audit facts defined by its capability, but MUST NOT certify
itself, alter the execution ledger, or issue the institutional audit verdict.

## Diagnostics Rules

- Producer diagnostics MUST use stable, versioned diagnostic codes.
- Diagnostics MUST distinguish validation, dependency, context, capability, analytical, and
  contract failures.
- Diagnostics MUST be deterministic when derived from identical complete inputs.
- Diagnostics MUST reference the affected input or output without exposing unauthorized data.
- Diagnostics MUST NOT replace structured failure state.
- Diagnostics MUST NOT contain fabricated remediation, retry, fallback, or orchestration decisions.
- Human-readable messages MAY accompany stable codes but MUST NOT carry unique semantic meaning.
- Diagnostic schema evolution MUST preserve historical interpretability.

## Observability Rules

- Producer-authored semantic trace facts MUST be separated from execution-plane operational
  telemetry.
- The producer MUST NOT emit directly to unapproved metrics, trace, event, or logging sinks.
- Observability failure MUST NOT change analytical output.
- Operational telemetry MUST NOT enter producer-result identity.
- Sampling MUST NOT apply to authoritative producer result, failure, or audit facts.
- Retention, audience, redaction, and exporter rules are governed by ADR-EPIP017-17 as mandated by
  ADR-EPIP017-01.

## Security Rules

- Every producer MUST have an owner, trust classification, and approved capability scope.
- Inputs MUST be least-privilege projections.
- Credentials MUST NOT be semantic inputs or producer outputs.
- A producer MUST NOT discover or elevate permissions during execution.
- A producer MUST NOT access undeclared network, filesystem, process, environment, registry,
  EventBus, cache, result-store, portfolio, risk, execution, or decision resources.
- Producer outputs and diagnostics MUST be validated and treated according to their trust boundary
  before commitment.
- Secret, personal, portfolio-sensitive, and operationally sensitive information MUST NOT leak
  through diagnostics, metrics, trace facts, metadata, or digests.
- Trust revocation MUST prevent new availability without rewriting historical evidence.
- Detailed admission, signing, isolation, authorization, and revocation governance belongs to
  ADR-EPIP017-03.

## Certification Rules

A producer certification profile MUST verify at least:

1. Descriptor completeness and version consistency.
2. Capability semantic conformance.
3. Input-visibility and least-privilege conformance.
4. Absence of producer-to-producer invocation and runtime dependency discovery.
5. Output-schema, provenance, completeness, and valid-empty conformance.
6. Failure classification and deterministic diagnostic conformance.
7. No producer-owned retry, fallback, cache, or orchestration behavior.
8. No Decision, Candidate, Confidence, execution instruction, or graph mutation output.
9. Immutability and invocation-state isolation.
10. Side-effect classification and enforcement.
11. Idempotency behavior declared by the profile.
12. Determinism profile conformance across repeated real executions.
13. Replay profile conformance where claimed.
14. Cancellation and resource-release conformance.
15. Security, trust, and unauthorized-access conformance.
16. Compatibility claims for every enabled version combination.
17. Multi-capability atomic-group conformance where declared.
18. Retirement and historical interpretability obligations.

Certification MUST fail closed on unknown behavior. Successful certification MUST NOT authorize
enablement; registry governance remains a separate decision.

## Migration Rules

Existing analytical engines MUST integrate through producer adapters or equivalent architectural
boundaries that conform to this ADR without moving orchestration responsibilities into the
analytical domains.

Migration MUST:

- inventory every existing producer's inputs, outputs, state, side effects, clocks, randomness,
  external access, retries, caches, and failure behavior;
- classify nonconforming behavior before registration;
- prohibit certification until hidden dependencies and mutable shared state are eliminated or
  explicitly externalized through approved contracts;
- preserve the existing analytical public API unless a separate compatibility decision approves a
  change;
- use shadow execution only under ADR-EPIP017-16;
- prevent shadow producer outputs from entering authoritative EPIP-016 evidence;
- define producer-specific rollback and retirement criteria;
- retain historical producer identity and certification records.

An adapter MUST NOT conceal prohibited behavior. Wrapping a nonconforming producer does not make
it conforming unless the adapter provides an approved isolation boundary and the complete behavior
is certified.

## Backward Compatibility

This ADR changes no production module, public API, evidence schema, Decision Framework behavior,
replay behavior, EventBus behavior, financial calculation, risk behavior, portfolio behavior,
execution behavior, or serialization format.

Existing producers MAY continue through the legacy authoritative path during the governed
migration window. They MUST NOT be described as EPIP-017 producers until registered, certified,
and enabled under this contract.

Registration of a new producer or producer version MUST NOT silently change an existing pipeline's
selection. Historical runs MUST remain interpretable using their original producer, capability,
contract, configuration, and certification identities.

## Forbidden Behaviours

An Evidence Producer MUST NEVER:

1. Call, schedule, discover, or recursively execute another producer.
2. Create a Decision.
3. Create a Candidate.
4. Create or assign Confidence owned by EPIP-016.
5. Create an execution order, portfolio mutation, risk decision, or financial action.
6. Change the producer registry or its lifecycle state.
7. Change the semantic plan or dispatch authorization.
8. Modify context or retain a mutable context reference.
9. Change the dependency graph or dependency selection.
10. Use uncontrolled randomness or random business identifiers.
11. Use ambient current time or an undeclared clock.
12. Use mutable global or cross-invocation state.
13. Create or consult a hidden cache.
14. Perform retries, fallback selection, or recovery coordination.
15. Publish directly to EPIP-016, EventBus, execution, risk, portfolio, or external systems.
16. Read undeclared files, networks, databases, environment variables, credentials, or services.
17. Mutate an input, upstream result, registry snapshot, graph, plan, ledger, cache, checkpoint, or
    committed result.
18. Emit semantically usable partial evidence before atomic result submission.
19. Convert failure, timeout, cancellation, or missing dependency into valid empty evidence.
20. Change orchestration authority or claim authoritative completion.
21. Depend on runtime discovery, thread order, completion order, memory identity, or container
    iteration order for semantic output.
22. Self-certify, self-enable, self-deprecate, self-disable, or self-retire.

Violation of any prohibition is a producer contract failure and an institutional certification
failure. It MUST NOT be silently degraded.

## Non-goals

This ADR does not define:

- implementation classes, interfaces, protocols, methods, or language bindings;
- producer discovery mechanisms;
- registry storage, signatures, voting, or approval workflow;
- capability-selection algorithms;
- evidence dependency graph algorithms;
- temporal calendars, watermarks, or cross-timeframe aggregation;
- semantic-plan or dispatch-plan representation;
- invocation state storage, leases, fencing, or atomic commit implementation;
- digest algorithms or canonical serialization format;
- durable result-store or cache architecture;
- replay-controller implementation;
- snapshot or checkpoint representation;
- retry scheduling, backoff, fallback, or recovery algorithms;
- parallel worker topology;
- EPIP-016 handoff representation;
- trading, market analysis, Decision, Candidate, Confidence, risk, portfolio, execution, or
  financial logic.

These matters MUST be decided by their mandatory ADRs and MUST NOT be inferred by implementation.

## Alternatives Considered

### Trust producer declarations without enforcement

Rejected. Self-declared determinism, idempotency, or replay safety provides no institutional
assurance.

### Permit stateful reusable producer instances

Rejected as the default contract. Cross-invocation mutable state creates hidden inputs,
concurrency hazards, cache ambiguity, and replay divergence. Any future stateful capability would
require an explicit new ADR and authoritative state dependency.

### Allow producers to invoke dependencies directly

Rejected. It violates ADR-EPIP017-01, hides the graph, bypasses planning, and prevents complete
audit and deterministic replay.

### Allow producers to perform their own retries and caching

Rejected. Retry and cache behavior would become hidden semantic inputs and would evade centralized
failure, lineage, replay, and audit rules.

### Allow arbitrary side-effecting producers

Rejected. Side effects cannot be rolled back through evidence snapshots, can be duplicated by
retry, and contaminate deterministic analytical execution. The institutional producer contract is
side-effect-free except for authorized result submission.

### Use one version for producer, capability, contract, and certification

Rejected. These concepts evolve independently and collapsing them makes historical interpretation
and compatibility claims unverifiable.

### Separate capability semantics from producer execution behavior

Accepted. A stable capability may have multiple certified producers, and a producer may expose
multiple capabilities without conflating semantic contracts with implementation lineage.

## Decision

EPIP SHALL adopt the producer, capability, input, output, dependency, context, failure, lifecycle,
authority, ownership, determinism, immutability, replay, audit, diagnostics, observability,
security, certification, migration, compatibility, and prohibition rules in this ADR as the sole
institutional Evidence Producer contract for EPIP-017.

Only a producer that is Registered, Certified, Enabled, compatible with the admitted request, and
available under the frozen registry and policy snapshots MAY be selected for a new authoritative
semantic plan.

Conformance MUST be demonstrated through certification. Naming an existing analytical engine an
Evidence Producer, wrapping it in an adapter, or registering a descriptor SHALL NOT establish
conformance.

## Consequences

### Positive

- Producer behavior becomes bounded and auditable.
- Hidden dependencies, state, retries, caches, and orchestration are prohibited.
- Determinism and replay claims become profile-specific and certifiable.
- Capability semantics evolve independently from producer implementations.
- Multi-producer substitution cannot occur merely through registration.
- Parallel and incremental execution can later rely on explicit state and side-effect rules.
- EPIP-016 remains isolated from producer lifecycle and execution concerns.

### Negative

- Existing analytical engines may require significant remediation before certification.
- Producers cannot use convenient ambient services or local caches.
- Every semantic or behavioral change requires explicit version and certification analysis.
- Registration and enablement require more governance than plugin discovery.
- Some producers may remain legacy-only if their hidden state or external dependencies cannot be
  certified.

### Trade-offs

EPIP accepts stricter producer constraints and higher certification cost in exchange for credible
determinism, replay, failure isolation, concurrency safety, and ten-year maintainability.

## Invariants

1. A producer owns analytical transformation only.
2. A producer executes only an authorized invocation.
3. Every semantic input is listed in an immutable input manifest.
4. No mutable state crosses invocation boundaries.
5. No producer invokes or discovers another producer.
6. Every dependency is explicit and pre-resolved.
7. Every context field is explicitly projected.
8. Every capability is immutable and versioned.
9. Producer version and capability version remain independent.
10. Registration, certification, and enablement remain separate decisions.
11. A producer never retries, recovers, caches, schedules, or commits its own result.
12. A producer result contains no Decision, Candidate, EPIP-016 Confidence, or execution action.
13. Valid empty output remains distinct from failure and missing output.
14. Producer-authored semantic diagnostics are deterministic under the applicable profile.
15. Operational telemetry cannot change producer semantics or result identity.
16. Ambient time, uncontrolled randomness, and hidden external state are prohibited.
17. Output submission is not authoritative result commitment.
18. Timeout classification belongs to the execution authority.
19. Lifecycle transitions are governed and immutable in history.
20. Retired producer versions remain historically interpretable.
21. Compatibility is explicit, directional, multidimensional, and certified.
22. Unknown compatibility fails closed.
23. Shadow results never enter the authoritative path.
24. Producer contract violations are never silently degraded.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 and the frozen EPIP-016 and H001–H007
architecture.

It creates or confirms mandatory dependencies on:

- ADR-EPIP017-03 for registry admission, trust, certification governance, revocation, and
  lifecycle authority;
- ADR-EPIP017-04 for capability semantics, dependency resolution, selection stability, and
  optional dependency rules;
- ADR-EPIP017-05 for temporal boundaries, calendars, availability, and timeframe semantics;
- ADR-EPIP017-06 for input manifests and semantic-plan versus dispatch-plan separation;
- ADR-EPIP017-07 for invocation states, attempts, cancellation fencing, and atomic result commit;
- ADR-EPIP017-08 for determinism profiles, environmental manifests, numeric behavior, and allowed
  nondeterminism;
- ADR-EPIP017-09 for producer implementation identity, canonicalization, and digest hierarchy;
- ADR-EPIP017-10 for durable result storage, cache isolation, and invalidation;
- ADR-EPIP017-11 for historical recomputation and operational reproduction;
- ADR-EPIP017-13 for failure propagation, retry eligibility, fallback, and recovery;
- ADR-EPIP017-14 for execution isolation, reentrancy, concurrency, and parallel equivalence;
- ADR-EPIP017-15 for output provenance, evidence completeness, and EPIP-016 handoff;
- ADR-EPIP017-16 for legacy migration, shadow comparison, rollback, and retirement;
- ADR-EPIP017-17 for telemetry, trace, retention, redaction, and
  diagnostic governance;
- ADR-EPIP017-18 for resource profiles, admission
  budgets, graph limits, and operational availability.

No new architectural dependency beyond those mandated by the institutional review has appeared.
This ADR clarifies their required scope.

## Future Evolution

Future capability categories MAY permit explicitly governed external reads, streaming inputs,
stateful analytical services, accelerators, or additional isolation profiles only through new or
amended ADRs. Such evolution MUST make state and external effects explicit, preserve one
orchestration authority, and define new determinism, replay, security, compatibility, and
certification rules.

A future producer contract version MAY add obligations but MUST NOT reinterpret historical
producer descriptors or certification evidence. Migration between producer contract versions MUST
be explicit and recertified.

Registration-only integration remains valid only for producers conforming to existing approved
capability, temporal, trust, resource, execution, and determinism classes. A producer requiring a
new class MUST undergo architecture review before registration.

## Approval Gate

Approval of this ADR resolves the producer-execution-contract blocker only. It does not approve a
registry, planner, scheduler, producer adapter, interface, implementation, or Programme A.

EPIP-017 implementation remains prohibited until the full mandatory ADR set is accepted and the
remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
