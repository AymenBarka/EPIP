# A05 Execution Plan

## Temporal Availability and Cross-Timeframe Semantics

## 1. Document status

This document is the approved normative execution plan for Programme A05.

Status:

APPROVED

This document has received independent architecture and governance review and the explicit decision:

A05 EXECUTION PLAN APPROVED

The ADR-EPIP017-05 frozen-architecture approval gate has been satisfied.

This document authorizes A05 implementation only through the package sequencing, ownership boundaries, activation gates, implementation gates, verification gates, delivery gates, and closure gates defined herein.

---

## 2. Governing authority

Programme A05 SHALL remain subordinate to:

- ADR-EPIP017-01;
- ADR-EPIP017-02;
- ADR-EPIP017-03;
- ADR-EPIP017-04;
- ADR-EPIP017-05;
- ADR-EPIP017-11 where replay semantics apply;
- the Consolidated Architecture;
- approved governance amendments;
- frozen A03;
- frozen A04.

This plan SHALL allocate implementation responsibility only.

This plan MUST NOT:

- amend or reinterpret an ADR;
- amend or reinterpret the Consolidated Architecture;
- redefine A03 or A04;
- transfer architectural authority;
- transfer repository ownership;
- transfer package ownership;
- redefine existing semantic identities;
- introduce an alternative authoritative path;
- authorize implementation mechanics prohibited by governing ADRs.

Where this plan conflicts with an ADR or the Consolidated Architecture, the higher authority SHALL prevail and A05 implementation MUST stop pending governance resolution.

---

## 3. Activation rule

A05 implementation SHALL begin ONLY when BOTH of the following conditions have been satisfied:

1. this A05 Execution Plan has received independent approval; and
2. the ADR-EPIP017-05 frozen-architecture approval gate has been satisfied.

Approval of this Execution Plan alone MUST NOT authorize implementation.

Satisfaction of the ADR-EPIP017-05 frozen-architecture approval gate alone MUST NOT authorize implementation.

Both activation conditions have been satisfied.

A05 implementation is authorized only one package at a time and only after the package-specific kickoff, ownership, predecessor, implementation, verification, quality, Git delivery, and closure requirements defined by this plan have been satisfied.

---

## 4. Programme purpose

Programme A05 SHALL implement the deterministic temporal architecture governed by ADR-EPIP017-05.

A05 SHALL provide a forward-only pipeline for:

1. immutable temporal semantic facts;
2. governed timeframe and temporal-mapping facts;
3. availability analysis;
4. observation validation;
5. completeness validation;
6. temporal dependency validation;
7. revision validation;
8. replay compatibility validation;
9. temporal certification preparation;
10. integrated temporal closure.

A05 SHALL preserve the independence of:

- Observation Time;
- Validity Time;
- Publication Time;
- Availability Time;
- Knowledge Time;
- Revision Time;
- Expiration Time;
- Historical Time;
- Replay Time.

A05 MUST prevent:

- future leakage;
- implicit timeframe conversion;
- implicit timezone conversion;
- hidden aggregation;
- hidden inheritance;
- historical rewriting;
- ambient-time semantics;
- mutation of accepted temporal facts;
- replacement of missing authoritative facts with inferred values.

---

## 5. Architectural scope

A05 owns ONLY the implementation of ADR-EPIP017-05 temporal semantics allocated by this plan.

A05 SHALL consume frozen predecessor facts without modifying their meaning.

A05 SHALL NOT own:

- producer capability definitions;
- producer execution protocols;
- registry governance;
- provider enumeration;
- provider selection;
- Evidence semantic identity;
- Evidence dependency-graph construction;
- provider execution;
- execution orchestration;
- execution tracking;
- lineage ownership already allocated to A04;
- replay engine mechanics;
- cache implementation;
- persistence implementation;
- scheduling;
- decision semantics;
- EPIP-016 handoff architecture.

A05 temporal processing SHALL remain deterministic and declarative.

No A05 package SHALL execute a provider, schedule runtime work, aggregate Evidence, or mutate a frozen A04 artifact.

---

## 6. Predecessor boundary

A03 and A04 are frozen predecessors.

A05 MAY consume only their committed, immutable, publicly authorized repository contracts.

A05 MUST NOT:

- modify an A03 production or test file;
- modify an A04 production or test file;
- duplicate an A03 or A04 responsibility;
- reinterpret an A03 or A04 semantic identity;
- introduce reverse dependencies from A03 or A04 into A05;
- require predecessor reopening unless separately authorized by governance.

Missing predecessor authority MUST fail closed.

An A05 package MUST NOT invent a substitute contract when a required predecessor contract is absent.

