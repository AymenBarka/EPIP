# P02-F14 Confidence Input Candidate Cardinality Contract

## 1. Status and scope

P02-F14 is the normative reconciliation for confidence-input extraction cardinality. It changes
no Python contract, implementation, test, workflow, release, or compliance inventory. P02-F09
remains blocked until a separately authorized P02-F15 implements this contract.

This contract is governed by
[ADR-0025](../adr/ADR-0025-ConfidenceInputExtractionCardinalityUsesExistingActions.md).
Actual frozen Python types govern their own shape. In particular, `missing_action` and
`conflict_action` belong to `ConfidencePolicy`; `ConfidenceInput` contains `input_key`,
`source_selector`, and `required`.

## 2. Reconciled contradiction

One successful `CandidateRuleResult` contains a canonical tuple of zero, one, or many
`SemanticCandidate` values. One `ConfidenceInputValue` contains exactly one candidate. No
confidence-input selection or ranking rule exists. P02 therefore requires a cardinality boundary
between extraction and construction of the model input.

The boundary is mechanical, not semantic selection:

| Extraction outcome | Cardinality classification | Result |
| --- | --- | --- |
| `SUCCESS`, zero candidates | missing | Apply the policy `missing_action` |
| `SUCCESS`, exactly one candidate | included | Construct one value with that exact candidate |
| `SUCCESS`, two or more candidates | conflict | Apply the policy `conflict_action` |
| `NO_MATCH` | missing | Apply the same `missing_action` as success-empty |
| `REJECTED` | terminal semantic rejection | P01 `REJECTED` |
| `INVALID_INPUT` | terminal invalid execution | P01 `INVALID_INPUT` |
| `FAILED` | terminal execution failure | P01 `FAILED` |

`SUCCESS` with an empty candidate tuple is a valid source-extraction result under the frozen
result contract. It is not malformed output. For confidence cardinality it is observably
equivalent to `NO_MATCH`: both mean that no singular input can be formed and activate
`missing_action`. Their rule states remain distinct in invocation evidence; the adapter does not
rewrite one state as the other.

`SUCCESS` with multiple valid candidates is also a valid extraction result. It is not structural
`INVALID_INPUT`; it is a confidence-input conflict because the frozen model input is singular.

## 3. Existing action semantics

The policy-level action is applied separately to the input whose cardinality activated it. The
action vocabulary remains exactly `NonAcceptanceAction`.

| Action | Optional input | Required input |
| --- | --- | --- |
| `REJECT` | Terminal P01 `REJECTED` | Terminal P01 `REJECTED` |
| `NO_FACT` | Omit that input | Terminal P01 `REJECTED` |
| `REQUIRE_SINGLE` | Terminal P01 `REJECTED` | Terminal P01 `REJECTED` |
| `REQUIRE_EXPLICIT_SELECTION_RULE` | P01 `INVALID_INPUT` | P01 `INVALID_INPUT` |

`NO_FACT` never changes a required input into an optional input. `REQUIRE_SINGLE` asserts the
already-frozen singular boundary; failure to meet it is rejection, not a winner-selection
instruction. `REQUIRE_EXPLICIT_SELECTION_RULE` cannot be satisfied by the current confidence
profile because it has no selection-rule field. When that action is activated, the profile cannot
authorize execution and fails as `INVALID_INPUT`. It does not cause registry lookup or implicit
rule discovery.

For a missing outcome, the table is applied using `ConfidencePolicy.missing_action`. For a
multiple-candidate outcome, it is applied using `ConfidencePolicy.conflict_action`. Exactly one
candidate bypasses both actions.

## 4. Required, optional, and model cardinality

`ConfidenceInput.required` is the sole per-input inclusion classification. A required input is
never omitted. An optional input may be omitted only when the activated policy action is
`NO_FACT`. Other actions retain their terminal meaning.

After all non-terminal optional omissions, the confidence rule receives only included
`ConfidenceInputValue` objects. Every included object contains exactly one candidate. Included
objects preserve the existing canonical `ConfidencePolicy.inputs` order by `input_key`; candidate,
frame, binding, and invocation order never reorder model inputs.

The runtime minimum is:

| Model kind | Declared invariant | Runtime invariant |
| --- | --- | --- |
| `DIRECT` | Exactly one declared input | Exactly one included input |
| `WEIGHTED` | One or more declared inputs | One or more included inputs |
| `RULE` | One or more declared inputs | One or more included inputs |
| `CALIBRATED` | One or more declared inputs | One or more inputs reach the base model; calibration receives its exact result |

