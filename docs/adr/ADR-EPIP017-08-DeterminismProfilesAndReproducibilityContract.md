# ADR-EPIP017-08 — Determinism Profiles and Reproducibility Contract

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-07 are approved, frozen, and normative. This ADR MUST NOT
modify their orchestration authority, producer contract, governance, Evidence semantics, temporal
model, plan separation, execution lifecycle, EPIP-016 boundary, or single-authoritative-path rule.

This ADR defines determinism architecture only. It authorizes no implementation, random service,
clock, planner, scheduler, replay engine, comparator, certification engine, interface, placeholder,
or Programme A activity.

## Executive Summary

EPIP-017 SHALL treat determinism as a collection of explicit, profile-scoped guarantees rather
than one universal claim.

**Determinism** means that identical complete authoritative inputs under the same contract and
profile produce the same canonical authoritative outcome. **Reproducibility** means that an
independent conforming evaluation can verify the required equivalence relation from preserved
inputs and artifacts. Reproducibility does not require identical CPU scheduling, thread
interleaving, machine speed, worker location, process identity, memory addresses, or elapsed time.

EPIP SHALL distinguish strict, semantic, operational, replay, and certification equivalence.
Matching terminal values alone SHALL never establish equivalence.

Every run SHALL declare exactly one Execution Profile and its required Determinism Profile. The
supported Execution Profiles are Institutional, Certification, Replay, Historical, Simulation,
Development, Testing, and Benchmark. Profiles MAY strengthen guarantees but MUST NOT silently
weaken an admitted pipeline's requirements.

Semantic Plan, Evidence, dependencies, committed result, Commit Record, authoritative lifecycle
transitions, authority decisions, semantic diagnostics, canonical ordering, and certification
verdict SHALL be deterministic whenever authoritative use is permitted. Dispatch Plan and the
canonical authoritative projection of the Execution Ledger SHALL be reproducible from their own
complete inputs. Operational telemetry MAY vary but MUST remain outside semantic identity,
authority, and certification meaning.

The full raw Execution Ledger may contain variable operational observations. Those observations
MUST be classified as non-semantic and non-authoritative unless validated into an authoritative
lifecycle fact. Exact raw-ledger reproduction is required only when an operational reproduction
profile explicitly includes the same recorded operational events. This distinction prevents
physical timing from masquerading as semantic determinism.

## Purpose

Establish the constitutional meaning of determinism, reproducibility, equivalence, variability,
execution profiles, certification profiles, observable behavior, and determinism authority across
EPIP-017.

This ADR defines:

- which complete inputs determine each artifact;
- which artifacts and behaviors MUST be reproducible;
- which physical and operational elements MAY vary;
- which equivalence relation applies to each profile;
- how environment, clocks, randomness, numeric behavior, scheduling, and authority are bounded;
- how determinism is diagnosed, audited, migrated, and certified.

## Problem Statement

The word deterministic is often used imprecisely. A planner can be deterministic while a producer
is not. Evidence can be semantically identical while workers, timings, retries, or diagnostic
telemetry differ. Conversely, two runs can have identical terminal values while using different
inputs, authorities, dependencies, or failures and therefore not be equivalent.

The original EPIP-017 proposal conflated:

- deterministic planning;
- deterministic producer computation;
- deterministic Evidence and diagnostics;
- deterministic scheduling;
- deterministic failure and authority decisions;
- exact execution-trace reproduction;
- historical replay;
- physical timing reproducibility.

This creates impossible or unsafe promises. Timeouts based on elapsed time can vary. Thread
interleaving can vary. Floating-point behavior can vary across certified environments. External
inputs can change unless captured. A raw ledger containing operational timestamps cannot be byte
identical across independent execution.

EPIP therefore requires profile-specific inputs, equivalence relations, observable boundaries,
and certification rules. Any unclassified variability MUST fail closed for authoritative use.

## Architectural Context

ADR-EPIP017-01 requires semantic authority to remain independent of operational execution.

ADR-EPIP017-02 requires producers to declare determinism profiles and prohibits ambient time,
uncontrolled randomness, global mutable state, hidden caches, and incidental ordering.

ADR-EPIP017-03 requires deterministic governance derivation from immutable governance facts and
registry snapshots.

ADR-EPIP017-04 requires deterministic Evidence semantics, dependency resolution, graph identity,
and diagnostics.

ADR-EPIP017-05 freezes temporal authorities and prevents wall-clock execution from changing
Observation, Availability, Knowledge, or Replay semantics.

