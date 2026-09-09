# A07 E02/E08 Ordered Evidence-Set Continuity Reconciliation

## Status and decision

The A07 E02/E08 ordered evidence-set continuity contract is **NORMATIVELY RECONCILED**.
Implementation remains a separate milestone. P03-F00 stays blocked until that implementation is
complete and verified. This reconciliation changes no production code, tests, schema, identity
algorithm, or serialization format.

## Discovery and confirmed defects

P03-F00 design exposed two independent contradictions between frozen A07 and the later frozen
P01/P02 evidence model.

First, A07 E02 `_snapshots()` accepts a tuple and then sorts it by evidence key, item identity,
provenance, and strategy identity. `EvidenceBinding` therefore makes permutations equal and loses
the P02-authoritative semantic order. Its equality and hash include that reordered tuple, and
`test_binding_derives_all_fields_and_canonicalizes_permutations` explicitly freezes the obsolete
behavior.

Second, A07 E08 `SignalExpiration` requires every snapshot item identity to equal the single
`StrategyEvaluationRequest.evidence_identity`. P02 deliberately assigns distinct identities to
items and one different identity to their ordered set. For two distinct members, both item
identities cannot equal the same set identity.

No other A07 source transforms the evidence collection. Other uses of `sorted`, `set`, and
`frozenset` govern diagnostics, policy declarations, or duplicate detection. E09 carries the E08
predecessor indirectly but contains no evidence identity or evidence reordering rule.

## Authoritative P01/P02 model

An evidence-item identity identifies one immutable `StrategyEvidenceSnapshot`, including its key,
semantic mapping, selected lineage, freshness, temporal eligibility, profile, adapter, bundle, and
manifest provenance. Item identities are unique within a bundle.

`StrategyFactBundle.evidence_identity` is the evidence-set identity. It identifies the complete,
non-empty ordered evidence collection. Its digest commits to each ordered key, item identity,
candidate selection, source binding, and lineage. P02's successful evidence-ordering rule supplies
the authoritative final order; `derive_evidence_set_identity()` consumes that order without
sorting. Therefore order is semantic:

```text
(item A, item B) != (item B, item A)
```

Item and set identities occupy different semantic namespaces. Their equality is neither required
nor privileged, including when cardinality is one.

P01 validates unique keys and item identities and commits both the set identity and exact evidence
tuple into the immutable bundle identity. P02 owns item/set derivation and semantic ordering. Both
remain correct and frozen.

## E00 meaning and input continuity

`StrategyEvaluationRequest.evidence_identity` unambiguously represents the complete P01/P02
evidence-set identity. Its existing opaque `StrategyEvidenceIdentity` type and field shape are
compatible with that meaning.

The bundle-to-A07 transition must satisfy:

```text
a07_request.evidence_identity == bundle.evidence_identity
admitted_evidence == bundle.evidence
```

The second equality is exact tuple equality, including item order and immutable content. The
transition copies these values; it never reconstructs, sorts, collapses, or derives identities.
The future P03 implementation owns this exact transition because it holds the accepted bundle and
constructs E00. `a07_request` means `StrategyEvaluationRequest`, not the P01
`StrategyRuntimeRequest`. This is preservation of the P02-authoritative identity, not comparison
against an independent caller expectation, P03 identity reconciliation, or workaround.

## E02 ownership and replacement invariant

E02 owns structural tuple/type/duplicate validation, evidence-policy reconciliation, and A07
acceptance diagnostics. It does not own P02 semantic ordering or item/set identity derivation.

E02 must validate the supplied tuple without reordering. `EvidenceBinding.available_evidence`
preserves the exact input tuple. `bound_required` and `bound_optional` remain policy projections in
their existing policy-declaration order; they do not replace or reorder `available_evidence`.
Downstream predecessors retain the exact binding by immutable value equality.

Duplicate evidence keys or duplicate item identities remain malformed structural input and raise
`DataIntegrityError`. This duplicate check may use a set for cardinality comparison; it must not
materialize or reorder evidence through that set.

## E08 replacement invariant and membership model

E08 must remove item/set equality. The governed rule is:

- the E00 request identity remains the set identity;
- every E08 snapshot is an exact member of the E02-admitted ordered tuple;
- E08 reaches that tuple only through the immutable `EvidenceValidation` -> `DirectionalDecision`
  -> geometry -> reward/risk -> `StrategyConfidence` predecessor chain;
- E08 verifies that every item identity retains the same manifest provenance as the set identity;
  and
- E08 never recomputes set membership or an identity digest.

The exact set ID is proven at the bundle-to-E00 transition. Within A07, exact immutable predecessor
equality proves member, content, cardinality, and order preservation. Set/member manifest
provenance completes the minimum A07-owned continuity check. An arbitrary opaque set ID cannot be
reverse-verified by A07 without violating dependency direction; that is why exact set equality is
checked where both bundle and request exist.

Missing, extra, mutated, or reordered members between admission and E08 are predecessor-integrity
failures. Existing constructors/reconstruction checks must fail closed with `DataIntegrityError`.
No partial acceptance, automatic extension, repair, or reordering is allowed.

## Cardinality and provenance

Cardinality one, two, and greater than two are valid. Every member has a unique item identity and
the collection has one distinct set identity. All item identities and the set identity must carry
the same exact provenance manifest reference. Existing A07 strategy-identity checks remain in
force. P01/P02 retain evaluation, profile, adapter, source, and fact lineage; the bundle-to-E00
boundary retains evaluation and set identity continuity.

