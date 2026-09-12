# P02-R05 — Semantic Fact Identity and Multi-Input Geometry Request Amendment

Status: **AUTHORIZED / READY FOR IMPLEMENTATION**

Scope: strictly additive generic P02 contract capability; no P04 implementation

## Purpose and authority

This amendment follows frozen P02-R03, P02-R04, P04-F00, P04-F01, and
P04-F02-R01. It supplies the smallest generic contracts needed for a future
P04-F02 readiness review to distinguish same-valued semantic facts and to
transport governed candidate/source populations into directional geometry
rules.

P02-R05 does not implement P04-F02, alter any frozen rule identity or
fingerprint, expand F01 extraction, or change P03 or A07. A07 E07 remains the
exclusive risk, reward, RR, threshold, and zero-risk authority.

## Existing contract assessment

| Contract | Current shape | Assessment |
| --- | --- | --- |
| `SemanticCandidate` | source/provenance/instrument/timeframe/rule/value/role | INSUFFICIENT: no semantic fact identity |
| `SourceExtractionRequest` | context plus one typed source | SUFFICIENT for extraction |
| `StructuralApplicabilitySetRequest` | context, candidates, sources | SUFFICIENT only for structural applicability |
| `ApplicabilityRequest` | context, one candidate, direction | INSUFFICIENT for source-aware geometry |
| `BoundarySelectionRequest` | context, one candidate, direction | PARTIALLY SUFFICIENT |
| `PriceTransformationRequest` | context, one candidate, direction | INSUFFICIENT for multi-input transforms |
| `CandidateRankingRequest` | context, canonical candidates, optional direction | SUFFICIENT for ranking transport |
| `CandidateSelectionRequest` | context, canonical candidates, optional direction | SUFFICIENT for selection transport |
| `DirectionRuleRequest` | context, candidates, allowed source states | SUFFICIENT once facts are distinguishable |
| Existing result contracts | typed family-specific outputs | SUFFICIENT |

Existing checked dispatch accepts exact request types for each invocation kind.
The closed `SemanticRuleRequest` union and public exports enumerate those types.
The tagged serializer reconstructs immutable dataclasses from named fields and
therefore honors omitted fields that have dataclass defaults.

## Semantic fact identity

Add this generic immutable value object to `rule_values.py`:

```text
SemanticFactIdentity
    namespace: str
    name: str
    version: str
```

All three fields are non-empty normalized text. `namespace` identifies the
governing fact vocabulary, `name` identifies one semantic fact inside that
vocabulary, and `version` identifies its contract version. The object is
frozen, slotted, ordered, hashable, and serializable. P02 defines the mechanism
but no P04-specific fact constants or closed domain enum.

Append this defaulted field after `SemanticCandidate.role`:

```text
fact_identity: SemanticFactIdentity | None = None
```

`None` is the explicit `UNSPECIFIED` state. Missing, omitted, and explicit
`None` are equivalent. A non-`None` value must have exact
`SemanticFactIdentity` type.

Rule identity answers which rule produced a candidate. Role answers how a
candidate is used structurally. Fact identity answers what semantic fact its
value represents. None may substitute for another.

### Canonical compatibility

For `fact_identity is None`, candidate construction and validation exclude
`fact_identity` from the canonical-ID projection and hash projection. Existing
`role == UNSPECIFIED` exclusion remains unchanged. Therefore every historical
candidate retains its candidate ID, equality, and hash, and old positional and
keyword construction remains valid.

For a non-default fact identity, the field participates in dataclass equality,
candidate ID, and hash. Two otherwise identical candidates with distinct fact
identities are distinct. Two candidates with the same complete identity remain
duplicates and fail before canonical sorting.

Historical payloads missing `fact_identity` reconstruct with `None`. Writers
emit the field as canonical `null` for the default or as a tagged
`SemanticFactIdentity` for a specified fact. Unknown types, malformed fields,
empty text, and tampered candidate IDs fail closed. No serializer-framework
change is authorized.

## Directional candidate/source set request

Add one generic immutable request to `rule_requests.py`:

```text
DirectionalCandidateSourceSetRequest
    context: SemanticRuleInvocationContext
    candidates: tuple[SemanticCandidate, ...]
    sources: tuple[AnalyticalSourceBinding, ...]
    direction: StrategyDirection
```

Both tuples are non-empty. Candidates are duplicate-checked by candidate ID
before sorting by candidate ID. Sources are duplicate-checked by
`source_binding_id` before sorting by source binding ID. Every candidate and
source must match the invocation context, and every candidate source binding
must be present in `sources`. Direction has exact `StrategyDirection` type.

Tuple order carries no business meaning. Rules identify inputs through typed
role, typed fact identity, producer identity, source kind, and provenance.
Distinct same-valued candidates with distinct fact identities are valid
members. Arbitrary payloads, metadata maps, tuple-position inference, and
rule-name parsing remain prohibited.

The new request is added to `SemanticRuleRequest` and public exports. Exact
checked dispatch admits it only for these existing invocation kinds:

- `APPLICABILITY`;
- `BOUNDARY`;
- `PRICE_TRANSFORMATION`.

The historical request types remain admitted exactly as before. Wrong request
types fail before implementation invocation. Invocation/result compatibility
and every existing result type remain unchanged.

## Design alternatives and decision