ADR-EPIP017-06 separates Semantic Plan, Dispatch Plan, and Execution Ledger and defines semantic
and dispatch equivalence.

ADR-EPIP017-07 defines immutable Invocations, attempts, leases, fences, tokens, atomic commit, and
authoritative lifecycle transitions while acknowledging that physical timing may vary.

This ADR defines the determinism guarantees that those artifacts MUST satisfy. Digest algorithms
remain in ADR-EPIP017-09 and replay modes remain in ADR-EPIP017-11.

## Definitions

### Determinism

The property that one complete authoritative input manifest, interpreted under one exact contract,
policy, environment, and Determinism Profile, yields one canonical authoritative outcome.

### Reproducibility

The ability of an independent conforming evaluation to reconstruct or verify the equivalence
required by a declared profile using preserved authoritative inputs and artifacts.

### Repeatability

Reproduction within the same controlled environment and authority boundary. Repeatability is
necessary evidence for some profiles but MUST NOT be substituted for independent reproducibility.

### Determinism Profile

An immutable, versioned contract defining required deterministic artifacts, allowed variability,
complete inputs, canonicalization scope, numeric and environment constraints, equivalence relation,
diagnostics, and certification evidence.

### Execution Profile

An immutable, versioned contract defining the purpose of a run and the minimum governance,
determinism, replay, observability, security, failure, and certification guarantees it requires.

### Certification Profile

An immutable, versioned contract specifying how conformance to one or more Determinism and
Execution Profiles is evaluated, including evidence, environments, repetitions, equivalence,
tolerance, and failure criteria.

### Deterministic Context

The complete immutable set of semantically and authoritatively relevant context inputs, including
identity, configuration, registry, plans, Evidence, dependencies, temporal boundaries, policy,
numeric environment, controlled randomness where permitted, and external-input manifests.

### Environmental Manifest

The immutable declaration of every environment property allowed to influence a governed result,
including numeric model, precision, rounding, architecture constraints, runtime contract, locale,
timezone prohibition, dependency versions, and approved external execution class.

### Observable Behaviour

Any behavior or artifact visible to a producer consumer, downstream Invocation, handoff, audit,
certification, replay comparison, governance authority, or contractually defined operator
interface.

### Non-observable Behaviour

Physical or operational variation explicitly excluded from semantic and authoritative contracts,
such as CPU scheduling or memory address, provided it cannot influence Observable Behaviour.

### Strict Equivalence

Equality of all canonical artifacts and authoritative events required by a profile, including exact
identities, ordering, diagnostics, transitions, and represented values. Explicitly excluded raw
operational telemetry MAY differ.

### Semantic Equivalence

Equality of semantic meaning, Evidence, dependencies, temporal scope, completeness, provenance,
semantic diagnostics, committed result, and EPIP-016 handoff obligations under one Semantic Plan.

### Operational Equivalence

Equality of authoritative operational lifecycle and outcome under one Dispatch Plan or certified
equivalent Dispatch Plans, excluding physical timing and placement unless the profile includes
them.

### Replay Equivalence

Equality required by one declared replay mode between original and replay artifacts. Its exact
scope is governed by ADR-EPIP017-11.

### Certification Equivalence

Equality of certification-relevant facts and verdict under one Certification Profile. It does not
mean all physical execution details were identical.

### Equivalent Execution

Two executions that satisfy the equivalence relation required by their shared profile and preserve
the same authoritative semantic obligations. Equivalent does not necessarily mean byte-identical
raw telemetry.

### Unexpected Variability

Any difference not explicitly allowed by the applicable Determinism Profile.

## Determinism Model

EPIP SHALL classify determinism into independent guarantees.

### Governance Determinism

Identical governance manifests and policy versions MUST derive identical eligibility,
certification standing, authority decisions, and registry snapshots.

### Planning Determinism

Identical Planning Input Manifests and planner-policy versions MUST derive identical Semantic Plans,
dependency graphs, selections, semantic diagnostics, and canonical ordering.

### Dispatch Determinism

Identical Semantic Plan, Dispatch Request, dispatch-admission facts, operational-policy versions,
and declared resource classes MUST derive identical Dispatch Plans. Mutable runtime outcomes are
not dispatch-planning inputs.

### Producer Determinism

Identical complete Invocation Context and producer profile inputs MUST derive equivalent producer
outputs, semantic metadata, semantic diagnostics, and failure classifications according to the
producer's certified Determinism Profile.

### Result Determinism