## Normative E00 -> E02 -> E08 chain

```text
P02 ordered StrategyEvidenceSnapshot tuple + set identity
-> immutable P01 StrategyFactBundle
-> E00 request with the same set identity and exact bundle tuple
-> E02 structural/policy validation without reordering
-> immutable A07 predecessor chain preserving the exact EvidenceBinding
-> E08 member and common-manifest provenance continuity
-> E09 signal construction
```

No stage changes tuple order or reinterprets a set identity as an item identity.

## Failure vocabulary and diagnostics

No public diagnostic or state expansion is required.

- Duplicate keys/identities, malformed evidence, reconstruction mismatch, missing/extra/mutated/
  reordered predecessor members, and set/member provenance mismatch are structural integrity
  failures expressed by deterministic sanitized `DataIntegrityError` messages.
- Missing required, unexpected, stale, temporally ineligible, and strategy-mismatched evidence
  retain the existing E02 validation diagnostics.
- A mismatch introduced while constructing E00 is a P03 implementation defect. It is prevented
  and tested by observing that the A07 request receives the exact accepted-bundle identity; it is
  not a caller-supplied runtime coherence state and requires no new failure vocabulary.

E02 needs no new diagnostic code: it either preserves a structurally valid tuple or rejects
malformed structure. E08 likewise needs no new diagnostic record; set/member provenance or
predecessor discontinuity is a contract-integrity error. Messages must name only the stable
continuity category and must not expose payloads or object representations.

## Dependency and identity-algorithm constraints

`epip.a07` must not import `epip.strategy_mapping` or call/copy
`derive_evidence_item_identity()` or `derive_evidence_set_identity()`. A07 consumes opaque validated
identities. P02 remains the sole derivation authority and no second SHA/digest implementation is
authorized.

## Serialization, hashing, and compatibility

No fields, constructors, tagged payloads, serializer registrations, profile/runtime fingerprints,
identity domains, or digest formulas change. Public API signatures remain stable. Existing P02
bundles with distinct item/set identities become admissible end to end. Legacy equal item/set
values receive no special case and are accepted only when all ordinary structural, policy, and
provenance rules succeed.

E02 value equality and hashing remain order-sensitive after implementation because
`available_evidence` retains the supplied semantic tuple. Reversing members creates a different
binding rather than an equivalent canonical permutation.

## Exact implementation impact

The separately authorized `A07-E02-E08-R01` milestone may change only:

- `epip/a07/evidence.py`: remove `_snapshot_key` and the sort in `_snapshots`; preserve input order;
- `epip/a07/confidence.py`: replace item/set equality with exact common-manifest provenance and
  immutable-predecessor continuity; and
- `tests/a07/test_evidence.py` and `tests/a07/test_confidence.py`: focused governed expectations.

Minimal documentation status updates may accompany the implementation. No P01, P02, P03, E00,
E09, serialization, profile, adapter, or identity-helper production file is authorized.

## Test migration

| Old test | Old expectation | Why invalid | New expectation/action in R01 |
| --- | --- | --- | --- |
| `test_binding_derives_all_fields_and_canonicalizes_permutations` | Reversed inputs produce equal bindings sorted lexically | P02 order is semantic and set-identity-significant | Rename to an order-preservation test; assert each input order is retained and reversed bindings differ |
| `test_binding_reconstruction_round_trip_and_contradictions` reversed-input case | Reversal conflicts with canonical sorted fields | Canonical sorting is superseded | Preserve round trip; assert reconstruction rejects fields from a different admitted order |
| `test_request_continuity_mismatch[evidence]` | Any request/item identity difference fails | It conflates set and member levels | Replace with set/member provenance mismatch and immutable-member discontinuity cases |

All other duplicate, malformed-container, policy-projection, immutability, reconstruction, and A07
stage tests remain valid unless their fixtures accidentally rely on item/set equality. Such fixture
updates may create distinct identities but may not weaken assertions.

## Mandatory R01 tests

R01 must prove exact E02 input-order preservation; unequal reversed bindings; cardinalities one,
two, and at least three with distinct item/set IDs; duplicate rejection; set/member provenance
mismatch rejection; missing, extra, mutated, and reordered predecessor rejection; strategy and
evaluation continuity; deterministic repetition; unchanged serialization; unchanged P01/P02
regressions; unchanged unrelated A07 stages; and a P03 blocker reproducer that proceeds through
E08 with a genuine P02-shaped multi-item set.

The wrong exact set-ID test belongs to the future P03 runtime boundary, where both bundle and E00
request are available. R01 must document this boundary explicitly and must not pretend A07 can
reverse an opaque P02 digest.

## P03 unblock criteria

P03-F00 remains blocked until R01 is separately authorized, implemented, locally and remotely
green, and closed/frozen. P03 may not reorder evidence, translate identity types, synthesize a set
identity, collapse item identities, special-case one item, or otherwise compensate for A07.

## Authorization decision

The two known defects are fully reconciled without schema or identity-algorithm changes. No third
A07 evidence transformation or E09 identity conflict was found. `A07-E02-E08-R01 Ordered
Evidence-Set Continuity Implementation` is ready for separate authorization. P03 implementation
remains blocked.
