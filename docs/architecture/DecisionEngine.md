# Decision Engine

The EPIP-016 Decision Engine performs deterministic final selection from
immutable candidates, confidence assessments, graph references, and declared
constraint results. It selects but never analyses the market.

## Boundary

The engine does not create Evidence, Hypotheses, Scenarios, Candidates, or
Confidence Assessments. It does not calculate risk, portfolio, exposure,
security, compliance, or runtime facts. It consumes their immutable results and
never executes a decision.

## Components

- `DecisionConstraintEvaluator` applies declared mandatory results fail-closed.
- `DecisionSelector` applies the published deterministic selection policy.
- `DecisionExplanationBuilder` derives explanation from preserved provenance.
- `DecisionTrace` records selected and rejected candidates and applied facts.
- `DecisionRegistry` enforces lifecycle and deterministic indexes.
- `DecisionSnapshot` provides canonical serialization and replay.
- `DecisionAudit` and `DecisionDiagnostics` expose read-only observations.

Identical complete inputs produce the same decision, explanation, trace, digest,
and snapshot. Runtime identity, timestamps, randomness, discovery order, and
hash order never participate.

## Example

```python
report = DecisionEngine(
    resolver,
    candidate_registry,
    confidence_registry,
).decide(context)
decision = report.decision
```

A `None` decision with a validation failure indicates that immutable inputs did
not permit a structurally valid selection.
