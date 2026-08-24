# P02-F00 Additive Strategy Mapping Foundation Contract

Status: NORMATIVE CONTRACT RECONCILED / IMPLEMENTATION NOT AUTHORIZED

Authority: [ADR-0016](../adr/ADR-0016-CanonicalStrategyPipeline.md),
[ADR-0017](../adr/ADR-0017-CanonicalStrategyRuntimeContracts.md), and
[ADR-0018](../adr/ADR-0018-TypedStrategyMappingAndAvailabilityBoundaries.md).

## 1. Purpose and classification

P02-F00 defines additive schemas needed before a concrete P02 Fact Adapter. It composes frozen P01
objects and never changes their fields or identities.

| Area | Classification |
| --- | --- |
| P01 contracts | FROZEN |
| P02-F00 schemas | NORMATIVE; FUTURE IMPLEMENTATION |
| Generic Fact Adapter | P02; FUTURE IMPLEMENTATION |
| Elliott/Fibonacci rule instance | P04; FUTURE IMPLEMENTATION |
| MTF direction rule instance | P05; FUTURE IMPLEMENTATION |

No concrete source choice, direction map, geometry hierarchy, confidence weight, evidence key,
freshness threshold, or MTF aggregation is authorized here.

## 2. Common contract standard

Public P02-F00 values shall be frozen, slot-based, exactly typed, value-equal, hashable, and
nested-immutable. Collections are tuples and use the specified canonical ordering. Reconstruction
recomputes derived values and rejects contradictions.

`FOUNDATION_SCHEMA_VERSION` is exactly `p02-f00-v1`. Timestamps are timezone-aware ISO-8601 and
normalize to UTC microsecond form. Numbers are finite. Serialization extends P01's canonical tagged
format: enums use values, tuples retain tuple tags, optional values are explicit, object keys are
sorted, and NaN/Infinity are rejected.

Every derived identity is lowercase SHA-256 over canonical semantic serialization with only its
own identity field excluded. No random UUID, ambient clock, environment, filesystem, network,
mutable registry, or hash iteration may influence a value.

## 3. Closed vocabularies

`AnalyticalSourceKind` has exactly:

```text
SWING
MARKET_STRUCTURE
LIQUIDITY
FIBONACCI
MARKET_CONTEXT
ELLIOTT
DECISION
KERNEL
```

`SourceSelectorKind` has exactly `DIRECT_ENUM`, `DIRECT_VALUE`, `ZONE_CANDIDATES`,
`PRICE_CANDIDATES`, `HYPOTHESIS_RULE`, `ELLIOTT_COUNT_RULE`, `CONFIDENCE_INPUT`,
`EVIDENCE_INPUT`, and `MTF_RULE`. Selectors use rule identities, never arbitrary field paths.

`NonAcceptanceAction` has exactly `REJECT`, `NO_FACT`, `REQUIRE_SINGLE`, and
`REQUIRE_EXPLICIT_SELECTION_RULE`. `NO_FACT` never fabricates an A07 fact; when the fact is required
for a complete bundle it yields `FactAdapterState.REJECTED`.

`ConfidenceModelKind` is exactly `DIRECT`, `WEIGHTED`, `RULE`, `CALIBRATED`.
`EvidenceRequirement` is exactly `REQUIRED`, `OPTIONAL`. `FreshnessBasis` is exactly
`OBSERVATION`, `AVAILABILITY`. `DirectionFactName` is exactly `ELLIOTT`, `TREND`, `STRUCTURE`,
`PRIMARY`, `ALTERNATE`, `MTF`.

## 4. Instrument identity

### `InstrumentAlias`

| Field | Type | Rule |
| --- | --- | --- |
| `provider_id` | `str` | Non-empty exact provider identity |
| `symbol` | `str` | Non-empty exact provider symbol |

Aliases sort by `(provider_id, symbol)` and are unique by that pair.

### `InstrumentBinding`

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | `str` | Exact foundation version |
| `binding_id` | `str` | Derived SHA-256 |
| `instrument_id` | `str` | Exact canonical ID matching `EvaluationContext` |
| `canonical_symbol` | `str` | Canonical EPIP symbol |
| `aliases` | `tuple[InstrumentAlias, ...]` | Canonical unique aliases; may be empty |
| `binding_version` | `str` | Non-empty immutable mapping version |

Symbol equality alone does not establish identity. A payload symbol must equal the canonical symbol
or an admitted alias. Unknown aliases, mixed binding IDs, and context ID mismatches are structural
`INVALID_INPUT` conditions.

