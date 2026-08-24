# P02-F02 Semantic Rule Execution and Adapter Invocation Contract

Status: NORMATIVE CONTRACT RECONCILED / IMPLEMENTATION NOT AUTHORIZED

Authority: [ADR-0016](../adr/ADR-0016-CanonicalStrategyPipeline.md),
[ADR-0017](../adr/ADR-0017-CanonicalStrategyRuntimeContracts.md),
[ADR-0018](../adr/ADR-0018-TypedStrategyMappingAndAvailabilityBoundaries.md), and
[ADR-0019](../adr/ADR-0019-ImmutableSemanticRuleExecution.md).

## 1. Purpose and ownership

P02-F02 defines the additive execution boundary needed by a future generic
`CanonicalFactAdapter`. It changes neither frozen P01 nor frozen P02-F01. P02 validates resolved
inputs, dispatches explicitly injected rules, validates their outputs, assembles caller-authoritative
A07 facts, and returns the frozen P01 `FactAdapterResult`. It never owns rule content.

P03 will assemble one exact profile, typed source bundle, invocation binding, and resolved rule set.
P04 will provide concrete Elliott/Fibonacci rules and profile content. P05 will provide concrete
MTF aggregation rules. No implementation in P02-F02 may discover a profile or rule dynamically.

`EXECUTION_SCHEMA_VERSION` is exactly `p02-f02-v1`. Public value objects are frozen, slot-based,
exactly typed, hashable, canonically ordered, nested-immutable, and reconstructed with derived
identities revalidated. Timestamps use the existing UTC microsecond profile. Numbers are finite.

## 2. Closed vocabularies

### `SemanticRuleFamily`

The exact values are:

```text
SOURCE_EXTRACTION
DIRECTION_MAPPING
CANDIDATE_SELECTION
CANDIDATE_RANKING
BOUNDARY_SELECTION
APPLICABILITY
PRECEDENCE
PRICE_TRANSFORMATION
CONFIDENCE
TEMPORAL_ELIGIBILITY
EVIDENCE_MAPPING
EVIDENCE_ORDERING
MTF_AGGREGATION
```

`PRICE_TRANSFORMATION` covers the P02-F01 buffer, volatility-adjustment, threshold, and extension
rule positions. The concrete implementation identity distinguishes those operations. Freshness is
not a rule family: P02 executes the complete P02-F01 basis/maximum-age formula natively.

### Invocation and result kinds

`SemanticInvocationKind` has exactly `SOURCE_EXTRACTION`, `DIRECTION`, `SELECTION`, `RANKING`,
`BOUNDARY`, `APPLICABILITY`, `PRICE_TRANSFORMATION`, `CONFIDENCE`,
`TEMPORAL_ELIGIBILITY`, `EVIDENCE_MAPPING`, `EVIDENCE_ORDERING`, and `MTF_AGGREGATION`.

`SemanticResultKind` has exactly `CANDIDATES`, `DIRECTION`, `SELECTION`, `RANKING`, `BOUNDARY`,
`APPLICABILITY`, `PRICE_TRANSFORMATION`, `CONFIDENCE`, `TEMPORAL_ELIGIBILITY`,
`EVIDENCE_MAPPING`, `EVIDENCE_ORDERING`, and `MTF_AGGREGATION`. A declaration contains the exact
pair; family, invocation kind, and result kind must match the compatibility table in section 9.

`SemanticRuleState` has exactly `SUCCESS`, `NO_MATCH`, `REJECTED`, `INVALID_INPUT`, and `FAILED`.
`SemanticValueKind` has exactly `TEXT`, `BOOLEAN`, `FINITE_FLOAT`, `PRICE`, and `PRICE_RANGE`.

`SemanticRuleDiagnosticCode` has exactly:

```text
RULE_NOT_RESOLVED
RULE_IDENTITY_MISMATCH
RULE_INPUT_INVALID
RULE_OUTPUT_INVALID
RULE_REJECTED
SELECTOR_NO_MATCH
AMBIGUOUS_CANDIDATE
EVIDENCE_IDENTITY_ERROR
INVOCATION_BINDING_MISMATCH
```

## 3. Canonical semantic values and candidates

