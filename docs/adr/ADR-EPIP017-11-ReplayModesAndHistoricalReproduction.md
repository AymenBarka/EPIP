# ADR-EPIP017-11 — Replay Modes and Historical Reproduction

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-10 are approved, frozen, and normative. This ADR MUST NOT
modify their orchestration authority, producer contract, governance, Evidence semantics, temporal
model, plan separation, execution lifecycle, determinism profiles, identity hierarchy, storage
authority, EPIP-016 boundary, or single-authoritative-path rule.

This ADR defines replay architecture only. It authorizes no implementation, Replay Engine,
historical analyzer, simulator, comparator, cache, store, interface, placeholder, or Programme A
activity.

## Executive Summary

EPIP-017 SHALL treat replay as a read-only, isolated, observational evaluation of preserved
authoritative artifacts under exactly one declared Replay Mode. Replay MUST NOT become production
execution, mutate authoritative history, create production Durable Results, alter plans, populate
or invalidate shared caches, or publish Evidence to EPIP-016.

A **Replay Session** SHALL have an independent identity, authority, context, lifecycle, ledger,
outputs, comparison rules, and retention. It SHALL reference original artifacts without replacing
their identities. Any recomputed artifact SHALL exist only in a replay-specific identity domain and
MUST remain non-authoritative.

EPIP SHALL distinguish at least eight Replay Modes:

- Historical Replay;
- Certification Replay;
- Operational Replay;
- Diagnostic Replay;
- Simulation Replay;
- Regression Replay;
- Explainability Replay;
- Migration Replay.

Historical Replay SHALL recompute semantic behavior from only the facts knowable at the historical
Knowledge Boundary. Operational Replay SHALL reproduce and validate recorded lifecycle and
authority outcomes from the original Dispatch Plan and Execution Ledger. These modes answer
different questions and MUST NOT be conflated.

Certification Replay SHALL independently test conformance under a frozen Certification Profile.
Diagnostic Replay SHALL investigate a bounded historical subject without altering its verdict.
Simulation Replay SHALL evaluate explicitly synthetic or counterfactual inputs and MUST NOT claim
historical fidelity. Regression Replay SHALL compare governed baselines. Explainability Replay
SHALL reconstruct explanations from preserved provenance without inventing reasoning. Migration
Replay SHALL compare legacy and target architectural interpretations without promoting either
result automatically.

Every Replay Session SHALL select one equivalence contract: strict, semantic, operational,
certification, historical, or another versioned relation approved by ADR. Differences SHALL be
reported, never repaired silently. Missing historical facts SHALL produce an inconclusive or failed
replay according to profile, never substitution with current state.

## Purpose

Establish the constitutional replay, historical reproduction, authority, identity, isolation,
equivalence, lifecycle, diagnostics, audit, certification, migration, and compatibility model for
EPIP-017.

This ADR defines:

- what replay means and explicitly does not mean;
- the supported Replay Modes and their contractual boundaries;
- replay authority, identity, scope, context, inputs, outputs, ledger, and report;
- historical recomputation versus operational reproduction;
- replay equivalence and deterministic comparison;
- immutable replay lifecycle and isolation from production state;
- treatment of missing, revised, migrated, or incompatible historical artifacts.

## Problem Statement

The original EPIP-017 proposal used replay to mean several incompatible activities:

- recomputing analytical results from historical inputs;
- reproducing the exact operational attempt history;
- rerunning certification;
- investigating failures;
- testing counterfactual inputs;
- comparing software versions;
- reconstructing explainability;
- validating migration.

These activities consume different inputs, permit different outputs, and require different
equivalence relations. A historical recomputation should not reproduce incidental worker timing. An
operational reproduction should not recalculate a timeout from current machine speed. A simulation
should not claim that its synthetic inputs were historically knowable. A diagnostic investigation
should not mutate the original result.

Without explicit modes and isolation, replay could:

- import current registry, code, cache, calendar, or revision state into the past;
- overwrite historical plans, results, ledgers, or certifications;
- create production Evidence from replay output;
- conceal divergence through hidden correction or fallback;
- treat revised-history analysis as original historical replay;
- mix operational and semantic equivalence;
- use mutable runtime state;
- contaminate production cache or invalidation state;
- replace original authority with a replay verdict.

Replay must therefore be observational, mode-specific, identity-separated, historically bounded,
and fail closed when required facts are unavailable.

## Architectural Context

ADR-EPIP017-01 makes replay a separate authority and prohibits it from rewriting planning,
execution, storage, audit, or EPIP-016 authority.

ADR-EPIP017-02 requires replay-eligible producers to consume only declared replay inputs and
prohibits ambient time, live state, and hidden cache.

ADR-EPIP017-03 preserves original registry snapshots, governance epochs, trust, certification, and
later revocation as separate facts.

ADR-EPIP017-04 requires historical Evidence semantics, dependency graph, candidate selection, and
provenance to remain versioned and reproducible.