Equivalent eligible Attempt Results under identical commit predicates MUST yield the same
authoritative committed result and Commit Record identity scope.

### Authority Determinism

Identical authoritative lifecycle facts and policies MUST yield identical legal transitions,
lease/fence/token validity, commit eligibility, winning terminal authority, and authoritative
ledger projection.

### Ordering Determinism

Every semantic, collection, diagnostic, transition, and authority order that affects Observable
Behaviour MUST use an explicit canonical rule. Physical execution order MUST NOT substitute for
canonical order.

### Diagnostic Determinism

Semantic and authority diagnostics MUST be deterministic for identical complete inputs. Operational
diagnostics MAY include variable measurements but MUST preserve stable codes, causality, scope, and
classification and MUST NOT alter semantic or authority outcomes.

### Certification Determinism

Identical certification inputs, profile, environment, evidence set, and authority facts MUST yield
the same certification verdict and deterministic findings. Human exceptions MUST be explicit
governance actions rather than hidden variability.

## Deterministic Artifacts

Under every profile that permits authoritative or certification use, the following MUST be
reproducible according to the stated equivalence:

### Semantic Plan

The exact Semantic Plan MUST be strictly reproducible from its complete Planning Input Manifest.

### Dispatch Plan

The exact Dispatch Plan MUST be strictly reproducible from its complete Dispatch Request and
dispatch-admission facts. Different equivalent Dispatch Plans MUST remain distinct artifacts and
MUST NOT claim strict equivalence.

### Evidence

Evidence identity, meaning, value representation, metadata, semantic diagnostics, provenance,
temporal facts, completeness, and validity MUST satisfy the producer's required semantic or strict
equivalence profile.

### Dependencies

Requirements, candidate sets, selections, rejected alternatives, graph nodes and edges, optional
and conditional outcomes, compatibility, conflicts, and canonical order MUST be strictly
reproducible from planning inputs.

### Execution Ledger

Authoritative lifecycle entries, causality, legal transitions, authority decisions, commit facts,
and canonical authoritative ledger projection MUST be reproducible from the same authoritative
event inputs.

Raw operational observations MAY vary across independent execution and MUST be stored in a
separate observational projection or explicitly marked non-semantic. Exact raw-ledger reproduction
MUST be required only by an operational reproduction profile using the same recorded events.

### Commit Records

Commit eligibility, authoritative winner, committed-result binding, fence generation, transition,
and downstream visibility MUST be strictly reproducible from identical authoritative commit inputs.

### Lifecycle Transitions

Legal-state validation and authoritative transitions MUST be strictly reproducible. Physical
transition observation times MAY vary but MUST NOT change transition authority.

### Snapshots and Checkpoints

Snapshot semantic content and authoritative state MUST be reproducible from their declared source
boundary. Checkpoint operational state MUST satisfy the profile and consistency rules of
ADR-EPIP017-12.

### Diagnostics

Semantic, planning, contract, authority, and certification diagnostics MUST be strictly
reproducible. Variable operational measurements MUST be excluded from strict diagnostic identity.

### Ordering Rules

Every ordering rule that affects identity, semantics, authority, diagnostics, result collection, or
certification MUST be explicit, versioned, canonical, and reproducible.

### Authority Decisions

Registry eligibility, selection authority, attempt authorization, lease/fence/token validation,
commit, cancellation race resolution, revocation scope, and certification verdict MUST be
reproducible from the same complete authority facts and policies.

## Non-deterministic Artifacts and Elements

The following MAY vary only when excluded by the applicable profile and prevented from affecting
semantic or authoritative outcomes:

- CPU scheduling;
- thread interleaving and execution order;
- machine speed and load;
- physical wall-clock observation time;
- memory addresses and object identity;
- operating-system process and thread identifiers;
- execution, queue, network, storage, and lock latency;
- worker host, region, process, or location;
- transient resource utilization;
- telemetry delivery order;
- log formatting that carries no unique semantic meaning;
- retry delay observation where retry authority and result semantics remain unchanged;
- benchmark measurements.

Variable elements MUST be isolated from producer analytical inputs, canonical ordering, semantic
identity, Evidence, dependency selection, temporal meaning, authority, commit winner, handoff,
replay semantics, and certification verdict.

An element not explicitly classified as permitted variability MUST be treated as unexpected
variability and MUST fail the relevant certification profile.

## Execution Profiles

Every run MUST declare exactly one Execution Profile version. A profile SHALL impose a minimum
Determinism Profile and MAY impose stricter domain-specific obligations.

### Institutional Profile

