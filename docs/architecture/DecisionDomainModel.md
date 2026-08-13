# Decision Domain Model

EPIP-016 introduces an immutable vocabulary for decision reasoning. It separates evidence, hypotheses, scenarios, candidates, recommendations, constraints, explanations, decisions, and snapshots without implementing ranking or trading algorithms.

## Responsibilities

- Evidence records attributable facts and stable source metadata.
- Hypothesis records a testable interpretation and its evidence references.
- Scenario groups compatible hypotheses and explicit invalidation conditions.
- DecisionCandidate represents a possible action and evaluated constraints.
- Recommendation identifies the proposed disposition of one candidate.
- Decision records the approved outcome, context, explanation, and metadata.
- DecisionSnapshot captures one versioned immutable decision.

## Invariants

All records are frozen and slotted. Identifiers and versions are explicit, normalized scores remain in the closed interval zero to one, collections are tuples, and scenarios cannot reference themselves. Equality, hashing, canonical JSON, and content digests depend only on stored values.

## Lifecycle

Evidence feeds hypotheses; hypotheses form scenarios; scenarios support candidates; constraints qualify candidates; recommendations and explanations support the final decision; snapshots preserve the resulting state.

No object in this module executes orders, computes financial values, or selects a winning candidate.