## 5. Observation, availability, as-of, and revision

Observation time describes when the market/domain fact occurred. Availability time is the earliest
instant the complete revision could legally be consumed. As-of time is the deterministic cutoff
used upstream to select that exact revision.

### `RevisionIdentity`

| Field | Type | Rule |
| --- | --- | --- |
| `source_series_id` | `str` | Stable identity of the revisable semantic source |
| `revision_id` | `str` | Opaque immutable revision identity |
| `revision_ordinal` | `int` | Non-negative ordinal within the series |
| `supersedes_revision_id` | `str \| None` | Explicit immediate predecessor, if present |

An ordinal never authorizes choosing the highest value. P03 or an upstream deterministic assembler
resolves one legal revision. P02 receives it and never queries mutable history or selects latest.

### `AnalyticalSourceBinding`

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | `str` | Exact foundation version |
| `source_binding_id` | `str` | Derived SHA-256 |
| `source_kind` | `AnalyticalSourceKind` | Closed category |
| `source_contract` | `str` | Fully qualified public contract identity |
| `source_contract_version` | `str` | Exact producer contract version |
| `source_object_id` | `str` | Immutable source object identity |
| `instrument` | `InstrumentBinding` | Canonical instrument relationship |
| `timeframe` | `str` | Exact canonical timeframe |
| `observation_timestamp` | `str` | Fact occurrence time |
| `availability_timestamp` | `str` | Earliest legal consumption time |
| `as_of_timestamp` | `str` | Revision-resolution cutoff |
| `revision` | `RevisionIdentity` | Explicit resolved revision |
| `superseded_at` | `str \| None` | First instant revision ceased to be legal |
| `closed` | `bool` | Exact producer final/closed status |
| `provenance_ref` | `str` | Existing P01 source provenance identity |
| `payload` | `AnalyticalPayload` | Closed typed payload union |

`AnalyticalPayload` is exactly `SwingSequence`, `MarketStructureSnapshot`, `LiquiditySnapshot`,
`FibonacciSnapshot`, `MarketContextSnapshot`, `WaveSnapshot`, `DecisionSnapshot`, or `KernelResult`.
Runtime type must match source kind and source contract.

Validation requires:

```text
observation_timestamp <= availability_timestamp <= as_of_timestamp
as_of_timestamp <= EvaluationContext.evaluation_timestamp
availability_timestamp <= EvaluationContext.evaluation_timestamp
closed is True
```

If present, `superseded_at` follows availability and must be later than `as_of_timestamp`. Exposed
payload symbol/timeframe must agree with the binding. `provenance_ref` resolves in the composed P01
manifest, whose contract, object, and timestamp agree. Missing availability evidence is structural
invalidity; P02 cannot substitute observation time.

Source construction must account for Swing right-bar confirmation latency, Structure's confirmed
Swing dependency, Liquidity sweep recognition, Fibonacci confirmed pivots, Elliott revision, and
Decision's inherited availability. Producers or deterministic assemblers own those facts; P02
validates but never fabricates them.

## 6. Typed MTF analytical bundle

### `TimeframeAnalyticalFrame`

| Field | Type | Rule |
| --- | --- | --- |
| `frame_id` | `str` | Derived SHA-256 |
| `frame` | P01 `TimeframeInput` | Frozen coherence metadata |
| `sources` | `tuple[AnalyticalSourceBinding, ...]` | Non-empty, unique, ordered |
| `provenance_refs` | `tuple[str, ...]` | Exact required source refs |

Sources order by `(source_kind.value, source_contract, source_object_id, revision_id)` and are
unique by binding ID. Their timeframe, instrument, closed state, provenance, and availability must
agree with the frame.

### `MultiTimeframeAnalyticalBundle`

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | `str` | Exact foundation version |
| `bundle_id` | `str` | Derived SHA-256 |
| `instrument` | `InstrumentBinding` | One canonical instrument |
| `coherence` | P01 `MultiTimeframeInputSet` | Exact frozen object |
| `frames` | `tuple[TimeframeAnalyticalFrame, ...]` | One typed frame per coherence frame |
| `provenance_manifest_id` | `str` | Exact P01 manifest identity |

Frame identities exactly equal the coherence set: one primary, zero or more higher, zero or more
lower, without omission or addition. Ordering is PRIMARY, HIGHER, LOWER, then timeframe. P01
closed-frame/alignment rules remain authoritative. No `mtf_direction` is derived; P05 supplies a
concrete rule later.

