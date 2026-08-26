# P02-F06 Transition and Evidence Identity Contract

Status: NORMATIVE CONTRACT RECONCILED / IMPLEMENTATION NOT AUTHORIZED

Authority: [ADR-0016](../adr/ADR-0016-CanonicalStrategyPipeline.md),
[ADR-0017](../adr/ADR-0017-CanonicalStrategyRuntimeContracts.md),
[ADR-0018](../adr/ADR-0018-TypedStrategyMappingAndAvailabilityBoundaries.md),
[ADR-0019](../adr/ADR-0019-ImmutableSemanticRuleExecution.md),
[ADR-0020](../adr/ADR-0020-EvidenceMappingAndFailFastSemanticExecution.md), and
[ADR-0021](../adr/ADR-0021-EvidenceIdentityAndSemanticTransitions.md).

## 1. Purpose and scope

This governance-only milestone closes the five transition blockers found after P02-F05. It
authorizes no production code, test change, concrete rule, `CanonicalFactAdapter`, P03, P04, or
P05 behavior. P02-F07 must implement only the corrections frozen here, after which P02 requires a
new implementation-readiness review.

P02 may perform structural transformations only when their result is completely determined by an
immutable contract. Candidate choice, aggregation, scoring, price adjustment, and interpretation
remain executable-rule behavior. P02 never substitutes first, last, minimum, maximum, nearest,
farthest, mean, weighted mean, ATR, Fibonacci, Elliott, majority, fallback, or repaired output
unless an exact rule result has already made that choice.

## 2. Evidence item and set identities

The current model conflates two identities. Frozen A07 E02 treats
`StrategyEvidenceSnapshot.evidence_identity` as one evidence-member identity: snapshots must have
unique identities. P01 `StrategyFactBundle.evidence_identity` is the identity of the complete
included collection. A07 remains unchanged.

P02-F07 changes the narrow P01 bundle invariant. Every snapshot must retain the bundle strategy
identity, use a unique item identity, and have a unique evidence key. A snapshot item identity must
not be required to equal the bundle set identity. The bundle's canonical digest continues to
commit to the set identity and all snapshots. The P01 adapter protocol, result states, runtime
contracts, and serialization system do not change.

### Evidence-item identity

`derive_evidence_item_identity()` returns the existing A07 `StrategyEvidenceIdentity` type. Its
domain is exactly:

```text
epip.strategy-evidence-item.p02-f06-v1
```

Its SHA-256 payload contains:

```text
domain
strategy_id
strategy_version
semantic_profile_identity
adapter_identity
typed_bundle_id
provenance_manifest_id
evidence_key
mapping_rule
validity_rule
revision_rule
selected_candidate_ids
selected_source_binding_ids
selected_provenance_refs
fresh
temporally_eligible
```

Candidate IDs, source-binding IDs, and provenance references are non-empty, sorted, and unique.
The key is exact taxonomy text. Rule identities are exact profile-bound identities. The state
fields are exact booleans. The returned identity's `provenance` is exactly the manifest ID.
Different keys cannot share an item identity merely because they share mapping or source lineage.
No clock, iteration order, environment, or runtime address enters the digest.

### Evidence-set identity

`derive_evidence_set_identity()` continues to return `StrategyEvidenceIdentity`, used only as
`StrategyFactBundle.evidence_identity`. Its replacement domain is exactly:

```text
epip.strategy-evidence-set.p02-f06-v1
```

Its payload contains:

```text
domain
strategy_id
strategy_version
semantic_profile_identity
adapter_identity
typed_bundle_id
provenance_manifest_id
ordered entries of:
  evidence_key
  evidence_item_identity
  selected_candidate_ids
  selected_source_binding_ids
  selected_provenance_refs
```

Entries are consumed exactly as supplied after the evidence-ordering rule succeeds. The helper
must not sort them. Keys and item identities must each be unique, and every item identity's
provenance must equal the supplied manifest ID. The returned set identity also uses that manifest
ID as its `provenance`.

## 3. Evidence ordering

Before semantic ordering, included evidence records are held in canonical `evidence_key` order.
P02 passes exactly that sorted unique key tuple to `EvidenceOrderingRequest`. On `SUCCESS`,
`ordered_evidence_keys` must be an exact permutation of all and only included keys: non-empty,
same cardinality, no duplicate, unknown, or omitted key. Optional keys omitted earlier are absent
from both request and result. Required included keys may not be omitted.

P02 materializes final records by exact output order, derives item identities, derives the set
identity from that same ordered tuple, and constructs snapshots in that order. Semantic output is
not re-sorted. A malformed permutation is `RULE_OUTPUT_INVALID`, translated to adapter
`INVALID_INPUT`; it is not `NO_MATCH`, `REJECTED`, or repairable.

## 4. Per-frame direction and MTF input

Existing direction policies contain the selector, allowed states, direct enum map or exact
direction rule needed to produce a direction, but the profile does not select one for per-frame
MTF inputs. P02-F07 adds one mandatory field to `MtfDirectionPolicyRef`:

| Field | Type | Rule |
| --- | --- | --- |
| `frame_direction_fact` | `DirectionFactName` | One of the five non-MTF fact names |

`MTF` is forbidden. This reuses one existing `DirectionFactPolicy`; it creates no second direction
taxonomy and adds no executable identity. The field participates in canonical serialization,
reconstruction, equality, hashing, and semantic-profile fingerprinting. Exact closure already
traverses the referenced direction policy, so closure gains no new identity.

P02 selects typed frames whose timeframe is in `required_timeframes` and whose role is in
`required_roles`. Each required timeframe identifies exactly one frame, every required role is
represented, and no selected `(timeframe, role)` pair duplicates. Missing or ambiguous required
frames are structural `INVALID_INPUT`.

