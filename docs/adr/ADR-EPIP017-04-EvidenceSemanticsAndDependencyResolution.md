# ADR-EPIP017-04 — Evidence Semantics and Dependency Resolution

## Status

Approved and frozen.

ADR-EPIP017-01, ADR-EPIP017-02, and ADR-EPIP017-03 are approved, frozen, and normative. This ADR
MUST NOT modify their orchestration boundary, producer contract, governance model, EPIP-016
boundary, or single-authoritative-path rule.

This ADR defines architecture only. It authorizes no implementation, interface, registry, planner,
producer, placeholder, or Programme A activity.

## Executive Summary

EPIP-017 SHALL treat Evidence as an immutable, versioned, attributable semantic claim about one
explicit subject, scope, and logical data boundary. Evidence records what an authoritative source
asserted under a certified capability contract. It does not decide, recommend, execute, schedule,
resolve dependencies, or establish that the claim is objectively true.

Evidence identity, semantic meaning, provenance, validity, quality, and disposition SHALL remain
distinct. Two evidence artifacts MAY be semantically compatible without being identical, MAY be
redundant without being duplicates, and MAY conflict while each remains individually valid.

All dependencies SHALL be explicit requirements of immutable capability versions and SHALL be
resolved by the semantic planning authority before invocation. Producers MUST NOT discover,
select, invoke, rewrite, or recursively resolve dependencies. The execution plane MUST NOT change
dependency meaning or substitute producers.

Dependency resolution SHALL operate against one frozen registry snapshot, one admitted pipeline
request, one semantic policy profile, and one temporal input boundary. Candidate providers SHALL
be filtered by capability semantics, governance eligibility, compatibility, scope, timeframe,
completeness, and certification. Ambiguity, unresolved conflict, incompatible meaning, missing
mandatory input, forbidden edges, and cycles SHALL fail closed.

The dependency graph belongs to EPIP-017's semantic plan. Evidence artifacts MAY preserve stable
provenance identities, but MUST NOT contain navigable producer orchestration, call another Evidence,
or own dependency resolution. This preserves the frozen EPIP-016 principle that Evidence does not
know another Evidence while retaining complete lineage outside mutable runtime relationships.

## Purpose

Establish the constitutional semantic model for Evidence and every relationship by which one
producer result depends on another source of Evidence.

This ADR defines:

- what Evidence represents and explicitly does not represent;
- the formal evidence taxonomy;
- semantic identity, equivalence, compatibility, conflict, redundancy, completeness, and
  independence;
- dependency types, authority, lifecycle, resolution, validation, diagnostics, and certification;
- deterministic and replayable preservation of semantic dependency graphs;
- the rules that prevent new producers from silently changing existing pipelines.

## Problem Statement

Capability names and serializable schemas are insufficient to establish semantic compatibility.
Two producers can emit structurally identical outputs while differing in subject, timeframe,
availability boundary, units, validity, completeness, assumptions, provenance, or analytical
meaning.

Without a frozen semantic contract, EPIP-017 could:

- select a producer merely because it emits a matching schema;
- treat optional availability as permission to change semantics at runtime;
- silently replace an existing producer after registration of a new producer;
- collapse conflicting evidence into one apparently authoritative value;
- mistake duplicate identity for semantic redundancy;
- allow producers to discover hidden dependencies;
- introduce cycles or conditional graph mutation during execution;
- reinterpret historical evidence under current capability definitions;
- transfer analytical ownership from producers to the planner;
- hand semantically incomplete evidence to EPIP-016.

Dependency correctness must therefore be defined before planner, scheduler, cache, replay, or
handoff architecture can be frozen.

## Architectural Context

ADR-EPIP017-01 establishes EPIP-017 as the sole semantic orchestration authority before the
EPIP-016 handoff. It assigns semantic planning to the control plane and prohibits the execution
plane from altering meaning.

ADR-EPIP017-02 establishes immutable capability contracts, explicit dependencies, narrow context
visibility, producer isolation, and the prohibition on producer-owned dependency resolution.

ADR-EPIP017-03 establishes immutable registry snapshots, exact governance eligibility, explicit
compatibility decisions, capability admission, selection stability, and fail-closed treatment of
unknown compatibility.

EPIP-016 remains the authority for Evidence registration and downstream decision theory. This ADR
MUST NOT add Decision, Candidate, Confidence, recommendation, risk, portfolio, or execution meaning
to Evidence.

Temporal correctness remains dependent on ADR-EPIP017-05. Semantic-plan representation remains
dependent on ADR-EPIP017-06. Evidence-set handoff and completeness remain dependent on
ADR-EPIP017-15.

## Definitions

### Evidence

An immutable, versioned, attributable semantic claim produced or admitted under one authoritative
source contract for one explicit subject, scope, and logical data boundary.

### Evidence Artifact

One immutable materialization of Evidence together with its semantic metadata, provenance
references, validity state, completeness state, schema identity, and content identity.