## 7. Rule identity and P01 composition

### `RuleIdentity`

Fields are `rule_id`, `rule_version`, `rule_schema_version`, and `fingerprint`. All are non-empty;
fingerprint is SHA-256 of the complete concrete rule. No latest, nearest, implicit, or fallback
resolution exists.

### `SemanticProfileIdentity`

| Field | Type |
| --- | --- |
| `semantic_profile_id` | `str` |
| `semantic_profile_version` | `str` |
| `mapping_schema_version` | `str` |
| `parent_profile_identity` | P01 `StrategyProfileIdentity` |
| `fingerprint` | `str` |

Fingerprint covers every rule and the parent identity. The P01 profile's mapping, confidence,
evidence-taxonomy, and MTF references must equal corresponding exact successor identities. Mismatch
is `INVALID_INPUT`; neither side is resolved implicitly.

## 8. Direction policy

`SourceSelector` fields are `source_kind`, `source_contract`, `selector_kind`, exact
`selector_rule: RuleIdentity`, and `required_provenance`, which must be true for fact-producing
selectors.

`EnumDirectionMapping` contains exact `source_value: str` and A07
`strategy_direction: StrategyDirection`. Values are unique and unmapped values have no default.

`DirectionFactPolicy` fields are:

```text
fact_name
selector
allowed_source_states
enum_mappings
strategy_rule
missing_action
conflict_action
```

Direct enum mapping uses canonical enum mappings. Hypothesis/Elliott selection requires a non-null
exact strategy rule. A concrete semantic profile contains one unique policy for ELLIOTT, TREND,
STRUCTURE, PRIMARY, and ALTERNATE.

`MtfDirectionPolicyRef` contains required roles, required exact timeframes, a P05 `RuleIdentity`,
missing action, and conflict action. Until P05 supplies that rule, a profile requiring MTF direction
cannot be accepted. No mapping values or aggregation formula are defined here.

## 9. Geometry policy

All candidate selectors are typed `SourceSelector` values with exact rule identities and required
provenance.

`EntrySourcePolicy` contains `policy_identity`, `allowed_selectors`, `candidate_selector`,
`ranking_rule`, `required_boundary_rule`, `direction_applicability_rule`, `missing_action`,
`conflict_action`, and `require_provenance` (true). No OTE, golden, Fibonacci, Decision, Liquidity,
or other source is selected now.

`StopSourcePolicy` contains `policy_identity`, `allowed_selectors`, `candidate_selector`,
`precedence_rule`, `buffer_rule`, optional `volatility_adjustment_rule`,
`direction_applicability_rule`, `missing_action`, `conflict_action`, and `require_provenance`
(true). No hierarchy, buffer, or volatility behavior is defined now.

`TargetSourcePolicy` contains `policy_identity`, `allowed_selectors`, `candidate_selector`,
`ranking_rule`, optional `threshold_rule`, optional `extension_rule`,
`direction_applicability_rule`, `missing_action`, `conflict_action`, and `require_provenance`
(true). No Elliott, Fibonacci, Liquidity, Structure, or Decision target is preferred.

All rules are exact `RuleIdentity` values. An optional rule means absence of that transformation,
never a default implementation.

## 10. Confidence policy

`ConfidenceInput` contains unique `input_key`, typed `source_selector`, and `required` boolean.
`ModelParameter` contains unique `parameter_key` and finite float `value`; all parameters are
canonically ordered and included in the fingerprint.

`ConfidencePolicy` contains `policy_identity`, `model_kind`, `model_identity`, `inputs`,
`parameters`, optional `calibration_identity`, exact output range `0.0..1.0`, `missing_action`, and
`conflict_action`. `DIRECT` requires exactly one input. Other kinds require an exact model identity;
`CALIBRATED` also requires calibration identity. P04 supplies formula, inputs, weights, and
calibration. There is no `0.5` default.

## 11. Evidence, freshness, and temporal eligibility

`FreshnessPolicy` contains `policy_identity`, `basis`, non-negative `max_age_seconds`, and
`failure_action`. A concrete profile supplies the threshold. Age uses injected evaluation time,
never wall time. Availability and freshness are distinct.

`TemporalEligibilityPolicy` contains `policy_identity`, required timeframe roles,
`validity_rule`, `revision_rule`, and `failure_action`. It governs strategy constraints beyond
availability and freshness.

`EvidenceKeyPolicy` contains canonical `evidence_key`, `requirement`, typed source selector,
freshness policy, temporal eligibility policy, and required provenance. Keys are unique and sorted.

