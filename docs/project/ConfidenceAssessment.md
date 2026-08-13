# Confidence Assessment

## Assessment

`ConfidenceAssessment` is the immutable output for exactly one candidate. Its
identifier is derived from candidate identity, candidate version, and ordered
graph references. The assessment includes all eight metrics and its canonical
digest.

## Registry and collection

The registry rejects duplicate assessment identifiers and provides deterministic
lookup by identifier, candidate, confidence level, quality level, and digest.
Collections support immutable filtering, grouping, lookup, and ordered
iteration.

## Snapshot and replay

Snapshots serialize as canonical JSON with an explicit format version and
SHA-256 digest. Deserialization validates types, normalized ranges, assessment
digests, and the snapshot digest. A round trip is byte stable.

## Audit and diagnostics

Audit reports assessment, duplicate, validation-failure, coverage, and registry
statistics without mutating runtime state. Diagnostics report missing
candidates, invalid provenance or graph references, duplicate identifiers,
digest inconsistencies, and registry/snapshot inconsistencies. Diagnostics
never repair data.

## Interpretation

An assessment describes one candidate in isolation. It must not be interpreted
as a probability of profit, candidate rank, recommendation, risk approval, or
authorization to trade.