### `SemanticValue`

| Field | Type | Rule |
| --- | --- | --- |
| `kind` | `SemanticValueKind` | Exact enum |
| `text_value` | `str \| None` | Present only for `TEXT` |
| `bool_value` | `bool \| None` | Present only for `BOOLEAN` |
| `float_value` | `float \| None` | Present only for `FINITE_FLOAT` or `PRICE`; price is positive |
| `range_lower` | `float \| None` | Present only for `PRICE_RANGE`; positive |
| `range_upper` | `float \| None` | Present only for `PRICE_RANGE`; positive and not below lower |

Exactly one shape is populated. Exact built-in types are required; NaN, infinity, mutable values,
and negative zero are rejected. This is the closed generic interchange boundary. Domain objects do
not cross from extraction rules into generic policy execution.

### `SemanticCandidate`

| Field | Type | Rule |
| --- | --- | --- |
| `candidate_id` | `str` | SHA-256 using domain `epip.semantic-candidate.p02-f02-v1` and all following fields |
| `source_binding_id` | `str` | Exact P02-F01 binding identity |
| `provenance_ref` | `str` | Exact P01 source reference |
| `instrument_binding_id` | `str` | Exact instrument binding identity |
| `timeframe` | `str` | Canonical timeframe |
| `source_rule_identity` | `RuleIdentity` | Extraction rule that produced the candidate |
| `value` | `SemanticValue` | Exact closed value |

Candidate tuples sort by `candidate_id` and reject duplicates. Rules may return candidate IDs, but
may not manufacture candidates with unknown source bindings or provenance. P02 validates every
returned candidate against the invocation source set.

## 4. Rule invocation context

### `SemanticRuleInvocationContext`

| Field | Type | Rule |
| --- | --- | --- |
| `evaluation_id` | `str` | Exact P01 evaluation identity |
| `evaluation_timestamp` | `str` | Canonical explicit UTC timestamp |
| `semantic_profile_identity` | `SemanticProfileIdentity` | Exact P02-F01 identity |
| `rule_identity` | `RuleIdentity` | Rule being invoked |
| `instrument_binding_id` | `str` | Exact P02-F01 instrument binding |
| `timeframe` | `str \| None` | Present with `timeframe_role`, or both absent for cross-frame rules |
| `timeframe_role` | `TimeframeRole \| None` | Exact P01 role |
| `source_binding_ids` | `tuple[str, ...]` | Non-empty, sorted, unique |
| `provenance_refs` | `tuple[str, ...]` | Non-empty, sorted, unique |

The context contains no policy implementation, clock, registry, service, cache, broker, portfolio,
filesystem, network, or environment handle. Its rule identity must equal the invoked implementation
identity and every referenced source/provenance identity must exist in the bound typed bundle.

## 5. Typed invocation requests

Every request is a frozen dataclass with an exact `context: SemanticRuleInvocationContext`.

| Object | Additional exact fields |
| --- | --- |
| `SourceExtractionRequest` | `source: AnalyticalSourceBinding` |
| `DirectionRuleRequest` | `candidates: tuple[SemanticCandidate, ...]`, `allowed_source_states: tuple[str, ...]` |
| `CandidateSelectionRequest` | `candidates: tuple[SemanticCandidate, ...]`, `direction: StrategyDirection \| None` |
| `CandidateRankingRequest` | `candidates: tuple[SemanticCandidate, ...]`, `direction: StrategyDirection \| None` |
| `BoundarySelectionRequest` | `candidate: SemanticCandidate`, `direction: StrategyDirection` |
| `ApplicabilityRequest` | `candidate: SemanticCandidate`, `direction: StrategyDirection` |
| `PriceTransformationRequest` | `candidate: SemanticCandidate`, `direction: StrategyDirection` |
| `ConfidenceRuleRequest` | `inputs: tuple[ConfidenceInputValue, ...]`, `parameters: tuple[ModelParameter, ...]`, `base_confidence: float \| None` |
| `TemporalEligibilityRequest` | `candidates: tuple[SemanticCandidate, ...]`, `required_roles: tuple[TimeframeRole, ...]`, `revision_ids: tuple[str, ...]` |
| `EvidenceMappingRequest` | `evidence_key: str`, `candidates: tuple[SemanticCandidate, ...]` |
| `EvidenceOrderingRequest` | `evidence_keys: tuple[str, ...]` |
| `MtfAggregationRequest` | `directions: tuple[TimeframeDirectionValue, ...]`, `required_roles: tuple[TimeframeRole, ...]`, `required_timeframes: tuple[str, ...]` |

