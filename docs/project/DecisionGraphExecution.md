# Decision Graph Execution

Decision graph execution is a structural scheduling operation. It determines
when a node is eligible to run; it does not execute financial or inference
logic.

## Planning

`DecisionExecutionPlan.from_graph()` first validates the complete graph. A
plan is produced only when every dependency is present and the topology is a
directed acyclic graph.

The planner applies Kahn's algorithm with a lexical priority queue. Nodes with
no remaining dependencies are selected by identifier. This makes ordering
stable across processes and independent of construction order.

## Layers

The plan groups nodes into immutable layers. All nodes in a layer depend only
on nodes in earlier layers. A consumer may process a layer sequentially or use
its own concurrency policy, but EPIP does not claim parallel execution merely
because nodes share a layer.

## Failure policy

Planning fails closed. Invalid references, missing declarations, orphan nodes,
and cycles raise `ValueError`; no partial plan is returned. Callers that need
non-raising inspection use `DecisionGraphValidator.diagnose()` or
`DecisionGraphAudit.inspect()`.