ADR-EPIP017-05 defines Observation, Publication, Availability, Knowledge, Revision, Historical, and
Replay Time and prohibits future leakage.

ADR-EPIP017-06 separates Semantic Replay, Dispatch Replay, equivalent dispatch, and the Execution
Ledger.

ADR-EPIP017-07 requires immutable Invocation, Attempt, lease, fence, token, Commit, and lifecycle
history.

ADR-EPIP017-08 defines strict, semantic, operational, replay, and certification equivalence.

ADR-EPIP017-09 creates independent Replay Session, artifact, comparison, lineage, and digest
domains.

ADR-EPIP017-10 makes Durable Results authoritative and caches disposable, preventing replay from
using future or incompatible cache state.

This ADR composes those contracts into one replay constitution.

## Definitions

### Replay

A governed read-only evaluation of preserved authoritative facts and explicitly admitted replay
inputs for one declared purpose and Replay Mode.

### Replay Session

One immutable replay request, identity, mode, scope, context, input manifest, profile, lifecycle,
ledger, outputs, comparison, and authority lineage.

### Replay Mode

An immutable, versioned contract defining replay purpose, permitted authority, required inputs,
allowed evaluation, outputs, equivalence, prohibited artifacts, and certification rules.

### Replay Authority

The independent authority that admits a Replay Session, freezes its mode and inputs, controls its
observational lifecycle, and issues its Replay Report. It MUST NOT become the authority of original
artifacts.

### Replay Context

The immutable, least-privilege projection of historical, semantic, temporal, governance,
operational-record, environment, and profile facts permitted for one Replay Session.

### Replay Input Manifest

The complete immutable inventory of every artifact and policy visible to the Replay Session,
including versions, identities, availability, provenance, and missing-input declarations.

### Replay Scope

The exact original run, plan, graph, invocation, result, temporal boundary, diagnostic subject,
migration unit, certification subject, or other governed artifact set the Session may evaluate.

### Replay Projection

A mode-specific immutable view of original or replay-generated artifacts selected for comparison.
It MUST identify included and excluded facts.

### Replay Ledger

The append-only immutable history of Replay Session admission, preparation, observations,
evaluations, comparisons, diagnostics, verdicts, certification, cancellation, failure, and archival
facts. It is distinct from every original Execution Ledger.

### Replay Report

The immutable final report describing mode, authority, input sufficiency, execution profile,
comparison scope, equivalence verdict, differences, diagnostics, limitations, and certification
status.

### Replay Observation

A non-authoritative fact generated during replay about original or replay-generated artifacts.

### Replay Artifact

An immutable non-production artifact created inside the Replay Session's isolated identity and
storage scope. It MUST NOT replace an original artifact or become production Evidence.

### Replay Comparison

The immutable comparison between explicitly identified original and replay projections under one
equivalence relation.

### Replay Difference

One structured, attributable difference in content, identity, semantics, authority, temporal state,
ordering, diagnostics, lifecycle, or certification between compared projections.

### Historical Recomputation

Mode-governed recalculation from only the semantic inputs knowable at the declared historical
Knowledge Boundary. It creates replay artifacts, not original or production artifacts.

### Operational Reproduction

Mode-governed validation or re-enactment of recorded dispatch, attempt, authority, lifecycle, and
commit facts using preserved operational events. It does not infer original outcomes from current
machine timing.

### Replay Certification

An immutable Certification Authority attestation that one Replay Session satisfied one exact
Replay Certification Profile. It does not certify the original artifact beyond its declared scope.

## Replay Model

Every Replay Session MUST:

- declare exactly one Replay Mode and mode version;
- identify one Replay Authority and owner;
- bind one Replay Profile and applicable Determinism and Certification Profiles;
- freeze one complete Replay Input Manifest before evaluation;
- identify original artifacts and their authoritative identities;
- declare Historical Time, Replay Time, Knowledge Boundary, registry snapshot, temporal contracts,
  and revision view where applicable;
- declare one comparison projection and equivalence relation;
- isolate every replay-generated artifact from production authority and storage;
- preserve all missing, ambiguous, incompatible, revised, revoked, or destroyed input facts;
- append every lifecycle and comparison fact to its Replay Ledger;
- issue exactly one terminal Replay Report or structured failure.

Replay MAY execute certified analytical transformations within the isolated Replay Session when the
selected mode explicitly authorizes recomputation. Such activity is replay evaluation, not
production execution. It MUST use replay-specific Invocations, Attempts, plans where required,
ledgers, identities, and non-authoritative result domains.

Replay MUST NOT claim that a replay-generated artifact existed historically merely because it is
semantically equivalent to an original artifact.

## Replay Modes

### Historical Replay

**Purpose:** Recompute semantic behavior from facts knowable at one declared Historical and
Knowledge Boundary.

**Authority:** Replay Authority using the Historical Execution Profile and original historical
governance and temporal authorities.