`ConfidenceInputValue` contains `input_key: str`, `candidate: SemanticCandidate`, and
`required: bool`. `TimeframeDirectionValue` contains exact `timeframe`, `role`,
`StrategyDirection`, `source_binding_ids`, and `provenance_refs`. Both are frozen and order by their
canonical keys. Requests reject empty required collections, duplicate identities, context/source
mismatch, wrong value kinds, and mutable input.

The closed type alias `SemanticRuleRequest` is the union of these request types. It is not `Any`, a
mapping, or an arbitrary object.

## 6. Typed rule results

Every result contains exact `state: SemanticRuleState` and canonically sorted unique
`diagnostic_codes: tuple[SemanticRuleDiagnosticCode, ...]`. `SUCCESS` requires its governed output
and forbids rejection diagnostics. Every non-success state forbids output values.

| Object | Success output |
| --- | --- |
| `CandidateRuleResult` | `candidates: tuple[SemanticCandidate, ...]` |
| `DirectionRuleResult` | `direction: StrategyDirection` |
| `SelectionRuleResult` | `selected_candidate_ids: tuple[str, ...]` |
| `RankingRuleResult` | `ordered_candidate_ids: tuple[str, ...]`, an exact permutation without duplicates |
| `BoundaryRuleResult` | `value: SemanticValue`, kind `PRICE` or `PRICE_RANGE` |
| `ApplicabilityResult` | `applicable: bool` |
| `PriceTransformationResult` | `candidate: SemanticCandidate` with `PRICE` value |
| `ConfidenceRuleResult` | `confidence: float`, exact built-in finite value in `[0.0, 1.0]` |
| `TemporalEligibilityResult` | `eligible: bool` |
| `EvidenceMappingResult` | `selected_candidate_ids: tuple[str, ...]` |
| `EvidenceOrderingResult` | `ordered_evidence_keys: tuple[str, ...]`, exact permutation |
| `MtfAggregationResult` | `direction: StrategyDirection` |

The closed type alias `SemanticRuleResult` is their union. P02 validates output type against the
declaration before using it. It never clips confidence, invents a missing candidate, repairs a
price, or changes ordering.

## 7. Executable rule protocol

### `ExecutableSemanticRule`

The exact public protocol is:

```python
class ExecutableSemanticRule(Protocol):
    @property
    def identity(self) -> RuleIdentity: ...

    @property
    def family(self) -> SemanticRuleFamily: ...

    @property
    def invocation_kind(self) -> SemanticInvocationKind: ...

    @property
    def result_kind(self) -> SemanticResultKind: ...

    @property
    def implementation_id(self) -> str: ...

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult: ...
```

Implementations are stateless or immutable. They consume only the request. The declared identity,
family, invocation kind, result kind, and implementation ID must exactly match their manifest
entry. P02 performs exact runtime request/result type checks; duck-typed alternative contracts are
rejected.

Domain non-match and governed rejection use typed results. Structural violations may raise
`DataIntegrityError`. Unexpected exceptions are caught only at the adapter implementation boundary
and translate to `FAILED` with stable diagnostic codes; exception messages and stack traces never
participate in semantic identity.

## 8. Persistent declarations and runtime implementations

### `SemanticRuleDeclaration`

| Field | Type | Rule |
| --- | --- | --- |
| `identity` | `RuleIdentity` | Exact persistent governance identity |
| `family` | `SemanticRuleFamily` | Exact family |
| `invocation_kind` | `SemanticInvocationKind` | Compatible with family |
| `result_kind` | `SemanticResultKind` | Compatible with family |
| `implementation_id` | `str` | Non-empty immutable certification/declaration ID |

