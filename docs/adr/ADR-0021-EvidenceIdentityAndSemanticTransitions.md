# ADR-0021: Evidence Identity Separation and Governed Semantic Transitions

## Status

Accepted

## Context

The final post-P02-F05 readiness review found five contract gaps. A07 treats snapshot evidence
identity as member identity while P01 required it to equal one bundle-level set identity. The
evidence-set helper discarded governed ordering. MTF aggregation had no profile-bound source for
per-frame directions. Entry point/range conversion and stop/target single-winner transitions were
not explicit. Implementing the adapter would therefore require observable policy invention.

## Decision

EPIP separates evidence-item identity from evidence-set identity without changing A07. Snapshot
identities use `epip.strategy-evidence-item.p02-f06-v1` and commit to the exact key, profile,
adapter, analytical bundle, provenance, rule identities, selected lineage, freshness, and temporal
eligibility. The bundle identity uses `epip.strategy-evidence-set.p02-f06-v1` and commits to the
final semantically ordered collection of item identities and lineage. P01 no longer requires
snapshot identities to equal the set identity; it instead requires unique item identities and
coherent strategy identity.

Evidence ordering receives canonically key-sorted included keys, must return their exact
permutation, and governs final snapshot and set-identity order. The identity helper does not
re-sort semantic output.

`MtfDirectionPolicyRef` gains one non-MTF `frame_direction_fact`. P02 reuses that existing
direction policy independently per required typed frame, preserving timeframe, role, source, and
provenance in `TimeframeDirectionValue`; only the P05-owned executable rule aggregates them.

Entry `PRICE` boundary output is a degenerate range and `PRICE_RANGE` supplies exact bounds. Stop
precedence and target extension success each require exactly one request-member candidate. Entry
and target ranking use the already governed first ordered ID. Contextual cardinality, permutation,
lineage, and shape violations are invalid rule output, never fallback or non-match.

## Consequences

A07 and `FactAdapterProtocol` remain frozen. P02-F07 must make narrow additive corrections to the
P01 bundle evidence invariant, P02 MTF profile field, evidence identity helpers, serialization,
fingerprinting, closure validation where applicable, and focused tests. It must not implement the
adapter or concrete strategy content. P02 remains blocked until P02-F07 closes and a new readiness
review succeeds.

The generic adapter can then assemble deterministic synthetic BUY/SELL, MTF, geometry,
confidence, and multi-key evidence flows without P03, P04, or P05 semantics and without selecting
a candidate itself.