---

## 7. Successor boundary

A05 SHALL end with an immutable integrated temporal-closure result.

A05 SHALL NOT implement responsibilities allocated to a successor programme.

A05 outputs MUST remain declarative facts and diagnostics.

A05 MUST NOT:

- make trading decisions;
- rank analytical outcomes;
- allocate capital;
- schedule execution;
- invoke providers;
- perform replay execution;
- persist runtime state;
- implement lifecycle management;
- create successor-package placeholders.

---

## 8. Package sequence

A05 SHALL contain EXACTLY ten implementation packages:

```text
A05-V1-E00
↓
A05-V1-E01
↓
A05-V1-E02
↓
A05-V1-E03
↓
A05-V1-E04
↓
A05-V1-E05
↓
A05-V1-E06
↓
A05-V1-E07
↓
A05-V1-E08
↓
A05-V1-E09
```

Dependencies SHALL be forward-only.

Each package SHALL consume only frozen predecessor outputs and immutable repository facts expressly allocated to it.

No package SHALL consume a successor output.

No package SHALL skip an unresolved mandatory predecessor.

No circular dependency is permitted.

A package MUST be independently implemented, verified, delivered, published, and closed before its immediate successor may begin.

---

## 9. Repository ownership

Repository ownership SHALL be allocated exactly once.

| Package | Production ownership | Test ownership |
| --- | --- | --- |
| A05-V1-E00 | `epip/temporal/__init__.py`, `epip/temporal/model.py` | `tests/temporal/__init__.py`, `tests/temporal/test_model.py` |
| A05-V1-E01 | `epip/temporal/timeframe.py` | `tests/temporal/test_timeframe.py` |
| A05-V1-E02 | `epip/temporal/availability.py` | `tests/temporal/test_availability.py` |
| A05-V1-E03 | `epip/temporal/observation.py` | `tests/temporal/test_observation.py` |
| A05-V1-E04 | `epip/temporal/completeness.py` | `tests/temporal/test_completeness.py` |
| A05-V1-E05 | `epip/temporal/dependency.py` | `tests/temporal/test_dependency.py` |
| A05-V1-E06 | `epip/temporal/revision.py` | `tests/temporal/test_revision.py` |
| A05-V1-E07 | `epip/temporal/replay.py` | `tests/temporal/test_replay.py` |
| A05-V1-E08 | `epip/temporal/certification.py` | `tests/temporal/test_certification.py` |
| A05-V1-E09 | `epip/temporal/closure.py` | `tests/temporal/test_closure.py` |

The normative documentation file `A05_EXECUTION_PLAN.md` SHALL remain governance-owned and SHALL NOT be owned by an implementation package.

A package SHALL modify ONLY its allocated production and test files.

No package SHALL modify:

- an ADR;
- the Consolidated Architecture;
- this Execution Plan;
- a predecessor file;
- a successor file;
- an unrelated repository file;
- package exports unless separately and explicitly authorized by an approved amendment.

Untracked unrelated files MUST NOT be included in an A05 delivery.

---

## 10. Immutable fact rules

All authoritative A05 inputs and outputs SHALL be immutable.

Collections crossing package boundaries MUST use immutable representations.

Canonical equality and hashing SHALL depend only on stored semantic values.

Input order MUST NOT alter semantic equality, hashes, diagnostics, or results where ordering is not itself authoritative.

Every package SHALL preserve:

- authority identity;
- authority version;
- policy version;
- governance epoch where applicable;
- calendar identity and version where applicable;
- timeframe identity and version where applicable;
- source and consumer temporal boundaries;
- knowledge boundary;
- revision lineage;
- diagnostic context.

No package SHALL use:

- ambient wall-clock time;
- machine timezone;
- locale;
- thread order;
- scheduler order;
- process arrival order;
- mutable global configuration;
- current calendar state in place of frozen calendar facts.

Missing, incomplete, inconsistent, unauthoritative, revoked, superseded, or unsupported mandatory facts MUST fail closed.

---

## 11. Package allocations

## 11.1 A05-V1-E00 — Immutable temporal semantic baseline

### Purpose

E00 SHALL own the immutable semantic baseline required by all A05 successors.

### Production ownership

- `epip/temporal/__init__.py`
- `epip/temporal/model.py`

### Test ownership

- `tests/temporal/__init__.py`
- `tests/temporal/test_model.py`

### Responsibilities

E00 SHALL define immutable repository representations for:

