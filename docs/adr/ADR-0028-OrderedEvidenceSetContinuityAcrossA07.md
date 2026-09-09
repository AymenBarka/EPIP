# ADR-0028: Ordered Evidence-Set Continuity Across A07

- **Status:** Accepted
- **Milestone:** A07 E02/E08 and P01/P02 continuity reconciliation
- **Decision scope:** Ordered evidence admission and set/member continuity through A07

## Context

ADR-0021 correctly separates P02 evidence-item identities from the identity of their semantically
ordered set. Two older A07 behaviors conflict with that later frozen model: E02 sorts evidence and
canonicalizes permutations, while E08 requires every item identity to equal the single E00
identity. P03 cannot invoke A07 for a genuine multi-item P02 bundle without violating one contract.

## Decision

`StrategyEvaluationRequest.evidence_identity` is the P01/P02 evidence-set identity. The exact
ordered `StrategyFactBundle.evidence` tuple is admitted to A07 with it. The bundle-to-E00 boundary
must copy both values exactly.

A07 E02 validates the tuple without sorting. Its binding preserves exact input order, and that
immutable binding flows through every successor. Duplicate keys and item identities remain
structural errors. A reversed tuple is a different semantic evidence set, not an equivalent
permutation.

A07 E08 no longer compares item identities to the set identity. It relies on exact immutable
predecessor continuity for membership, cardinality, content, and order, and requires every member
identity to carry the set identity's exact manifest provenance. Exact bundle/request set-ID
equality is validated at the boundary holding both objects. A07 never imports or duplicates P02
identity derivation.

Existing fields, public signatures, serializers, identity algorithms, fingerprints, and state
enums remain unchanged. Structural discontinuity uses `DataIntegrityError`; existing E02 policy
diagnostics retain their meanings.

## Consequences

P01 and P02 remain frozen and authoritative. A narrow implementation may modify only A07 E02/E08
and focused tests. Genuine one-item and multi-item P02 evidence sets can reach A07 without identity
collapse. P03 remains blocked until that implementation closes, and may never work around this
boundary.
