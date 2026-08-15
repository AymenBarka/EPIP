# ADR-EPIP017-05 — Temporal Availability and Cross-Timeframe Semantics

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-04 are approved, frozen, and normative. This ADR MUST NOT
modify their orchestration boundary, producer contract, governance model, Evidence semantics,
dependency model, EPIP-016 boundary, or single-authoritative-path rule.

This ADR defines temporal architecture only. It authorizes no implementation, clock, calendar,
planner, scheduler, replay mechanism, cache, interface, placeholder, or Programme A activity.

## Executive Summary

EPIP-017 SHALL use a multi-temporal model. Observation Time, Validity Time, Publication Time,
Availability Time, Knowledge Time, Revision Time, Expiration Time, Historical Time, and Replay Time
are independent architectural concepts. No timestamp may substitute for another without an
explicit, certified temporal contract.

Evidence MAY describe an old observation that arrives late. Its Observation Time remains old, its
Publication and Availability Times remain later, and no run with an earlier Knowledge Boundary may
consume it. This rule prevents future knowledge from contaminating historical computation.

Every temporal value SHALL identify a canonical instant or interval, precision, timezone basis,
calendar identity where applicable, boundary convention, and source authority. EPIP SHALL use
half-open intervals whose start is inclusive and end is exclusive. Display labels, local times, and
timezone aliases MUST NOT define semantic identity.

M1, M5, M15, M30, H1, and H4 are governed duration-based timeframe contracts aligned by an
explicit epoch and calendar/session policy. Daily, Weekly, and Monthly are calendar-based
timeframe contracts and MUST NOT be treated as fixed durations. Daylight-saving transitions,
holidays, shortened sessions, missing intervals, and market closures SHALL be resolved only by a
versioned Calendar Authority contract.

Cross-timeframe use SHALL require an explicit Temporal Mapping Contract declaring source and target
timeframes, alignment, window membership, closure, completeness, visibility, revision propagation,
and conflict behavior. Aggregation is an admitted producer capability, not planner behavior.
Inheritance between timeframes is prohibited unless an explicit compatibility contract authorizes
the exact use.

Revisions SHALL never mutate Evidence. Correction, replacement, and withdrawal create new immutable
temporal facts and lineage. Active plans SHALL retain their frozen availability and knowledge
boundaries; later arrivals and revisions require a new semantic plan identity.

## Purpose

Establish the constitutional definition of time for every EPIP-017 Evidence artifact, producer
input, dependency, semantic plan, dispatch authorization, result, snapshot, checkpoint, replay, and
EPIP-016 handoff.

This ADR defines:

- independent temporal dimensions and their authorities;
- when Evidence becomes visible, usable, obsolete, historical, expired, or invalid;
- canonical timeframe identities and interval boundaries;
- cross-timeframe alignment, aggregation, compatibility, and conflicts;
- late arrival, duplicate, revision, withdrawal, and missing-window semantics;
- rules preventing future leakage and historical rewriting;
- deterministic temporal diagnostics and certification.

## Problem Statement

One timestamp cannot represent when a fact occurred, when a source published it, when EPIP admitted
it, when a run could know it, when it was valid, or when it was revised. Conflating these concepts
causes look-ahead bias, replay divergence, stale evidence reuse, inconsistent higher-timeframe
aggregation, and silent historical rewriting.

Timeframe names alone are also insufficient. Daily, Weekly, and Monthly boundaries vary with
calendar, session, timezone, holidays, and daylight-saving rules. Even fixed-duration intervals
require an alignment origin and a policy for closures, gaps, provisional data, and revisions.

Without a frozen temporal contract, implementations could:

- use Publication Time as Observation Time;
- expose late evidence to a run that could not historically know it;
- aggregate an incomplete H1 interval from M15 inputs;
- treat Daily as twenty-four elapsed hours regardless of market calendar;
- convert timezones or timeframes implicitly;
- replace a historical artifact after correction;
- let runtime arrival change an accepted semantic plan;
- reuse a higher-timeframe artifact containing future lower-timeframe knowledge;
- infer interval completeness from wall-clock time;
- produce irreproducible replay results around revisions and daylight-saving transitions.

Temporal meaning must therefore be decided independently of scheduling, replay execution, and
cache implementation.

## Architectural Context

ADR-EPIP017-01 separates semantic planning from operational execution and prohibits runtime state
from changing semantic meaning.

ADR-EPIP017-02 prohibits ambient time, hidden state, producer-owned dependency discovery, and
undeclared external inputs. Producers consume only the temporal boundary granted in an immutable
input manifest.

ADR-EPIP017-03 requires immutable registry snapshots, versioned governance, authentic authority,
and deterministic certification inputs.

ADR-EPIP017-04 defines Evidence as an immutable semantic claim and requires temporal semantics,
compatibility, completeness, and dependency presence to be explicit before execution.

This ADR supplies those temporal semantics. It does not define scheduling order, replay algorithms,
cache retention, snapshot persistence, or execution timeouts.