### Evidence Semantics

The stable meaning of an Evidence claim, including subject, predicate, value domain, units, scope,
temporal interpretation, assumptions, validity rules, completeness rules, and authoritative
capability contract.

### Evidence Type

An immutable, versioned semantic contract defining the meaning and admissible representation of a
class of Evidence. Evidence type is not merely a serialization schema.

### Evidence Requirement

A versioned semantic requirement declared by a consumer capability for Evidence satisfying stated
type, compatibility, scope, validity, completeness, temporal, provenance, cardinality, and
certification constraints.

### Dependency

An immutable directed relationship in a semantic plan from an Evidence requirement to one or more
resolved upstream Evidence sources or admitted external inputs.

### Provider Candidate

A producer capability or admitted external source that claims it can satisfy an Evidence
requirement. Candidate status grants no selection authority.

### Resolution Profile

An immutable, versioned governance policy that constrains provider selection, cardinality,
priority, pinning, substitution, compatibility, certification, and ambiguity handling.

### Provenance Reference

A stable, non-navigable identity linking an Evidence artifact to its authoritative source and
semantic inputs for audit and lineage. It does not grant runtime access or dependency authority.

### Semantic Plan Graph

The immutable directed acyclic graph of resolved Evidence requirements, producer invocations,
admitted external inputs, and terminal evidence-set requirements. It is owned by the semantic
planning authority, not by Evidence or producers.

## Evidence Definition

Every Evidence artifact MUST identify:

- immutable evidence identity and evidence-type version;
- authoritative producer capability or admitted external-source identity;
- producer and implementation versions where produced by a producer;
- subject and semantic scope;
- logical data and availability boundaries;
- value, value domain, and units where applicable;
- validity and completeness status;
- quality and uncertainty declarations where defined by the evidence type;
- explicit assumptions and invalidation conditions;
- immutable provenance references;
- canonical representation and content identity under ADR-EPIP017-09;
- disposition without changing the underlying semantic claim.

Evidence represents an attributable claim. It MUST NOT represent:

- objective truth guaranteed by the orchestrator;
- a Decision, Candidate, recommendation, EPIP-016 Confidence, or execution instruction;
- producer availability or registry trust;
- dependency resolution policy;
- a mutable pointer to another Evidence artifact;
- permission to invoke another producer;
- an implicit conversion to another evidence type;
- a replacement for risk, portfolio, execution, or financial authority.

Evidence meaning MUST NOT change after creation. Correction, enrichment, reclassification,
recalculation, or reinterpretation MUST create a new Evidence artifact and identity with explicit
lineage to the prior artifact where applicable.

## Evidence Taxonomy

The taxonomy SHALL use independent axes. A single Evidence artifact MAY occupy one value on each
axis. Terms from different axes MUST NOT be treated as mutually exclusive.

### Provenance Axis

#### Primary Evidence

Evidence admitted directly from an authoritative source boundary without analytical derivation by
another EPIP-017 producer. Primary does not mean true, trusted, complete, or decision-ready.

#### Derived Evidence

Evidence produced through a declared transformation of explicit Evidence or admitted external
inputs. Its complete derivation lineage MUST be preserved.

#### Secondary Evidence

Derived Evidence whose declared semantic purpose is interpretation, classification, summarization,
or contextualization of Primary or other Derived Evidence. Secondary status MUST NOT imply lower
quality or weaker authority by itself.

#### Synthetic Evidence

Derived Evidence constructed from a declared model, simulation, normalization, aggregation, or
counterfactual transformation rather than direct observation. It MUST declare its construction
method, assumptions, input lineage, and certification profile. Synthetic MUST NOT mean fabricated
or provenance-free.

#### Composite Evidence

Derived Evidence whose semantic claim requires multiple explicitly declared input artifacts.
Composition order, cardinality, completeness, conflict handling, and atomicity MUST be part of the
capability contract.

### Disposition Axis

#### Accepted Evidence

Evidence that satisfies the applicable structural, semantic, temporal, governance, and policy
validation for a stated use. Acceptance is use-specific and MUST NOT rewrite the Evidence.

#### Rejected Evidence

Evidence preserved but declared ineligible for a stated use with an immutable reason code.
Rejection MUST NOT erase, mutate, or reclassify the original semantic claim as failure.

### Temporal Axis

#### Historical Evidence

Evidence whose logical data boundary precedes the current admitted boundary or is consumed under a
historical replay policy. Historical status MUST retain the original semantic and governance
versions.

#### Current Evidence

Evidence valid for the exact admitted current logical boundary. Current MUST NOT mean latest by
wall-clock arrival.

### Retention Axis

#### Transient Evidence

Evidence eligible only within a bounded run or plan scope and not approved as a durable reusable
result. Transient Evidence MUST still remain immutable and auditable for its required retention
scope.

#### Persistent Evidence

