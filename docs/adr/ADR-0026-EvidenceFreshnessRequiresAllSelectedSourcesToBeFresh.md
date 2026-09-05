# ADR-0026: Evidence Freshness Requires All Selected Sources To Be Fresh

- **Status:** Accepted
- **Milestone:** P02-F16 evidence freshness cardinality reconciliation
- **Decision scope:** Generic P02 evidence behavior only

## Context

One evidence mapping may select multiple candidates and source bindings, but the frozen A07
snapshot exposes one freshness Boolean. Existing contracts define per-source age and threshold
semantics but did not define how multiple selected sources reduce to that Boolean. Selecting one
source or accepting any fresh source would silently discard temporal meaning from contributing
lineage.

## Decision

P02 evaluates freshness once for every unique source binding referenced by the non-empty mapped
selected subset. Each source uses the evidence key's single configured observation-or-availability
basis, the shared explicit evaluation timestamp, and the inclusive existing maximum-age boundary.
The evidence item is fresh if and only if every selected source is fresh.

Any selected future or malformed timestamp is structural `INVALID_INPUT`; it is not reduced as
stale. A stale required item is `REJECTED`. A stale optional item is omitted under the existing
P02-F04 authorization. Freshness remains separate from and precedes temporal validity and revision
eligibility.

The rule is invariant under candidate, binding, and frame order. It does not choose a newest,
oldest, first, canonical, PRIMARY, HIGHER, or LOWER source. `ANY` semantics are rejected because
they allow one fresh source to mask stale evidence that remains part of the item's lineage.

## Consequences

The reduction is native generic P02 structure rather than an executable semantic rule. Existing
policy fields are sufficient. P01, A07, source resolution, exact closure, serialization, profile
fingerprinting, and evidence identity algorithms do not change. The final reduced Boolean enters
the existing item identity; complete selected lineage remains auditable.

P02-F17 will implement and test only this private mechanical boundary. `CanonicalFactAdapter`
remains blocked until F17 closes. P03, P04, and P05 are not authorized.