For each selected frame in PRIMARY, HIGHER, LOWER, then timeframe order, P02 applies the referenced
direction policy only to eligible sources in that frame. It invokes extraction in canonical
source-binding order, then performs the exact direct enum map or invokes the exact
`DIRECTION_MAPPING` rule. A required per-frame `NO_MATCH` becomes `REJECTED`; malformed output is
`INVALID_INPUT`; other terminal states retain F04 translation. The successful direction and exact
frame, source, and provenance values form one `TimeframeDirectionValue`. The canonical tuple is
supplied unchanged to `MTF_AGGREGATION`. P02 performs no aggregation.

## 5. Entry transition and cardinality

The exact entry sequence is applicability, candidate selection, ranking, boundary, and
`EntryFacts` construction.

Applicability runs once per extracted candidate in candidate-ID order. `False` removes that
candidate. Zero applicable candidates becomes required non-match and `REJECTED`. Selection returns
a non-empty unique subset. Ranking returns an exact permutation of that subset. Its first ID is the
explicit rule-governed winner already authorized by F02, not an input-order fallback. Boundary
runs once on that winner.

For successful boundary output:

- `PRICE_RANGE` maps exact validated bounds to `zone_lower` and `zone_upper`;
- `PRICE` maps structurally to `zone_lower == zone_upper == float_value`.

The scalar conversion adds no width, tick, epsilon, buffer, or market adjustment. Missing output,
wrong shape, invalid range, unknown candidate, or invalid permutation is `RULE_OUTPUT_INVALID` and
adapter `INVALID_INPUT`.

## 6. Stop precedence and final pipeline

The exact stop sequence is applicability, selection, precedence, buffer transformation, optional
volatility transformation, and `StopFacts`.

Applicability and selection follow the entry subset rules. `PRECEDENCE` receives the complete
selected candidate tuple. Its successful `SelectionRuleResult` must contain exactly one request
candidate ID. Zero cannot be successful; multiple or unknown IDs are `RULE_OUTPUT_INVALID` and
adapter `INVALID_INPUT`. P02 never chooses among them.

The winner enters mandatory buffer `PRICE_TRANSFORMATION`. Its result must preserve source,
provenance, instrument, and timeframe lineage and contain `PRICE`. Optional volatility consumes
that exact output under the same requirements. The final exact price becomes
`StopFacts.invalidation_price`. Buffer and ATR behavior remain P04 content.

## 7. Target extension and final pipeline

The exact target sequence is applicability, selection, ranking, optional threshold, optional
extension, and `TargetFacts`.

Applicability and selection follow entry. Ranking returns an exact permutation; its first ID is
the governed base winner. Configured threshold runs once on that winner; `False` is required
non-match and `REJECTED`. Absence skips it.

Without extension, the base winner must contain `PRICE`. With extension, the P02-F08 reconciliation
requires `RankedCandidateSelectionRequest` to contain the complete ranked candidate tuple in
ranking-rule order; canonical `CandidateSelectionRequest` remains reserved for unordered selection.
Success must name exactly one request candidate. Zero, multiple, duplicate, or unknown winners are
invalid output. That exact candidate must contain `PRICE` and becomes `TargetFacts.target_price`.
Extension selects; it does not implicitly transform or choose by magnitude or distance. A derived
extension price must already be an exact candidate produced by strategy-owned rules.

## 8. Failure and closure rules

For all reconciled transitions:

- required `NO_MATCH` becomes `REJECTED`;
- optional-evidence omission remains the sole non-terminal exception;
- rule terminal states retain F04 translation;
- contextual subset, permutation, cardinality, lineage, or shape violation is
  `RULE_OUTPUT_INVALID` and adapter `INVALID_INPUT`;
- unexpected executable exceptions become sanitized `FAILED`;
- malformed output is never repaired or converted to non-match.

The new profile field adds no identity. Existing closure remains authoritative: missing, extra,
duplicate, conflicting-family, kind, and implementation mismatches are structural invalidity. No
registry or dynamic resolution is introduced.

## 9. P02-F07 implementation scope

P02-F07 may change only:

- `MtfDirectionPolicyRef` plus affected serialization/profile tests;
- the P01 `StrategyFactBundle` evidence invariant and focused tests;
- evidence identity derivation by adding item identity and correcting final-order consumption;
- exports and immutable-compliance expectations only if mechanically required;
- focused tests for every transition frozen here.

It must not implement `CanonicalFactAdapter`, concrete rules, P03, P04, P05, or modify A07. After
P02-F07 passes and is published, a new final P02 readiness review is mandatory.

## 10. Synthetic and negative proofs

A test profile can reuse `PRIMARY` as `frame_direction_fact`, apply it separately to PRIMARY and
HIGHER frames, and inject a synthetic MTF rule. Synthetic entry ranking selects a governed winner
whose boundary returns a point or range. Stop precedence returns one winner before transformations.
Target ranking returns a base candidate and optional extension selects exactly one price candidate.
Confidence returns a finite unit value.

Two evidence keys may share one mapping identity while mapping executes per key. Each key derives
a distinct item identity. An ordering rule may return `(zeta, alpha)` from canonical input
`(alpha, zeta)`; snapshots and set identity retain `(zeta, alpha)`. The P01 bundle uses one set
identity while its two snapshots use two unique item identities. The complete synthetic bundle
requires no P03 or concrete P04/P05 semantics.

The contracts reject duplicate item identity, duplicate/unknown/omitted ordering keys, duplicate
or inconsistent MTF pairs, missing frame-direction implementation, malformed entry ranges, zero
or multiple stop winners, ambiguous target extension, and unknown candidate references.

Remaining implementation-significant ambiguities: **NONE**.
