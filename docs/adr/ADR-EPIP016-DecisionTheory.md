# ADR-EPIP016 — Decision Theory

## Status

Proposed for institutional approval.

No EPIP-016 implementation may begin until this ADR is accepted.

## Context

EPIP already provides deterministic market observations, analytical snapshots, risk controls,
execution management, portfolio state, and institutional hardening guarantees. A decision engine
must combine those facts without collapsing observation, interpretation, recommendation, and
execution into one opaque operation.

This ADR establishes the official decision theory for EPIP-016. It defines the conceptual model,
responsibility boundaries, relationships, and invariants that every future implementation must
preserve. It introduces no runtime behavior and no implementation design.

## Decision

EPIP adopts an explicit, staged decision model:

```text
Market Observation
        ↓
Evidence
        ↓
Hypothesis
        ↓
Scenario
        ↓
Candidate
        ↓
Constraint Evaluation
        ↓
Ranking
        ↓
Recommendation
        ↓
Decision
        ↓
Execution
```

No stage may silently assume the responsibility of another stage. In particular, observations do
not decide, hypotheses do not recommend, constraints do not create candidates, and decisions do
not execute themselves.

## 1. Objectives

### Decision

A **Decision** is an immutable, versioned, explainable recommendation that has survived every
applicable mandatory constraint. It represents the framework's official conclusion for a defined
symbol, logical time, input set, and policy version.

A decision expresses what the framework recommends. It does not place an order, mutate a
portfolio, or guarantee an outcome.

### Evidence

An **Evidence** is an immutable, deterministic, versioned statement derived from one authoritative
source. It describes a relevant fact or analytical result without deciding what action should be
taken.

### Hypothesis

A **Hypothesis** is a reversible interpretation supported by one or more evidence items. It states
what may explain the observed market state. It can be supported, weakened, contradicted, or
invalidated, but it never creates a decision.

### Candidate

A **Candidate** is a fully described potential action considered by the framework. It links an
action to its evidence, hypotheses, scenarios, arguments, uncertainty, and applicable constraints.
It is eligible for evaluation but is not yet a recommendation or decision.

### Recommendation

A **Recommendation** is the highest-ranked admissible candidate after constraint evaluation. It is
the proposed conclusion awaiting final decision validation. A recommendation becomes a decision
only when its provenance, validity, constraints, ranking, and explanation are complete.

### Explanation

An **Explanation** is the immutable causal record of how a decision was obtained. It includes the
supporting and opposing evidence, accepted and rejected hypotheses, scenarios considered,
constraints applied, rejected alternatives, ranking reasons, and uncertainty.

An explanation is part of the decision contract, not optional presentation metadata.

## 2. Conceptual Model

### Market Observation to Evidence

A **Market Observation** is an authoritative input produced by an existing EPIP domain, such as a
snapshot, event, price fact, structure state, liquidity state, or analytical result.

The transition to Evidence:

- identifies the authoritative source and its version;
- preserves the logical timestamp and provenance;
- evaluates whether the observation is valid for the current decision context;
- represents its quality, confidence, and uncertainty explicitly;
- creates no interpretation beyond the source's declared meaning.

### Evidence to Hypothesis

The transition to Hypothesis combines compatible evidence into a named, testable interpretation.
Every hypothesis must declare which evidence supports or contradicts it and the conditions that
would invalidate it. Evidence remains unchanged and independently auditable.

### Hypothesis to Scenario

The transition to Scenario groups mutually compatible hypotheses into a coherent possible market
description. Compatibility is explicit and deterministic. Contradictory scenarios may coexist
because uncertainty about the market is represented rather than hidden.

### Scenario to Candidate

The transition to Candidate asks which actions are logically supported under each scenario. A
candidate records its arguments, provenance, assumptions, uncertainty, and priority. Several
candidates may arise from one scenario, and the same action may be supported by several scenarios.

### Candidate to Constraint Evaluation

Constraint evaluation determines whether a candidate is admissible. Constraints may accept,
reject, restrict, or mark a candidate unavailable. They do not add analytical support and cannot
invent a new action.

### Constraint Evaluation to Ranking

Only admissible candidates enter ranking. Ranking compares candidates using explicit, versioned,
deterministic criteria. It preserves the reasons for ordering and never relies on incidental
collection order.

### Ranking to Recommendation

The highest-ranked candidate becomes a recommendation when all mandatory inputs and evaluations
are complete. If no candidate is admissible, the outcome must be an explicit WAIT or INVALID
recommendation according to the governing policy; absence of a result is not a decision.

### Recommendation to Decision

A recommendation becomes a decision after final validation confirms:

- complete and valid provenance;
- successful mandatory constraint evaluation;
- deterministic ranking;
- a complete explanation;
- a stable identity, version, logical timestamp, and digest;
- compliance with the active decision policy.

