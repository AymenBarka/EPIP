# Candidate Model

The candidate model represents a possible decision outcome assembled from
validated EPIP-016 inputs.

## Identity and content

A candidate contains a deterministic identifier, candidate type, scenario
reference, evidence references, graph-node references, lifecycle state, version,
and immutable metadata. Its digest is derived from canonical serialized content.

Technical metadata does not introduce implicit ranking or preference. Two
candidate values compare using their complete immutable value semantics, while
the digest provides stable content identity for persistence and replay.

## Supporting models

- `CandidateDigest` records canonical content identity.
- `CandidateStatistics` reports deterministic aggregate counts.
- `CandidateAudit` records registry and lifecycle observations.
- `CandidateDiagnostics` reports validation findings without mutation.
- `CandidateGenerationReport` records generation inputs and outputs.
- `CandidateSnapshot` captures a complete immutable registry view.

## Serialization

Serialization uses canonical JSON-compatible values with stable ordering.
Deserialization validates field types, lifecycle values, relationships, and
digests. A valid round trip preserves identity, equality, ordering, and digest.

## Explicit exclusions

The model contains no score-based selection, recommendation, execution command,
position sizing, portfolio allocation, or financial calculation.