## Definitions

### Canonical Instant

An unambiguous point on the governed EPIP time scale with declared precision. A Canonical Instant
MUST be independent of display timezone and locale.

### Canonical Interval

An interval identified by one inclusive start instant and one exclusive end instant. Empty,
negative, or inverted intervals are invalid.

### Temporal Boundary

The immutable set of observation, availability, knowledge, calendar, timeframe, revision, and
visibility constraints admitted for a semantic plan or Evidence artifact.

### Observation Time

The instant or interval in the authoritative source domain at which the observed phenomenon
occurred or to which the claim refers.

### Validity Time

The interval during which the Evidence claim is semantically applicable to its declared subject
under its capability contract. Validity Time MAY differ from Observation Time.

### Publication Time

The authoritative instant at which the source declared a specific immutable publication or
revision artifact. Publication does not imply EPIP availability or validity.

### Availability Time

The earliest governed instant or logical boundary at which a specific publication artifact passed
the applicable source-boundary admission and became eligible for EPIP planning. Arrival alone does
not establish availability.

### Knowledge Time

The earliest governed boundary at which a specific run context could legitimately know an Evidence
artifact after considering publication, availability, required validation, dependency knowledge,
and temporal policy. Knowledge Time is run- and policy-relative but MUST be derived from immutable
facts.

### Revision Time

The publication and availability boundary of a new immutable correction, replacement, or withdrawal
related to an earlier artifact. Revision Time MUST NOT mutate the earlier artifact.

### Expiration Time

The explicit logical boundary after which an Evidence artifact is no longer eligible for a stated
use under a versioned policy. Expiration MUST NOT be inferred from ambient wall-clock time.

### Historical Time

The logical boundary from whose knowledge perspective historical visibility and admissibility are
evaluated. Historical Time MUST identify the governing calendar, availability, revision, and policy
state.

### Replay Time

The replay authority's current logical position. Replay Time controls which recorded or historical
facts may be exposed under a replay mode; it MUST NOT rewrite Observation, Publication,
Availability, Knowledge, Revision, or Validity Time.

### Timeframe

An immutable, versioned contract defining interval formation, alignment, calendar or session
authority, closure, completeness, and labeling. A timeframe name without its contract identity is
not a complete semantic reference.

### Calendar

An immutable, versioned authority contract defining timezone rules, sessions, holidays, closures,
shortened sessions, week and month boundaries, and exceptional intervals for a declared market or
domain scope.

### Watermark

An immutable statement by an authoritative input boundary that data up to a specified availability
or observation boundary satisfies a declared completeness policy. A watermark is evidence of
boundary completeness, not proof that no future revision will occur.

### Temporal Mapping Contract

An immutable, versioned semantic contract defining how Evidence in one timeframe may satisfy a
dependency in another timeframe.

### Late Arrival

An artifact whose Availability Time occurs after the expected availability boundary for its
Observation Time or target window. Late does not mean invalid.

### Stale Evidence

Evidence that remains structurally valid but no longer satisfies the freshness or validity
requirement of a specified consumer at its Knowledge Boundary.

## Temporal Model

Every Evidence artifact MUST declare or reference:

- Observation Time;
- Validity Time or an explicit rule establishing it;
- Publication Time;
- Availability Time;
- the derivation basis for Knowledge Time;
- Revision Time and lineage where revised;
- Expiration Time or an explicit non-expiring policy for the stated use;
- timeframe identity where interval-scoped;
- calendar identity where calendar or session semantics apply;
- canonical precision and boundary convention;
- temporal source authorities and policy versions.

These values MUST remain independent. Equality MAY occur but MUST NOT be assumed.

Temporal state SHALL be derived relative to a specific use and Knowledge Boundary:

- **Not visible** means Availability Time exceeds the run's permitted Knowledge Boundary.
- **Visible** means the artifact may be considered by planning, subject to governance and semantic
  validation.
- **Usable** means it is visible and satisfies validity, completeness, freshness, compatibility,
  revision, and policy requirements for the exact consumer.
- **Obsolete** means a newer admitted artifact is preferred for a later plan under an explicit
  replacement or freshness policy; obsolete does not mean invalid and MUST NOT rewrite prior use.
- **Historical** means the artifact belongs to a prior logical boundary relative to the evaluating
  Historical Time; historical does not mean unusable.
- **Expired** means its explicit Expiration Time has been reached for the stated use.
- **Invalid** means a structural, semantic, temporal, provenance, or authority invariant failed.

Visibility, usability, obsolescence, historical status, expiration, and invalidity MUST NOT be
collapsed into one status.

## Temporal Identity

Temporal identity MUST include every field capable of changing temporal meaning:

- canonical start and end instants or point instant;
- precision;
- timeframe identity and version;
- calendar identity and version;
- session identity where applicable;
- boundary convention;
- observation and availability source identities;
- publication or revision lineage;
- provisional or final closure state;
- data-revision identity;
- temporal-policy version.