`EvidenceTaxonomy` contains `taxonomy_identity`, key policies, `unknown_source_action`,
`duplicate_action`, and `ordering_rule`. Required/optional classification exactly reconciles with
P01 `StrategyProfile` and A07 `StrategyPolicy`. Unknown evidence cannot be invented, ignored, or
promoted. Concrete keys and mappings remain P04.

## 12. Conflict, fallback, and profile

Every policy explicitly declares missing/conflict behavior. `REQUIRE_EXPLICIT_SELECTION_RULE` is
valid only with an exact supplied rule identity. Structural corruption is never a semantic policy
outcome.

Forbidden without later explicit deterministic governance are previous snapshot, latest
profile/revision, first candidate, default BUY/SELL, undefined-to-NO_TRADE coercion, default
geometry/confidence, missing alternate equals primary, implicit precedence, majority vote, and
random tie-breaking.

`StrategySemanticMappingProfile` has exact fields:

```text
schema_version
identity: SemanticProfileIdentity
parent_profile: P01 StrategyProfile
direction_policies
mtf_direction_policy
entry_policy
stop_policy
target_policy
confidence_policy
evidence_taxonomy
global_conflict_action
```

Construction requires exact parent/reference reconciliation, complete unique policy families,
supported schemas, no dangling rules, and a matching fingerprint. Resolution uses the complete
identity. P04 will instantiate the Elliott/Fibonacci profile; P05 will provide its MTF rule. P02
executes a complete supplied profile but does not create or infer it.

## 13. Error and P01 result states

| Condition | P01 `FactAdapterState` |
| --- | --- |
| Complete valid bundle | `ACCEPTED` |
| Required fact legitimately absent | `REJECTED` |
| Explicit profile conflict rejection | `REJECTED` |
| Freshness/strategy temporal rule unsatisfied | `REJECTED` |
| No profile-governed acceptable candidate | `REJECTED` |
| Wrong type or unsupported schema/rule | `INVALID_INPUT` |
| Broken instrument/timeframe/time/revision | `INVALID_INPUT` |
| Invalid fingerprint, duplicate identity, dangling provenance | `INVALID_INPUT` |
| Unexpected adapter implementation fault | `FAILED` |

Malformed input is never silently converted into strategy rejection. P01 states remain unchanged.

## 14. Dependency and ownership contract

Allowed dependencies are frozen P01, frozen A07 facts/identities, official public analytical
contracts, Core deterministic/integrity/temporal values, and deterministic standard-library code.

Forbidden dependencies are P03 behavior, Capital Risk implementation, Execution, Portfolio
implementation, broker/MT5 clients, filesystem runtime state, network, environment-derived state,
ambient clocks, and randomness.

P02 owns type, instrument, timeframe, availability, revision, provenance, ordering, explicit-rule
execution, and result construction. P03 owns orchestration and resolved input/profile provision.
P04 owns concrete Elliott/Fibonacci rules. P05 owns concrete MTF direction. A07 remains final.

## 15. Future implementation and tests

The additive package shall be `epip/strategy_mapping/`, separate from frozen
`epip/strategy_runtime/`:

```text
epip/strategy_mapping/__init__.py
epip/strategy_mapping/_base.py
epip/strategy_mapping/instrument.py
epip/strategy_mapping/source_binding.py
epip/strategy_mapping/mtf_bundle.py
epip/strategy_mapping/rule_identity.py
epip/strategy_mapping/direction_policy.py
epip/strategy_mapping/geometry_policy.py
epip/strategy_mapping/confidence_policy.py
epip/strategy_mapping/evidence_policy.py
epip/strategy_mapping/profile.py
epip/strategy_mapping/serialization.py
```

Tests under `tests/strategy_mapping/` must cover schemas/types, equality, hashing, immutability,
ordering, UTC equivalence, observation/availability/as-of ordering, evaluation cutoff, revision and
supersession, missing availability, confirmation latency binding, instrument aliases/mismatch,
source kind/payload matching, MTF frame equality/primary/closure/instrument/availability, profile
composition/fingerprints, every policy variant, confidence range/parameters, evidence taxonomy,
freshness versus eligibility, explicit conflict/no-fallback, serialization, reconstruction, tamper
rejection, dependency isolation, P01 compatibility, and P04/P05 isolation.

No arbitrary test count is frozen:

```text
PRE-FOUNDATION = 2673
POST-FOUNDATION = 2673 + actual foundation test contribution
predecessor removals = 0
```