**Required inputs:** Historical Semantic Plan or complete Planning Input Manifest, registry
snapshot, capability and producer versions, historical context, original availability and revision
facts, dependencies, calendars, timeframes, policies, and required Durable Results.

**Allowed outputs:** Replay Evidence, Semantic Plan reconstruction, dependency graph, semantic
diagnostics, Replay Comparison, differences, and Replay Report in replay-only domains.

**Forbidden inputs and outputs:** Current mutable state, later knowledge, latest-only revisions,
future caches, current registry substitution, production Durable Results, EPIP-016 handoff, or
claims of exact operational reproduction.

Historical Replay MUST fail or report historical inconclusiveness when required historical facts
cannot be reconstructed. It MUST NOT use corrected current history unless the Session is explicitly
classified under a different revised-history policy within a separately governed Replay Mode
version.

### Certification Replay

**Purpose:** Independently reproduce certification-relevant artifacts and verdicts under one frozen
Certification Profile.

**Authority:** Replay Authority and independent Certification Authority.

**Required inputs:** Original certification subject, evidence, profiles, environments, plans,
results, diagnostics, authority facts, and certification versions.

**Allowed outputs:** Certification Replay artifacts, comparison, deterministic findings, Replay
Report, and separate Replay Certification.

**Forbidden inputs and outputs:** Self-certification, altered acceptance criteria, missing-test
substitution, production activation, modification of original certification, or retrospective
waiver.

Certification Replay MUST distinguish reproduction of the original verdict from certification
under a newer profile. A newer profile creates a separate certification subject and lineage.

### Operational Replay

**Purpose:** Reproduce or validate recorded dispatch, Invocation, Attempt, lease, fence, token,
cancellation, failure, Commit, and authoritative ledger behavior.

**Authority:** Replay Authority using preserved operational records and the original authority
profiles.

**Required inputs:** Original Semantic and Dispatch Plans, Execution Ledger, authoritative event
facts, Invocations, Attempts, leases, fences, Commit Records, operational policy and environment
manifests, and Durable Results.

**Allowed outputs:** Replay Ledger, authoritative-projection comparison, lifecycle diagnostics,
operational differences, and Replay Report.

**Forbidden inputs and outputs:** Recalculation of original timeout or race outcomes from current
machine speed, mutation of the original ledger, new production Commit, current scheduler state, or
claim of semantic recomputation unless separately selected in another Session.

Operational Replay MUST reproduce recorded authority decisions from preserved authoritative event
inputs. Physical thread interleaving, host, and elapsed time need not be re-enacted unless the
original profile explicitly recorded and included them.

### Diagnostic Replay

**Purpose:** Investigate a bounded historical failure, divergence, lifecycle fact, Evidence result,
or diagnostic subject.

**Authority:** Replay Authority under an approved diagnostic scope and access policy.

**Required inputs:** Exact subject artifacts, original plans, relevant ledger segments, Durable
Results, diagnostics, profiles, and provenance.

**Allowed outputs:** Replay observations, expanded diagnostics, causal analysis, differences, and
Replay Report.

**Forbidden inputs and outputs:** Modification of original diagnostics or verdicts, production
repair, hidden input expansion, unrestricted data exploration, or promotion of investigative output
to Evidence.

Diagnostic Replay MAY add observations but MUST preserve original facts and clearly identify every
inference.

### Simulation Replay

**Purpose:** Evaluate synthetic, counterfactual, fault-injected, or alternative governed inputs
against a historical or recorded baseline.

**Authority:** Replay Authority under the Simulation Execution Profile.

**Required inputs:** Explicit baseline, synthetic-input manifest, simulation model and seed where
applicable, altered assumptions, policies, and comparison scope.

**Allowed outputs:** Simulation-only Evidence, plans, results, diagnostics, comparisons, and Replay
Report with synthetic classification.

**Forbidden inputs and outputs:** Claims of historical truth, original knowledge, production
authority, original replay equivalence, EPIP-016 handoff, or hidden replacement of baseline inputs.

Every simulated difference MUST be attributable to an explicit synthetic or counterfactual input.

### Regression Replay

**Purpose:** Detect unintended behavioral change between one governed baseline and one candidate
contract, producer, policy, environment, or architecture version.

**Authority:** Replay Authority under a versioned Regression Profile.

**Required inputs:** Baseline artifacts, candidate versions, complete input manifests, equivalence
rules, expected-difference declarations, and acceptance criteria.

**Allowed outputs:** Baseline and candidate projections, structured differences, regression verdict,
diagnostics, and Replay Report.

**Forbidden inputs and outputs:** Updating the baseline because the candidate differs, suppressing
unexpected differences, production promotion, or mixing profiles without separate Sessions.

Expected differences MUST be declared before comparison and MUST remain auditable.

### Explainability Replay

**Purpose:** Reconstruct and verify why Evidence was produced, selected, rejected, committed, or
handed off using preserved provenance and authoritative reasoning artifacts.

**Authority:** Replay Authority under an Explainability Profile.