An optional omission is permitted for every variant only if these runtime invariants still hold.
If omissions leave no included input, model and calibration rules are not invoked and the adapter
returns P01 `REJECTED` with a missing-fact diagnostic. For `DIRECT`, omission of its sole input has
the same result. P02 supplies no formula, weight adjustment, default, or synthetic replacement;
P04 must make any concrete optional-input profile semantically coherent.

## 5. Candidate preservation and prohibited selection

When extraction returns exactly one candidate, P02 places that exact object in
`ConfidenceInputValue`. Its candidate identity, source-binding lineage, provenance, timeframe,
rule identity, value kind, and value remain unchanged. P02 creates no derived candidate.

P02 must not select the first, last, smallest identifier, canonical minimum, preferred frame, or
preferred source. Sorting may canonicalize a set-like extraction result but may never determine a
winner. No confidence selection or ranking rule is added, and `ConfidenceInputValue` remains
singular. Collection-valued confidence inputs would change the frozen request, serialization, and
concrete-rule boundary and are rejected for this milestone.

## 6. Diagnostics and fail-fast behavior

P02-F15 must use the existing P01 diagnostic types and codes. No enum member is added.

| Condition | Code | Severity | Exact message |
| --- | --- | --- | --- |
| Missing input causing rejection | `MISSING_FACT` | `ERROR` | `CONFIDENCE_INPUT_MISSING` |
| Optional missing input omitted | `MISSING_FACT` | `WARNING` | `CONFIDENCE_INPUT_OMITTED` |
| Multiple candidates causing rejection | `ADAPTER_REJECTED` | `ERROR` | `CONFIDENCE_INPUT_CONFLICT` |
| Optional conflicting input omitted | `ADAPTER_REJECTED` | `WARNING` | `CONFIDENCE_INPUT_CONFLICT_OMITTED` |
| No runtime inputs remain | `MISSING_FACT` | `ERROR` | `CONFIDENCE_INPUT_SET_EMPTY` |
| Activated explicit-selection action | `INVALID_REQUEST` | `ERROR` | `CONFIDENCE_SELECTION_RULE_UNAVAILABLE` |

The diagnostic `subject_ref` is the exact `input_key`, except the empty-set diagnostic uses the
confidence policy identity reference. `source_refs` are the canonical provenance references known
at that boundary. Exact duplicate diagnostics deduplicate through existing P01 canonicalization.
Terminal outcomes stop before the confidence model and all downstream evidence work. Warnings for
earlier optional omissions remain in canonical diagnostic order on a later accepted or terminal
result. No raw candidate, payload, exception, path, or runtime data enters a message.

## 7. Existing boundaries remain frozen

Cardinality is evaluated only after F10/F11 `resolve_source_bindings()` and exact F12/F13
confidence source extraction. Frame scope and exact rule closure do not change. No rule identity,
family, invocation kind, result kind, request, result, or profile field is added.

Existing dataclass serialization already includes `required`, `missing_action`, and
`conflict_action`; no schema change is required. Those nested values already participate in the
semantic-profile fingerprint, so no fingerprint mechanism changes. P01 protocol/result contracts
and A07 confidence/bundle contracts remain unchanged. P03 does not decide cardinality, P04 owns
only concrete profile choices and semantic formulas, and P05 is unaffected.

## 8. P02-F15 implementation boundary

P02-F15 is limited to the private mechanical cardinality reduction used later by the canonical
adapter, exact existing-action translation, deterministic diagnostics, focused tests, and minimal
fixtures. It must not implement `CanonicalFactAdapter`, change closure, add selection/ranking,
change public value shapes, or implement P03, P04, or P05.

P02-F15 tests must prove:

1. success-one constructs one exact input value;
2. success-empty and `NO_MATCH` activate the same missing action while preserving their states;
3. success-two and success-many activate conflict action without choosing a candidate;
4. required inputs never omit and optional inputs omit only under `NO_FACT`;
5. all four actions have the exact consequences above;
6. included identity and canonical input order are preserved;
7. every model kind enforces its runtime minimum;
8. `REJECTED`, `INVALID_INPUT`, and `FAILED` remain terminal;
9. diagnostics and fail-fast invocation counts are exact;
10. closure, frame scope, serialization, fingerprinting, and predecessor behavior are unchanged.

P02-F09 may resume only after P02-F15 is separately authorized, implemented, validated, published,
and closed/frozen with no new contradiction.