Evidence accepted by the durable result authority for governed retention and reuse. Persistence
MUST NOT change semantic meaning, validity, trust, or completeness.

Retention authority and cache behavior remain governed by ADR-EPIP017-10.

## Evidence Categories

Every evidence type MUST belong to one governed primary semantic category and MAY declare
additional governed facets. Initial categories are:

- **Structural** — market topology, pivots, breaks, ranges, and structural state;
- **Liquidity** — liquidity locations, imbalances, sweeps, and related observations;
- **Trend** — direction, persistence, transition, or trend classification;
- **Volatility** — variability, dispersion, expansion, contraction, or volatility regime;
- **Pattern** — declared recurring structural or statistical pattern;
- **Wave** — wave count, degree, alternates, projections, or invalidation;
- **Macro** — macroeconomic facts, events, releases, or governed interpretations;
- **Session** — market-session identity, boundary, or session-specific state;
- **Calendar** — trading calendars, holidays, closures, and governed temporal boundaries;
- **Execution** — immutable execution-domain facts admitted as evidence, never execution commands;
- **Risk** — immutable risk-domain facts admitted as evidence, never duplicated risk calculations;
- **External** — admitted facts from an external authoritative boundary not owned by an EPIP
  analytical domain.

Category identity and meaning MUST be immutable and versioned. New categories MAY be added through
ADR-EPIP017-03 capability governance without modifying existing categories when they conform to
the approved evidence and dependency model. A category that introduces new state, trust, temporal,
side-effect, execution, or authority semantics MUST require a new or amended ADR.

Category membership MUST NOT imply compatibility, authority, quality, priority, or producer
selection.

## Semantic Model

### Semantic Identity

Semantic identity MUST include the evidence type, semantic version, subject kind, scope kind,
value-domain meaning, unit semantics, temporal interpretation, completeness model, and
authoritative capability contract. Representation identity and artifact identity remain separate
under ADR-EPIP017-09.

### Semantic Equivalence

Two evidence artifacts are semantically equivalent only when an explicit certified equivalence
decision states that their claims have the same meaning for a specified consumer scope.

Semantic equivalence MUST require compatible evidence types, subjects, scopes, units, temporal
boundaries, validity semantics, completeness semantics, assumptions, and provenance constraints.
Equal values or equal schemas MUST NOT establish semantic equivalence.

Semantic equivalence does not imply artifact identity. Different producers MAY create distinct
artifacts that are semantically equivalent for one scope.

### Semantic Compatibility

Semantic compatibility is a directional, versioned relation stating that Evidence satisfying one
contract MAY be consumed by a specified requirement without hidden meaning loss.

Compatibility MUST identify allowed conversion, narrowing, widening, unit, completeness,
temporal, quality, and provenance effects. Unknown compatibility MUST fail closed.

### Semantic Conflict

Evidence conflicts when two or more individually admissible claims cannot simultaneously satisfy a
consumer's declared semantic constraints for the same relevant subject and boundary.

Conflict MUST be preserved and diagnosed. The planner MUST NOT decide which claim is true. A
consumer capability MAY accept multiple conflicting inputs only when its immutable contract
declares conflict interpretation, cardinality, ordering, and output semantics.

### Semantic Redundancy

Evidence is redundant for a requirement when multiple artifacts provide equivalent claim coverage
beyond the declared cardinality or diversity need. Redundancy MUST NOT imply duplication or
invalidity. A resolution profile MUST state whether redundant inputs are rejected, retained for
corroboration, or supplied to a declared multi-provider consumer.

### Semantic Completeness

Completeness states whether all evidence dimensions, cardinalities, temporal windows, required
facets, and provenance constraints declared by a requirement are satisfied.

Completeness MUST be explicit, use-specific, and independently validated. Absence, valid empty
Evidence, partial Evidence, rejected Evidence, and unavailable dependency MUST remain distinct.

### Semantic Independence

Evidence artifacts are semantically independent for a stated use only when they do not share a
provenance source or derivation dependency that the applicable independence policy considers
material.

Different producer identities, capabilities, or values MUST NOT prove independence. Independence
MUST be evaluated from explicit lineage and policy.

## Dependency Model

### Explicit Dependency

Every dependency MUST originate from an immutable Evidence requirement declared by a capability
version or terminal evidence-set contract. It MUST appear in the semantic plan graph before
execution.

### Mandatory Dependency

A mandatory dependency MUST be resolved by the required compatible and valid Evidence cardinality.
If it cannot be resolved, the consumer invocation MUST NOT become eligible.

### Optional Dependency

An optional dependency MAY be absent only when the capability contract defines the exact absence
semantics and proves that absence does not create runtime ambiguity. Whether the optional
dependency is present MUST be frozen in the semantic plan identity.

Runtime provider availability MUST NOT decide optional-dependency presence after planning.

### Conditional Dependency