**Required inputs:** Original Semantic Plan, dependencies, Evidence, diagnostics, rejected
alternatives, producer semantic trace facts, Commit Record, handoff manifest, and relevant audit
artifacts.

**Allowed outputs:** Explainability projection, provenance graph, missing-explanation diagnostics,
comparison, and Replay Report.

**Forbidden inputs and outputs:** Invented rationale, current-policy reinterpretation, new Decision,
new Confidence, altered original explanation, or narrative unsupported by preserved provenance.

Explainability Replay MUST distinguish recorded facts from replay-derived observations.

### Migration Replay

**Purpose:** Compare legacy and target architectural interpretations, artifacts, plans, results, and
authority during governed migration.

**Authority:** Replay Authority and Migration Authority under ADR-EPIP017-16.

**Required inputs:** Legacy artifacts and contracts, target ADR profiles, mappings, migration
manifests, known gaps, temporal and identity versions, and acceptance criteria.

**Allowed outputs:** Legacy and target projections, compatibility findings, divergences, historical
ambiguities, rollback evidence, and Replay Report.

**Forbidden inputs and outputs:** Silent legacy reinterpretation, automatic identity migration,
automatic production promotion, baseline rewriting, or concealment of missing historical facts.

Migration Replay MUST preserve each side's original authority and identity.

## Replay Authority

- The Replay Mode Authority SHALL own immutable Replay Mode definitions and permitted equivalence.
- The Replay Authority SHALL admit, configure, prepare, isolate, execute observational evaluation,
  compare, report, cancel, fail, and archive Replay Sessions.
- Original Registry, Producer, Plan, Execution, Commit, Durable Result, and Handoff Authorities SHALL
  remain authoritative for original artifacts.
- The Certification Authority SHALL issue Replay Certification when requested by profile.
- The Audit Authority SHALL verify Replay Session conformance without changing replay or original
  facts.
- The Migration Authority SHALL govern Migration Replay acceptance and rollback under
  ADR-EPIP017-16.

The Replay Authority MUST NOT create production authority, replace an original authority, mutate
original state, self-certify, or select a different Replay Mode after Session acceptance.

## Replay Identity

Every Replay Session MUST have an identity independent from:

- original run;
- original Semantic and Dispatch Plans;
- original Invocations and Attempts;
- original Execution Ledger;
- original Evidence and Durable Results;
- replay-generated plans, attempts, results, diagnostics, and ledger;
- Replay Report, Comparison, Difference, Validation, and Certification identities.

Replay Session identity MUST bind mode, scope, authority, original-artifact references, Replay
Input Manifest, context, profiles, equivalence, environment, and lifecycle schema under
ADR-EPIP017-09.

A changed mode, scope, input, historical boundary, profile, equivalence relation, expected
difference, or authority MUST create a new Replay Session identity.

## Replay Lifecycle

### Replay States

- **Created** — Replay Session identity and requested mode exist but are not admitted.
- **Configured** — scope, mode, profiles, equivalence, authority, and requested inputs are frozen.
- **Prepared** — input sufficiency, identity, temporal visibility, isolation, and compatibility are
  validated.
- **Executing** — authorized observational evaluation is active in replay isolation.
- **Completed** — evaluation ended and immutable replay outputs are available for comparison.
- **Compared** — required original and replay projections were compared and differences recorded.
- **Certified** — independent Replay Certification was issued when required.
- **Cancelled** — replay authority ended the Session without successful terminal report.
- **Failed** — preparation, execution, comparison, or report requirements failed.
- **Archived** — terminal replay artifacts and ledger are retained under policy.

### Legal Transitions

- Created SHALL transition only to Configured, Cancelled, or Failed.
- Configured SHALL transition only to Prepared, Cancelled, or Failed.
- Prepared SHALL transition only to Executing, Cancelled, or Failed.
- Executing SHALL transition only to Completed, Cancelled, or Failed.
- Completed SHALL transition only to Compared, Cancelled, or Failed.
- Compared SHALL transition to Certified when certification is required and succeeds, directly to
  Archived when certification is not required, or to Failed.
- Certified SHALL transition only to Archived.
- Cancelled and Failed SHALL transition only to Archived.
- Archived SHALL be terminal.

A Replay Session MUST NOT change mode or scope through a lifecycle transition. Illegal, skipped,
backward, or duplicate transitions MUST be rejected and recorded.

## Replay Context

Replay Context MUST be immutable, mode-specific, least privilege, and separate from production
Semantic, Execution, Operational, Scheduling, and Diagnostic Contexts.

It MUST identify:

- Replay Session, mode, scope, and profiles;
- original and replay identities;
- Historical Time, Replay Time, Knowledge Boundary, temporal and revision view;
- original registry snapshot and governance facts;
- producer, capability, implementation, configuration, and environment versions;
- permitted Durable Results, plans, ledgers, snapshots, checkpoints, diagnostics, and audit facts;
- comparison projection and equivalence relation;
- missing, destroyed, ambiguous, redacted, or inaccessible artifacts;
- security and redaction scope;
- replay-local working-artifact policy.