### Decision to Execution

Execution consumes a decision through its official downstream contract. It remains independently
responsible for order lifecycle, broker interaction, fills, slippage, commissions, and execution
state. A decision never performs execution and never claims that execution occurred.

## 3. Evidence Model

Every Evidence possesses:

- **source**: the authoritative producer and source identity;
- **version**: the source schema or semantic version used to interpret it;
- **validity**: whether it is applicable and internally valid in the decision context;
- **quality**: the fitness and integrity of the underlying observation;
- **confidence**: the declared strength of support for the statement;
- **uncertainty**: the explicitly represented incompleteness or ambiguity;
- **dependencies**: immutable references to the source inputs from which it was derived;
- **logical timestamp**: the decision-domain time associated with the observation;
- **digest**: a deterministic fingerprint of its canonical content and provenance.

Evidence is always:

- immutable;
- deterministic;
- versioned;
- explainable;
- attributable to one authoritative source;
- serializable through a canonical representation;
- independent of runtime object identity.

Evidence never knows another Evidence. Relationships between evidence items belong to the
Hypothesis or Scenario that consumes them. This prevents hidden graphs, mutual mutation, and
implicit coupling between analytical domains.

Evidence does not contain a recommendation, execution instruction, or downstream state mutation.

## 4. Hypothesis Model

A Hypothesis is a named interpretation of multiple evidence items. Examples include:

- Wave 3;
- Wave 5;
- ABC correction;
- bull trend;
- bear trend;
- liquidity sweep;
- breakout;
- compression;
- expansion.

Every Hypothesis declares:

- its immutable identity and version;
- the evidence it consumes by stable reference;
- supporting and contradicting arguments;
- explicit assumptions;
- validity and invalidation conditions;
- confidence, quality, and uncertainty assessments;
- its logical timestamp and deterministic digest.

A Hypothesis:

- consumes one or more evidence items;
- produces an interpretation, never a decision;
- remains reversible and auditable;
- may be invalidated when its conditions no longer hold;
- cannot mutate its supporting evidence;
- cannot suppress contradictory evidence;
- cannot directly invoke constraints, ranking, or execution.

Invalidation does not erase a hypothesis. It records that the hypothesis is no longer valid for the
specified decision context while preserving its audit history.

## 5. Scenario Model

A Scenario is an immutable, coherent set of compatible hypotheses describing one possible market
state. Typical scenarios include:

- Bull Scenario;
- Bear Scenario;
- Range Scenario;
- Reversal Scenario.

Several scenarios may coexist. Coexistence is required when available evidence permits multiple
interpretations. Scenarios do not automatically exclude one another merely because they imply
different outcomes.

Every Scenario declares:

- its constituent hypotheses;
- explicit compatibility rules;
- supporting and contradicting evidence references;
- assumptions and invalidation conditions;
- confidence, quality, validity, and uncertainty;
- its deterministic ranking inputs;
- its version, logical timestamp, and digest.

Scenario ranking orders interpretations; it does not decide an action. Rejected or lower-ranked
scenarios remain present in the explanation.

## 6. Decision Candidate

The official candidate actions are:

- **LONG**: propose establishing a long position;
- **SHORT**: propose establishing a short position;
- **WAIT**: propose no position-changing action until conditions change;
- **EXIT**: propose closing an existing position;
- **REDUCE**: propose reducing an existing position without fully exiting;
- **ADD**: propose increasing an existing position;
- **INVALID**: state that no valid decision can be produced from the available inputs.

Every Candidate possesses:

- the proposed action;
- supporting and opposing arguments;
- stable references to supporting evidence;
- stable references to supporting and contradicting hypotheses;
- the scenarios under which it is applicable;
- all applicable constraint results;
- confidence;
- uncertainty;
- quality;
- priority;
- validity and invalidation conditions;
- version, logical timestamp, identity, and digest.

A Candidate is immutable, comparable, explainable, and filterable. It is not executable and does
not imply authorization. WAIT and INVALID are explicit modeled outcomes, not missing values or
exceptions.

## 7. Constraint Model

Constraints never create a decision or candidate. They evaluate only whether an existing candidate
is admissible under authoritative rules and state.

Official constraint categories are:

- **Risk**: risk appetite, limits, and safety restrictions owned by the Risk domain;
- **Portfolio**: portfolio concentration and portfolio-state restrictions;
- **Exposure**: gross, net, long, short, symbol, or grouped exposure restrictions;
- **Capital**: availability and allocation restrictions;
- **Policy**: explicit institutional or strategy policy restrictions;
- **Compliance**: legal, regulatory, mandate, and governance restrictions;
- **Security**: trust, capability, and authorization restrictions;
- **Runtime**: availability, degradation, resource, and operational-safety restrictions.