Local display labels, locale, daylight-saving abbreviations, ingestion sequence, machine timezone,
process timezone, and formatting MUST NOT determine temporal identity.

Changing calendar rules, interval alignment, closure policy, precision, revision lineage, or
availability semantics MUST create a new temporal identity and, when consumed, a new semantic-plan
identity.

## Availability Model

An artifact SHALL become visible only when:

- its immutable publication identity exists;
- its source identity and authenticity are valid;
- its Availability Time has been established by the admitted boundary;
- its temporal metadata is complete;
- the evaluating Knowledge Boundary is not earlier than its Availability Time;
- governance and trust rules permit visibility.

Visibility MUST NOT imply usability, compatibility, completeness, or truth.

An artifact SHALL become usable only when the consumer's complete temporal requirement is
satisfied. This includes timeframe compatibility, interval coverage, closure state, validity,
freshness, revision policy, and absence of future leakage.

An artifact SHALL become obsolete only through an explicit versioned policy applied at a later
Knowledge Boundary. A new artifact's arrival MUST NOT mutate or erase the earlier artifact.

An artifact SHALL become expired only at its declared Expiration Time or when a versioned
expiration predicate over frozen logical facts evaluates true. Runtime wall-clock delay MUST NOT
silently expire an artifact inside an accepted semantic plan.

An artifact SHALL become invalid only through a new immutable validation or revocation fact. The
original artifact MUST remain unchanged and historically attributable.

Availability changes after semantic-plan acceptance MUST be represented as new immutable
availability facts for a new planning boundary. They MUST NOT dynamically alter the accepted plan.

## Knowledge Model

Knowledge Time SHALL model what the run was permitted to know, not what data eventually became
available.

For Primary Evidence, Knowledge Time MUST be no earlier than Publication Time and Availability
Time. For Derived Evidence, Knowledge Time MUST additionally be no earlier than the Knowledge Time
of every semantic input and the governed availability of the committed derived result.

A producer MUST receive one frozen Knowledge Boundary. It MUST NOT query later availability,
current time, future revisions, or live registry state.

Knowledge Time MUST preserve source delays, validation delays, admission delays, and revision
visibility relevant to the governed mode. Removing those delays during historical evaluation is
future leakage unless the evaluation is explicitly classified as a different non-historical
analysis.

Knowledge state MUST be monotonic within one authoritative run: later stages MAY receive only facts
authorized by the run's frozen boundary and plan. They MUST NOT make an earlier invocation
retroactively aware of later facts.

## Observation Model

Observation Time identifies the subject matter of the claim. It MUST be sourced from the
authoritative domain or derived under an admitted temporal transformation.

Point observations and interval observations MUST remain distinct. An interval observation MUST
declare start, end, closure, and completeness. A value labeled by interval end MUST NOT be treated
as observable throughout that interval.

An interval-derived Evidence artifact MUST NOT become semantically final before the interval is
closed and required watermark or completeness conditions are satisfied. Provisional Evidence MAY
exist only under an explicit provisional evidence type and MUST NOT masquerade as final Evidence.

Observation Time MAY precede Publication and Availability Time. Late arrival MUST preserve this
relationship rather than moving Observation Time forward.

Source timestamp correction MUST create revision lineage. It MUST NOT silently alter Observation
Time in place.

## Revision Model

### Initial Publication

An initial publication creates a new immutable Evidence or source artifact with its own identity,
Publication Time, Availability Time, and temporal metadata.

### Correction

A correction creates a new immutable artifact asserting corrected content for the same declared
subject and observation scope. It MUST reference the corrected artifact, state the correction
reason, and receive new Publication, Availability, Revision, and content identities.

### Replacement

A replacement creates a new immutable artifact approved to supersede an earlier artifact for
specified future Knowledge Boundaries and consumer policies. Replacement MUST declare scope and
compatibility. It MUST NOT erase the replaced artifact or change historical plans.

### Withdrawal

A withdrawal creates an immutable governance or source fact stating that a prior artifact is no
longer eligible under a defined scope. Withdrawal MUST preserve the withdrawn artifact and reason.
It MUST NOT substitute valid empty Evidence.

### Historical Preservation

Every correction, replacement, and withdrawal MUST preserve lineage to all affected artifacts,
their original timestamps, authorities, registry state, and prior uses. Historical plans and
results MUST remain interpretable from the facts available at their original Knowledge Boundary.

### Revision Visibility

A revision MUST be invisible to a run whose Knowledge Boundary precedes the revision's Availability
Time. A later run MUST apply the revision policy frozen in its semantic plan. Revisions MUST NOT
mutate active plans dynamically.

Multiple competing revisions MUST be treated as a temporal and semantic conflict unless an
authoritative revision lineage declares their precedence deterministically.

## Historical Model

Historical evaluation MUST identify:

- Historical Time and permitted Knowledge Boundary;
- registry snapshot and governance epoch;
- calendar and timeframe versions;
- publication and availability facts visible by that boundary;
- revision lineage visible by that boundary;
- temporal and semantic policy versions;
- source data revisions and watermarks;
- whether the purpose is historical recomputation or operational reproduction.

Historical visibility MUST be based on what was knowable, not on the latest corrected dataset,
unless the evaluation is explicitly classified as revised-history analysis. Revised-history
analysis MUST receive a new mode and result identity and MUST NOT be presented as original
historical replay.

Historical ambiguity MUST fail closed when required availability, revision precedence, calendar,
or timeframe identity cannot be reconstructed.

## Cross-Timeframe Model

### Canonical Timeframes

EPIP-017 SHALL initially recognize these governed timeframe families:

- **M1** — one-minute duration-based interval;
- **M5** — five-minute duration-based interval;
- **M15** — fifteen-minute duration-based interval;
- **M30** — thirty-minute duration-based interval;
- **H1** — one-hour duration-based interval;
- **H4** — four-hour duration-based interval;
- **Daily** — one governed calendar or session day;
- **Weekly** — one governed calendar week or market-week contract;
- **Monthly** — one governed calendar month or market-month contract.

M1 through H4 MUST declare an alignment epoch and applicable calendar or session inclusion policy.
They MUST NOT be aligned from the first observed data point.

Daily, Weekly, and Monthly MUST use versioned calendar boundaries. They MUST NOT be represented as
fixed multiples of elapsed hours or seconds.

Every timeframe identity MUST include its version, alignment rule, calendar identity, session
scope, closure rule, completeness rule, labeling rule, and provisional-data policy.

### Alignment

Cross-timeframe alignment MUST be defined by a Temporal Mapping Contract. Exact interval membership
MUST be determined from canonical boundaries, never labels or arrival order.

A lower-timeframe interval belongs to a higher-timeframe interval only when the mapping contract
defines its observation interval as included. Partial overlap MUST NOT imply membership.

### Aggregation

Aggregation MUST be an admitted, versioned producer capability with explicit semantic ownership.
The planner, scheduler, cache, replay engine, and handoff adapter MUST NOT aggregate evidence
implicitly.

An aggregation capability MUST declare source timeframe, target timeframe, window membership,
required cardinality, missing-interval policy, duplicate policy, closure, watermark, provisional
behavior, revision propagation, units, ordering, and output completeness.

### Inheritance

Evidence from one timeframe MUST NOT automatically inherit validity, quality, completeness,
confidence, uncertainty, or authority into another timeframe. Cross-timeframe inheritance requires
an explicit directional semantic compatibility contract.

### Visibility

Higher-timeframe final Evidence MUST remain invisible until its target interval is closed and its
declared lower-timeframe inputs, source boundary, and watermark conditions are satisfied.

Lower-timeframe Evidence published after a higher-timeframe result's Knowledge Time MUST NOT enter
that historical result. It MAY trigger a new revision and semantic plan under explicit policy.

### Compatibility

Timeframe compatibility MUST be explicit, directional, versioned, and use-specific. A finer
timeframe MUST NOT be assumed compatible with a coarser requirement, and a coarser timeframe MUST
NOT be assumed compatible with a finer requirement.

### Conflicts

Cross-timeframe conflict exists when aligned evidence claims cannot simultaneously satisfy the
consumer's declared temporal and semantic constraints. Conflict MUST be preserved and diagnosed.
Higher timeframe MUST NOT automatically override lower timeframe, and lower timeframe MUST NOT
automatically override higher timeframe.

## Temporal Dependency Rules

### Historical Dependency

A historical dependency refers to Evidence whose Observation or Validity Time precedes the
consumer boundary and whose Knowledge Time is within the permitted Knowledge Boundary. It MUST
declare the permitted lookback, freshness, revision, and calendar policy.

### Future Dependency

A future dependency requires knowledge, observation closure, publication, availability, or revision
that occurs after the consumer's permitted Knowledge Boundary. Future dependencies are forbidden
for authoritative historical, replay, and deterministic execution.

### Forbidden Dependency

A dependency is temporally forbidden when it violates Knowledge Boundary, validity, availability,
timeframe compatibility, interval membership, closure, watermark, calendar, revision, or future
leakage rules. It MUST fail planning or validation.

### Same-time Dependency

A same-time dependency requires explicitly compatible temporal scopes under one mapping contract.
Matching labels or timestamps alone MUST NOT establish same-time semantics.

### Cross-time Dependency

A cross-time dependency connects different Observation or Validity intervals. It MUST declare
direction, lookback or look-forward policy, mapping, freshness, completeness, and availability.
Look-forward knowledge is forbidden unless the capability is explicitly non-historical and the
result cannot enter an authoritative historical or replay path.

### Revision Dependency

A revision dependency links a correction, replacement, or withdrawal to immutable predecessor
artifacts. It MUST preserve original lineage and must not make the revision visible before its
Availability Time.

### Late-arrival Dependency