| Option | Decision | Reason |
| --- | --- | --- |
| Closed fact enum | Rejected | Couples P02 to every future domain vocabulary |
| Raw string or metadata key | Rejected | Not a typed governed identity |
| Overload candidate role | Rejected | Structural use is not semantic meaning |
| Parse rule identity | Rejected | One rule must emit multiple facts |
| Optional typed fact value object | Selected | Generic, deterministic, extensible, legacy-safe |
| Reuse structural applicability set for all families | Rejected | Obscures invocation-family semantics and lacks direction |
| Extend every historical request | Rejected | Wider compatibility surface than necessary |
| Family-specific new set requests | Rejected | Duplicates the same validated population contract |
| One directional candidate/source set request | Selected | Smallest exact transport with checked family admission |

## Fit proofs

### Market-structure facts

A future extraction rule can emit two candidates from one source with identical
TEXT values and `UNSPECIFIED` roles while assigning different domain-owned
fact identities, for example one trend-direction fact and one structure-state
fact. Their candidate IDs differ because their fact identities differ. P02
production contains neither domain name.

### Fibonacci entry

The new request can carry the frozen F01 Fibonacci `ANCHOR_START` and
`ANCHOR_END` candidates together with their typed Fibonacci source binding and
direction. A future P04 rule can inspect the exact `FibonacciSnapshot` zones,
retracement levels, labels, and endpoint consistency without metadata or F01
expansion. Applicability and boundary rules retain their existing result types.

This amendment provides transport only. It does not decide P04 entry ranking,
candidate cardinality, or selection policy.

### Target transformation

The new request can carry both W1 anchors and their typed source binding. A
future transformation can select `ANCHOR_START` and `ANCHOR_END` by role and
compute a domain-governed result without tuple-position semantics. Existing
`PriceTransformationResult` already returns one provenance-bearing PRICE
candidate and requires no replacement.

## Provenance and ordering

Candidate provenance remains source binding, provenance reference, instrument,
timeframe, producer rule identity, role, and optional fact identity. A derived
candidate must retain the governed source lineage; unrelated producers are not
merged.

Population validation always follows this order:

1. validate exact tuple/member types;
2. detect duplicate candidate or source identities;
3. validate context and candidate-to-source relationships;
4. canonicalize by candidate ID and source binding ID.

No implementation may call `set(candidates)` before duplicate validation.

## Public API and implementation boundary

The only new public contracts are:

- `SemanticFactIdentity`;
- `SemanticCandidate.fact_identity`;
- `DirectionalCandidateSourceSetRequest`.

Expected production files:

- `epip/strategy_mapping/rule_values.py`;
- `epip/strategy_mapping/rule_requests.py`;
- `epip/strategy_mapping/resolved_rules.py`;
- `epip/strategy_mapping/__init__.py`.

No serializer, adapter, P03, A07, P04 profile, or F01 production change is
authorized in P02-R05. Adapter use of the new request belongs to a separately
authorized successor after these contracts are implemented and frozen.

Expected tests:

- `tests/strategy_mapping/test_rule_execution_contracts.py`;
- `tests/strategy_mapping/test_execution_serialization.py`;
- `tests/strategy_mapping/test_resolved_rules.py`;
- `tests/strategy_mapping/test_directional_candidate_source_set.py`.

## Exact generic test matrix

P02-R05 implementation must add exactly 34 governed test conditions:

1. historical candidate construction retains its candidate ID;
2. historical candidate equality is unchanged;
3. historical candidate hash is unchanged;
4. old positional construction remains valid;
5. old keyword construction remains valid;
6. omitted fact identity equals explicit `None`;
7. default fact identity is excluded from candidate ID;
8. default fact identity is excluded from hash;
9. specified fact identity changes candidate ID;
10. specified fact identity changes equality;
11. specified fact identity changes hash;
12. same value/source/rule/role with different facts remains distinct;
13. same complete fact-bearing candidate is rejected as a duplicate;
14. fact identity rejects empty namespace;
15. fact identity rejects empty name;
16. fact identity rejects empty version;
17. fact identity round-trips through JSON;
18. historical candidate payload missing the new field reconstructs unchanged;
19. default-bearing candidate round-trips;
20. fact-bearing candidate round-trips;
21. unknown or malformed fact type fails closed;
22. tampered fact-bearing candidate ID fails closed;
23. request accepts one candidate and one source;
24. request accepts two role-distinct candidates;
25. candidate permutation reconstructs equal canonical order;
26. source permutation reconstructs equal canonical order;
27. duplicate candidate ID is rejected before sorting;
28. duplicate source binding is rejected before sorting;
29. distinct same-valued fact identities coexist in one request;
30. candidate whose source is absent is rejected;
31. candidate/source/context mismatch is rejected;
32. request round-trips through JSON;
33. exact dispatch accepts the request for applicability, boundary, and price transformation;
34. exact dispatch rejects it for every other invocation kind before calling implementation.

Generic synthetic fixtures must additionally demonstrate that conditions 12,
24, and 29 represent two facts from one source; two role-addressed anchors; and
a typed Fibonacci-like source plus candidates without placing P04 identifiers
in P02 production.

All existing P02, P03, A07, and P04-F01 regressions remain required. Historical
request serialization and dispatch tests must remain unchanged.

## Compliance and non-goals

The implementation adds exactly two frozen dataclasses, so the expected
compliance inventory is `612`. The implementation digest must be measured after
the code exists and must not be predicted in governance.

P02-R05 does not decide P04 entry or target ranking, stop precedence, the F02
executable subset, F02 failure policy, F02 test count, RR, F03, F04, or P05. It
does not authorize P04-F02. A fresh F02 readiness review is mandatory after
P02-R05 implementation and closure.

## Decision

The amendment is strictly additive and implementation-ready. P02-R05 is
**AUTHORIZED / READY FOR IMPLEMENTATION**. P04-F02 remains
**NOT AUTHORIZED / PREDECESSOR AMENDMENT REQUIRED** until P02-R05 is complete,
closed, and frozen.