- temporal dimensions;
- canonical instants;
- canonical intervals;
- half-open boundary convention;
- temporal authority references;
- temporal boundaries;
- authoritative calendar facts;
- authoritative calendar-fact collections;
- calendar sessions;
- holidays;
- timezone rules;
- shortened sessions;
- market closures;
- exceptional intervals;
- stable temporal diagnostic codes;
- immutable temporal diagnostic reasons.

E00 SHALL provide deterministic canonicalization, equality, and hashing for its immutable facts.

E00 MUST reject invalid, incomplete, ambiguous, mutable, or unsupported semantic facts.

### Immutable outputs

E00 SHALL produce only immutable temporal semantic facts and diagnostics.

### Boundaries

E00 MUST NOT perform:

- timeframe computation;
- temporal mapping;
- availability analysis;
- observation validation;
- completeness validation;
- temporal dependency validation;
- revision validation;
- replay compatibility validation;
- certification preparation;
- integrated closure.

---

## 11.2 A05-V1-E01 — Timeframe and Temporal Mapping Contract facts

### Purpose

E01 SHALL own deterministic timeframe-contract interpretation and production of immutable Temporal Mapping Contract facts.

### Production ownership

- `epip/temporal/timeframe.py`

### Test ownership

- `tests/temporal/test_timeframe.py`

### Inputs

E01 SHALL consume only:

- frozen E00 temporal models;
- canonical instants and intervals;
- temporal authority references;
- authoritative immutable calendar facts;
- calendar sessions;
- holidays;
- timezone rules;
- shortened sessions;
- market closures;
- exceptional intervals;
- immutable timeframe declarations authorized by ADR-EPIP017-05;
- immutable policy and governance facts.

### Responsibilities

E01 SHALL:

- preserve canonical timeframe identity and version;
- distinguish duration-based and calendar-based timeframes;
- determine canonical half-open timeframe boundaries;
- apply declared alignment epochs;
- apply declared calendar and session inclusion policies;
- preserve timezone and calendar authority;
- resolve holiday, closure, shortened-session, and exceptional-interval facts;
- reject unsupported or ambiguous timeframe declarations;
- produce immutable, versioned Temporal Mapping Contract facts;
- preserve source and target timeframe identities;
- preserve alignment and membership rules;
- preserve closure and completeness requirements;
- preserve visibility rules;
- preserve revision-propagation rules;
- preserve conflict behavior;
- canonicalize all produced facts deterministically.

The immutable Temporal Mapping Contract fact boundary SHALL be produced by E01 before any successor consumes it.

E01 is the sole A05 owner of Temporal Mapping Contract fact production.

### Immutable outputs

E01 SHALL produce:

- immutable canonical timeframe outcomes;
- immutable Temporal Mapping Contract facts;
- immutable timeframe diagnostics.

### Consumers

E02 through E09 MAY consume canonical timeframe outcomes where expressly required.

E05 SHALL consume E01 Temporal Mapping Contract facts for temporal dependency validation.

E08 and E09 MAY consume the frozen E01 facts for certification and integrated closure.

### Boundaries

E01 MUST NOT:

- aggregate Evidence;
- synthesize missing observations;
- analyze availability;
- validate observations;
- validate completeness;
- validate temporal dependencies;
- choose providers;
- construct A04 dependency graphs;
- schedule or execute work.

---

## 11.3 A05-V1-E02 — Availability and knowledge-boundary analysis

### Purpose

E02 SHALL own deterministic availability, visibility, usability, staleness, expiration, and knowledge-boundary analysis.

### Production ownership

- `epip/temporal/availability.py`

### Test ownership

- `tests/temporal/test_availability.py`

### Inputs

E02 SHALL consume only:

- frozen E00 temporal facts;
- frozen E01 timeframe facts where applicable;
- immutable publication facts;
- immutable availability facts;
- immutable knowledge boundaries;
- immutable validity and expiration facts;
- immutable authority, policy, governance, and trust facts;
- immutable A04 context expressly required for the evaluated artifact or plan.

### Responsibilities

E02 SHALL:

- preserve Publication Time and Availability Time independently;
- enforce the frozen Knowledge Boundary;
- distinguish visibility from usability;
- determine staleness and expiration only from explicit immutable facts;
- reject future knowledge;
- reject ambient-time expiration;
- preserve late-arrival facts without changing Observation Time;
- preserve accepted-plan temporal stability;
- produce deterministic fail-closed diagnostics.

### Immutable outputs

E02 SHALL produce immutable availability decisions and diagnostics.

### Boundaries

E02 MUST NOT:

- modify observation facts;
- compute timeframe mappings;
- infer missing availability;
- perform revision precedence;
- validate dependency graphs;
- execute replay;
- mutate active plans.