Replay Context MUST NOT contain mutable live registry, scheduler, worker, cache, portfolio,
execution, EventBus, environment, current-time, or production service references.

Replay-local working state MAY exist only inside the isolated Session and MUST be destroyed or
archived according to replay policy. It MUST NOT populate production or shared caches.

## Replay Inputs

Replay MAY consume immutable, authorized versions of:

- Durable Results and their manifests;
- Committed Results and Commit Records;
- Semantic Plans and Planning Input Manifests;
- Dispatch Plans and dispatch-admission facts;
- original Execution Ledger and authoritative projections;
- Snapshots and Checkpoints validated under ADR-EPIP017-12;
- registry snapshots, governance, trust, compatibility, and certification facts;
- Evidence, dependencies, provenance, and semantic diagnostics;
- calendars, timeframes, temporal mappings, availability, knowledge, revision, and watermark facts;
- Replay, Determinism, Execution, Certification, Migration, and comparison profiles;
- historical context and admitted external-input manifests;
- environment and numeric manifests;
- explicitly synthetic inputs where the mode permits them.

Every input MUST be listed in the Replay Input Manifest. Replay MUST NEVER consume mutable runtime
state, ambient current state, undeclared external services, hidden cache, latest-only configuration,
or implicit current policy.

Missing required inputs MUST be explicit. They MUST NOT be silently reconstructed from unrelated
current artifacts.

## Replay Outputs

Replay MAY produce only replay-domain artifacts, including:

- Replay Report;
- Replay Diagnostics;
- Replay Ledger;
- Replay Comparison;
- Replay Differences;
- Replay Observations;
- replay-specific plans, Invocations, Attempts, Evidence, results, and explainability projections
  when the selected mode permits evaluation;
- Replay Validation and Replay Certification;
- historical inconsistency, ambiguity, and input-sufficiency findings.

Every output MUST reference its Replay Session, mode, original subjects, inputs, profile,
equivalence, and non-authoritative status.

Replay outputs MUST NOT:

- overwrite or replace original artifacts;
- become production Durable Results;
- enter shared cache;
- release production dependency barriers;
- publish to EPIP-016;
- change original governance, certification, validity, or Commit;
- claim original historical existence;
- authorize retry, recovery, migration, activation, or deployment automatically.

Replay MAY generate observations. Observations MUST distinguish preserved fact, deterministic
derivation, inference, synthetic input, and comparison finding.

## Replay Equivalence

Every Replay Session MUST select exactly one primary equivalence relation and MAY report additional
secondary comparisons without changing the primary verdict.

### Strict Replay Equivalence

Strict Replay SHALL require canonical equality of every artifact and authoritative event included
by the Strict Replay Projection: plans, dependencies, Evidence, semantic diagnostics, authority
transitions, Commit Records, and other declared artifacts. Excluded operational telemetry MAY vary
only when the profile explicitly excludes it.

### Semantic Replay Equivalence

Semantic Replay SHALL require identical semantic obligations, Evidence meaning and values,
dependencies, provenance, temporal visibility, completeness, semantic diagnostics, committed
semantic result, and handoff eligibility. Operational attempts and equivalent Dispatch Plans MAY
differ.

### Operational Replay Equivalence

Operational Replay SHALL require the same authoritative Dispatch, lifecycle, attempt lineage,
lease/fence/token decisions, cancellation/failure classification, Commit winner, and authoritative
ledger projection from the same recorded operational inputs. Physical timing and location MAY be
excluded.

### Certification Replay Equivalence

Certification Replay SHALL require identical certification-relevant inputs, findings, profile,
authority decisions, and verdict. Semantic equality alone is insufficient if a certification
invariant differs.

### Historical Replay Equivalence

Historical Replay SHALL require semantic equivalence using only the facts visible at the declared
historical Knowledge Boundary and original semantic interpretation. It does not require exact
operational history.

### Comparison Rules

Replay comparison MUST:

- compare complete profile-defined projections, not terminal values only;
- preserve qualified identities and domain versions;
- include successful, valid-empty, invalid, rejected, failed, cancelled, expired, aborted, stale,
  degraded, and missing outcomes where applicable;
- distinguish missing comparison input from unequal output;
- distinguish expected from unexpected difference when expected differences were declared before
  execution;
- preserve canonical ordering and causality;
- never repair a difference during comparison;
- issue one immutable verdict: equivalent, divergent, inconclusive, failed, or not-applicable as
  permitted by profile.

## Replay Determinism

Given identical Replay Session request, mode, scope, Replay Input Manifest, original artifacts,
Replay Context, profiles, environment, comparison projection, and authority facts, replay MUST
produce identical:

- Session identity and lifecycle validation;
- visible input set and missing-input classification;
- replay-generated semantic artifacts under the selected Determinism Profile;
- Replay Ledger authoritative projection;
- comparison scope, differences, diagnostics, and verdict;
- Replay Report and Certification-relevant content.

