# P02-F08 Ranked Candidate Selection Contract

## 1. Status and authority

P02-F08 is the additive governance reconciliation between the frozen P02-F03 execution model and
the frozen P02-F06 Target transition. Actual implementation remains authoritative where earlier
text and code differ. ADR-0022 records this decision. P02 implementation may resume only after
this contract, its minimal contract implementation, tests, and exact-SHA validation are closed.

## 2. Confirmed contradiction

`CandidateSelectionRequest` uses the shared candidate normalizer. It validates an exact non-empty
`SemanticCandidate` tuple, rejects duplicate candidate identities, and sorts by `candidate_id`.
That is correct for canonical, set-like selection. It is insufficient for Target extension because
P02-F06 requires the extension selector to receive the exact permutation emitted by Target
ranking. For example, ranking output `(candidate_z, candidate_a)` must not become
`(candidate_a, candidate_z)` at the next boundary.

## 3. Additive request split

`CandidateSelectionRequest` remains the canonical unordered request. Its existing sorting,
validation, immutability, equality, hashing, and serialization behavior are frozen.

`RankedCandidateSelectionRequest` is a distinct frozen, slotted dataclass with the same contextual
fields and an ordered non-empty `SemanticCandidate` tuple. Caller-provided order is semantic and
is preserved exactly. The request performs no sort or canonical reorder. Exact candidate typing,
candidate identity reconstruction, duplicate-ID rejection, context typing, optional exact
`StrategyDirection` typing, immutability, deterministic equality, and hashing remain fail closed.
Because `candidate_id` is the digest of the complete semantic candidate payload, a duplicate
semantic candidate necessarily has a duplicate ID and is rejected by the same invariant.

## 4. Target extension transition

After Target ranking returns an exact permutation, the future adapter must resolve every ranked ID
to the original request candidate and construct `RankedCandidateSelectionRequest` with that exact
tuple. Identity, cardinality, lineage, payload, and order must be unchanged. The configured Target
extension rule is invoked once with this ordered request.

Successful extension names exactly one input member. Zero winners, multiple winners, duplicate
winner references, an unknown winner, a non-success state, or a winner without required `PRICE`
is invalid rule output. Existing F04 translation makes that adapter `INVALID_INPUT`; no repair,
fallback, magnitude comparison, distance heuristic, or implicit transformation is permitted.

## 5. Invocation, result, resolver, and profile compatibility

No new semantic family or invocation kind is required. Target extension remains the existing
`CANDIDATE_SELECTION` family with `SELECTION` invocation and `SELECTION` result. The request shape
distinguishes ranked extension input without creating a competing taxonomy. Its existing
`RuleIdentity`, manifest declaration, exact profile closure, and implementation binding remain
unchanged. Resolver rejection of missing, extra, family-mismatched, invocation-mismatched,
result-mismatched, identity-conflicting, or implementation-mismatched rules remains authoritative.

## 6. Serialization and reconstruction

The existing tagged dataclass serializer records the candidate tuple in field order. Reconstruction
calls the request constructor and therefore validates every candidate and duplicate invariant while
retaining the supplied order. Reordered but otherwise valid serialized candidates reconstruct in
that reordered order; they are never silently canonicalized. Empty, duplicate, malformed,
non-`SemanticCandidate`, or invalid tagged payloads fail closed. Requests carry no separate
semantic identity, so P02-F08 invents none and serializes no executable implementation.

## 7. Determinism and boundaries

Ordered state is deterministic because it is explicit input, not ambient discovery. No time,
filesystem, network, broker, MT5, registry, latest-version lookup, `Any` semantic payload,
mutable mapping, `eval`, `exec`, or pickle behavior is introduced.

P01 adapter protocols and result vocabulary remain frozen. A07 geometry and identity semantics
remain frozen. P02 semantic families, rule identities, resolver behavior, and all non-Target
requests remain unchanged. P03 runtime orchestration, P04 Elliott/Fibonacci semantics, and P05 MTF
semantics remain unauthorized.

## 8. Implementation and validation closure

P02-F08 may add only the ordered request, its request union and public export, compatibility in the
pure selection transition validator, focused tests, mechanical immutable-compliance expectation,
and this governance record. It must not implement `CanonicalFactAdapter`, dispatch, orchestration,
or a concrete rule.

Closure requires proof that `(candidate_z, candidate_a)` is stored, serialized, and reconstructed
in that order; canonical selection still sorts; ordered equality and hashing reflect order;
duplicates and invalid payloads fail closed; exact-one Target extension selection works; predecessor
nodes are not removed; all required regressions, coverage, quality, documentation, compliance, and
exact-SHA remote checks pass.

## 9. Gate for resuming P02

After P02-F08 is CLOSED / FROZEN, the ranked-information-loss contradiction is closed and P02 may
return to a separate implementation authorization. This milestone does not itself authorize P02,
P03, P04, P05, release, tagging, or deployment.

Remaining implementation-significant ambiguities: **NONE**.
