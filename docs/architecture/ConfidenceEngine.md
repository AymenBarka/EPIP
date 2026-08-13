# Confidence Engine

The EPIP-016 Confidence Engine creates immutable descriptive assessments for
validated decision candidates. It evaluates each candidate independently and
does not rank, select, recommend, authorize, or execute an action.

## Boundary

The engine consumes only a candidate and its stable Evidence, Hypothesis,
Scenario, and Decision Graph references. It does not read market, portfolio,
risk, execution, clock, or other runtime state.

## Components

- `ConfidenceBuilder` resolves provenance and performs deterministic propagation.
- `ConfidenceEngine` assesses requested candidates independently.
- `ConfidenceRegistry` and `ConfidenceCollection` provide immutable indexes.
- `ConfidenceSnapshot` provides canonical replay serialization.
- `ConfidenceAudit` and `ConfidenceDiagnostics` expose read-only observations.

Every digest is SHA-256 over canonical JSON containing immutable business
content. Timestamps, runtime identity, memory addresses, and hash order never
participate.

## Architectural prohibition

Confidence is not a probability of profit. The engine produces no final score,
winner, candidate comparison, or trading signal. Selection remains the sole
responsibility of Programme G.

## Example

```python
report = ConfidenceEngine(resolver, candidates).assess(
    ("candidate-a",),
    graph_node_ids=("candidate-node",),
)
assessment = report.assessments.items[0]
```

The report contains the immutable collection, registry, snapshot, audit, and
diagnostics for the assessment request.