CPU scheduling, thread ordering, machine speed, worker location, elapsed time, memory address, and
operational telemetry MUST NOT change replay semantics or verdict unless the Operational Replay
Profile explicitly consumes the same recorded observations.

Replay MUST use explicit logical Replay Time. Ambient current time MUST NOT determine historical
visibility, expiry, revision, authority, or comparison.

## Replay Isolation

Replay SHALL be observational and isolated.

Replay MUST NOT:

- mutate original history;
- mutate Semantic or Dispatch Plans;
- mutate original Execution or Audit Ledgers;
- mutate Durable Results, Commit Records, Evidence, Snapshots, or Checkpoints;
- read or mutate production or shared cache;
- create production cache entries;
- change registry, trust, certification, compatibility, lifecycle, or authority;
- invoke EPIP-016 production handoff;
- publish production EventBus events or execution actions;
- use live mutable portfolio, risk, execution, account, market, environment, or scheduler state;
- reuse production Invocation, Attempt, Lease, Fence, Token, or Commit identity;
- acquire production operational authority.

Replay-generated execution-like artifacts MUST use replay-specific domains, authorities, stores,
ledgers, security scopes, and lifecycle. They MUST remain non-authoritative outside their Session.

Replay cancellation or failure MUST affect only the Replay Session. It MUST NOT cancel, retry,
invalidate, or repair original or production work.

## Replay Invariants

1. Every Replay Session declares exactly one Replay Mode.
2. Replay is read-only with respect to original and production authority.
3. Replay authority is independent from original artifact authority.
4. Replay identity never replaces original identity.
5. Replay history and ledger are immutable and append-only.
6. Replay never creates production Durable Results or Evidence.
7. Replay never publishes to EPIP-016.
8. Replay never mutates or populates shared cache.
9. Replay never changes Semantic or Dispatch Plans.
10. Replay never rewrites original Execution Ledger or Commit history.
11. Replay uses only inputs in its immutable manifest.
12. Mutable runtime state never enters replay.
13. Future knowledge never enters Historical Replay.
14. Operational Replay uses recorded authority events, not current physical timing.
15. Simulation remains explicit and never claims historical truth.
16. Explainability Replay never invents rationale.
17. Migration Replay preserves both identity domains and authorities.
18. Missing historical facts remain missing or inconclusive.
19. Replay differences are reported and never silently corrected.
20. Replay equivalence always names one mode, profile, and projection.
21. Replay never becomes production execution.
22. Decision remains outside EPIP-017 Replay Authority.

## Replay Diagnostics

Diagnostics MUST use stable, versioned codes and distinguish at minimum:

- Replay Mode, profile, scope, authority, or lifecycle mismatch;
- missing, inaccessible, destroyed, redacted, ambiguous, or incompatible replay input;
- historical Knowledge, availability, revision, calendar, or registry inconsistency;
- original-versus-replay identity or domain mismatch;
- canonicalization or digest mismatch;
- strict, semantic, operational, certification, or historical replay divergence;
- unexpected replay result or expected-difference mismatch;
- mutable runtime state or future-knowledge injection;
- cache contamination or production mutation attempt;
- mixed Replay Modes or equivalence projections;
- hidden recomputation, correction, substitution, migration, or fallback;
- original authority replacement attempt;
- ledger, lifecycle, ordering, causality, Commit, or diagnostic mismatch;
- replay-generated artifact escaping isolation;
- inconclusive replay due to insufficient historical facts;
- Replay Report or Certification inconsistency.

Every diagnostic MUST identify Session, mode, scope, original and replay artifacts, profiles,
Historical and Replay Time, Knowledge Boundary, authorities, comparison path, expected and observed
facts, and reason. Diagnostics MUST NOT repair, rerun, migrate, or certify automatically.

## Replay Audit

Audit MUST preserve:

- Replay Session request, identity, owner, authority, mode, scope, and lifecycle;
- complete Replay Context and Input Manifest;
- original and replay qualified identities and lineage;
- historical Knowledge, temporal, revision, governance, and environment facts;
- every replay-generated artifact and its non-authoritative classification;
- complete Replay Ledger and causal sequence;
- projections, equivalence relations, expected differences, comparisons, and verdicts;
- all diagnostics, ambiguities, missing inputs, divergences, failures, and cancellations;
- Replay Report, Validation, Certification, expiry, and revocation;
- proof of isolation from production stores, caches, ledgers, plans, handoff, and authority.

Audit MUST distinguish original fact, replay observation, recomputed artifact, synthetic input,
inference, migration mapping, and certification verdict. It MUST NOT infer historical truth from a
successful simulation or semantic equivalence from matching terminal values alone.

## Replay Certification

Certification MUST verify at least:

1. Exact Replay Mode, authority, scope, profile, and identity.
2. Complete immutable Replay Context and Input Manifest.
3. Historical Knowledge and future-leakage controls.
4. Original identity, profile, registry, temporal, revision, and governance preservation.
5. Isolation from production execution, cache, storage mutation, EventBus, and EPIP-016 handoff.
6. Separate replay-specific plans, Invocations, Attempts, results, ledger, and identities.
7. Mode-specific permitted and forbidden inputs and outputs.
8. Strict, semantic, operational, certification, and historical comparison correctness.
9. Inclusion of non-success terminal outcomes and complete diagnostics.
10. Missing-input, historical-ambiguity, revision, revocation, migration, and destruction behavior.
11. Deterministic Replay Report, Comparison, Difference, and verdict.
12. No hidden correction, fallback, profile mixing, or authority replacement.
13. Cancellation and failure isolation.
14. Long-term reconstruction under original schema and identity profiles.

Certification MUST use real historical revisions, late arrivals, failed Attempts, cancellation and
Commit races, missing artifacts, cache eviction, archived Durable Results, profile evolution, and
migration divergence. Nominal successful replay is insufficient.

## Migration

- Every legacy replay activity MUST be classified by actual purpose into one Replay Mode.
- Existing systems mixing historical recomputation, operational reproduction, simulation,
  diagnostics, and regression MUST separate them into distinct Sessions.
- Legacy replay inputs MUST be inventoried for mutable state, latest-only data, hidden caches,
  current registry, current code, wall clock, random state, and unavailable revisions.
- Legacy outputs MUST be classified as original, replay-generated, synthetic, migrated,
  diagnostic, or ambiguous.
- Historical runs lacking Knowledge or Availability facts MUST be declared inconclusive where
  faithful replay cannot be proven.
- Existing replay that writes to production stores, caches, ledgers, EventBus, or EPIP-016 MUST be
  prohibited before certification.
- Legacy identities MUST remain separate from replay and migrated identities.
- Shadow replay MUST compare mode-specific complete projections and isolation evidence.
- Migration Replay MUST govern comparison and MUST NOT activate the target path automatically.
- Acceptance, rollback, divergence, and legacy retirement MUST follow ADR-EPIP017-16.

## Backward Compatibility

This ADR changes no production replay engine, public API, producer, EPIP-016 contract, EventBus
behavior, financial calculation, risk rule, portfolio behavior, execution behavior, cache, storage,
or serialization format.

Existing Replay remains governed by its legacy contracts until migrated and certified. It MUST NOT
be labeled EPIP-017 Historical, Operational, Certification, or other Replay without satisfying the
exact mode contract.

EPIP-016 replay and deterministic Decision semantics remain frozen. EPIP-017 Replay MUST NOT
replace them, publish replay Evidence into them, or reinterpret Decision history.

Historical Replay Sessions, input manifests, reports, differences, diagnostics, and certifications
MUST remain interpretable under their original mode, profile, schema, and identity versions.

## Forbidden Behaviours

EPIP-017 MUST NEVER permit:

1. History rewriting or original-artifact mutation.
2. Production result, ledger, plan, registry, certification, or authority mutation by replay.
3. Shared or production cache read or mutation outside an explicitly immutable authoritative input
   reference permitted by mode; Cache Entry state itself MUST NOT become replay input.
4. Replay-generated artifact promoted to production Durable Result or EPIP-016 Evidence.
5. Implicit recomputation when the mode does not authorize it.
6. Authority replacement by Replay Authority.
7. Hidden replay correction, fallback, substitution, migration, or repair.
8. Mutable runtime state injection.
9. Future knowledge, later revision, current registry, or current calendar injected into Historical
   Replay.
10. Mixed Replay Modes within one Session.
11. Replay Mode or equivalence change after Session acceptance.
12. Current machine speed used to reconstruct original timeout or race outcomes.
13. Simulation represented as historical fact.
14. Explainability narrative unsupported by preserved provenance.
15. Regression baseline rewritten because a candidate differs.
16. Missing historical input silently replaced by current data.
17. Replay identity reused as original run, result, Commit, or certification identity.
18. Replay cancellation or failure affecting production work.
19. Matching terminal values treated as complete replay equivalence.
20. Replay certification modifying original certification.
21. Replay producing Decision, Candidate, Confidence, risk decision, or execution action.

Any forbidden behavior SHALL be an architecture and certification failure and MUST fail closed.

## Alternatives Considered

### One universal replay mode

One mechanism reruns historical, operational, certification, simulation, diagnostic, and migration
activities under the same semantics.

Rejected because purposes, inputs, authority, equivalence, and outputs differ materially.

### Replay as production re-execution

Replay uses the production execution path and may write normal results and cache entries.

Rejected because it risks authority contamination, duplicate Commit, future leakage, and history
mutation.

### Latest-state historical replay

Historical replay uses current code, registry, calendar, revisions, and cache.

Rejected because it answers a revised-analysis question and cannot reproduce what was knowable.

### Recorded-output playback only

Replay merely reads prior outputs without recomputation or comparison.

Rejected as the complete model because it cannot certify semantic reproducibility, diagnose
divergence, or validate migration. It MAY be one operational observation inside a mode.