A late-arrival dependency MAY satisfy a new plan whose Knowledge Boundary includes the late
artifact. It MUST NOT modify a prior plan or historical result. The plan MUST diagnose lateness and
apply the declared revision and completeness policy.

### Validity Rules

Every temporal dependency MUST satisfy:

- source and consumer temporal identities are complete;
- required observation and validity intervals relate as declared;
- Publication and Availability Times are within the consumer's Knowledge Boundary;
- interval closure and completeness requirements are satisfied;
- calendar and timeframe versions are compatible;
- freshness and expiration requirements are satisfied;
- applicable revisions are visible and deterministically ordered;
- no future leakage or hidden conversion exists.

## Temporal Conflicts

### Late Data

Late data MUST retain original Observation Time and later Availability Time. It MUST be excluded
from earlier Knowledge Boundaries and MAY create a new revision or plan only under explicit policy.

### Duplicate Data

Artifacts with identical identity are duplicates and MUST count once. Distinct artifacts covering
the same interval MUST be evaluated for semantic redundancy, correction, or conflict; temporal
coincidence alone MUST NOT merge them.

### Revised Data

Revised data MUST use correction, replacement, or withdrawal lineage. Conflicting revisions without
authoritative precedence MUST fail closed.

### Missing Timeframe

A missing required interval or timeframe MUST remain missing. It MUST NOT be synthesized, filled,
forward-filled, interpolated, or borrowed from another timeframe unless an admitted capability
explicitly produces such Synthetic Evidence.

### Overlapping Timeframe

Unexpected or ambiguously overlapping intervals MUST fail validation. Expected overlap between
different timeframe families MUST be governed by an explicit mapping contract and MUST NOT imply
equivalence.

### Future Leakage

Any input whose Knowledge Time or required closure exceeds the consumer's Knowledge Boundary is
future leakage. It MUST be rejected as a certification failure for historical or replay use.

### Historical Ambiguity

If original availability, calendar, revision, or timeframe semantics cannot be reconstructed, the
historical result MUST be classified as inconclusive or invalid under the governing profile. The
latest known data MUST NOT be substituted silently.

### Stale Evidence

Stale Evidence MUST be diagnosed against the exact consumer freshness policy. Staleness does not
mutate Evidence, prove invalidity, or permit automatic replacement.

## Temporal Authority

- The source domain SHALL own Observation and Publication Time for Primary Evidence.
- The source-boundary admission authority SHALL own Availability Time facts.
- The producer capability SHALL own declared Validity Time derivation for Derived Evidence.
- The Calendar Authority SHALL own calendar, session, holiday, timezone, and exceptional-boundary
  contracts.
- The Temporal Architecture Authority SHALL admit timeframe and Temporal Mapping Contracts.
- The semantic planning authority SHALL freeze Knowledge Boundary and temporal dependencies; it
  SHALL NOT invent timestamps or aggregate Evidence.
- The revision source or governed Revision Authority SHALL issue correction, replacement, and
  withdrawal facts within its domain scope.
- The replay authority SHALL own Replay Time without modifying other temporal dimensions.
- The Compatibility Authority SHALL approve directional temporal compatibility.
- The Certification Authority SHALL certify temporal conformance; it SHALL NOT rewrite source time.

Every temporal authority identity and version MUST be governed under ADR-EPIP017-03 and preserved
for audit.

## Temporal Invariants

1. Observation, Validity, Publication, Availability, Knowledge, Revision, Expiration, Historical,
   and Replay Time remain distinct.
2. Knowledge and observation are never substituted for one another.
3. Evidence meaning and identity never change with availability.
4. Observation Time never moves forward to hide late arrival.
5. Future knowledge never affects a past authoritative run or replay.
6. A run never observes Evidence available after its frozen Knowledge Boundary.
7. Revision never rewrites or deletes history.
8. Correction, replacement, and withdrawal create new immutable artifacts.
9. Availability changes create new facts and never mutate an accepted plan.
10. Expiration uses explicit logical policy and never ambient wall-clock time.
11. Historical status, obsolescence, expiration, and invalidity remain distinct.
12. Every timeframe has immutable versioned semantics.
13. Daily, Weekly, and Monthly are calendar-based, not fixed durations.
14. Cross-timeframe dependencies remain explicit.
15. Aggregation is a producer capability, never implicit planner behavior.
16. Timeframe inheritance is prohibited without compatibility approval.
17. Higher-timeframe final Evidence is unavailable before closure and completeness.
18. Missing intervals are never silently synthesized.
19. Canonical interval boundaries are start-inclusive and end-exclusive.
20. Timezone conversion is explicit and identity-preserving.
21. Semantic correctness is independent of scheduling and execution completion order.
22. Historical ambiguity fails closed.
23. Replay Time never rewrites source temporal facts.
24. Decision remains outside temporal dependency resolution.

## Diagnostics

Temporal diagnostics MUST use stable, versioned codes and distinguish at minimum:

- missing Observation, Publication, Availability, Validity, Revision, or Expiration Time;
- invalid or ambiguous canonical instant or interval;
- invalid precision or boundary convention;
- unknown or incompatible timezone, calendar, session, or timeframe version;
- late arrival;
- duplicate temporal artifact;
- conflicting revision;
- missing interval or timeframe;
- unexpected interval overlap;
- incomplete aggregation window;
- provisional data used as final;
- missing or insufficient watermark;
- stale or expired Evidence;
- future dependency or future leakage;
- historical ambiguity;
- hidden aggregation, inheritance, or timeframe conversion;
- revision lineage violation;
- dynamic availability mutation attempt;
- cross-timeframe incompatibility or conflict.

Every diagnostic MUST identify affected evidence, source and consumer boundaries, timeframe and
calendar identities, Knowledge Boundary, revision lineage, policy version, and reason. Diagnostics
MUST NOT repair, interpolate, aggregate, convert, or select temporal data.

## Temporal Certification

Certification MUST verify at least:

1. Independent preservation of every temporal dimension.
2. Canonical instant, interval, precision, and boundary semantics.
3. Calendar and timezone behavior across holidays, closures, shortened sessions, and
   daylight-saving transitions.
4. Fixed-duration alignment against declared epochs and session policies.
5. Daily, Weekly, and Monthly calendar boundaries.
6. Point, interval, provisional, closed, and final observation semantics.
7. Availability and Knowledge Boundary enforcement.
8. Late-arrival exclusion from earlier runs.
9. Correction, replacement, withdrawal, and competing-revision behavior.
10. Same-time, historical, cross-time, revision, late-arrival, and forbidden dependencies.
11. M1, M5, M15, M30, H1, H4, Daily, Weekly, and Monthly mapping behavior.
12. Missing, duplicate, overlapping, incomplete, stale, expired, and future-leakage diagnostics.
13. No implicit aggregation, inheritance, timezone conversion, or timeframe conversion.
14. Deterministic graph reproduction for identical temporal facts.
15. Historical visibility using original availability and revision state.
16. Cross-timeframe revision propagation without historical mutation.

Certification MUST use real calendar exceptions and real late/revision scenarios. Nominal uniform
intervals alone are insufficient.

## Replay Compatibility

This ADR does not define replay algorithms. It defines the temporal facts every replay mode MUST
preserve.

Replay MUST preserve:

- original Observation, Validity, Publication, Availability, Knowledge, and Revision Times;
- original Calendar, Timeframe, Temporal Mapping, and policy versions;
- original interval closure, completeness, provisional, and watermark states;
- original Knowledge Boundary and registry snapshot;
- late arrivals and revisions only when their Availability Times become visible;
- original temporal dependency graph and diagnostics;
- distinction between original historical evaluation and revised-history analysis.

Replay Time MUST control exposure but MUST NOT replace any source timestamp. Operational
reproduction and historical recomputation remain governed separately by ADR-EPIP017-11.

A replay that cannot reconstruct required availability or calendar state MUST fail closed rather
than use current data or policy.

## Determinism

Given identical Evidence artifacts, source temporal facts, registry snapshot, Calendar and
Timeframe versions, Temporal Mapping Contracts, Knowledge Boundary, revision lineage, watermarks,
and temporal-policy versions, EPIP-017 MUST derive identical:

- visibility and usability decisions;
- validity, freshness, staleness, expiration, and historical classifications;
- timeframe interval identities and membership;
- closure and completeness outcomes;
- active revisions and replacement relationships;
- temporal dependency validity;
- cross-timeframe graph edges;
- temporal conflicts and diagnostics;
- semantic-plan temporal identity.

Wall-clock execution time, data arrival observation by a process, machine timezone, locale,
daylight-saving abbreviation, scheduler order, thread order, storage order, or current calendar
configuration MUST NOT affect these results.

Deterministic temporal classification does not define execution timeout determinism, replay mode,
or producer-output determinism. Those remain governed by ADR-EPIP017-07, ADR-EPIP017-08,
ADR-EPIP017-11, and ADR-EPIP017-13.

## Audit

Every temporal audit record MUST preserve:

- all temporal dimensions and their source authorities;
- precision, timezone basis, timeframe, calendar, session, and boundary versions;
- temporal mapping and aggregation capability identities;
- Knowledge Boundary and Historical or Replay Time;
- publication, availability, watermark, closure, and completeness facts;
- corrections, replacements, withdrawals, and complete revision lineage;
- late, duplicate, missing, overlapping, stale, expired, and conflicting classifications;
- every temporal compatibility and dependency decision;
- temporal diagnostics and certification profile;
- the semantic plan and Evidence identities affected.

Audit MUST explain what was knowable and usable at the governed boundary. It MUST NOT replace
missing historical facts with current facts or declare analytical truth.

## Migration

- Every legacy timestamp MUST be inventoried by actual meaning. Field names such as timestamp,
  created, updated, close, or published MUST NOT determine semantics.
