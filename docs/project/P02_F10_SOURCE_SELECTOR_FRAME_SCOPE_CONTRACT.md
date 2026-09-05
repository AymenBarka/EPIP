# P02-F10 Source Selector Frame Scope Contract

## 1. Status and authority

P02-F10 is a governance-only reconciliation. It closes the source-frame ambiguity found when
P02-F09 attempted to implement `CanonicalFactAdapter`. It authorizes no Python or test changes.
Actual frozen implementation governs obsolete prose. ADR-0023 records the architectural decision.

P02-F09 remains blocked until a separately authorized P02-F11 implements this contract and closes.

## 2. Confirmed contradiction

`SourceSelector` currently contains `source_kind`, `source_contract`, `selector_kind`,
`selector_rule`, and `required_provenance`, but no frame role or scope. A valid
`MultiTimeframeAnalyticalBundle` may contain PRIMARY, HIGHER, and LOWER frames with sources matching
the same kind and contract. F06 defines active-frame narrowing only while deriving per-frame MTF
direction inputs. Ordinary direction, entry, stop, target, confidence, and evidence selection
therefore cannot distinguish PRIMARY-only visibility from all-frame visibility.

Implicit PRIMARY is rejected because it hides profile semantics in adapter control flow. Implicit
all-frame visibility is rejected because it changes candidate cardinality, invocation counts,
geometry, confidence, evidence lineage, and identities. First-frame, nearest-frame,
highest/lowest-timeframe, caller-inferred, and empty-as-wildcard behavior are forbidden.

## 3. Final model

`SourceSelector` gains one mandatory field:

```text
frame_roles: tuple[TimeframeRole, ...]
```

One ordinary selector **may consume more than one timeframe role**, but only by explicitly listing
each admitted role. This is required so future P04 profiles can deliberately express multi-frame
confidence or evidence without P02 inference. Exact-one-role selection is represented by a
one-element tuple; no separate single-role type or wildcard exists.

The invariants are:

- the value is an exact tuple and is non-empty;
- every member is an exact `TimeframeRole`;
- duplicate roles are invalid;
- the canonical role order is PRIMARY, HIGHER, LOWER;
- construction canonicalizes an otherwise valid permutation into that order;
- `None`, strings, foreign enums, missing fields, and empty tuples fail closed;
- no default is provided, including during reconstruction.

Frame scope is structural semantic-profile data. P04 chooses concrete values; P02 only validates
and resolves them mechanically.

## 4. Deterministic resolution algorithm

Resolution consumes one exact `SourceSelector`, one validated `MultiTimeframeAnalyticalBundle`, and
an optional explicit active-frame constraint used only by F06 per-frame direction execution.

1. Validate the selector and complete typed bundle before invoking any semantic rule.
2. For ordinary execution, effective roles are exactly `selector.frame_roles`.
3. For F06 per-frame execution, the active frame role must occur in `selector.frame_roles`; the
   effective role tuple is then exactly that active role. Absence is structural `INVALID_INPUT`.
4. Select frames whose exact `TimeframeRole` occurs in the effective tuple.
5. Every effective role must resolve at least one frame. A missing role is structural
   `INVALID_INPUT`; no other role substitutes for it.
6. Within each effective role, order frames by exact `timeframe` text.
7. Within each frame, select sources whose `source_kind` and exact `source_contract` equal the
   selector and whose instrument, timeframe, closed-state, availability, revision, and provenance
   validations succeed.
8. Order matching sources by their existing `AnalyticalSourceBinding.canonical_key()`.
9. The final tuple order is canonical role order, then timeframe, then source canonical key.
10. A selected `source_binding_id` may occur only once across the complete result. Cross-frame
    duplicate identity, conflicting binding metadata, or inconsistent instrument/provenance is
    structural `INVALID_INPUT`.
11. A role with frames but no matching binding produces governed `SELECTOR_NO_MATCH`. Required
    direction/geometry/confidence/evidence paths become P01 `REJECTED`; optional evidence may omit
    only under the existing F04 rule. No fallback or silent role expansion occurs.

Sources in valid but undeclared roles remain outside that selector's visibility. They do not become
errors merely by existing in the typed bundle. A resolved tuple containing an undeclared role is
invalid adapter behavior.

## 5. Candidate assembly and ordering

