# P02-R04 — Structural Applicability Input and Candidate-Set Amendment

Status: **AUTHORIZED / READY FOR IMPLEMENTATION**

Scope: generic additive P02 contract only

P04-F01 remains **NOT AUTHORIZED / ARCHITECTURALLY BLOCKED**.

## Purpose and authority

P02-R03 added direction-neutral structural applicability, but its request
carries only one `SemanticCandidate`. Some structural rules require a governed
candidate population and original typed analytical context. This amendment
defines the smallest generic additive capability without domain-specific types,
string metadata, positional conventions, or opaque payloads.

Authority is the frozen P02-R03 contract, P04-F00-R03, P04-R00, ADR-0029, and
the current P02 source-binding, candidate, request, result, dispatch,
serialization, identity, provenance, and failure contracts.

## Existing contracts preserved

These contracts remain unchanged:

- `StructuralApplicabilityRequest(context, candidate)`;
- `CandidateSelectionRequest(context, candidates, direction)`;
- `SelectionRuleResult(state, diagnostic_codes, selected_candidate_ids)`;
- `CandidateRuleResult(state, diagnostic_codes, candidates)`;
- `SemanticCandidate` and `SemanticCandidateRole`;
- `SemanticInvocationKind.STRUCTURAL_APPLICABILITY`.

Historical construction, equality, hashing, serialization, and dispatch remain
unchanged. No historical field, tag, payload, or identity is rewritten.

## New generic request

Add this public frozen slotted dataclass in `rule_requests.py`:

```python
@dataclass(frozen=True, slots=True)
class StructuralApplicabilitySetRequest:
    context: SemanticRuleInvocationContext
    candidates: tuple[SemanticCandidate, ...] = ()
    sources: tuple[AnalyticalSourceBinding, ...] = ()
```

Add it to `SemanticRuleRequest`, module/package exports, and the existing
checked-dispatch entry for `STRUCTURAL_APPLICABILITY`. No new invocation or
result enum is required. A distinct class preserves the historical request
rather than widening or reinterpreting it.

## Population contract

Construction enforces:

1. exact context, tuple, candidate, and source types;
2. at least one candidate or source;
3. candidates sorted by `candidate_id`;
4. unique candidate IDs;
5. sources sorted by `source_binding_id`;
6. unique source-binding IDs;
7. candidate instrument, timeframe, binding, and provenance admitted by context;
8. source instrument, timeframe, binding, and provenance admitted by context;
9. when sources are supplied, every candidate refers to one of them.

The request therefore supports zero, one, or many candidates and zero, one, or
many sources, but rejects an entirely empty structural input.

Candidate roles are not globally unique. Cross-source inputs may legitimately
contain one `ANCHOR_START` from each producer. Duplicate roles remain visible;
each rule validates its explicitly governed role cardinality. P02 adds no
first-match lookup or duplicate-collapsing helper.

## Typed source and provenance model

Every candidate retains its source binding, provenance, role, identity,
instrument, and timeframe. Every supplied source remains a complete immutable
`AnalyticalSourceBinding` with its exact payload.

Distinct producer and binding identities are valid. Coherence is proven by
independent admission to one invocation context, not by equating producer or
binding identities. Direct payload access is allowed only through the existing
closed `AnalyticalPayload` union validated by `AnalyticalSourceBinding`.
`Any`, arbitrary objects, dictionaries, JSON blobs, and string metadata are
prohibited.

## Responsibility boundary

Extraction may validate source kind/contract, read governed fields, emit
canonical scalar or range candidates, and preserve provenance. It must not
absorb applicability, structural eligibility, selection, direction, or
geometry.

Structural applicability owns business predicates over candidates and, where
scalar candidates cannot preserve relationships such as indices or timestamps,
typed source payloads. Malformed populations are `INVALID_INPUT` or
`DataIntegrityError`; well-formed business non-matches are `REJECTED`.

## Selection pair semantics

`SelectionRuleResult` already carries one or more unique selected IDs and
canonicalizes them lexically. The IDs form a canonical set; tuple position is
not semantic.

An exact pair requires one governed `ANCHOR_START` and one governed
`ANCHOR_END`. A rule returns exactly those two IDs. Roles on the referenced
candidates—not result order—define pair meaning. Missing, extra, unknown, or
duplicate required-role populations fail closed. The exact-one
`selection_winner` helper is not used for pair selection. No new result type,
first-match behavior, or hidden ranking is required.

