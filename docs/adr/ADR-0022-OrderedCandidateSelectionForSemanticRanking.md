# ADR-0022: Ordered Candidate Selection for Semantic Ranking

## Status

Accepted

## Context

The P02-F03 implementation correctly canonicalizes `CandidateSelectionRequest` candidates by
identity for unordered subset selection. P02-F06 later required Target extension to consume the
complete tuple produced by ranking in ranking-rule order. Reusing the canonical request erased
semantic ordering and left a future adapter unable to satisfy both frozen contracts.

## Decision

EPIP adds `RankedCandidateSelectionRequest`. It is immutable, preserves the exact non-empty
caller-provided `SemanticCandidate` tuple, rejects duplicate identities, and participates in the
existing tagged serialization and strict reconstruction model. `CandidateSelectionRequest`
retains its canonical sorting behavior.

Target extension uses the ranked request. The existing selection transition validator accepts
either exact request contract and still requires a successful exact-one input-member winner, with
`PRICE` enforced for Target extension. No request order is repaired or inferred.

No semantic family, invocation kind, result kind, manifest declaration, resolver rule, profile
field, or rule identity changes. Target extension remains `CANDIDATE_SELECTION / SELECTION /
SELECTION`; the additive request type expresses the distinct input semantics.

## Consequences

P01 and A07 remain frozen. P03, P04, and P05 ownership is unchanged. The future
`CanonicalFactAdapter` can pass Target ranking output into extension without information loss, but
neither the adapter nor any concrete strategy semantics are implemented here. P02 may resume only
under separate authorization after P02-F08 validation and publication close.
