# P02-F16 Evidence Freshness Cardinality Contract

Status: NORMATIVE CONTRACT RECONCILED / IMPLEMENTATION NOT AUTHORIZED

Authority: [ADR-0016](../adr/ADR-0016-CanonicalStrategyPipeline.md),
[ADR-0017](../adr/ADR-0017-CanonicalStrategyRuntimeContracts.md),
[ADR-0018](../adr/ADR-0018-TypedStrategyMappingAndAvailabilityBoundaries.md),
[ADR-0019](../adr/ADR-0019-ImmutableSemanticRuleExecution.md),
[ADR-0020](../adr/ADR-0020-EvidenceMappingAndFailFastSemanticExecution.md),
[ADR-0021](../adr/ADR-0021-EvidenceIdentityAndSemanticTransitions.md), and
[ADR-0026](../adr/ADR-0026-EvidenceFreshnessRequiresAllSelectedSourcesToBeFresh.md).

## 1. Purpose and scope

Evidence mapping may select a non-empty subset containing multiple `SemanticCandidate` values.
Those candidates may refer to multiple source bindings, while A07 stores one `fresh` Boolean for
the resulting evidence item. Earlier singular wording did not define that reduction. This
governance-only milestone freezes the missing generic rule. It authorizes no Python, test,
`CanonicalFactAdapter`, P03, P04, or P05 implementation.

## 2. Selected subset and source lineage

Freshness runs only after successful source extraction, evidence mapping, and exact non-empty
subset validation. It consumes all and only the source bindings referenced by the mapped selected
candidates. Unselected candidates and their sources have no effect. An empty mapping result is
invalid rule output before freshness; neither vacuous `all` nor `any` semantics apply.

Freshness evaluates the unique selected `source_binding_id` values. Several selected candidates
from the same binding describe one temporal observation and therefore contribute one per-source
truth value. Candidate identity, insertion order, mapping order, binding order, dictionary order,
frame role, and canonical sorting never privilege a source or change the result. Candidate and
source lineage remain preserved by the existing item-identity inputs.

## 3. Per-source calculation

For each unique selected source, P02 uses the one `FreshnessPolicy.basis` attached to the evidence
key. `OBSERVATION` selects `observation_timestamp`; `AVAILABILITY` selects
`availability_timestamp`. Bases are never mixed within one item. Every calculation uses the exact
shared `EvaluationContext.evaluation_timestamp`; no wall clock is read.

After existing timestamp parsing and normalization, whole-second age is:

```text
age(source) = evaluation timestamp - selected basis timestamp
```

The source is fresh exactly when `0 <= age(source) <= max_age_seconds`. Equality at
`max_age_seconds` is fresh. A negative age is not ordinary staleness: any selected future basis
timestamp makes the complete evidence item structurally `INVALID_INPUT` immediately. Missing,
malformed, incoherent, or unavailable required temporal metadata is likewise structural
`INVALID_INPUT`, never stale and never eligible for optional omission.

## 4. Cardinality reduction

For every supported cardinality `N >= 1`, final freshness is the conjunction of the per-source
values:

```text
final_fresh = fresh(source_1) AND ... AND fresh(source_N)
```

For `N == 1`, final freshness equals that source's freshness. For `N > 1`, every selected source
must be fresh. Thus all-fresh yields `True`; mixed fresh/stale and all-stale yield `False`. The
reduction is order-independent and adds no ranking or selection.

`ANY` is rejected because a fresh source would mask stale lineage that still contributes to the
evidence item. Newest, oldest, first, canonical-first, PRIMARY, HIGHER, LOWER, candidate-order, and
binding-order ownership are rejected because no frozen mapping contract designates a temporal
owner. A separate evidence-level timestamp is unnecessary and would expand the public model.

## 5. Required, optional, and stage behavior

Required evidence with `final_fresh is False` terminates immediately as P01 `REJECTED` with no
bundle. Optional evidence with `final_fresh is False` is omitted, as already authorized by P02-F04,
and canonical evaluation continues. Optionality never converts future or malformed temporal data
into omission.

Source-extraction `NO_MATCH`, extraction terminal states, malformed or empty mapping output, and
mapping terminal states are resolved before freshness under their existing rules. Freshness does
not reinterpret them. Freshness remains before temporal validity and revision eligibility. A fresh
item may fail either later rule; a stale item never reaches either rule. Revision eligibility
cannot make stale evidence fresh.

## 6. Diagnostics and auditability

No new public diagnostic code is required. Required staleness uses existing P01
`TEMPORAL_FAILURE` at stage `TEMPORAL`, severity `ERROR`, and terminal state `REJECTED`. Optional
staleness records the same stable code and stage with severity `WARNING` before omission. Future or
malformed selected temporal data uses `TEMPORAL_FAILURE`, stage `TEMPORAL`, severity `ERROR`, and
state `INVALID_INPUT`.

The diagnostic `subject_ref` is the exact evidence key and `source_refs` is the canonical unique
tuple of all stale source provenance references, or all structurally invalid source provenance
references. Mixed input therefore identifies precisely which contributing sources failed without
exposing payloads, paths, exception text, or runtime state. All-stale records all selected source
references. Existing selected candidate, binding, and provenance identity lineage supplies the
remaining audit trail.

## 7. Identity and contract impact

`derive_evidence_item_identity()` continues to consume only the final reduced Boolean plus its
existing complete selected lineage. The raw per-source Boolean vector is transient private
calculation state and is not serialized. `derive_evidence_set_identity()` remains unchanged and
continues to consume final item identities in governed evidence order.

A07 retains one Boolean per snapshot. P01, F11 source resolution, F13 exact rule closure, and F15
confidence cardinality remain unchanged. `FreshnessPolicy.policy_identity` remains descriptive and
provenance-bearing, not executable. No executable rule, family, invocation, result, profile field,
schema, serialization tag, closure edge, or profile-fingerprint change is introduced.

The conjunction is one global generic P02 invariant, not profile-configurable or strategy-specific
behavior. P04 still owns concrete evidence selectors and mappings; P05 supplies no timeframe
freshness preference; P03 cannot choose or override the reduction.

## 8. P02-F17 implementation scope

P02-F17 is the separately authorized evidence freshness cardinality implementation milestone. It
may add only a private deterministic helper that:

1. accepts the validated mapped selected candidates and their exact source bindings;
2. deduplicates by exact source-binding identity while retaining canonical lineage;
3. evaluates the configured basis against the explicit evaluation timestamp;
4. rejects any future or malformed selected timestamp as `INVALID_INPUT`;
5. reduces non-empty per-source results with the frozen conjunction;
6. applies required rejection or optional omission and deterministic diagnostics; and
7. supplies the reduced Boolean to existing evidence identity and snapshot assembly.

F17 must not implement `CanonicalFactAdapter`, change public contracts, or enter P03/P04/P05.
P02-F09 remains blocked until F17 is implemented, validated, published, and separately reviewed.

## 9. Required P02-F17 proofs

Tests must cover one fresh source; one stale source; two all-fresh sources; mixed fresh/stale; all
stale; selected-subset isolation; an unselected stale source; candidate and binding order
independence; duplicate candidates sharing one source; observation and availability bases; exact
threshold equality; future timestamps in every tuple position; malformed timestamps; required
rejection; optional omission and inclusion; prohibition of empty-set evaluation; freshness before
validity and revision; item identity receiving the reduced Boolean; unchanged set identity,
serialization, fingerprint, closure, F11, F13, F15, P01, and A07 contracts.

Remaining implementation-significant ambiguities: **NONE**.
