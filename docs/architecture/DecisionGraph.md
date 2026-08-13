# Decision Graph

The EPIP-016 decision graph is the deterministic structural layer between
inference outputs and later decision evaluation. It represents evidence,
hypotheses, scenarios, constraints, aggregations, and candidates as immutable
nodes connected by explicit directed dependencies.

## Architectural boundary

The graph describes relationships only. It does not interpret market data,
score evidence, infer hypotheses, select trades, or perform financial
calculations. Programmes A through C remain the owners of their domain models
and inference behaviour.

## Immutable model

`DecisionGraph` contains tuples of `DecisionNode` and `DecisionEdge` values.
Node metadata is exposed through an immutable mapping. A node declares every
dependency explicitly, and each declaration must have exactly one matching
edge. Graph snapshots preserve the canonical payload, digest, and topology.

## Determinism

Canonical serialization uses sorted keys, compact JSON, and stable ordering.
Topological execution uses lexical node identifiers to break ties. Equivalent
graphs therefore produce the same topology, execution order, JSON payload,
and SHA-256 digest regardless of insertion order.

## Structural guarantees

Validation rejects duplicate nodes, duplicate edges, self-edges, unknown
references, missing or undeclared dependencies, cycles, and disconnected
nodes. Multiple roots are permitted by default and can be prohibited at a
validation boundary.

## Public components

- `DecisionGraphBuilder` constructs graphs without repairing invalid input.
- `DecisionGraphValidator` reports complete deterministic diagnostics.
- `DecisionTopology` exposes roots, leaves, parents, children, and layers.
- `DecisionExecutionPlan` exposes stable topological execution.
- `DecisionGraphSnapshot` verifies canonical payload integrity.
- `DecisionGraphAudit` combines diagnostics, topology statistics, and plan.