A conditional dependency SHALL be required only when a deterministic predicate over already
frozen pipeline, context, temporal, or policy facts evaluates true during semantic planning.

The predicate, inputs, version, and outcome MUST be part of semantic-plan identity. Producer
output, execution order, runtime availability, timeout, or failure MUST NOT create a new
conditional dependency during execution.

### Derived Dependency

A derived dependency is a provenance relation showing that one Evidence artifact was produced from
specified upstream semantic inputs. It MUST correspond to an authorized planned dependency or an
admitted primary-input relation. It MUST NOT be invented after execution to conceal an undeclared
input.

### Transitive Dependency

A transitive dependency is lineage reachable through one or more explicit dependency edges. It is
available to planning, audit, invalidation, and independence analysis but MUST NOT grant a producer
direct visibility of a dependency not listed in its own input manifest.

### Forbidden Dependency

A forbidden dependency is any relationship prohibited by domain ownership, capability contract,
trust policy, temporal policy, cycle policy, EPIP-016 boundary, or explicit semantic rule. A
forbidden dependency MUST fail planning and MUST NOT be converted to optional or hidden input.

### Dependency Cardinality

Every requirement MUST declare exact, minimum, maximum, or bounded-set cardinality. Multi-provider
cardinality MUST declare canonical ordering, independence constraints, redundancy behavior,
conflict behavior, and completeness semantics.

Unspecified cardinality MUST fail closed.

## Dependency Resolution

Dependency resolution SHALL be performed only by the semantic planning authority and SHALL use one
frozen registry snapshot, admitted pipeline request, semantic policy profile, context boundary,
temporal boundary, and compatibility evidence set.

Resolution SHALL apply the following normative precedence:

1. The planner MUST freeze the requirement identity, capability version, resolution profile, and
   all predicate inputs.
2. Mandatory and deterministically active conditional requirements MUST be expanded before
   provider selection.
3. Provider candidates MUST match the required evidence type and capability semantics.
4. Candidates MUST satisfy exact registry eligibility, trust, certification, compatibility,
   timeframe, context, provenance, completeness, and policy constraints.
5. Explicit producer or certified selection-profile pins MUST be applied before general priority.
6. Cardinality, independence, diversity, redundancy, and conflict constraints MUST be evaluated.
7. If more than one valid resolution remains without an explicit deterministic selection rule, the
   dependency MUST be diagnosed as ambiguous and planning MUST fail.
8. The complete expanded graph MUST be validated for forbidden edges and cycles.
9. Resolved nodes and edges MUST receive canonical identity and ordering independent of discovery,
   registration, storage, or enumeration order.
10. The resolution evidence, rejected candidates, and reason codes MUST be preserved for audit.

Registration of a new producer MUST NOT change an already frozen semantic plan. It MUST NOT change
future resolution for a pinned pipeline or certified selection profile unless an explicit governed
profile version authorizes that change.

### Missing Dependency

A missing mandatory dependency MUST fail planning. A missing optional dependency MUST use only the
predeclared absence semantics and MUST be represented explicitly in the semantic plan.

### Invalid Dependency

A structurally, semantically, temporally, or governance-invalid dependency MUST be rejected with a
stable diagnostic. Invalid Evidence MUST NOT satisfy cardinality or completeness.

### Incompatible Dependency

An incompatible dependency MUST fail closed. Hidden conversion, implicit unit conversion,
reinterpretation, schema coercion, or producer substitution is prohibited.

### Conflicting Dependency

Conflicting candidates MUST remain explicit. If the consumer contract does not declare a certified
conflict model, resolution MUST fail. Priority MUST NOT be used to conceal semantic conflict.

### Duplicate Dependency

The same artifact identity referenced more than once for one requirement is a duplicate and MUST
count once unless the capability contract explicitly defines positional multiplicity. Duplicate
identity MUST NOT be mistaken for independent corroboration.

### Dependency Cycle

The semantic plan graph MUST be acyclic. Direct, indirect, cross-timeframe, conditional, and
capability-substitution cycles are forbidden. Cycle detection MUST occur after complete dependency
expansion and before plan acceptance.

### Dependency Ambiguity

Ambiguity exists when multiple admissible resolutions remain and no frozen rule selects exactly
the required cardinality. Ambiguity MUST fail planning. Discovery order, registration order,
version recency, runtime availability, or implementation preference MUST NOT break ties.

## Dependency Compatibility

Dependency compatibility MUST be explicit, directional, versioned, scoped, certified, and
governed by the Compatibility Authority from ADR-EPIP017-03.

A compatibility decision MUST address:

- evidence-type and capability versions;
- subject and scope semantics;
- value domain and units;
- temporal and availability semantics;
- validity and completeness states;
- quality and uncertainty requirements;
- provenance and independence constraints;
- configuration and context assumptions;
- consumer requirement and permitted transformations;
- replay and determinism profiles where material.