## Serialization, equality, and identity

The generic tagged dataclass serializer supports the request without registry
changes. Construction canonicalizes candidate and source order before equality,
hashing, or serialization. Membership, roles, per-item provenance, and the
candidate-versus-source distinction are identity-bearing; input order is not.
Round-trip reconstruction revalidates every invariant and rejects tampering.

Historical `StructuralApplicabilityRequest` positional and keyword construction,
serialization, equality, and hash remain byte-for-byte stable.

## Dispatch and implementation boundary

`ResolvedSemanticRuleSet.invoke()` accepts either exact structural request type
for `STRUCTURAL_APPLICABILITY`; every other request type fails before invoking
the implementation. Reflection, rule-name parsing, dynamic imports, and runtime
discovery remain prohibited.

Authorized future production files are exactly:

- `epip/strategy_mapping/rule_requests.py`;
- `epip/strategy_mapping/resolved_rules.py`;
- `epip/strategy_mapping/__init__.py`.

Expected tests are a focused structural-set request suite plus existing
serialization, dispatch, and compatibility tests. This artifact and ROADMAP are
the only expected documentation changes. No P03, A07, P04, runtime, result, or
serializer production file requires modification.

## P04-F01 fit proof

This proves fit without authorizing or implementing P04-F01.

- `extract.elliott` emits exactly two PRICE candidates from primary W1:
  `ANCHOR_START` and `ANCHOR_END`.
- `extract.fibonacci` emits exactly two PRICE candidates from retracement
  start/end with the same roles. Extension endpoints remain available through
  the typed source, avoiding duplicate canonical candidates when endpoints are
  equal. F01 emits no zone, entry, stop, or target candidate.
- `applicability.elliott-wave3` receives the Elliott source and its two anchors,
  permitting exact sequence, degree, index, timestamp, price, count,
  projection, orientation, and W2-origin validation.
- `applicability.fibonacci-wave3` receives both sources and all four anchors,
  permitting exact retracement/extension, cross-domain price, context, and raw
  orientation validation without StrategyDirection or ENTRY membership.
- `select.wave1-anchor` receives the four qualified candidates and selects the
  two Elliott IDs: exactly one start and one end. Source-rule identity and role,
  not position, identify the authoritative pair.

Exactly the five frozen P04-F01 identities remain sufficient. Their IDs,
versions, fingerprints, families, and catalog entries need not change.

## Failure and execution barriers

`INVALID_INPUT` covers wrong types, empty total input, duplicate candidate or
source identities, context mismatch, invalid provenance, impossible role/value
shape, malformed required-role cardinality, or output IDs outside the request.

`REJECTED` covers well-formed structural non-match: invalid wave progression,
W2 origin touch/cross, non-W3 projection, endpoint inequality, or orientation
mismatch.

Extraction failure prevents applicability. Elliott rejection prevents the
cross-domain rule and selection. Fibonacci rejection prevents selection.
Selection rejection prevents every successor invocation.

## Compliance and test authorization

One frozen dataclass is added, so expected compliance inventory is 610. The
implementation must generate, not predict, the new digest.

Implementation must cover exactly 55 conditions:

- historical compatibility: 7;
- population validation, ordering, emptiness, and duplicates: 12;
- context/source/provenance coherence: 8;
- dispatch and pre-invocation rejection: 5;
- serialization, equality, hashing, and tampering: 8;
- selection pair/set semantics: 7;
- generic P04-neutral fit fixtures: 2;
- P02, P03, A07, P04-F00, full regression, and compliance gates: 6.

Every new branch requires coverage. Black, Ruff, MyPy, `git diff --check`,
documentation, at least 95% aggregate coverage, and exact-SHA Quality, CodeQL,
and Documentation are mandatory.

## Non-goals and disposition

P02-R04 does not implement P04, add domain-specific types or roles, change
directional applicability or selection results, replace serialization, alter
P03/A07, or authorize any P04/P05 feature.

- P02-R04: **AUTHORIZED / READY FOR IMPLEMENTATION**.
- P04-F01: **NOT AUTHORIZED / ARCHITECTURALLY BLOCKED** pending implemented and
  frozen P02-R04.
- P04-F02, P04-F03, P04-F04, and P05: **NOT AUTHORIZED**.
