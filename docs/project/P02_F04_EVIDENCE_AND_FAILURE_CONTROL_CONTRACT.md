# P02-F04 Evidence Mapping and Failure Control Contract

Status: NORMATIVE CONTRACT RECONCILED / IMPLEMENTATION NOT AUTHORIZED

Authority: [ADR-0016](../adr/ADR-0016-CanonicalStrategyPipeline.md),
[ADR-0017](../adr/ADR-0017-CanonicalStrategyRuntimeContracts.md),
[ADR-0018](../adr/ADR-0018-TypedStrategyMappingAndAvailabilityBoundaries.md),
[ADR-0019](../adr/ADR-0019-ImmutableSemanticRuleExecution.md), and
[ADR-0020](../adr/ADR-0020-EvidenceMappingAndFailFastSemanticExecution.md).

## 1. Purpose and scope

P02-F04 closes two additive contract gaps before `CanonicalFactAdapter` may be implemented:

1. `EVIDENCE_MAPPING` is executable but has no profile-bound `RuleIdentity`.
2. P02-F02 does not freeze semantic failure short-circuit and diagnostic accumulation.

This milestone is governance only. P02-F05 must implement the additions below. P01, A07, existing
P02-F01 semantics, and existing P02-F03 execution contracts remain frozen. P02, P03, P04, and P05
behavior is not authorized.

## 2. Evidence mapping ownership

Evidence mapping remains executable strategy-specific semantic behavior. It is not native P02
structural behavior. P02 may filter source kind, exact source contract, frame, role, availability,
revision, and provenance, but it may not decide which extracted candidates substantiate a taxonomy
key.

`EvidenceKeyPolicy` gains one mandatory exact field:

| Field | Type | Rule |
| --- | --- | --- |
| `mapping_rule` | `RuleIdentity` | Required `EVIDENCE_MAPPING` implementation for this key |

Per-key placement is the narrowest ownership boundary because `EvidenceMappingRequest` contains one
exact `evidence_key`. A taxonomy-wide mapping rule would contradict that request cardinality and
couple independent key evaluation. Multiple keys may explicitly share the same `RuleIdentity`;
sharing is identity equality, never implicit lookup.

`mapping_rule` participates in normal dataclass canonical serialization, reconstruction, equality,
hashing, taxonomy state, and `StrategySemanticMappingProfile` fingerprinting. Changing it changes
the semantic-profile fingerprint. No default, optional value, latest version, fallback, or inferred
mapping identity is permitted.

## 3. Mapping cardinality and validation

P02 invokes evidence mapping once for each evidence key that reaches mapping, in canonical
`EvidenceTaxonomy.keys` order by `evidence_key`. The request contains that key and the complete
canonical candidate tuple extracted for its exact `source_selector`.

On `SUCCESS`, `EvidenceMappingResult.selected_candidate_ids` must be non-empty, unique, canonical,
and an exact subset of the request candidate IDs. Unknown, duplicate, or fabricated IDs are invalid
rule output. The selected candidates define that key's source-binding and provenance lineage for
the complete evidence-set identity. Mapping does not create an evidence key or candidate.

## 4. Exact profile closure

Future P02-F05 changes `ResolvedSemanticRuleSet.validate_profile_closure()` as follows:

1. traverse `EvidenceTaxonomy.keys` in canonical `evidence_key` order;
2. require every `source_selector.selector_rule` as `SOURCE_EXTRACTION`;
3. require every `mapping_rule` as `EVIDENCE_MAPPING`;
4. require both temporal identities as `TEMPORAL_ELIGIBILITY`;
5. require the taxonomy `ordering_rule` as `EVIDENCE_ORDERING`.

Identity/family pairs are deduplicated only after canonical traversal. Shared mapping rules are
legal and resolve once. One identity required under conflicting families is invalid. Missing rules,
unused extras, duplicates in the manifest, and runtime declaration mismatches remain invalid. Rule
resolution is exact-version only.

## 5. Evidence execution pipeline

For every taxonomy key, P02 mechanically performs:

1. structural source resolution;
2. exact `SOURCE_EXTRACTION` invocation for each resolved source in canonical source-binding order;
3. candidate lineage and domain validation;
4. one exact `EVIDENCE_MAPPING` invocation;
5. selected-candidate subset validation;
6. native freshness calculation over selected source bindings;
7. exact temporal-validity invocation;
8. exact revision-eligibility invocation;
9. snapshot inclusion or governed omission/rejection;
10. canonical taxonomy ordering-rule invocation over included keys;
11. one complete evidence-set identity derivation;
12. `StrategyEvidenceSnapshot` construction using that shared identity.

The identity domain remains exactly `epip.strategy-evidence-set.p02-f02-v1`. It is computed once,
never per key or rule. Its entries use mapping-selected lineage in ordering-rule output order.

P02 produces taxonomy-keyed snapshots. `EvidenceRequirement.OPTIONAL` authorizes omission after a
governed `NO_MATCH`, failed freshness, or temporal ineligibility; it does not authorize fallback.
For required keys the same conditions terminate as `REJECTED`. A07 E01 remains the sole final
required/optional reconciliation authority and P02 does not reproduce A07 validation.

## 6. Freshness and temporal ownership

Freshness remains native deterministic P02 behavior. For one or more mapped selected sources, the
per-source calculation and final conjunction are frozen by
[P02-F16](P02_F16_EVIDENCE_FRESHNESS_CARDINALITY_CONTRACT.md). Each source uses the configured
`FreshnessBasis`, the explicit canonical evaluation timestamp, and the inclusive
`max_age_seconds` boundary. Future timestamps are structural invalid input. No wall clock is read.

Temporal validity and revision eligibility remain semantic rule behavior. Mapping precedes both;
freshness precedes temporal invocation. A temporal rule never runs without successfully mapped,
fresh evidence where freshness is required.

## 7. Global failure policy

P02 uses dependency-aware fail-fast execution. Structural validation is globally fail-fast and
completes before the first semantic invocation. A structural failure causes zero semantic-rule
invocations.

For semantic execution, the first terminal non-success in canonical stage/invocation order stops
all later dependent and independent semantic work. P02 does not continue merely to collect more
diagnostics. The only non-terminal non-success is an explicitly permitted optional-evidence
omission. No placeholder candidate, direction, price, confidence, or evidence value is fabricated.

The terminal behavior is:

| P02 outcome | P01 state | Bundle | Rule execution |
| --- | --- | --- | --- |
| Structural corruption or closure mismatch | `INVALID_INPUT` | None | None or stop immediately |
| Required `NO_MATCH` | `REJECTED` | None | Stop |
| Optional-evidence `NO_MATCH` | Continue with omission | None yet | Continue canonically |
| `REJECTED` | `REJECTED` | None | Stop |
| Rule `INVALID_INPUT` or malformed output | `INVALID_INPUT` | None | Stop |
| Governed `FAILED` | `FAILED` | None | Stop |
| Unexpected executable exception | `FAILED` | None | Stop |
| Required freshness/temporal failure | `REJECTED` | None | Stop |
| Optional freshness/temporal failure | Continue with omission | None yet | Continue canonically |
| Complete valid bundle | `ACCEPTED` | Exact bundle | Complete |

An absent profile stage is skipped only when its field is normatively optional. A missing required
identity is structural invalidity, not `NO_MATCH`.

Unexpected exceptions are caught at the adapter boundary and converted to deterministic `FAILED`.
Raw exception text and stack traces never enter semantic results, diagnostics, identities, or
serialized contracts. Operational logging is outside this immutable boundary. Rules are invoked
once; the adapter does not double-execute to test determinism.

## 8. Diagnostic translation

Diagnostics produced before and including the terminal outcome are retained; later stages produce
none. Exact duplicates are removed. Final P01 diagnostics sort by:

```text
runtime stage order
RuntimeDiagnosticCode.value
subject_ref
source_refs
message
```

`source_refs` are themselves sorted and unique. `message` is exactly the P02 diagnostic-code value.
Rule subjects use `RuleIdentity.reference`; binding subjects use `binding_id`. Severity is `ERROR`.