---

## 11.4 A05-V1-E03 — Observation and validity validation

### Purpose

E03 SHALL own deterministic validation of Observation Time and Validity Time semantics.

### Production ownership

- `epip/temporal/observation.py`

### Test ownership

- `tests/temporal/test_observation.py`

### Inputs

E03 SHALL consume only:

- frozen E00 temporal facts;
- frozen E01 canonical timeframe outcomes;
- frozen E02 availability outcomes;
- immutable observation facts;
- immutable validity facts or authorized validity-rule references;
- immutable closure and provisional-state declarations;
- immutable source-authority and policy facts.

### Responsibilities

E03 SHALL:

- distinguish point and interval observations;
- validate canonical observation instants and intervals;
- validate declared validity intervals or rules;
- preserve Observation Time independently from publication and availability;
- reject source timestamp mutation;
- reject interval-end substitution for an interval observation;
- reject provisional data represented as final;
- preserve late-arrival relationships;
- produce deterministic fail-closed diagnostics.

### Immutable outputs

E03 SHALL produce immutable observation-validation outcomes and diagnostics.

### Boundaries

E03 MUST NOT:

- compute availability;
- aggregate observations;
- infer completeness;
- resolve revisions;
- validate temporal dependencies;
- execute providers or replay.

---

## 11.5 A05-V1-E04 — Interval closure and completeness validation

### Purpose

E04 SHALL own deterministic closure, coverage, watermark, and completeness validation.

### Production ownership

- `epip/temporal/completeness.py`

### Test ownership

- `tests/temporal/test_completeness.py`

### Inputs

E04 SHALL consume only:

- frozen E00 temporal facts;
- frozen E01 timeframe and calendar outcomes;
- frozen E02 availability outcomes;
- frozen E03 observation-validation outcomes;
- immutable interval-membership facts;
- immutable closure facts;
- immutable provisional or final status;
- immutable watermark facts;
- immutable completeness policies.

### Responsibilities

E04 SHALL:

- validate interval closure;
- validate required interval coverage;
- validate immutable watermarks;
- validate required cardinality where declared;
- detect missing intervals;
- detect duplicate intervals;
- detect unexpected overlap;
- reject incomplete windows represented as complete;
- reject provisional data represented as final;
- preserve calendar exceptions and closure context;
- produce deterministic fail-closed diagnostics.

### Immutable outputs

E04 SHALL produce immutable completeness outcomes and diagnostics.

### Boundaries

E04 MUST NOT:

- aggregate Evidence;
- synthesize missing intervals;
- interpolate or forward-fill data;
- select providers;
- build dependency graphs;
- perform revision precedence;
- execute runtime work.

---

## 11.6 A05-V1-E05 — Temporal dependency validation

### Purpose

E05 SHALL own deterministic validation of temporal dependency relationships.

### Production ownership

- `epip/temporal/dependency.py`

### Test ownership

- `tests/temporal/test_dependency.py`

### Inputs

E05 SHALL consume only:

- frozen E00 temporal facts;
- frozen E01 Temporal Mapping Contract facts;
- frozen E02 availability outcomes;
- frozen E03 observation-validation outcomes;
- frozen E04 completeness outcomes;
- immutable A04 dependency facts;
- immutable consumer temporal requirements;
- immutable compatibility and policy facts.

### Responsibilities

E05 SHALL:

- validate same-time dependencies;
- validate historical dependencies;
- validate cross-time dependencies;
- validate cross-timeframe dependencies;
- validate interval membership against the frozen Temporal Mapping Contract;
- validate source and target timeframe compatibility;
- validate closure and completeness requirements;
- validate knowledge-boundary constraints;
- detect future dependencies and future leakage;
- detect hidden aggregation;
- detect hidden inheritance;
- detect hidden timeframe conversion;
- reject missing or unsupported mapping facts;
- preserve dependency direction and A04 topology;
- produce deterministic fail-closed diagnostics.

E05 MUST consume E01 Temporal Mapping Contract facts and MUST NOT reproduce or infer them.

### Immutable outputs

E05 SHALL produce immutable temporal dependency-validation outcomes and diagnostics.

### Boundaries

E05 MUST NOT:

- construct or alter the A04 dependency graph;
- enumerate or select providers;
- aggregate Evidence;
- execute dependencies;
- reinterpret semantic compatibility;
- schedule work.

---

## 11.7 A05-V1-E06 — Revision and historical continuity validation

### Purpose

E06 SHALL own deterministic correction, replacement, withdrawal, revision-lineage, and historical-continuity validation.

### Production ownership

- `epip/temporal/revision.py`