- Every legacy producer MUST identify Observation, Publication, Availability, Validity, Revision,
  and Expiration behavior before certification.
- Existing timeframe aliases MUST be mapped to explicit versioned timeframe contracts.
- Existing timezone, session, holiday, week, and month assumptions MUST be documented and governed.
- Hidden resampling, aggregation, interpolation, forward filling, and timezone conversion MUST be
  exposed as capabilities or prohibited.
- Historical datasets MUST preserve original availability and revision facts where available.
- Where original knowledge state cannot be reconstructed, migration MUST declare historical
  ambiguity and MUST NOT claim faithful replay.
- Shadow execution MUST compare interval identity, visibility, graph edges, aggregation
  completeness, revision handling, and outputs across known temporal edge cases.
- Migration MUST include daylight-saving transitions, holidays, shortened sessions, missing bars,
  late arrivals, duplicate data, and corrections.
- Legacy and EPIP-017 temporal semantics MUST remain separate until equivalence is certified under
  ADR-EPIP017-16.

## Backward Compatibility

This ADR changes no production timestamp, timeframe, calendar, public API, producer implementation,
EPIP-016 contract, Replay behavior, EventBus behavior, financial calculation, risk rule, portfolio
behavior, execution behavior, or serialization format.

Legacy temporal fields remain interpreted by their existing authoritative domains until migrated.
EPIP-017 adapters MUST NOT silently reinterpret them.

EPIP-016 SHALL continue to receive Evidence under its frozen contracts. ADR-EPIP017-15 MUST prove
that EPIP-017 temporal provenance and completeness can be handed off without changing Decision
semantics or allowing future knowledge.

Historical artifacts MUST remain interpretable under their original Calendar, Timeframe, policy,
and revision versions after new versions are introduced.

## Forbidden Behaviours

EPIP-017 MUST NEVER permit:

1. Implicit timeframe conversion.
2. Hidden aggregation, resampling, interpolation, or forward filling.
3. Future knowledge or future-interval leakage into historical execution or replay.
4. Silent revision, correction, replacement, or withdrawal.
5. History rewriting or deletion of superseded artifacts.
6. Runtime temporal reinterpretation.
7. Dynamic mutation of availability inside an accepted semantic plan.
8. Implicit timezone, locale, session, calendar, week, or month conversion.
9. Use of machine local time as semantic time.
10. Use of wall-clock arrival as Observation Time.
11. Use of Publication Time as Availability or Knowledge Time without explicit authority.
12. Treating Daily, Weekly, or Monthly as fixed elapsed durations.
13. Alignment from the first available observation.
14. Higher-timeframe finalization before closure and completeness.
15. Automatic higher-timeframe precedence over lower-timeframe Evidence or the reverse.
16. Missing interval synthesis outside an admitted Synthetic Evidence capability.
17. Late data inserted into a prior run.
18. Current registry, calendar, revision, or availability state substituted for missing historical
    state.
19. Hidden timeframe inheritance of validity, completeness, quality, confidence, or authority.
20. Replay Time replacing source temporal dimensions.
21. Ambient current time determining expiration in an active semantic plan.
22. Scheduler completion order determining temporal meaning.

Any forbidden temporal behavior SHALL be an architecture and certification failure and MUST fail
closed.

## Alternatives Considered

### One universal timestamp

One field represents occurrence, publication, ingestion, availability, validity, and revision.

Rejected because it cannot prevent future leakage or reconstruct historical knowledge.

### Event time and processing time only

Time is reduced to when something happened and when EPIP processed it.

Rejected because publication, governed availability, validity, revision, expiration, and replay
visibility remain unresolved.

### Latest-known-data historical evaluation

Historical computation always uses the latest corrected dataset.

Rejected because it rewrites what was knowable and produces look-ahead bias. Revised-history
analysis remains possible only as a distinct mode and identity.

### Fixed-duration timeframes for all periods

Daily, Weekly, and Monthly are represented by elapsed seconds.

Rejected because market calendars, sessions, holidays, shortened days, and daylight-saving rules
make their semantics calendar-dependent.

### Planner-owned aggregation

The semantic planner automatically aggregates fine timeframes to satisfy coarse requirements.

Rejected because aggregation has analytical semantics, ownership, configuration, revision, and
certification obligations. It MUST be a producer capability.

### Immutable multi-temporal facts with explicit mapping contracts

Every temporal dimension remains independent, and cross-timeframe use requires a governed mapping
and aggregation capability.

Accepted because it preserves historical knowledge, prevents hidden conversion, and supports
deterministic replay across calendar and revision changes.

## Decision

EPIP SHALL adopt the temporal definitions, identities, availability rules, knowledge rules,
observation rules, revision model, historical model, canonical timeframes, cross-timeframe mapping,
temporal dependencies, authority boundaries, invariants, diagnostics, certification, replay
compatibility, determinism, audit, migration, backward compatibility, and prohibitions in this ADR
as the constitutional temporal model for EPIP-017.

