# P02-F12 Confidence Source Extraction Closure Contract

## 1. Status and authority

P02-F12 is a governance-only reconciliation. It freezes the missing confidence-extraction edge in
the exact executable profile-closure graph. ADR-0024 records the decision. No Python, tests,
compliance inventory, adapter behavior, P03, P04, or P05 implementation is authorized here.

P02-F09 remains blocked until P02-F13 implements this contract and closes.

## 2. Confirmed contradiction

`ConfidenceInput` contains a `source_selector: SourceSelector`. The selector contains an exact
`selector_rule: RuleIdentity`. Source resolution alone does not create a confidence input value;
the selected `AnalyticalSourceBinding` must be passed to the selector rule through the existing
source-extraction request/result contract.

The current `validate_profile_closure()` traversal collects the confidence model identity and the
optional calibration identity, but does not collect confidence-input selector rules. Consequently,
a required extraction rule is rejected as an unused extra when included and is unavailable for
legal invocation when omitted. Exact closure and executable confidence cannot both succeed.

## 3. Required closure graph

For every canonical confidence input, the closure graph contains:

```text
ConfidenceInput
  -> SourceSelector
  -> selector_rule
  -> SOURCE_EXTRACTION
  -> SOURCE_EXTRACTION invocation
  -> CANDIDATES result
```

The graph separately contains the policy's confidence model rule and, only for `CALIBRATED`, its
calibration rule. Extraction is not confidence computation and must not be collapsed into the
model.

| Concern | Family | Invocation kind | Result kind |
| --- | --- | --- | --- |
| Confidence input extraction | `SOURCE_EXTRACTION` | `SOURCE_EXTRACTION` | `CANDIDATES` |
| Confidence model | `CONFIDENCE` | `CONFIDENCE` | `CONFIDENCE` |
| Calibration, when present | `CONFIDENCE` | `CONFIDENCE` | `CONFIDENCE` |

No new execution vocabulary is required.

## 4. Canonical confidence-input traversal

`ConfidencePolicy` already canonicalizes its non-empty input tuple by `input_key`. Closure must
traverse that stored tuple in order. For each input it must:

1. inspect the exact `SourceSelector`;
2. collect its exact `selector_rule`;
3. require `SemanticRuleFamily.SOURCE_EXTRACTION`;
4. rely on the existing family compatibility table for invocation and result kinds;
5. proceed to the next canonical input.

After input traversal, closure collects the model identity and then the optional calibration
identity. This traversal order makes requirement discovery deterministic. Final manifest ordering
and runtime invocation ordering remain separate concerns.

## 5. Identity reuse and conflicts

Several confidence inputs may reference the same exact extraction identity. One resolved
declaration satisfies all identical requirements; duplicate manifest declarations remain invalid.

The same extraction identity may also be shared with direction, entry, stop, target, or evidence
selectors. Cross-stage sharing is valid when every reference requires the identical family and its
fixed compatibility metadata. Sharing is not prohibited by policy location.

If one exact identity is required under different families, the existing closure conflict check
must fail closed. P02-F13 must preserve this behavior rather than choosing one interpretation.

## 6. Confidence variants and cardinality

The frozen `ConfidencePolicy` requires a non-empty `ConfidenceInput` tuple for every model kind.
Closure behavior is therefore:

- `DIRECT`: all input selector rules plus the model rule;
- `WEIGHTED`: all input selector rules plus the model rule;
- `RULE`: all input selector rules plus the model rule;
- `CALIBRATED`: all input selector rules, the base model rule, and the calibration rule.

The existing `DIRECT` constraint of exactly one input remains unchanged. No current valid variant
has a zero-input case. P02-F12 does not alter input cardinality or define confidence formulas.

## 7. Exact resolved-rule-set behavior

A valid resolved rule set must contain every distinct confidence-input extraction identity. A
missing referenced identity is invalid. The exact referenced identity is valid. An unrelated extra
identity is invalid. Family, invocation-kind, result-kind, implementation identity, declaration,
and executable implementation matching remain governed by the existing exact compatibility path.

This reconciliation changes only which profile-owned identities are discovered. It does not weaken
closed-world validation or create a second confidence-specific validator.

## 8. Frame scope, fingerprints, and serialization

P02-F10 and P02-F11 remain authoritative. Each confidence selector independently declares exact
`frame_roles`, but closure membership depends on `selector_rule`, not on its frame roles. Changing
only `PRIMARY` to `HIGHER` changes the semantic-profile fingerprint while leaving the required rule
identity set unchanged.

Confidence inputs and nested selectors already participate in tagged serialization,
reconstruction, equality, hashing, and semantic-profile fingerprinting. The extraction identity is
already transitively fingerprinted. P02-F13 must not add a parallel fingerprint or serialization
path.

## 9. Frozen boundaries

P01 protocol signatures, states, results, and diagnostics are unchanged. A07 confidence and fact
contracts are unchanged. Ranked target selection from P02-F08 is unrelated and unchanged.

P03 cannot discover or populate missing rules. P04 later chooses concrete confidence selectors,
identities, weights, formulas, and strategy semantics. P05 retains MTF aggregation semantics. No
concrete indicator, Elliott, Fibonacci, or confidence logic is introduced.

## 10. P02-F13 implementation scope

P02-F13 is limited to:

- extending the existing `validate_profile_closure()` traversal;
- adding focused closure tests;
- making minimal fixture adjustments if required;
- applying a mechanical compliance update only if inventory unexpectedly changes.

It must not implement `CanonicalFactAdapter`, create execution vocabulary, change P01 or A07, or
enter P03, P04, or P05.

## 11. Required P02-F13 tests

P02-F13 must prove:

1. confidence extraction identities enter expected closure;
2. a missing confidence extraction identity is rejected;
3. the exact extraction identity is accepted;
4. an unrelated extra extraction identity is rejected;
5. repeated confidence references deduplicate one requirement;
6. incompatible reuse of one identity fails closed;
7. identical sharing with entry is accepted;
8. identical sharing with evidence is accepted;
9. family mismatch is rejected;
10. invocation mismatch is rejected;
11. result-kind mismatch is rejected;
12. `DIRECT` closure is exact;
13. `WEIGHTED` closure is exact;
14. `RULE` closure is exact;
15. `CALIBRATED` closure is exact;
16. model identity requirements remain intact;
17. calibration identity requirements remain intact;
18. frame-role-only changes do not change closure membership;
19. frame-role changes still change the profile fingerprint;
20. no new identity or rule-family type appears;
21. predecessor closure behavior remains unchanged.

## 12. Gate for P02-F09 resumption

P02-F09 may resume only after P02-F13 implements this single authoritative closure edge, passes all
focused and predecessor validation, is published, and is CLOSED / FROZEN. P02 remains incomplete,
and P03 remains unauthorized.

Remaining implementation-significant ambiguities: **NONE**.