Semantic conversion MUST itself be an admitted, versioned capability or an explicit lossless
canonicalization allowed by the compatibility decision. The planner MUST NOT perform hidden
semantic conversion.

## Dependency Authority

- The Evidence Type Owner SHALL own evidence-type semantics.
- The Producer Owner SHALL own the analytical correctness of Evidence produced under its certified
  capability.
- The Capability Owner SHALL own dependency requirements and consumer semantics for that
  capability version.
- The Architectural Authority SHALL admit evidence categories and new semantic relationship
  classes.
- The Compatibility Authority SHALL declare directional compatibility and incompatibility.
- The semantic planning authority SHALL resolve dependencies strictly under frozen contracts and
  policies; it SHALL NOT invent meaning.
- The Certification Authority SHALL certify exact producer-capability and dependency-behavior
  conformance; it SHALL NOT certify objective market truth.
- The durable result authority SHALL validate commitment integrity; it SHALL NOT become semantic
  owner.
- The Audit Authority SHALL verify provenance and resolution compliance; it SHALL NOT rewrite
  evidence or resolve truth conflicts.
- EPIP-016 SHALL remain the authority for downstream evidence admission and decision semantics.

Every Evidence type and capability version MUST have exactly one authoritative semantic owner at a
governance epoch. Ownership transfer MUST follow ADR-EPIP017-03 and MUST NOT alter historical
meaning.

## Dependency Validation

Before semantic-plan acceptance, validation MUST establish:

- requirement and capability identities are admitted and version-compatible;
- every provider is eligible in the frozen registry snapshot;
- all mandatory and active conditional dependencies resolve;
- optional absence semantics are explicit;
- cardinality and canonical ordering are satisfied;
- subject, scope, unit, temporal, validity, completeness, provenance, and certification constraints
  are satisfied;
- no duplicate is counted as independent Evidence;
- conflicts are handled only by declared consumer semantics;
- redundancy policy is explicit;
- no hidden conversion or forbidden edge exists;
- the graph is complete, finite, bounded, and acyclic;
- every transitive lineage relation is reachable from explicit edges;
- terminal evidence-set requirements remain separate from EPIP-016 Decision work.

Before producer invocation, the execution boundary MUST verify that committed or authorized
dependency artifacts still match the frozen semantic references. It MUST NOT re-resolve them.

After result submission, provenance validation MUST confirm that every claimed derived dependency
corresponds to the authorized input manifest. An undeclared lineage input is a producer contract
failure.

## Dependency Invariants

1. Evidence meaning never changes after creation.
2. Evidence identity is immutable.
3. Every Evidence type and capability version has one semantic owner at an epoch.
4. Every dependency is explicit before execution.
5. No producer discovers, selects, invokes, or rewrites a dependency.
6. No execution-plane action changes semantic dependency meaning.
7. Optional-dependency presence is frozen in the semantic plan.
8. Conditional dependencies use only frozen pre-execution facts.
9. Transitive lineage does not grant direct producer visibility.
10. Hidden dependencies and hidden conversions are prohibited.
11. Semantic compatibility is directional, versioned, and certified.
12. Schema compatibility never implies semantic compatibility.
13. Semantic conflict remains diagnosable and is never hidden by priority.
14. Duplicate Evidence never counts as independent corroboration.
15. Redundancy remains distinct from duplication and conflict.
16. Missing, invalid, rejected, empty, partial, and unavailable remain distinct.
17. Dependency graphs are finite, bounded, immutable, and acyclic.
18. Resolution ambiguity fails closed.
19. Resolution does not create Evidence.
20. Resolution never transfers producer or semantic ownership.
21. Semantic correctness is independent of execution order.
22. Registration of a producer never mutates a frozen plan.
23. Historical Evidence retains original semantic versions and provenance.
24. Decision remains outside the EPIP-017 dependency graph.

## Dependency Diagnostics

Dependency diagnostics MUST use stable, versioned codes and MUST distinguish at minimum:

- missing mandatory dependency;
- absent optional dependency;
- invalid dependency;
- incompatible dependency;
- conflicting dependency;
- redundant dependency;
- duplicate dependency;
- obsolete or deprecated dependency;
- ambiguous dependency resolution;
- unsupported dependency type, capability, scope, timeframe, or profile;
- forbidden dependency;
- direct or transitive cyclic dependency;
- semantic inconsistency;
- cardinality violation;
- completeness violation;
- provenance or independence violation;
- hidden conversion attempt;
- ineligible provider;
- expired or revoked compatibility or certification.

Every diagnostic MUST identify the requirement, candidate or resolved provider, relevant semantic
versions, frozen registry snapshot, resolution profile, reason, and planning phase. Diagnostics
MUST preserve rejected candidates needed to explain selection.

Human-readable text MUST NOT carry unique semantic meaning. Diagnostics MUST NOT silently repair,
select, convert, or rewrite a dependency.

## Dependency Certification

Certification MUST verify at least:

1. Evidence-type and capability semantic definitions are complete and immutable.
2. Producer outputs conform to their declared evidence semantics.
3. Every consumed dependency is declared and visible in the input manifest.
4. Mandatory, optional, conditional, derived, and transitive relationships follow this ADR.
5. Optional absence produces the declared deterministic semantics.
6. Conditional predicates depend only on frozen permitted facts.
7. Cardinality, canonical ordering, independence, redundancy, and conflict rules are enforced.
8. Missing, invalid, incompatible, conflicting, duplicate, obsolete, ambiguous, unsupported, and
   cyclic cases produce the required diagnostics and fail-closed behavior.
9. No hidden producer invocation, dependency discovery, conversion, or graph mutation occurs.
10. Equivalent semantic planning inputs reproduce the same resolution and graph identity.
11. Historical semantics and provenance remain interpretable in replay.
12. New producer registration does not redirect pinned or profile-governed pipelines implicitly.
13. EPIP-016 receives no Decision work or hidden semantic conversion from resolution.

Certification of structural graph validity MUST NOT be represented as certification that the
market claim is objectively true.

## Determinism

Given the same admitted pipeline request, semantic policy and resolution-profile versions, frozen
registry snapshot, capability and evidence-type versions, context and temporal boundaries,
compatibility decisions, provider pins, and graph limits, dependency resolution MUST produce:

- the same expanded requirements;
- the same candidate set;
- the same accepted and rejected candidates;
- the same selected providers and cardinalities;
- the same optional and conditional outcomes;
- the same graph nodes and edges;
- the same canonical ordering;
- the same diagnostics;
- the same semantic-plan graph identity.

Filesystem order, registry enumeration order, network arrival, database order, hash order,
discovery order, registration order, thread order, execution completion, operational availability,
or current time MUST NOT affect semantic resolution.

Deterministic resolution does not prove deterministic producer output. Producer-output determinism
remains governed by ADR-EPIP017-08.

## Replay

Every replay MUST preserve or explicitly govern:

- the original evidence-type and capability versions;
- the original registry snapshot and resolution profile;
- the original dependency graph and semantic-plan identity;
- provider selections and rejected alternatives;
- optional and conditional dependency outcomes;
- original semantic compatibility decisions;
- historical provenance and transitive lineage;
- temporal and availability boundaries from ADR-EPIP017-05;
- later deprecation, incompatibility, or revocation as separate audit facts.

Operational reproduction MUST reproduce the original resolved graph. Historical recomputation MAY
resolve under an explicitly selected historical or contemporary governance policy only as defined
by ADR-EPIP017-11; it MUST produce a new semantic-plan identity when any resolution input differs.

Replay MUST NOT reinterpret historical Evidence using a newer evidence-type version, silently
replace an unavailable historical producer, or infer missing lineage from current registry state.

## Audit

The audit record for dependency resolution MUST preserve:

- every Evidence requirement and its owner;
- evidence-type, capability, producer, compatibility, and policy versions;
- the frozen registry snapshot and governance epoch;
- all provider candidates considered;
- every acceptance and rejection reason;
- selection pins and deterministic tie-breaking rules;
- cardinality, independence, redundancy, conflict, and completeness evaluations;
- optional and conditional outcomes and predicate inputs;
- graph validation, cycle detection, and forbidden-edge findings;
- canonical graph identity and semantic-plan identity;
- provenance lineage submitted by every produced result;
- later semantic deprecation or incompatibility without rewriting original history.

Audit MUST explain why a provider was selected and why every material alternative was not selected.
The Audit Authority MUST NOT alter resolution or declare objective analytical truth.

## Migration

- Existing domain outputs MUST be inventoried by evidence meaning, not only schema or module name.
- Every legacy producer MUST declare evidence types, categories, subjects, scopes, temporal
  semantics, completeness, assumptions, provenance, and dependency requirements before EPIP-017
  admission.
- Hidden dependencies, implicit conversions, recursive producer calls, and runtime discovery MUST
  be eliminated or represented through approved explicit contracts before certification.
- Existing chains such as Swing, Market Structure, Liquidity, Fibonacci, Market Context, and
  Elliott MUST be modeled as capability requirements rather than hard-coded producer calls.
- Migration MUST preserve contradictory and rejected Evidence required for audit.
- Shadow resolution MUST compare semantic graphs, selections, lineage, outputs, and diagnostics;
  matching execution order alone is insufficient.
- Legacy ordering MUST NOT be assumed semantically correct without explicit dependency evidence.
- A migrated producer MUST NOT automatically replace its legacy counterpart in authoritative
  pipelines.
- Divergence and rollback governance MUST follow ADR-EPIP017-16.

## Backward Compatibility

This ADR changes no production behavior, Evidence object, public API, producer implementation,
EPIP-016 contract, Replay behavior, EventBus behavior, financial calculation, risk rule, portfolio
behavior, execution behavior, or serialization format.