### Test ownership

- `tests/temporal/test_revision.py`

### Inputs

E06 SHALL consume only:

- frozen E00 temporal facts;
- frozen E02 availability outcomes;
- frozen E03 observation outcomes;
- frozen E04 completeness outcomes where applicable;
- frozen E05 dependency outcomes where applicable;
- immutable correction facts;
- immutable replacement facts;
- immutable withdrawal facts;
- immutable revision lineage;
- immutable authority and policy facts;
- immutable historical boundaries.

### Responsibilities

E06 SHALL:

- preserve original artifacts;
- validate correction lineage;
- validate replacement scope and precedence;
- validate withdrawal authority and scope;
- preserve original publication, availability, and observation facts;
- reject in-place historical mutation;
- reject competing revisions without deterministic authoritative precedence;
- enforce revision visibility at the frozen Knowledge Boundary;
- preserve prior plan interpretation;
- produce deterministic fail-closed diagnostics.

### Immutable outputs

E06 SHALL produce immutable revision-validation outcomes and diagnostics.

### Boundaries

E06 MUST NOT:

- mutate or delete historical artifacts;
- rewrite an active plan;
- choose revisions by runtime arrival order;
- execute replay;
- construct dependency graphs;
- perform lifecycle management.

---

## 11.8 A05-V1-E07 — Replay and historical compatibility validation

### Purpose

E07 SHALL own deterministic validation of temporal compatibility for governed replay and historical modes.

### Production ownership

- `epip/temporal/replay.py`

### Test ownership

- `tests/temporal/test_replay.py`

### Inputs

E07 SHALL consume only immutable repository facts already authorized by ADR-EPIP017-05 and ADR-EPIP017-11, including:

- frozen E00 temporal facts;
- frozen E01 timeframe, calendar, and Temporal Mapping Contract facts;
- frozen E02 availability outcomes;
- frozen E03 observation outcomes;
- frozen E04 completeness outcomes;
- frozen E05 dependency outcomes;
- frozen E06 revision outcomes;
- immutable replay mode;
- immutable Replay Time;
- immutable Historical Time;
- immutable Knowledge Boundary;
- immutable execution boundary;
- immutable registry and governance snapshots;
- immutable temporal-policy versions.

Runtime replay configuration, replay services, replay engines, execution configuration, and implementation classes SHALL NOT become semantic authority.

### Responsibilities

E07 SHALL:

- preserve Replay Time independently from every source temporal dimension;
- validate historical visibility;
- validate replay exposure boundaries;
- distinguish historical recomputation from operational reproduction;
- distinguish revised-history analysis from original historical evaluation;
- preserve original availability, revision, calendar, timeframe, mapping, watermark, and closure state;
- reject current-state substitution for missing historical facts;
- reject future knowledge;
- reject ambiguous or unreconstructable historical state;
- produce deterministic fail-closed diagnostics.

### Immutable outputs

E07 SHALL produce immutable replay-compatibility outcomes and diagnostics.

### Boundaries

E07 MUST NOT:

- implement a replay engine;
- select a replay mode;
- execute replay;
- load historical data;
- schedule work;
- mutate source temporal facts;
- replace missing history with current facts.

---

## 11.9 A05-V1-E08 — Temporal certification preparation

### Purpose

E08 SHALL own deterministic preparation of immutable temporal certification evidence.

### Production ownership

- `epip/temporal/certification.py`

### Test ownership

- `tests/temporal/test_certification.py`

### Inputs

E08 SHALL consume only the frozen immutable outputs of E00 through E07 and immutable certification profiles authorized by repository governance.

### Responsibilities

E08 SHALL prepare certification facts covering:

- independence of temporal dimensions;
- canonical instant and interval semantics;
- timezone and calendar behavior;
- holidays, closures, shortened sessions, and exceptional intervals;
- duration-based alignment;
- calendar-based Daily, Weekly, and Monthly boundaries;
- point and interval observations;
- provisional, closed, and final states;
- availability and Knowledge Boundary enforcement;
- late-arrival exclusion;
- correction, replacement, withdrawal, and competing revisions;
- same-time, historical, cross-time, and cross-timeframe dependencies;
- Temporal Mapping Contract behavior;
- missing, duplicate, overlapping, incomplete, stale, expired, and future-leakage cases;
- absence of implicit aggregation, inheritance, or conversion;
- deterministic reproduction;
- historical visibility and replay compatibility.

E08 SHALL preserve certification inputs and results immutably.

E08 MUST fail closed when mandatory certification facts are missing or inconsistent.

### Immutable outputs

E08 SHALL produce immutable certification-preparation results and diagnostics.