Declarations order by `identity.reference`. They are serializable. `implementation_id` names the
reviewed implementation declaration; it is not derived from `repr`, module order, a memory address,
or a callable object.

### `ResolvedRuleManifest`

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | `str` | Exact execution schema version |
| `rule_set_id` | `str` | Derived SHA-256 |
| `declarations` | `tuple[SemanticRuleDeclaration, ...]` | Non-empty, sorted, unique identity |

The rule-set identity is SHA-256 over canonical tagged serialization of the schema version and
ordered declarations, excluding only `rule_set_id`. Any identity, family, kind, fingerprint, or
implementation declaration change changes the rule-set identity.

### `ResolvedSemanticRuleSet`

This frozen runtime object contains exact `manifest: ResolvedRuleManifest` and
`implementations: tuple[ExecutableSemanticRule, ...]`. It validates a one-to-one ordered match by
rule identity and all declaration properties. Equality and hashing use the validated manifest;
runtime implementations with the same certified declaration are governed as the same semantics.
It exposes exact resolution by `RuleIdentity` and never accepts `latest`, nearest, fallback, string
lookup, or mutation.

The manifest is serializable and reconstructable. Python implementations are explicitly injected
runtime dependencies and are not serialized or reconstructed. Pickle and code serialization are
forbidden.

## 9. Family compatibility and profile closure

The exact family-to-kind mapping is:

| Family | Invocation | Result |
| --- | --- | --- |
| `SOURCE_EXTRACTION` | `SOURCE_EXTRACTION` | `CANDIDATES` |
| `DIRECTION_MAPPING` | `DIRECTION` | `DIRECTION` |
| `CANDIDATE_SELECTION` | `SELECTION` | `SELECTION` |
| `CANDIDATE_RANKING` | `RANKING` | `RANKING` |
| `BOUNDARY_SELECTION` | `BOUNDARY` | `BOUNDARY` |
| `APPLICABILITY` | `APPLICABILITY` | `APPLICABILITY` |
| `PRECEDENCE` | `SELECTION` | `SELECTION` |
| `PRICE_TRANSFORMATION` | `PRICE_TRANSFORMATION` | `PRICE_TRANSFORMATION` |
| `CONFIDENCE` | `CONFIDENCE` | `CONFIDENCE` |
| `TEMPORAL_ELIGIBILITY` | `TEMPORAL_ELIGIBILITY` | `TEMPORAL_ELIGIBILITY` |
| `EVIDENCE_MAPPING` | `EVIDENCE_MAPPING` | `EVIDENCE_MAPPING` |
| `EVIDENCE_ORDERING` | `EVIDENCE_ORDERING` | `EVIDENCE_ORDERING` |
| `MTF_AGGREGATION` | `MTF_AGGREGATION` | `MTF_AGGREGATION` |

Before execution, P02 derives the exact required declaration set from a
`StrategySemanticMappingProfile`:

- every `SourceSelector.selector_rule` is `SOURCE_EXTRACTION`;
- non-null `DirectionFactPolicy.strategy_rule` values are `DIRECTION_MAPPING`;
- `MtfDirectionPolicyRef.rule_identity` is `MTF_AGGREGATION`;
- geometry `candidate_selector` values are `CANDIDATE_SELECTION`;
- entry/target `ranking_rule` values are `CANDIDATE_RANKING`;
- entry `required_boundary_rule` is `BOUNDARY_SELECTION`;
- stop `precedence_rule` is `PRECEDENCE`;
- stop buffer and optional volatility rules are `PRICE_TRANSFORMATION`;
- target optional threshold and extension rules are `APPLICABILITY` and
  `CANDIDATE_SELECTION`, respectively;
- all geometry `direction_applicability_rule` values are `APPLICABILITY`;
- confidence `model_identity` and optional calibration identity are `CONFIDENCE`;
- evidence temporal validity and revision rules are `TEMPORAL_ELIGIBILITY`;
- evidence source selectors are `SOURCE_EXTRACTION`;
- taxonomy `ordering_rule` is `EVIDENCE_ORDERING`.

Policy, taxonomy, freshness, and semantic-profile identity objects describe/fingerprint policy and
are not independently executable unless also occupying one of the explicit positions above.

