# Decision Topology

`DecisionTopology` is the immutable, validated view of a decision graph's
shape.

## Views

The topology exposes:

- roots with no incoming dependencies;
- leaves with no outgoing dependants;
- parent identifiers for every node;
- child identifiers for every node;
- stable topological layers.

Parent and child mappings use `MappingProxyType`, while their values are
tuples. Consumers cannot mutate the topology through a returned view.

## Root policy

Multiple roots are valid because independent evidence or constraints may
enter the same decision structure. Boundaries that require one entry point can
set `require_single_root=True`. This policy changes validation only and never
rewrites the graph.

## Diagnostics and audit

`DecisionGraphStatistics` reports node, edge, root, leaf, and depth counts.
`DecisionGraphAudit` combines those statistics with validation failures and a
plan when the graph is valid. A failed audit preserves diagnostic evidence and
does not expose a partial execution plan.

## Snapshot integrity

Snapshots bind canonical graph JSON to a SHA-256 digest. Restoration verifies
the digest before parsing and then reconstructs the same immutable graph.
Tampered payloads or digests are rejected.