The dependency graph defined here is an EPIP-017 semantic-plan artifact. It MUST NOT introduce
navigable Evidence-to-Evidence relationships into frozen EPIP-016 Evidence contracts.

EPIP-016 handoff MAY preserve provenance through compatible immutable references or a separate
orchestration manifest as governed by ADR-EPIP017-15. It MUST NOT reinterpret Evidence or require
EPIP-016 to perform dependency resolution.

Legacy execution MAY continue during governed migration. Historical legacy Evidence MUST NOT be
silently reclassified under new EPIP-017 categories or semantic versions.

## Forbidden Behaviours

EPIP-017 MUST NEVER permit:

1. Implicit dependency creation.
2. Runtime dependency discovery.
3. Runtime dependency mutation.
4. Producer-owned dependency selection or resolution.
5. Producer-to-producer invocation or recursive execution.
6. Execution-plane dependency substitution.
7. Dependency rewriting after semantic-plan acceptance.
8. Hidden semantic conversion or unit conversion.
9. Reinterpretation of an Evidence artifact under a different semantic version.
10. Schema matching as proof of semantic compatibility.
11. Discovery, registration, storage, or completion order as a selection rule.
12. Runtime availability as an optional-dependency decision.
13. Conditional dependency predicates based on producer output or execution failure.
14. Dependency cycles.
15. Silent ambiguity resolution.
16. Priority-based suppression of semantic conflict.
17. Duplicate Evidence counted as independent corroboration.
18. Missing, rejected, invalid, empty, partial, or unavailable Evidence treated as equivalent.
19. Resolution that creates new Evidence or changes producer ownership.
20. Decision, Candidate, Confidence, recommendation, risk decision, or execution action as an
    EPIP-017 dependency output.
21. Historical dependency reconstruction from current registry state without an explicit replay
    policy.
22. Mutation or deletion of dependency-resolution audit history.

Any forbidden behavior SHALL be an architectural and certification failure and MUST fail closed.

## Alternatives Considered

### Direct producer references

Consumers declare concrete producers as direct dependencies.

Rejected as the general semantic model because it couples producer identity to evidence meaning
and prevents governed substitution. Explicit pins remain permitted through resolution profiles.

### Schema-based dependency matching

Any producer with a compatible output schema may satisfy a requirement.

Rejected because structural compatibility does not establish semantic, temporal, completeness,
provenance, or authority compatibility.

### Runtime dependency discovery

Producers request additional inputs while executing.

Rejected because it mutates graph meaning, defeats complete planning, and prevents deterministic
replay and audit.

### Priority resolves every conflict and ambiguity

The highest-priority provider or value is always selected.

Rejected because priority cannot determine truth, semantic compatibility, independence, or
conflict resolution.

### Evidence owns navigable dependency links

Each Evidence object directly knows and accesses its upstream Evidence objects.

Rejected because it violates frozen EPIP-016 semantics, creates hidden mutable graphs, and gives
Evidence runtime dependency authority. Stable provenance identities remain permitted.

### Capability requirements resolved by a frozen semantic planner

Consumers declare immutable Evidence requirements; the planner resolves them under one frozen
registry snapshot and versioned policy.

Accepted because it separates meaning from implementation, preserves governance and determinism,
and allows conforming future producers without silent redirection.

## Decision

EPIP SHALL adopt the Evidence definitions, taxonomy, categories, semantic relations, dependency
types, resolution precedence, compatibility rules, authority boundaries, validation rules,
diagnostics, certification obligations, determinism guarantees, replay preservation, audit model,
migration rules, compatibility guarantees, and prohibitions in this ADR as the constitutional
semantic model for EPIP-017.

Every producer capability, semantic plan, execution authorization, replay, diagnostic, audit, and
EPIP-016 handoff MUST conform to this model. No implementation MAY compensate for missing semantic
architecture through implicit conversion, runtime discovery, or procedural convention.

## Consequences

### Positive

- Evidence meaning remains stable independently of producer and storage implementation.
- Dependency graphs become explicit, deterministic, auditable, and replayable.
- New producer registration cannot silently redirect existing pipelines.
- Semantic conflict, redundancy, duplication, absence, and invalidity remain distinguishable.
- Capability-based extensibility no longer relies on schema coincidence.
- Producers remain isolated from planning and one another.
- Historical dependency semantics remain interpretable.
- EPIP-016 remains free of producer orchestration concerns.

### Negative

- Evidence types and capability requirements require substantial semantic governance.
- Compatibility must be proven across several dimensions.
- Ambiguous or incomplete graphs fail rather than selecting a convenient provider.
- Existing producer chains may reveal undocumented dependencies during migration.
- Multi-provider and conflict-aware capabilities require stronger certification.
- Historical replay requires retention of semantic versions and registry snapshots.

### Trade-offs