A constraint result must identify:

- the authoritative constraint source;
- the candidate evaluated;
- the applicable rule and version;
- the result: accepted, rejected, restricted, or unavailable;
- a stable reason code and explanation;
- the logical timestamp and deterministic digest.

Mandatory constraints fail closed. An unavailable mandatory constraint cannot be interpreted as an
acceptance. Constraint ownership remains with its authoritative EPIP domain; the decision model
must not duplicate risk, portfolio, security, or runtime calculations.

## 8. Confidence Theory

### Confidence

**Confidence** represents the strength of support for a statement, interpretation, scenario,
candidate, or recommendation. It answers: "How strongly do the available valid inputs support this
conclusion?"

Confidence does not imply correctness, data quality, certainty, or admissibility.

### Quality

**Quality** represents the fitness, integrity, resolution, and reliability of the information or
derivation. It answers: "How suitable is the underlying material for this use?"

High-quality information may support competing conclusions. Low-quality information limits the
reliability of any conclusion even when apparent confidence is high.

### Validity

**Validity** represents whether an item satisfies its declared structural, temporal, semantic, and
contextual conditions. It answers: "May this item legitimately participate in this decision?"

Validity is not a measure of preference. Invalid evidence or hypotheses cannot be repaired by high
confidence or high quality.

### Uncertainty

**Uncertainty** represents known incompleteness, ambiguity, disagreement, or unresolved
alternatives. It answers: "What remains unknown or contested?"

Uncertainty is not simply the inverse of confidence. A conclusion can have strong supporting
evidence and still retain material uncertainty because plausible alternatives exist.

### Relationships

The four concepts remain independent and are never substituted for one another:

- validity determines eligibility for use;
- quality characterizes the fitness of eligible information;
- confidence characterizes the strength of support;
- uncertainty preserves what the framework cannot resolve.

Their derivation must be explicit, deterministic, versioned, and explainable. No single combined
value may erase the four independent assessments.

## 9. Decision Theory

A Decision is a recommendation that has survived all applicable mandatory constraints.

Therefore:

- no Evidence directly produces a Decision;
- no Hypothesis directly produces a Decision;
- no Scenario directly produces a Decision;
- no Constraint creates or promotes a Candidate;
- ranking cannot restore a rejected Candidate;
- an invalid input cannot be overridden by confidence;
- an unavailable mandatory constraint cannot be silently ignored;
- execution cannot retroactively redefine the Decision that authorized it.

The Decision records the selected recommendation and every material alternative. It remains valid
only within its declared scope, logical time, input versions, constraints, and invalidation
conditions.

## 10. Explainability

Every Decision must answer, without requiring access to mutable runtime state:

- **Why?** The positive reasoning supporting the selected recommendation.
- **Why not?** The reasons competing actions were not selected.
- **Which evidence?** Every supporting, opposing, invalid, or unavailable evidence item.
- **Which hypotheses?** Accepted, rejected, weakened, and invalidated interpretations.
- **Which scenario?** The selected scenario and all material alternatives.
- **Which constraints?** Every applicable result and its authoritative source.
- **Which rejections?** Candidates and scenarios removed from consideration, with reason codes.
- **Which alternatives?** The deterministic ranking and differences between viable candidates.

The explanation must preserve provenance, versions, logical timestamps, digests, and reason codes.
It must distinguish observed facts from derived interpretations and policy decisions. It must never
invent a narrative that is absent from the decision graph.

## 11. Determinism

EPIP-016 adopts the following deterministic chain:

```text
Identical inputs
        ↓
Identical graph
        ↓
Identical decision
        ↓
Identical explanation
        ↓
Identical canonical JSON
        ↓
Identical digest
        ↓
Identical replay
```

"Identical inputs" includes the same source snapshots, logical clock, deterministic identifiers,
configuration, policy versions, graph version, and constraint facts.

The graph definition, node ordering, candidate ordering, tie-breaking, serialization order, and
event order must all be explicit and stable. Determinism applies equally to successful, WAIT,
INVALID, rejected, and degraded outcomes.

A replay is conformant only when it reproduces the same decision, explanation, canonical JSON,
digest, and observable event sequence for the same complete input context.

## 12. Invariants

The following invariants are mandatory:

1. An Evidence is immutable.
2. An Evidence has exactly one authoritative source.
3. An Evidence does not know another Evidence.
4. An Evidence never directly creates a Decision.
5. A Hypothesis is derived from explicit evidence references.
6. A Hypothesis remains reversible and can be invalidated.
7. A Hypothesis never decides.
8. A Scenario contains only explicitly compatible hypotheses.
9. Multiple contradictory scenarios may coexist.
10. A Scenario is deterministically rankable.
11. A Candidate represents exactly one proposed action.
12. A Candidate is filterable and never self-authorizing.
13. A Constraint only filters, restricts, accepts, rejects, or declares unavailability.
14. A Constraint never creates analytical support or a new Candidate.
15. Mandatory constraints fail closed.
16. Ranking considers only admissible candidates.
17. Ranking uses explicit stable tie-breaking.
18. A Recommendation is the highest-ranked admissible candidate.
19. A Decision is a validated Recommendation that survived every mandatory constraint.
20. A Decision is immutable, versioned, explainable, reproducible, and audited.
21. A Decision never executes itself.
22. WAIT and INVALID are explicit outcomes.
23. Rejected alternatives remain explainable.
24. Confidence, quality, validity, and uncertainty remain independent.
25. Technical metadata never changes business meaning.
26. Canonical serialization preserves identity, provenance, ordering, and digest.
27. Identical complete inputs produce identical observable outputs.
28. No stage may mutate an input owned by another stage or domain.

## 13. Prohibitions

EPIP-016 explicitly prohibits:

- randomness or random tie-breaking;
- machine learning in the official deterministic decision path;
- hidden heuristics or undocumented weights;
- ordering that depends on dictionary, set, hash, memory, or discovery order;
- direct use of system time in decision logic;
- random UUID generation in decision logic;
- runtime object identity as business identity;
- hidden shared mutable state;
- mutation of Evidence;
- mutation of a Decision;
- implicit constraint acceptance;
- silent removal of contradictory evidence or alternatives;
- duplication of Risk, Portfolio, Compliance, Security, or Execution responsibilities;
- callbacks or external side effects during conceptual evaluation;
- explanations generated independently from the decision provenance.

Any future probabilistic, statistical, or learned capability must remain outside the official
deterministic path until governed by a separate accepted ADR. Its output, if ever consumed, must be
treated as versioned external Evidence rather than an authority that bypasses this model.

## 14. Relationship with H001–H007

EPIP-016 reuses the existing hardening architecture and creates no parallel infrastructure.

### H001 — Determinism and Identity

H001 supplies injected clocks, deterministic identity generation, canonical identity semantics,
and replay reproducibility. EPIP-016 uses those services for evidence, hypotheses, scenarios,
candidates, decisions, explanations, and events.

### H002 — Data Integrity

H002 supplies immutability, validation, canonical representation, provenance integrity, and digest
guarantees. EPIP-016 applies those guarantees to every conceptual artifact and transition.

### H003 — Financial Correctness

H003 preserves authoritative financial meanings, dimensions, and validation boundaries. EPIP-016
does not recompute financial facts and does not reinterpret invalid monetary or market data as
valid evidence.

### H004 — Thread Safety and Concurrency

H004 supplies concurrency contracts, ownership, atomicity, isolation, and post-commit event
publication. EPIP-016 evaluation must respect those contracts and expose no hidden shared state.

### H005 — Memory Safety and Resource Management

H005 supplies lifecycle, retention, bounded history, recovery, and resource ownership policies.
EPIP-016 explanations and decision graphs must follow those policies and cannot create unbounded
or orphaned retention.

### H006 — Reliability and Fault Tolerance

H006 supplies exception taxonomy, retries, circuit breakers, degradation, and recovery contracts.
EPIP-016 uses those mechanisms at infrastructure boundaries while keeping decision semantics
explicit. Infrastructure failure cannot silently become positive evidence or constraint approval.

### H007 — Security and Defensive Programming

H007 supplies trust boundaries, validation contracts, security policies, secure failure handling,
audit, and observability. EPIP-016 validates all inputs according to their trust level and treats an
untrusted, unauthorized, or invalid source as ineligible evidence.

Together, H001–H007 provide the identity, integrity, correctness, concurrency, memory, reliability,
and security foundations required by this theory. EPIP-016 composes those guarantees; it does not
replace, fork, or duplicate them.

## Consequences

- The decision pipeline becomes conceptually explicit and institutionally auditable.
- Observation, interpretation, filtering, ranking, decision, and execution remain separate.
- Every selected and rejected alternative remains explainable.
- Deterministic replay includes the decision and its explanation.
- Existing EPIP domains retain authority over their own facts and constraints.
- Future implementation work is constrained by the invariants and prohibitions in this ADR.
- This ADR changes no public API, financial calculation, serialization format, or runtime behavior.

## Approval Criterion

This ADR is suitable for approval when a developer can understand the complete EPIP-016 decision
model, its stages, responsibilities, relationships, guarantees, and prohibitions without reading
implementation code.

After acceptance, every EPIP-016 implementation and review must demonstrate conformance to this
ADR before it can be merged.