The Institutional Profile SHALL govern production-authoritative Evidence eligible for EPIP-016.

It MUST require:

- Trusted, Certified, Enabled producers and frozen governance;
- strict planning and authority determinism;
- semantic producer and result equivalence at minimum;
- canonical committed Evidence and diagnostics;
- no uncontrolled randomness, ambient time, or undeclared external state;
- certified numeric and environmental boundaries;
- immutable ledger, result, and audit artifacts;
- failure closed on unexpected variability;
- certified handoff completeness.

### Certification Profile

The Certification Profile SHALL evaluate conformance and MUST be at least as strict as the profile
being certified.

It MUST require:

- complete preserved inputs and environmental manifests;
- repeated and independently attributable executions;
- strict comparison of required artifacts;
- serial and applicable parallel comparisons;
- negative and perturbation campaigns;
- deterministic verdicts and diagnostics;
- no waiver outside explicit governance.

Certification execution MUST NOT produce production-authoritative Evidence unless separately
admitted under the Institutional Profile.

### Replay Profile

The Replay Profile SHALL require the determinism and equivalence contract selected by one governed
replay mode. It MUST preserve semantic authority and future-knowledge prohibitions. Exact replay
mode rules remain in ADR-EPIP017-11.

### Historical Profile

The Historical Profile SHALL govern historical recomputation from facts knowable at the declared
Historical and Knowledge Boundaries.

It MUST require semantic equivalence, original temporal and governance interpretation, explicit
historical ambiguity, and prohibition of latest-known-data substitution. It MUST NOT claim exact
operational reproduction unless that separate profile is selected.

### Simulation Profile

The Simulation Profile SHALL permit synthetic inputs only when explicitly admitted and identified.
It MUST preserve deterministic planning, authority, semantic output, and canonical ordering under
the selected deterministic simulation seed and model versions. Simulation outputs MUST NOT be
presented as observed Primary Evidence or Institutional results.

### Development Profile

The Development Profile MAY permit incomplete certification, additional diagnostics, and
non-authoritative producers. It MUST still preserve plan immutability, authority boundaries,
Evidence immutability, lifecycle legality, and explicit variability classification.

Development output MUST NOT enter authoritative handoff or certify another profile.

### Testing Profile

The Testing Profile MAY use controlled fixtures, fault injection, synthetic clocks, and governed
deterministic randomness. Every such input MUST be explicit and reproducible. Testing MUST preserve
the contract being tested and MUST NOT silently bypass authority or invariants.

### Benchmark Profile

The Benchmark Profile MAY observe variable timing, throughput, memory, CPU, and resource metrics.
It MUST use a frozen semantic workload, identify environment and warm-up policy, separate measured
telemetry from semantic artifacts, and verify that benchmark instrumentation does not change
semantic or authoritative outcomes.

Benchmark results are observational and MUST NOT become Evidence unless a separately admitted
capability defines that semantic use.

### Profile Compatibility

A run from a weaker profile MUST NOT be promoted to a stronger profile retrospectively. A stronger
profile MAY satisfy a weaker profile only through an explicit directional compatibility decision.
Profile change MUST create a new run and execution identity.

## Certification Profiles

Every Certification Profile MUST define:

- exact subject Execution and Determinism Profiles;
- complete authoritative input inventory;
- required environmental manifests;
- permitted and prohibited variability;
- required equivalence relations per artifact;
- comparison scope and canonical projections;
- execution repetitions and independent environments;
- serial, parallel, cached, uncached, failure, and recovery variants where applicable;
- numeric exactness or explicitly governed tolerance;
- diagnostic and authority expectations;
- statistical treatment of observational benchmark data without weakening semantic equality;
- expiration, recertification, revocation, and incompatibility triggers;
- immutable evidence and verdict schema.

Certification MUST fail when:

- a required input cannot be reconstructed;
- variability is unexplained or unclassified;
- a semantic or authority artifact differs outside permitted equivalence;
- environment influences a prohibited outcome;
- comparison omits rejected, failed, empty, cancelled, or degraded cases;
- a tolerance is introduced without an approved numeric semantic contract;
- the profile, policy, producer, capability, environment, or canonicalization version differs from
  the certified scope.

Certification of one profile MUST NOT imply another profile.

## Observable Behaviour

Observable Behaviour MUST include at minimum:

- registry and authority decisions relevant to the run;
- Semantic and Dispatch Plans;
- selected and rejected dependencies;
- producer Evidence, semantic metadata, semantic diagnostics, and failure classification;
- temporal visibility and completeness;
- Invocation and Attempt authoritative lifecycle transitions;
- Commit Record and committed-result identity;
- canonical result and diagnostic ordering;
- snapshot semantic state;
- handoff manifest and certification verdict;
- every fact designated authoritative by a frozen ADR.

Observable Behaviour MAY include operational telemetry, but such telemetry MUST be explicitly
classified and MUST NOT change semantic equivalence unless a profile intentionally treats the same
recorded telemetry as an operational reproduction input.

An implementation detail becomes observable if any consumer, audit, certification, or authority
decision can detect and depend on it. It MUST then be governed or removed from the dependency.

## Equivalent Execution

### Strict Equivalence

Strict equivalence SHALL apply when exact canonical reconstruction is required for plans,
dependencies, authority facts, semantic diagnostics, Evidence representation, lifecycle decisions,
and Commit Records. It excludes only artifacts explicitly outside the strict projection.

### Semantic Equivalence

Semantic equivalence SHALL require the same Semantic Plan obligations, Evidence meaning and values,
dependencies, provenance, temporal scope, completeness, semantic diagnostics, committed result,
and handoff eligibility. Different workers, timings, attempts, or equivalent Dispatch Plans MAY be
permitted.

### Operational Equivalence

Operational equivalence SHALL require the same authorized lifecycle semantics, terminal
disposition, commit authority, failure classifications, and operational-policy outcomes. Physical
timing and placement MAY differ unless explicitly included.

### Replay Equivalence

Replay equivalence SHALL be selected by ADR-EPIP017-11 and MUST state whether strict, semantic, or
operational facts are reproduced. No run may claim replay equivalence without naming the mode and
profile.

### Certification Equivalence

Certification equivalence SHALL require identical certification-relevant facts and verdict under
the same Certification Profile. If two executions are semantically equivalent but expose different
forbidden variability, they MUST NOT be certification-equivalent.

### Comparison Rules

Equivalence comparison MUST include successful, valid-empty, rejected, invalid, failed, cancelled,
expired, aborted, stale, and degraded outcomes applicable to the profile. It MUST compare complete
sets and canonical ordering, not only a selected result.

## Determinism Boundaries

### Input Boundary

Every deterministic claim MUST enumerate all inputs capable of affecting its governed outcome.
Undeclared input access is a determinism violation.

### Time Boundary

Semantic time MUST use ADR-EPIP017-05. Operational lease and timeout observations MAY use an
authoritative operational clock only as explicit recorded inputs to authority decisions. Ambient
time MUST NOT influence semantics.

### Randomness Boundary

Institutional, Historical, and authoritative Replay profiles MUST prohibit uncontrolled randomness.
A profile permitting deterministic randomness MUST declare algorithm identity, seed, stream,
consumption contract, and scope as complete inputs. Random values MUST NOT grant authority or break
ties unless an ADR explicitly approves that semantic use.

### Numeric Boundary

Every producer and capability MUST declare its numeric semantic profile, including precision,
rounding, exceptional values, reduction ordering, and platform constraints. Floating-point
parallel reduction MUST NOT be assumed associative or equivalent. Unknown numeric variability MUST
fail certification.

### External Input Boundary

Every external read capable of affecting output MUST be captured as an immutable admitted input
with source, version, temporal availability, and content identity. Live mutable external state MUST
not enter deterministic execution.

### Environment Boundary

Environment variables, locale, timezone, filesystem order, hardware feature, library version, and
runtime defaults MUST NOT influence governed outcomes unless explicitly admitted in the
Environmental Manifest and certified.

### Scheduling Boundary

Scheduler and worker choices MAY alter permitted operational telemetry but MUST NOT alter semantic
results, authority, commit history, or certification. Parallel execution MUST satisfy
ADR-EPIP017-14.

### Cache Boundary

Cache availability is operational and MUST NOT change semantic intent. Cached and freshly computed
committed results MUST satisfy the equivalence required by ADR-EPIP017-10.

## Determinism Authority

- The Architectural Authority SHALL own this constitutional determinism taxonomy.
- The Determinism Profile Authority SHALL own immutable profile definitions and allowed
  variability.
- The Producer Owner SHALL declare producer inputs and conformance scope but MUST NOT self-certify.
- The semantic planning authority SHALL own deterministic plan derivation.
- The Dispatch Authority SHALL own deterministic dispatch-plan derivation.
- The Lifecycle and Commit Authorities SHALL own authoritative transition determinism.
- The Certification Authority SHALL issue determinism verdicts under exact Certification Profiles.
- The Replay Authority SHALL select replay equivalence under ADR-EPIP017-11.
- The Audit Authority SHALL verify evidence and MUST NOT redefine equivalence after execution.

