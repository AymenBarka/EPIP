# Decision Dependencies

A decision dependency is an explicit declaration that one node requires the
structural output of another node.

## Contract

Each `DecisionNode` lists `DecisionDependency` values. Each dependency must be
represented by exactly one `DecisionEdge` from the dependency to the dependent
node. Edges without declarations and declarations without edges are invalid.

Dependencies use stable node identifiers rather than runtime object identity.
They do not contain callbacks, mutable objects, scores, or inferred business
meaning.

## Validation rules

- A node identifier must be non-empty and unique.
- A dependency must reference an existing node.
- A node cannot depend on itself.
- Duplicate edges are forbidden.
- Cyclic dependency chains are forbidden.
- Disconnected nodes are forbidden when a graph contains multiple nodes.

The validator reports every detected structural failure in deterministic
order. It never inserts, removes, or rewrites dependencies.