### Boundaries

E08 MUST NOT:

- grant certification authority;
- rewrite source facts;
- repair failed cases;
- execute producers;
- execute replay;
- modify predecessor outcomes;
- declare integrated A05 closure.

---

## 11.10 A05-V1-E09 — Integrated temporal closure

### Purpose

E09 SHALL own deterministic integrated verification that the A05 temporal pipeline is complete and internally consistent.

### Production ownership

- `epip/temporal/closure.py`

### Test ownership

- `tests/temporal/test_closure.py`

### Inputs

E09 SHALL consume only the frozen immutable outputs of E00 through E08 and immutable repository identity, governance, and policy facts required for closure.

### Responsibilities

E09 SHALL:

- verify package-output completeness;
- verify temporal-dimension preservation;
- verify authority continuity;
- verify calendar and timeframe continuity;
- verify Temporal Mapping Contract continuity;
- verify availability and knowledge-boundary continuity;
- verify observation and validity continuity;
- verify closure and completeness continuity;
- verify dependency continuity;
- verify revision continuity;
- verify replay compatibility continuity;
- verify certification-preparation completeness;
- verify deterministic identity and diagnostic continuity;
- reject missing, inconsistent, unsupported, revoked, or superseded mandatory facts;
- produce an immutable integrated temporal-closure result;
- produce immutable deterministic diagnostics.

### Immutable outputs

E09 SHALL produce the terminal immutable A05 closure result and diagnostics.

### Boundaries

E09 MUST NOT:

- repair predecessor results;
- reinterpret ADR semantics;
- execute providers;
- execute replay;
- aggregate Evidence;
- schedule work;
- manage lifecycle;
- implement successor responsibilities.

---

## 12. Dependency graph

The normative package dependency graph SHALL be:

```text
A03 and A04 frozen repository facts
                 │
                 ▼
              A05-E00
                 │
                 ▼
              A05-E01
                 │
                 ▼
              A05-E02
                 │
                 ▼
              A05-E03
                 │
                 ▼
              A05-E04
                 │
                 ▼
              A05-E05
                 │
                 ▼
              A05-E06
                 │
                 ▼
              A05-E07
                 │
                 ▼
              A05-E08
                 │
                 ▼
              A05-E09
```

Specific immutable fact dependencies SHALL include:

| Fact | Owner | Authorized consumers |
| --- | --- | --- |
| Temporal semantic baseline | E00 | E01–E09 |
| Calendar sessions, holidays, timezone rules, shortened sessions, market closures, exceptional intervals | E00 | E01 and authorized successors |
| Canonical timeframe outcomes | E01 | E02–E09 where required |
| Temporal Mapping Contract facts | E01 | E05, E08, E09 |
| Availability outcomes | E02 | E03–E09 where required |
| Observation-validation outcomes | E03 | E04–E09 where required |
| Completeness outcomes | E04 | E05–E09 where required |
| Temporal dependency outcomes | E05 | E06–E09 where required |
| Revision outcomes | E06 | E07–E09 |
| Replay-compatibility outcomes | E07 | E08–E09 |
| Certification-preparation outcomes | E08 | E09 |
| Integrated temporal closure | E09 | authorized successor programmes only |

Every fact SHALL have exactly one producing package.

A consumer MUST NOT recreate, partially duplicate, infer, or bypass a predecessor-owned fact.

---

## 13. Diagnostic requirements

All A05 diagnostics SHALL:

- use stable, deterministic codes;
- be immutable;
- be hashable;
- preserve complete authoritative context;
- preserve affected artifact identity;
- preserve source and consumer boundaries;
- preserve timeframe and calendar identities where applicable;
- preserve Knowledge Boundary;
- preserve revision lineage;
- preserve policy version;
- preserve authority identity;
- preserve reason.

Diagnostics MUST NOT:

- repair facts;
- interpolate data;
- aggregate observations;
- select alternatives;
- infer authority;
- mutate inputs;
- suppress mandatory failure.

Equivalent immutable inputs MUST produce equal diagnostics with equal hashes.

---

## 14. Determinism requirements

For canonically identical immutable inputs, every package MUST produce identical:

- results;
- ordering;
- equality;
- hashes;
- diagnostics;
- failure classifications.

Permutations of semantically unordered input tuples MUST NOT alter results.

Authoritative ordering MUST be preserved where order carries semantic meaning.

Determinism MUST NOT depend on:

- runtime clock;
- local timezone;
- locale;
- storage order;
- thread order;
- scheduling order;
- object identity;
- hash randomization;
- provider completion order.

---