The manifest must contain exactly the unique required identities with exactly one compatible
family. Missing declarations, unused extras, one identity required with conflicting families,
duplicate identities, and runtime implementation mismatch are `INVALID_INPUT`. Exact closure
prevents hidden semantics.

## 10. Native structural operations

P02 performs source-kind filtering, source-contract equality, instrument binding, timeframe and
role matching, provenance resolution, closed-state validation, availability/as-of validation, and
revision validation without rule dispatch. Structural filtering produces a canonical binding tuple;
it never chooses between otherwise eligible semantic candidates.

Only `SOURCE_EXTRACTION` rules read payload public APIs. They receive one exact
`AnalyticalSourceBinding`, validate the expected source kind/contract, and return typed candidates.
Private attributes, reflection-based field guessing, arbitrary `getattr` paths, user strings, and
duck typing are forbidden.

## 11. Generic execution semantics

Direct enum direction policies are generic after extraction: P02 matches the extracted `TEXT`
value against the policy's exact `EnumDirectionMapping` tuple. Unmapped or multiple values follow
the declared missing/conflict actions; there is no default direction. Non-direct direction policies
invoke their exact `DIRECTION_MAPPING` rule.

Selection, ranking, boundary, precedence, transformation, confidence, evidence, temporal, and MTF
rules operate only through their typed requests/results. Ranking ties must be resolved by the
concrete rule's ordered candidate-ID result; an incomplete or duplicate order is invalid. P02 owns
no Elliott, Fibonacci, structure, liquidity, Decision, confidence, or MTF interpretation.

Entry execution extracts candidates from the allowed selectors, applies `candidate_selector`,
requires the ranking result to be an exact permutation of the selected IDs, and treats its first
ID as the explicit ranking-rule winner. It then invokes the boundary rule and constructs
`EntryFacts`; this use of the first ordered ID is authorized only by the explicit ranking result and
is not a fallback. Stop execution applies candidate selection, precedence, buffer, and optional
volatility transformation in that order. Target execution applies candidate selection, ranking,
optional threshold applicability, and optional extension selection in that order. Every stage
preserves candidate lineage. No stage is skipped except an explicitly absent optional P02-F01 rule.

All confidence variants invoke `model_identity`. `DIRECT` requires the frozen single input;
`WEIGHTED` and `RULE` pass the complete canonical inputs and parameters without P02 interpreting
them. For `CALIBRATED`, P02 first invokes `model_identity` with `base_confidence=None`, validates the
base result, then invokes `calibration_identity` with that exact value in `base_confidence`.
Non-calibration invocations require `base_confidence=None`; calibration invocations require a
finite value in `[0.0, 1.0]`. P02 validates the final output and never supplies a formula, weight,
normalizer, clipping rule, or default.

`FreshnessPolicy` is executed natively. P02 chooses the source observation or availability
timestamp according to `FreshnessBasis`, computes exact elapsed whole seconds against
`EvaluationContext.evaluation_timestamp`, and marks fresh exactly when age is non-negative and
`age <= max_age_seconds`. A future source timestamp is structural `INVALID_INPUT`, not fresh.

## 12. Adapter invocation binding

P01 remains exactly:

```python
adapter.adapt(context, inputs, profile, policy) -> FactAdapterResult
adapter.identity -> FactAdapterIdentity
```

### `AdapterInvocationBinding`

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | `str` | Exact execution schema version |
| `binding_id` | `str` | Derived SHA-256 |
| `adapter_identity` | `FactAdapterIdentity` | Exact future adapter identity |
| `semantic_profile_identity` | `SemanticProfileIdentity` | Exact P02-F01 identity |
| `resolved_rule_set_id` | `str` | Exact manifest identity |
| `typed_bundle_id` | `str` | Exact `MultiTimeframeAnalyticalBundle.bundle_id` |
| `analytical_input_digest` | `str` | Canonical SHA-256 of the frozen P01 `AnalyticalInputBundle` |
| `provenance_manifest_id` | `str` | Shared exact P01 manifest identity |
| `instrument_binding_id` | `str` | Exact P02-F01 binding identity |

