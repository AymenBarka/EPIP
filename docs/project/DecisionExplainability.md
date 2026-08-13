# Decision Explainability

Every selected Decision preserves:

- the selected Candidate and every rejected Candidate;
- applied constraints and their immutable results;
- the consumed Confidence Assessment identity and digest;
- Evidence, Hypothesis, and Scenario references;
- Decision Graph references;
- deterministic selection reasons and rejected-alternative reasons;
- uncertainty retained from the assessment.

`DecisionExplanation` is embedded in the final domain Decision.
`DecisionTrace` records the causal inputs independently for audit and replay.
Neither is generated from mutable runtime state or a narrative model.

Snapshots contain Decisions, traces, and lifecycle states in canonical JSON.
Their SHA-256 digest depends only on immutable content. Deserialization validates
field types, references, lifecycle values, nested digests, and the snapshot
digest before accepting replay data.

Audit counts selections, rejected Candidates, constraint applications,
duplicates, validation failures, and registry statistics. Diagnostics report
missing constraints or confidence, invalid references or lifecycle states,
duplicate identifiers, and digest or snapshot inconsistencies. Neither facility
automatically corrects data.