EPIP accepts more explicit semantic contracts and planning failures in exchange for preventing
silent meaning changes, hidden dependencies, false equivalence, and unreproducible orchestration.

## Semantic Invariants

1. Evidence is an immutable attributable claim, not guaranteed truth.
2. Evidence never changes meaning.
3. Evidence identity never changes.
4. Evidence never decides, recommends, executes, schedules, or resolves dependencies.
5. Evidence provenance uses immutable references and never grants runtime navigation authority.
6. Evidence taxonomy axes remain independent.
7. Semantic equivalence requires explicit certified scope.
8. Semantic compatibility is directional and versioned.
9. Semantic conflict is preserved and diagnosable.
10. Semantic redundancy is distinct from duplication.
11. Semantic completeness is explicit and use-specific.
12. Semantic independence is established from provenance, not producer count.
13. Dependencies are explicit and immutable before execution.
14. Resolution never creates hidden Evidence.
15. Resolution never changes Producer ownership.
16. Semantic correctness is independent of execution order.
17. The planner resolves requirements but does not determine objective truth.
18. Unknown compatibility, ambiguity, cycles, and forbidden edges fail closed.
19. Historical semantics remain bound to original versions.
20. EPIP-016 remains the downstream evidence and decision authority.

## Non-goals

This ADR does not define:

- implementation classes, interfaces, APIs, algorithms, stores, or graph libraries;
- producer execution behavior already governed by ADR-EPIP017-02;
- registry storage or governance workflow already governed by ADR-EPIP017-03;
- calendar, watermark, availability, or cross-timeframe boundary rules;
- semantic-plan or dispatch-plan representation;
- invocation states or result commitment;
- canonical serialization or digest algorithms;
- durable result stores, caches, or invalidation algorithms;
- replay execution mechanisms;
- retry, recovery, or fallback algorithms;
- scheduler or parallel worker topology;
- EPIP-016 handoff representation;
- analytical formulas, market interpretation, trading logic, Decision, Candidate, Confidence, risk,
  portfolio, execution, or financial calculations.

These exclusions MUST be resolved by their mandatory ADRs and MUST NOT be delegated to code.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01, ADR-EPIP017-02, ADR-EPIP017-03, and the frozen
EPIP-016 and H001–H007 architecture.

It creates or confirms mandatory dependencies on:

- ADR-EPIP017-05 for logical data boundaries, availability, calendars, watermarks, late data,
  revisions, and cross-timeframe compatibility;
- ADR-EPIP017-06 for semantic-plan graph, resolution evidence, input-manifest, and dispatch-plan
  boundaries;
- ADR-EPIP017-08 for determinism profiles and semantic-equivalence certification;
- ADR-EPIP017-09 for evidence identity, semantic identity, artifact identity, canonicalization, and
  digest hierarchy;
- ADR-EPIP017-10 for persistence, transient Evidence, durable results, cache reuse, lineage, and
  invalidation;
- ADR-EPIP017-11 for dependency-graph replay, historical recomputation, and operational
  reproduction;
- ADR-EPIP017-12 for preservation of semantic graphs in audit snapshots and checkpoints;
- ADR-EPIP017-13 for missing, failed, invalid, and conflicting dependency propagation;
- ADR-EPIP017-14 for order-independent parallel consumption and multi-provider equivalence;
- ADR-EPIP017-15 for evidence completeness, provenance mapping, and EPIP-016 handoff;
- ADR-EPIP017-16 for legacy graph migration, divergence, rollback, and retirement;
- ADR-EPIP017-17 for semantic diagnostic retention and graph
  explanation;
- ADR-EPIP017-18 for finite graph, fan-out, depth,
  and resolution-budget limits.

This ADR identifies no new ADR family beyond those already mandated. It makes the Evidence Type
Owner and Capability Owner roles explicit; ADR-EPIP017-03 governance SHALL apply to both without
requiring a separate authority model.

## Future Evolution

New evidence categories, semantic relationship classes, compatibility dimensions, or dependency
cardinalities MAY be added only through versioned governance. Existing semantic identities and
historical artifacts MUST NOT be reinterpreted.

Iterative, cyclic, streaming, dynamically expanding, probabilistic-provider, or fixed-point
dependency semantics remain unsupported. Any future requirement for them MUST introduce a new ADR
that defines termination, identity, determinism, replay, authority, and certification without
weakening this contract.

Semantic ontologies MAY become richer over time, but automated inference MUST NOT create hidden
compatibility or dependency edges. Every inference used for authoritative planning MUST be reduced
to an explicit, versioned, auditable governance or resolution fact before plan acceptance.

## Approval Gate

Approval of this ADR resolves the Evidence semantics and dependency-resolution architecture only.
It does not approve an Evidence implementation, capability registry, planner, graph, producer,
scheduler, adapter, replay mechanism, handoff, or Programme A.

EPIP-017 implementation remains prohibited until the complete mandatory ADR set is accepted and
the remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