The future `CanonicalFactAdapter` is an immutable, evaluation-scoped configured service constructed
with `identity`, exact `StrategySemanticMappingProfile`, exact `ResolvedSemanticRuleSet`, exact
`MultiTimeframeAnalyticalBundle`, and exact `AdapterInvocationBinding`. P03 creates a new configured
instance for an adaptation. There is no setter, current profile, current instrument, mutable cache,
or later dependency lookup.

At `adapt`, P02 proves that the four frozen P01 arguments match the binding: context evaluation,
profile identity and full parent value, policy/strategy identity and evidence keys, canonical
analytical-input digest, MTF coherence identity, provenance manifest, instrument, semantic profile,
adapter identity, and rule-set identity. It also proves that every primary P01 payload is the exact
value-equal payload represented by the corresponding typed primary-frame binding and that no typed
primary payload is omitted from the P01 bundle. Divergence is `INVOCATION_BINDING_MISMATCH` and
`INVALID_INPUT`. Evaluation-specific constructor binding is required only because P01 is frozen;
it is explicit immutable state, not hidden mutable state.

## 13. Evidence identity and keys

Concrete evidence keys are exactly `EvidenceKeyPolicy.evidence_key` from the supplied taxonomy.
P02 never constructs or concatenates a new key.

One A07 `StrategyEvidenceIdentity` represents the complete evidence set, as required by the P01
bundle contract. Its `evidence_id` is lowercase SHA-256 over canonical tagged data containing:

```text
domain = epip.strategy-evidence-set.p02-f02-v1
strategy_id
strategy_version
semantic_profile_identity
adapter_identity
typed_bundle_id
provenance_manifest_id
ordered entries of:
  evidence_key
  ordered source_binding_ids
  ordered provenance_refs
```

Its `provenance` field is exactly `ProvenanceManifest.manifest_id`. All inputs are explicit and
immutable. The identity is computed after evidence mapping and before constructing snapshots. All
snapshots use that same identity, their exact taxonomy key, and their natively computed freshness
and rule-produced temporal eligibility. P02 does not bypass A07 E02 validation.

## 14. Result and diagnostic translation

Rule `SUCCESS` continues execution. `NO_MATCH` becomes `REJECTED` when a required fact cannot be
completed; an optional evidence item may be omitted only as explicitly allowed by the profile.
`REJECTED` becomes adapter `REJECTED`. Rule `INVALID_INPUT`, missing resolution, identity/family
mismatch, invocation mismatch, or malformed output becomes adapter `INVALID_INPUT`. Rule `FAILED`
or an unexpected implementation exception becomes adapter `FAILED`. Only a complete validated
bundle becomes `ACCEPTED`.

Additive diagnostic codes translate to existing P01 `RuntimeDiagnostic` values. The P01 code is
`MISSING_FACT` for required no-match, `ADAPTER_REJECTED` for governed rejection,
`COHERENCE_FAILURE` or `TEMPORAL_FAILURE` for corresponding structural failures, and
`ADAPTER_FAILED` for failed execution. Other invalid rule/binding conditions use
`INVALID_REQUEST`. Stage is the nearest existing P01 stage, normally `ADAPTER`; severity is
`ERROR`; `subject_ref` is the rule or binding reference; `source_refs` are canonical; and `message`
is exactly the additive diagnostic code value. Free-form exception text is not exposed.

## 15. Dispatch lifecycle

The normative order is:

1. validate all structural inputs without reading semantic payload fields;
2. validate the invocation binding and P01/P02 bridge;
3. validate the semantic profile and parent P01 profile/policy continuity;
4. validate exact resolved-rule-set closure;
5. resolve structural selectors into canonical source tuples;
6. invoke the exact identity-bound extraction and semantic rules;
7. validate every exact result type, state, candidate lineage, and output domain;
8. assemble A07 `DirectionalFacts`, `EntryFacts`, `StopFacts`, and `TargetFacts`;
9. assemble evidence snapshots and the evidence-set identity;
10. create the complete P01 `StrategyFactBundle` with per-fact provenance;
11. return the exact P01 `FactAdapterResult`.

Revision selection never occurs in P02. P03 or an upstream deterministic assembler supplies one
legal revision. P02 never chooses the largest ordinal, latest binding, first candidate, or previous
snapshot.