Every Evidence artifact, capability, producer input, dependency, semantic plan, dispatch
authorization, result, replay, snapshot, checkpoint, cache identity, audit, and EPIP-016 handoff
MUST preserve these temporal semantics. No implementation MAY infer missing temporal meaning from
field names, runtime order, local timezone, or convenience.

## Consequences

### Positive

- Observation and knowledge remain distinct, preventing future leakage.
- Late data and revisions no longer rewrite historical runs.
- Cross-timeframe dependencies become explicit and certifiable.
- Calendar and daylight-saving behavior remain reproducible across years.
- Aggregation receives explicit semantic ownership.
- Historical replay can reconstruct what was knowable at the time.
- Active plans remain stable despite later availability and revisions.
- Cache and snapshot architecture receive precise temporal identity requirements.

### Negative

- Temporal metadata and historical lineage require substantial retention.
- Existing datasets may lack sufficient availability or revision history for faithful replay.
- Calendar and timeframe contracts require versioned governance.
- Cross-timeframe aggregation becomes more explicit and operationally demanding.
- Some legacy results must be classified as historically ambiguous rather than certified.
- Late corrections require new plans and results instead of in-place updates.

### Trade-offs

EPIP accepts greater temporal rigor, metadata volume, and explicit failure in exchange for eliminating
look-ahead bias, hidden aggregation, history rewriting, and cross-timeframe ambiguity.

## Non-goals

This ADR does not define:

- implementation classes, APIs, clock services, calendar libraries, databases, or interfaces;
- scheduling order, queues, workers, deadlines, or execution timeouts;
- replay algorithms or mode-selection policy;
- cache eviction, retention, reuse, or invalidation implementation;
- semantic-plan or dispatch-plan representation;
- invocation states or atomic result commitment;
- canonical serialization or digest algorithms;
- snapshot or checkpoint storage;
- retry, fallback, or recovery behavior;
- producer analytical formulas or aggregation algorithms;
- EPIP-016 handoff representation;
- trading, Decision, Candidate, Confidence, risk, portfolio, execution, or financial logic.

These exclusions MUST be resolved by their mandatory ADRs and MUST NOT be delegated to code.

## ADR Dependencies

This ADR depends normatively on ADR-EPIP017-01 through ADR-EPIP017-04 and the frozen EPIP-016 and
H001–H007 architecture.

It creates or confirms mandatory dependencies on:

- ADR-EPIP017-06 for freezing temporal boundaries and mapping outcomes in semantic and dispatch
  plans;
- ADR-EPIP017-07 for invocation-time validation without temporal re-resolution and for fencing
  late submissions;
- ADR-EPIP017-08 for temporal determinism profiles and environmental manifests;
- ADR-EPIP017-09 for canonical temporal identities, calendar identities, revision identities, and
  digest hierarchy;
- ADR-EPIP017-10 for revision-aware durable results, temporal lineage, cache reuse, obsolescence,
  expiration, and invalidation;
- ADR-EPIP017-11 for historical recomputation, operational reproduction, revised-history analysis,
  and Replay Time;
- ADR-EPIP017-12 for snapshot and checkpoint preservation of knowledge, availability, calendar,
  watermark, and revision state;
- ADR-EPIP017-13 for temporal failure classification, late data, and revision recovery policy;
- ADR-EPIP017-14 for order-independent cross-timeframe execution and barrier equivalence;
- ADR-EPIP017-15 for temporal completeness and future-leakage prevention at EPIP-016 handoff;
- ADR-EPIP017-16 for legacy timestamp migration, temporal divergence, rollback, and retirement;
- ADR-EPIP017-17 for temporal-event retention and redaction;
- ADR-EPIP017-18 for bounded timeframe expansion and
  historical retention obligations.

This ADR introduces one explicit governance role, the Calendar Authority, and one semantic role,
the Temporal Architecture Authority. Both MUST use ADR-EPIP017-03 ownership, separation,
authenticity, lifecycle, and audit rules. No separate governance model is required.

## Future Evolution

New timeframes, calendars, sessions, availability classes, watermark models, or temporal mappings
MAY be added through immutable versioned contracts. Existing intervals and historical Evidence MUST
NOT be reinterpreted.

Non-time-based bars, event windows, rolling windows, irregular intervals, continuous markets,
multi-calendar instruments, and probabilistic completeness remain unsupported until governed by
new or amended ADRs defining identity, availability, compatibility, determinism, replay, and
certification.

Higher-precision clocks or different canonical time scales MAY be introduced only with explicit
migration and equivalence rules preserving historical identity and ordering.

## Approval Gate

Approval of this ADR resolves temporal availability, cross-timeframe semantics, and historical
consistency only.

It does not approve a clock, calendar, timeframe object, aggregation producer, planner, scheduler,
replay system, cache, adapter, or Programme A.

EPIP-017 implementation remains prohibited until the complete mandatory ADR set is accepted and
the remediated architecture receives an independent **APPROVED AS FROZEN ARCHITECTURE** decision.