| P02 code | P01 stage | P01 code |
| --- | --- | --- |
| `RULE_NOT_RESOLVED` | `ADAPTER` | `INVALID_REQUEST` |
| `RULE_IDENTITY_MISMATCH` | `ADAPTER` | `INVALID_REQUEST` |
| `RULE_INPUT_INVALID` | `ADAPTER` | `INVALID_REQUEST` |
| `RULE_OUTPUT_INVALID` | `ADAPTER` | `INVALID_REQUEST` |
| `RULE_REJECTED` | `ADAPTER` | `ADAPTER_REJECTED` |
| `SELECTOR_NO_MATCH` | `ADAPTER` | `MISSING_FACT` |
| `AMBIGUOUS_CANDIDATE` | `ADAPTER` | `ADAPTER_REJECTED` |
| `EVIDENCE_IDENTITY_ERROR` | `COHERENCE` | `COHERENCE_FAILURE` |
| `INVOCATION_BINDING_MISMATCH` | `COHERENCE` | `COHERENCE_FAILURE` |

This mapping is total and requires no P01 vocabulary change. Structural profile mismatch may use
the existing `PROFILE` / `PROFILE_MISMATCH` diagnostic directly; it is not a P02 rule diagnostic.
Unexpected exceptions use `ADAPTER` / `ADAPTER_FAILED`, with the exact stable message `FAILED` and
the invoked rule reference as subject.

## 9. Canonical adapter stage and invocation order

The exact global order is:

1. exact structural input validation;
2. invocation-binding validation;
3. semantic-profile and exact rule-set closure validation;
4. structural selector resolution;
5. source extraction;
6. non-MTF direction facts in `DirectionFactName.value` order;
7. MTF aggregation;
8. entry applicability, selection, ranking, and boundary stages;
9. stop applicability, selection, precedence, buffer, and optional volatility stages;
10. target applicability, selection, ranking, optional threshold, and optional extension stages;
11. confidence model and optional calibration;
12. evidence keys in `evidence_key` order: extraction, mapping, freshness, validity, revision;
13. evidence ordering;
14. complete evidence-set identity;
15. A07 caller-authoritative fact and evidence-snapshot assembly;
16. `StrategyFactBundle` construction;
17. `FactAdapterResult` construction.

Within a stage, explicit profile tuple order governs where the tuple is already canonical. Source
bindings and candidates use their normative canonical keys. Multiple otherwise unordered rule
identities sort by `RuleIdentity.reference`. Geometry substage order above overrides identity order.

## 10. Implementation impact and future tests

P02-F05 is limited to additive implementation of this contract:

- add mandatory `EvidenceKeyPolicy.mapping_rule`;
- update all construction, serialization, reconstruction, equality, and profile fingerprints;
- extend exact profile-closure traversal;
- add private deterministic failure/diagnostic helpers only if implementation requires them;
- update explicit exports only if a new public value object is unavoidable (none is expected);
- add focused tests and mechanically update the immutable compliance digest.

Tests must cover per-key cardinality, shared mapping identities, fingerprint change, round trips,
missing/extra/conflicting closure, candidate subset validation, optional omission, each terminal
state, zero invocation after structural failure, fail-fast invocation counts, diagnostic translation
and ordering, unexpected exception sanitization, canonical stage order, and dependency isolation.

No `CanonicalFactAdapter`, concrete rule, P03/P04/P05 behavior, P01 change, or A07 change belongs to
P02-F05.

## 11. Dependency boundaries and closure

P03 retains orchestration, P04 retains concrete strategy rules and the production profile, and P05
retains concrete MTF semantics. P02 owns only generic structural validation, exact dispatch,
translation, and fact assembly.

P02-F04 closes when this specification and ADR-0020 are published with governance validation green.
That closure authorizes only P02-F05 implementation. P02 remains unauthorized until P02-F05 is
implemented, tested, published, and separately reviewed.

Remaining implementation-significant ambiguities: **NONE**.