Every authority and profile version MUST follow ADR-EPIP017-03 governance. No runtime component MAY
self-declare a stronger profile.

## Determinism Invariants

1. Every deterministic claim names its complete inputs, profile, contract, and equivalence.
2. Same complete inputs produce the required equivalent outputs.
3. Execution timing never changes semantic meaning.
4. Scheduling never changes authority.
5. CPU, thread, worker, process, memory, and machine variation never changes committed semantics.
6. Semantic Plan reproducibility is independent of dispatch.
7. Dispatch Plan reproducibility is independent of runtime outcome.
8. Evidence and semantic diagnostics are deterministic under authoritative profiles.
9. Dependency and ordering rules are explicit and canonical.
10. Thread ordering never changes committed history.
11. Exactly one authoritative Commit remains invariant across equivalent execution.
12. Operational telemetry remains outside semantic identity.
13. Unexpected variability fails closed.
14. Hidden randomness and ambient time are prohibited.
15. External state is either immutable declared input or forbidden.
16. Numeric variability is explicit, bounded by contract, and certified.
17. Replay preserves the semantic behavior required by its declared profile.
18. Equivalent execution produces equivalent certification only when all certification facts match.
19. A weaker profile never becomes a stronger profile retrospectively.
20. Failed, rejected, cancelled, empty, and degraded outcomes participate in equivalence.
21. Determinism never means objective analytical truth.
22. Decision remains outside EPIP-017 determinism authority.

## Diagnostics

Diagnostics MUST use stable, versioned codes and distinguish at minimum:

- determinism-profile absence, mismatch, expiry, or incompatibility;
- incomplete deterministic input or Environmental Manifest;
- hidden randomness or random-stream divergence;
- ambient-time or temporal-boundary violation;
- machine, platform, locale, timezone, dependency, or environment influence;
- numeric precision, rounding, reduction-order, or tolerance violation;
- semantic, strict, operational, replay, or certification equivalence violation;
- canonical ordering violation;
- planning or dispatch reproducibility violation;
- Evidence, dependency, diagnostic, snapshot, lifecycle, ledger, or Commit Record divergence;
- authority or commit-winner divergence;
- unexpected variability;
- non-observable behavior leaking into Observable Behaviour;
- profile-strength promotion attempt;
- certification-evidence insufficiency.

Diagnostics MUST identify artifact, profile, equivalence relation, expected and observed canonical
facts, environmental manifests, authority, policy, and comparison scope. Variable measurements MAY
be attached but MUST NOT change deterministic diagnostic classification.

## Audit

Audit MUST preserve:

- Execution, Determinism, and Certification Profile identities and versions;
- complete input and Environmental Manifests;
- every declared permitted and prohibited variability;
- canonical artifacts and projections compared;
- equivalence relation and comparison scope;
- producer, capability, numeric, temporal, registry, plan, dispatch, and authority versions;
- serial, parallel, cached, replayed, failed, and recovered variants where applicable;
- all divergences, diagnostics, waivers, and governance actions;
- certification evidence, verdict, expiry, revocation, and recertification lineage;
- separation of operational telemetry from authoritative facts.

Audit MUST be capable of explaining why two differing physical executions are equivalent or why an
apparently equal terminal result is not equivalent. It MUST NOT redefine profiles after observing
results.

## Determinism Certification

Certification MUST verify at least:

1. Complete input enumeration and prohibition of hidden inputs.
2. Repeatability and independent reproducibility under required environments.
3. Semantic and strict plan reproducibility.
4. Evidence, dependency, metadata, semantic diagnostic, and ordering equivalence.
5. Authority, lifecycle, fence, Commit Record, and canonical-ledger equivalence.
6. Isolation from CPU scheduling, thread ordering, machine speed, worker placement, process identity,
   memory address, latency, and resource telemetry.
7. Clock, randomness, external-input, environment, and numeric boundaries.
8. Successful, empty, invalid, rejected, failed, cancelled, expired, aborted, stale, and degraded
   outcomes.
9. Equivalent serial and parallel execution where the profile claims it.
10. Cached and fresh-result equivalence where the profile claims it.
11. Replay equivalence where the profile claims it.
12. Certification-verdict determinism and diagnostic stability.