## 16. Purity, security, and lifecycle

Rules and adapter execution may not read a wall clock, environment, filesystem, network, broker,
portfolio, execution state, mutable global, or randomness. Dynamic import by user-controlled
string, plugin discovery, `eval`, `exec`, pickle, callable serialization, and code hashing by
`repr`/address are forbidden. Explicit application construction is the only implementation source.

No execution cache is defined. Future optimization must remain outside semantic identity and may
not alter results. Correctness and deterministic replay take precedence.

## 17. Public implementation inventory

Future P02-F03 implements only these public contracts:

- `SemanticRuleFamily`, `SemanticInvocationKind`, `SemanticResultKind`, `SemanticRuleState`,
  `SemanticValueKind`, and `SemanticRuleDiagnosticCode`;
- `SemanticValue`, `SemanticCandidate`, `ConfidenceInputValue`, and `TimeframeDirectionValue`;
- `SemanticRuleInvocationContext` and the twelve typed request contracts;
- the twelve typed result contracts;
- `ExecutableSemanticRule`;
- `SemanticRuleDeclaration`, `ResolvedRuleManifest`, and `ResolvedSemanticRuleSet`;
- `AdapterInvocationBinding`;
- the canonical evidence-set identity derivation function.

No public selector helper, registry, loader, cache, plugin, concrete rule, or adapter is part of
P02-F03. The later P02 implementation adds only `CanonicalFactAdapter` as public behavior.

## 18. Serialization and reconstruction

Enums, values, candidates, invocation context, requests, results, declarations, manifests, and
invocation bindings extend the P01 tagged canonical format. Unknown tags, unsupported versions,
wrong exact types, mutable collections, non-finite numbers, contradictory states, and tampered
identities fail closed. Derived identities are recomputed.

`ResolvedSemanticRuleSet.implementations` and executable Python behavior are runtime-only and are
not passed to canonical serialization. Persist and reconstruct `ResolvedRuleManifest`; inject and
revalidate implementations afterward. No serialized document can cause code loading.

## 19. Future file plan

P02-F03 implementation is limited to:

```text
epip/strategy_mapping/rule_execution.py
epip/strategy_mapping/rule_values.py
epip/strategy_mapping/rule_requests.py
epip/strategy_mapping/rule_results.py
epip/strategy_mapping/resolved_rules.py
epip/strategy_mapping/invocation_binding.py
epip/strategy_mapping/evidence_identity.py
epip/strategy_mapping/__init__.py
tests/strategy_mapping/test_rule_execution_contracts.py
tests/strategy_mapping/test_resolved_rules.py
tests/strategy_mapping/test_invocation_binding.py
tests/strategy_mapping/test_evidence_identity.py
tests/strategy_mapping/test_execution_serialization.py
tests/strategy_mapping/test_execution_isolation.py
```

The future P02 adapter is limited to `epip/strategy_mapping/adapter.py` plus minimal private helpers
and adapter-focused tests.

## 20. Future validation contract

Tests must cover exact protocol signatures, all enum inventories, value shapes, candidate lineage,
request/result shape and state invariants, rule identity/declaration matching, family compatibility,
manifest identity, exact profile closure, missing/duplicate/extra rules, invocation and result type
mismatch, deterministic repeated execution, immutable injection, no latest/global lookup, binding
continuity, P01 signature continuity, evidence identity determinism, canonical serialization,
reconstruction, tamper rejection, dependency isolation, and every security prohibition.

Test-only executable rules live only under `tests/`, carry explicit synthetic identities, are
deterministic, and make no Elliott/Fibonacci/MTF production claim. No arbitrary count is frozen.

```text
PRE-P02-F03 = 2694
POST-P02-F03 = 2694 + actual P02-F03 test contribution
predecessor removals = 0
```

## 21. Program boundary after reconciliation

P00, P01, P02-F00, and P02-F01 remain closed and frozen. P02-F02 is governance only and requires
separate P02-F03 implementation authorization. P02 remains not authorized until P02-F03 is
implemented, validated, published, and closed. P03, P04, and P05 remain not authorized.