## 15. Fail-closed requirements

Every package MUST fail closed when a mandatory fact is:

- absent;
- incomplete;
- inconsistent;
- ambiguous;
- unauthenticated;
- unauthorized;
- uncertified where certification is mandatory;
- revoked;
- superseded;
- unsupported;
- temporally incompatible;
- historically unreconstructable.

No package MAY fabricate a missing semantic fact.

No package MAY silently select a fallback semantic interpretation.

No package MAY replace frozen historical authority with current authority.

---

## 16. Implementation gate

Before implementation of each package:

1. every predecessor package MUST be closed;
2. the package MUST be explicitly authorized;
3. its ownership scope MUST be confirmed;
4. its immutable inputs MUST exist;
5. its predecessor contracts MUST be public and frozen;
6. no unresolved governance finding may affect the package;
7. no unrelated tracked modification may be included.

Failure of any condition SHALL block implementation.

Authorization of one package MUST NOT authorize a successor package.

---

## 17. Component test gate

Each package test suite SHALL independently demonstrate:

- every allocated responsibility;
- deterministic behavior;
- repeated execution;
- immutability;
- equality and hashing where applicable;
- canonical ordering;
- permutation invariance where applicable;
- invalid-input rejection;
- fail-closed behavior;
- predecessor preservation;
- successor-boundary preservation;
- absence of unauthorized responsibilities.

Tests MUST validate repository behavior rather than caller-supplied conclusions.

Tests MUST NOT modify frozen predecessor facts.

---

## 18. Quality gate

Each package MUST pass:

- Black;
- Ruff;
- MyPy `--strict`;
- package-specific pytest;
- full repository regression;
- `git diff --check`.

Each owned production module MUST achieve:

- 100% statement coverage;
- 100% branch coverage.

The published commit MUST pass:

- repository Quality workflow;
- CodeQL workflow;
- full regression;
- configured coverage enforcement.

A package SHALL NOT reach completion while any mandatory quality gate is failing, skipped, or unverifiable.

---

## 19. Independent verification gate

After implementation and before Git delivery, each package SHALL receive an independent component-completion review.

The review SHALL verify:

- ownership;
- architecture;
- package responsibilities;
- immutable input and output boundaries;
- public production inventory;
- diagnostics;
- tests;
- quality;
- coverage;
- predecessor preservation;
- successor-boundary preservation.

The only successful decision SHALL be:

```text
COMPONENT COMPLETE VERIFIED: A05-V1-E0N
```

where `E0N` identifies the reviewed package.

A failed or partial review SHALL return the package to corrective implementation within the same ownership boundary.

---

## 20. Git delivery gate

Each package SHALL be delivered as one atomic commit.

Before commit:

- the current branch MUST be `develop`;
- the staged index MUST contain exactly the package-owned files;
- no unrelated tracked file may be staged;
- no predecessor or successor file may be staged;
- untracked unrelated files MUST be ignored;
- `git diff --check` MUST pass.

The commit title SHALL identify A05 and the package responsibility.

After commit:

- the commit MUST contain exactly the authorized package files;
- local HEAD MUST identify the package commit;
- no package-owned staged or tracked modification may remain.

After push:

- local HEAD MUST equal `origin/develop`;
- ahead count MUST be zero;
- behind count MUST be zero;
- the Quality workflow MUST pass;
- CodeQL MUST pass;
- required regression and coverage checks MUST pass.

A package SHALL remain open until publication verification succeeds.

---

## 21. Package completion gate

A package SHALL be complete only when:

1. all allocated production responsibilities are implemented;
2. all allocated tests are implemented;
3. no unauthorized responsibility is present;
4. predecessor packages remain unchanged;
5. successor packages remain untouched;
6. all quality and coverage gates pass;
7. independent verification declares component completion;
8. the atomic commit is published to `origin/develop`;
9. published CI passes;
10. repository synchronization is verified.

Completion of a package SHALL freeze its production and test files.

A frozen package MUST NOT be reopened without explicit governance authority.

---

## 22. Integrated A05 acceptance gate

After E09 is closed, A05 SHALL undergo an independent integrated architecture review.

The review SHALL verify:

- the complete E00–E09 dependency chain;
- forward-only dependency direction;
- absence of cycles;
- exactly-once responsibility allocation;
- immutable model flow;
- deterministic behavior;
- authority preservation;
- temporal-dimension independence;
- calendar and timeframe continuity;
- Temporal Mapping Contract continuity;
- availability and Knowledge Boundary enforcement;
- observation and completeness continuity;
- dependency and revision continuity;
- replay compatibility;
- certification preparation;
- integrated closure;
- repository ownership;
- public API consistency;
- full regression;
- Quality workflow;
- CodeQL.