A nondeterministic producer MAY be used only in a non-authoritative profile explicitly permitting
its variability. Its output MUST NOT be promoted into an Institutional, Certification, Historical,
or authoritative Replay path.

## Migration

- Every existing source of time, randomness, identity, environment, ordering, external state, and
  numeric variability MUST be inventoried.
- Existing claims of determinism MUST be decomposed into planning, producer, result, authority,
  replay, and operational guarantees.
- Legacy tests comparing only terminal values MUST be insufficient for EPIP-017 certification.
- Legacy dictionary, set, filesystem, registration, callback, event, thread, and completion order
  MUST be classified and removed from semantic authority.
- Existing floating-point and aggregation behavior MUST receive explicit numeric profiles.
- Existing clocks and random generators MUST be declared, injected through approved contracts, or
  prohibited for authoritative profiles.
- External inputs MUST be captured with content, source, temporal, and governance identities.
- Shadow validation MUST compare complete plans, Evidence, dependencies, diagnostics, authority,
  lifecycle, commit, and handoff artifacts.
- Benchmark variability MUST remain observational and MUST NOT weaken semantic equivalence.
- Migration gaps MUST be diagnosed; they MUST NOT be repaired through undocumented tolerance.
- Legacy retirement and divergence governance MUST follow ADR-EPIP017-16.

## Backward Compatibility

This ADR changes no production behavior, public API, producer implementation, EPIP-016 contract,
Replay behavior, EventBus behavior, financial calculation, risk rule, portfolio behavior, execution
behavior, or serialization format.

Existing legacy determinism guarantees remain governed by their frozen ADRs until migrated. They
MUST NOT be relabeled as EPIP-017 profile conformance without certification.

EPIP-016 deterministic Evidence and Decision semantics remain unchanged. ADR-EPIP017-15 MUST prove
that EPIP-017 handoff preserves them without exposing operational variability.

Historical profile and certification records MUST remain interpretable after new profiles,
environments, numeric rules, or equivalence relations are introduced.

## Forbidden Behaviours

EPIP-017 MUST NEVER permit:

1. Hidden or uncontrolled randomness.
2. Ambient current time affecting semantic or authority decisions.
3. Machine-dependent semantic results.
4. Scheduler-dependent Evidence, authority, or commit outcomes.
5. Thread, process, worker, memory, hash, filesystem, discovery, registration, or completion order
   as implicit semantic ordering.
6. Environment-dependent decisions outside an explicit certified Environmental Manifest.
7. Floating-point equality or tolerance assumed without a numeric semantic profile.
8. Operational telemetry entering Semantic Plan, Evidence, Commit, or handoff identity.
9. Matching terminal values presented as sufficient equivalence.
10. A weaker Execution Profile promoted retrospectively to a stronger profile.
11. Development, Testing, Simulation, or Benchmark output entering authoritative handoff without a
    separately certified Institutional execution.
12. Certification by self-declaration or successful single execution.
13. Unexplained variability classified as harmless after results are observed.
14. Profile or equivalence rules changed retroactively.
15. Latest environment or dependency versions substituted during historical verification.
16. Raw ledger timing differences treated as semantic divergence when excluded by profile.
17. Authoritative ledger divergence dismissed as operational noise.
18. Replay equivalence claimed without a declared replay mode and profile.
19. Cache or retry behavior changing semantic equivalence.
20. Nondeterministic tie-breaking for producer, dependency, result, authority, or certification.
21. Decision, Candidate, Confidence, risk decision, or execution instruction created by a
    determinism profile.

Any forbidden behavior SHALL be an architecture and certification failure and MUST fail closed.

## Alternatives Considered

### Universal byte-for-byte determinism

Every log, timestamp, thread event, and telemetry value must be identical.

Rejected because physical execution varies and forcing false equality would either be impossible or
hide useful operational facts.

### Terminal-value determinism

Runs are deterministic when the final numerical values match.

Rejected because inputs, dependencies, provenance, diagnostics, authority, failures, and
completeness may differ materially.

### Best-effort reproducibility

Components attempt stable behavior but unexplained differences are tolerated.

Rejected because institutional Evidence and certification require explicit boundaries and
fail-closed variability.

### Deterministic serial execution only

Only serial execution may be considered deterministic.

Rejected as a permanent model because physical concurrency can preserve semantics under strict
isolation and canonical commitment. Serial execution remains a certification reference.

### Profile-scoped determinism with explicit equivalence

Each artifact declares complete inputs, required equivalence, permitted variability, and
certification rules.

Accepted because it makes credible guarantees without conflating semantic identity with physical
execution.