### Isolated, mode-specific observational Replay Sessions

Each Session freezes purpose, inputs, scope, equivalence, authority, outputs, and isolation.

Accepted because historical recomputation, operational reproduction, certification, simulation,
diagnostics, regression, explainability, and migration remain precise and non-authoritative.

## Decision

EPIP SHALL adopt the Replay Model, Modes, Authority, Identity, Lifecycle, Context, Inputs, Outputs,
Equivalence, Determinism, Isolation, Diagnostics, Audit, Certification, Migration, Compatibility,
and prohibition rules in this ADR as the constitutional replay model for EPIP-017.

Every Replay Session SHALL be isolated, read-only toward original and production authority, and
bound to exactly one Replay Mode. Replay SHALL remain observational and SHALL never become
production execution or rewrite authoritative history.

## Consequences

### Positive

- Historical recomputation and operational reproduction can no longer be confused.
- Replay cannot contaminate production storage, cache, plans, ledgers, or EPIP-016.
- Every replay claim names its purpose, inputs, scope, and equivalence.
- Missing historical facts produce explicit inconclusive results rather than fabricated fidelity.
- Simulation, diagnostics, regression, explainability, and migration remain independently governed.
- Original identities and authorities remain intact.
- Replay certification becomes reproducible and auditable.

### Negative

- EPIP must retain extensive historical, temporal, governance, plan, ledger, and identity artifacts.
- Multiple Replay Modes require separate profiles and certification.
- Some legacy history cannot receive faithful replay status.
- Operational reproduction requires durable authoritative event facts.
- Replay-generated artifacts require isolated storage and lifecycle governance.

### Trade-offs

EPIP accepts greater replay metadata, isolation, and mode complexity in exchange for eliminating
future leakage, authority replacement, historical rewriting, and ambiguous replay claims.

## Replay Invariants Summary

The invariants in this ADR are cumulative and normative. No Replay Profile, implementation,
migration, diagnostic request, or operational emergency MAY weaken them. Any future Replay Mode
MUST be at least as explicit about authority, inputs, outputs, isolation, and equivalence as the
modes defined here.

## Non-goals

This ADR does not define:

- Replay Engine, validator, simulator, comparator, storage, or scheduling implementation;
- implementation classes, APIs, interfaces, databases, queues, or protocols;
- snapshot or checkpoint consistency and restoration rules;
- retry, fallback, failure recovery, or production cancellation policy;
- parallel replay scheduling or worker topology;
- cryptographic algorithms or serialization formats;
- EPIP-016 handoff representation;
- analytical formulas, trading, Decision, Candidate, Confidence, risk, portfolio, execution, or
  financial logic.

These exclusions MUST be resolved by their mandatory ADRs and MUST NOT be delegated to code.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 through ADR-EPIP017-10 and the frozen EPIP-016 and
H001–H007 architecture.

It creates or confirms mandatory dependencies on:

- ADR-EPIP017-12 for Snapshot versus Checkpoint consistency, restore admission, replay inputs, and
  in-flight state;
- ADR-EPIP017-13 for original failure, timeout, retry, cancellation, fallback, and recovery facts
  and their replay treatment;
- ADR-EPIP017-14 for parallel replay isolation and serial/parallel equivalence without production
  authority;
- ADR-EPIP017-15 for proving replay does not enter EPIP-016 handoff and for explainability
  provenance compatibility;
- ADR-EPIP017-16 for Migration Replay authority, acceptance, divergence, rollback, and legacy
  retirement;
- ADR-EPIP017-17 for Replay Ledger retention, Diagnostic Report,
  redaction, comparison evidence, and attestation;
- ADR-EPIP017-18 for replay resource isolation,
  bounded historical scope, archive availability, and retention obligations.

This ADR introduces the Replay Mode Authority as an explicit governance role. It MUST use
ADR-EPIP017-03 ownership, separation, authenticity, lifecycle, and audit rules. No new governance
model is required.

## Future Evolution

New Replay Modes MAY be introduced only through immutable versioned architecture defining purpose,
authority, inputs, outputs, isolation, equivalence, diagnostics, audit, and certification. Existing
Sessions MUST NOT be reclassified.

Revised-history analysis, forensic security replay, regulatory replay, distributed replay, and
probabilistic replay MAY evolve as separate governed modes. They MUST NOT weaken Historical Replay
or use production authority.

Future replay optimization MAY use replay-local ephemeral state, but that state MUST remain inside
the Session, non-authoritative, disposable, and excluded from production cache and history.

## Approval Gate

Approval of this ADR resolves EPIP-017 Replay Modes, Historical Reproduction, Replay Authority,
Identity, Equivalence, Determinism, and Isolation only.

It does not approve a Replay Engine, simulator, historical analyzer, regression framework,
certification implementation, cache, storage system, or Programme A.

EPIP-017 implementation remains prohibited until the complete mandatory ADR set is accepted and
the remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