The only successful integrated decision SHALL be:

```text
A05 ARCHITECTURE COMPLETE
```

Until that decision is issued, A05 MUST NOT be declared closed.

---

## 23. Final closure gate

A05 SHALL be closed only when:

- E00 through E09 are individually closed;
- no package remains open;
- no corrective implementation remains unpublished;
- every approved amendment has been applied;
- integrated acceptance has passed;
- local `develop` equals `origin/develop`;
- no A05 tracked modification remains;
- all mandatory CI checks pass;
- repository ownership remains intact.

The successful final closure status SHALL be:

```text
A05 CLOSED
```

Closure SHALL freeze all A05 package-owned files.

---

## 24. Repository-freeze rules

Once a package is closed:

- its implementation SHALL be frozen;
- its tests SHALL be frozen;
- its public contracts SHALL be frozen;
- successors MUST consume it without modification;
- defects requiring modification MUST trigger explicit reopening authority;
- planning deficiencies MUST trigger an Execution Plan amendment;
- architecture inconsistencies MUST trigger the governing ADR process;
- repository-model limitations MUST NOT be bypassed in implementation.

No package may be silently reopened.

No successor authorization may imply predecessor reopening.

---

## 25. Amendment governance

This plan MAY be amended only through an explicit governance decision.

An amendment SHALL:

- identify the exact deficiency;
- identify the governing repository evidence;
- remain subordinate to ADR authority;
- preserve architectural ownership;
- preserve repository ownership;
- preserve package sequencing unless higher authority explicitly requires otherwise;
- state package reopening impact;
- receive independent review and approval before application.

An Execution Plan amendment MUST NOT:

- redefine an ADR contract;
- create an unapproved semantic model;
- prescribe implementation mechanics beyond package allocation;
- transfer architectural authority;
- bypass a missing predecessor contract;
- authorize undocumented public APIs.

Where an implementation cannot satisfy its allocated dependency using frozen repository authority, implementation MUST stop and the issue SHALL be classified as:

- implementation defect;
- Execution Plan deficiency;
- repository-authority limitation; or
- architecture inconsistency.

No missing contract may be inferred.

---

## 26. Prohibited implementation behavior

A05 implementations MUST NOT:

- use ambient current time as semantic authority;
- use machine-local timezone as semantic authority;
- treat display labels as semantic identity;
- treat Daily, Weekly, or Monthly as fixed elapsed durations;
- align timeframes from the first available observation;
- synthesize missing intervals;
- silently interpolate or forward-fill;
- aggregate Evidence outside an admitted producer capability;
- mutate revisions or historical artifacts;
- insert late data into an earlier frozen run;
- replace missing historical state with current state;
- let Replay Time replace source temporal dimensions;
- let scheduler or provider completion order determine temporal meaning;
- modify A04 selection, graph, planning, orchestration, execution, tracking, or lineage;
- introduce successor-programme behavior.

Any prohibited behavior SHALL be a component-completion blocker.

---

## 27. Implementation order

The only authorized implementation order SHALL be:

1. A05-V1-E00 — immutable temporal semantic baseline;
2. A05-V1-E01 — timeframe and Temporal Mapping Contract facts;
3. A05-V1-E02 — availability and knowledge-boundary analysis;
4. A05-V1-E03 — observation and validity validation;
5. A05-V1-E04 — interval closure and completeness validation;
6. A05-V1-E05 — temporal dependency validation;
7. A05-V1-E06 — revision and historical continuity validation;
8. A05-V1-E07 — replay and historical compatibility validation;
9. A05-V1-E08 — temporal certification preparation;
10. A05-V1-E09 — integrated temporal closure.

Each step SHALL require separate kickoff authorization.

No parallel successor implementation is authorized.

---

## 28. Approval record

This plan has received independent architecture and governance review.

The approved decision is:

```text
A05 EXECUTION PLAN APPROVED
```

The approval confirms:

- ADR compliance;
- Consolidated Architecture compliance;
- A03 and A04 preservation;
- activation-rule completeness;
- package decomposition;
- ownership uniqueness;
- immutable fact boundaries;
- Temporal Mapping Contract allocation;
- immutable calendar-fact allocation;
- replay semantic authority;
- dependency direction;
- completion gates;
- quality gates;
- Git delivery gates;
- repository-freeze rules.

This document is the normative A05 Execution Plan.

Implementation authority remains package-specific and SHALL be granted only through the ordered kickoff, implementation, verification, Git delivery, publication, and closure process defined herein.