## Decision

EPIP SHALL adopt the determinism, reproducibility, profile, artifact, variability, equivalence,
context, authority, boundary, invariant, diagnostic, audit, certification, migration,
compatibility, and prohibition rules in this ADR as the constitutional determinism contract for
EPIP-017.

Every authoritative artifact and decision SHALL identify its applicable profiles and complete
inputs. No component MAY claim determinism without naming the equivalence relation it guarantees.

## Consequences

### Positive

- Determinism becomes precise and independently certifiable.
- Physical concurrency and timing can vary without changing semantics.
- Hidden environment, randomness, numeric, and ordering dependencies are prohibited.
- Plans, Evidence, authority, commit, diagnostics, and certification receive explicit guarantees.
- Replay and cache ADRs receive a stable equivalence vocabulary.
- Benchmark observations remain useful without contaminating semantic identity.
- Apparent equality cannot conceal different provenance or authority.

### Negative

- Every profile requires complete manifests and long-lived certification evidence.
- Numeric and environment compatibility require explicit governance.
- Raw telemetry cannot be used casually in deterministic identities.
- More than one equivalence relation must be understood and audited.
- Some existing producers may fail authoritative profiles despite stable nominal outputs.

### Trade-offs

EPIP accepts stricter input accounting and more nuanced equivalence in exchange for credible,
ten-year reproducibility rather than an untestable universal determinism claim.

## Non-goals

This ADR does not define:

- digest, hash, signature, or canonical serialization algorithms;
- replay modes, replay algorithms, or historical event reconstruction;
- implementation classes, APIs, comparators, clocks, random generators, workers, or schedulers;
- cache storage, reuse, invalidation, or eviction;
- retry, timeout, fallback, or recovery algorithms;
- parallel scheduling, fairness, backpressure, or worker topology;
- snapshot or checkpoint representation;
- EPIP-016 handoff representation;
- analytical formulas, trading, Decision, Candidate, Confidence, risk, portfolio, execution, or
  financial logic.

These exclusions MUST be resolved by their mandatory ADRs and MUST NOT be delegated to code.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 through ADR-EPIP017-07 and the frozen EPIP-016 and
H001–H007 architecture.

It creates or confirms mandatory dependencies on:

- ADR-EPIP017-09 for canonicalization, identity domains, digest hierarchy, algorithms, and version
  evolution;
- ADR-EPIP017-10 for cached versus fresh-result equivalence, content-addressed inputs, and
  invalidation determinism;
- ADR-EPIP017-11 for replay modes and exact replay-equivalence scopes;
- ADR-EPIP017-12 for deterministic snapshot projections and checkpoint operational state;
- ADR-EPIP017-13 for explicit timeout, retry, cancellation, fallback, and recovery facts within
  determinism profiles;
- ADR-EPIP017-14 for serial/parallel equivalence, numeric reduction ordering, isolation, fairness,
  and concurrency certification;
- ADR-EPIP017-15 for deterministic Evidence-set completeness and EPIP-016 handoff;
- ADR-EPIP017-16 for migration divergence, acceptance thresholds, rollback, and legacy retirement;
- ADR-EPIP017-17 for authoritative versus observational
  projections, retention, redaction, and comparison evidence;
- ADR-EPIP017-18 for environmental classes,
  operational clocks, resource profiles, and benchmark governance.

This ADR introduces the Determinism Profile Authority as an explicit governance role. It MUST use
ADR-EPIP017-03 ownership, separation, authenticity, lifecycle, and audit rules. No separate
governance model is required.

## Future Evolution

New Execution, Determinism, Certification, numeric, environment, or equivalence profiles MAY be
introduced through immutable versioned governance. Existing runs and certification records MUST
NOT be reinterpreted.

Hardware accelerators, distributed execution, probabilistic algorithms, machine learning,
controlled stochastic simulation, and alternative numeric models require explicit profiles and
certification. They MUST remain outside Institutional paths until equivalence, authority, replay,
and handoff guarantees are approved by ADR.

Future improvements MAY strengthen guarantees for new runs. They MUST NOT retroactively promote
historical weaker-profile outputs.

## Approval Gate

Approval of this ADR resolves the EPIP-017 determinism taxonomy, reproducibility contract,
execution profiles, equivalence model, and deterministic-identity foundations only.

It does not approve a digest engine, comparator, planner, scheduler, replay engine, cache, worker,
certification implementation, or Programme A.

EPIP-017 implementation remains prohibited until the complete mandatory ADR set is accepted and
the remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