Each selected binding is passed once to its exact extraction rule in the resolution order above.
Each successful `CandidateRuleResult` is contextually validated. The union of candidates is then
canonicalized by the existing candidate-ID rule before ordinary selection requests. Frame traversal
never creates semantic ranking. F08 remains authoritative: only a ranking result creates ranked
candidate order, and Target extension receives that exact order through
`RankedCandidateSelectionRequest`.

## 6. Stage consequences

Non-MTF direction policies resolve sources using their own explicit `frame_roles`. Direct enum and
rule-based direction processing receive only candidates from those roles.

F06 per-frame MTF direction uses the same resolver plus the exact active frame. The reused
`frame_direction_fact` policy must admit every role selected by the MTF policy. It is applied once
per selected frame and cannot see another frame during that invocation. F06 role/timeframe ordering
and P05 ownership of aggregation remain unchanged.

Entry, stop, and target resolve every allowed selector independently by its explicit roles before
applicability and selection. Multiple selector outputs join only through existing canonical
candidate normalization. Target ranking and F08 extension order remain unchanged.

Every confidence input selector resolves its explicit roles independently. If several extracted
candidates remain where the frozen confidence input requires one, existing missing/conflict policy
governs; frame scope supplies no implicit choice.

Every evidence-key selector resolves only its explicit roles. Mapping-selected candidate lineage
therefore fixes freshness inputs, temporal and revision requests, evidence-item identity, final
evidence ordering, evidence-set identity, and bundle identity without adapter inference.

## 7. Serialization, identity, and closure

`frame_roles` participates in normal tagged serialization as a tuple of `TimeframeRole` enums.
Round trips retain the canonical stored tuple. Reconstruction invokes `SourceSelector`; a missing
field, empty tuple, duplicate, foreign enum, malformed tag, or wrong type fails closed. A reordered
valid input reconstructs to canonical role order because visibility is set-like, not ranked.

Dataclass equality and hashing include `frame_roles`. `SourceSelector.canonical_key()` includes the
canonical role tuple so otherwise identical differently scoped selectors remain distinct and sort
deterministically. Because selectors are nested in every affected policy, scope participates in the
existing `StrategySemanticMappingProfile` fingerprint. PRIMARY and HIGHER profiles, and
`(PRIMARY,)` and `(PRIMARY, HIGHER)` profiles, necessarily have different fingerprints.

No executable `RuleIdentity`, semantic family, invocation kind, result kind, manifest declaration,
or resolver rule is added. Exact profile closure traverses the same rule identities. Only structural
selector validation and canonical keys change.

## 8. Migration impact and P02-F11

The current production package defines `SourceSelector` but constructs no concrete selector or
profile. The tracked Python inventory has one direct constructor in
`tests/strategy_mapping/conftest.py`; its shared synthetic profiles and all dependent tests must be
updated explicitly. Documentation examples and serialized fixtures, if introduced or discovered by
P02-F11, must also supply an explicit tuple. Existing payloads without the field fail reconstruction;
their intended scope must not be guessed.

P02-F11 may change only the `SourceSelector` contract and canonical key, constructor call sites,
serialization/reconstruction expectations, semantic-profile fingerprint expectations, exact
structural resolver helper if needed for focused proof, public exports only if a new public value is
unavoidable, focused tests, and the mechanical immutable-compliance digest if the inventory changes.
It must not implement `CanonicalFactAdapter`, P03, P04, P05, or concrete semantic rules.

P02-F09 may resume only after P02-F11 is CLOSED / FROZEN and a new readiness review finds no
remaining normative contradiction.

## 9. P02-F11 acceptance matrix

P02-F11 tests must prove PRIMARY-only, HIGHER-only, and explicit multi-role scope; PRIMARY/HIGHER/
LOWER canonical role ordering; timeframe and source-key ordering within a role; empty, duplicate,
missing, foreign, and wrong-type rejection; missing-role and cross-frame duplicate-binding failure;
tagged round trip; reconstruction failure without scope; canonicalization of reordered role input;
equality/hash and profile-fingerprint divergence; exact ordinary direction, entry, stop, target,
confidence, and evidence resolution; active-frame MTF narrowing; no implicit fallback; unchanged
rule closure; and zero new executable identity.

## 10. Ownership boundaries

P01 protocol, states, diagnostics, and result contracts are unchanged. A07 fact and evidence
contracts are unchanged. P03 supplies an already complete profile and typed bundle but does not
select roles. P04 chooses concrete selector scopes. P05 alone supplies MTF aggregation semantics.
P02 owns only exact validation, deterministic resolution, and lineage preservation.

Remaining implementation-significant ambiguities: **NONE**.
