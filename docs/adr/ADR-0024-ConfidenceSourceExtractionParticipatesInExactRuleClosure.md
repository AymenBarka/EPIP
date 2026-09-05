# ADR-0024: Confidence Source Extraction Participates in Exact Rule Closure

## Status

Accepted

## Context

Every `ConfidenceInput` owns a `SourceSelector`, and every selector names an executable
`selector_rule`. A future `CanonicalFactAdapter` must resolve the selector's declared frame scope
and invoke that rule before it can construct a `ConfidenceInputValue`.

The current exact-closure traversal includes the confidence model and optional calibration rules,
but omits confidence-input extraction rules. Including such a rule therefore looks like an unused
extra, while excluding it leaves no legal implementation to invoke. These outcomes contradict the
closed-world rule-set model.

## Decision

Each `ConfidenceInput.source_selector.selector_rule` participates in exact profile closure as the
existing combination:

- family: `SemanticRuleFamily.SOURCE_EXTRACTION`;
- invocation: `SemanticInvocationKind.SOURCE_EXTRACTION`;
- result: `SemanticResultKind.CANDIDATES`.

Inputs are traversed in the canonical `ConfidencePolicy.inputs` order by `input_key`. References
are normalized by exact `RuleIdentity`. Repeated references with identical compatibility metadata
create one closure requirement, including references shared with direction, geometry, or evidence
selectors. Reuse of one identity under incompatible families fails closed.

The confidence model remains a separate `CONFIDENCE` rule. A `CALIBRATED` policy also retains its
separate calibration rule. Extraction is not absorbed into either rule, and rules never discover
analytical sources.

This requirement applies uniformly to `DIRECT`, `WEIGHTED`, `RULE`, and `CALIBRATED`: every input
present in the policy contributes its extraction identity. The existing contract requires a
non-empty `ConfidenceInput` tuple, so every valid current policy contributes at least one such
identity.

## Consequences

The single authoritative `ResolvedSemanticRuleSet.validate_profile_closure()` traversal must be
extended by P02-F13. Missing confidence extraction rules and unrelated extras remain invalid.
Declaration compatibility validation remains exact; no new rule family, invocation kind, result
kind, request, result, or identity type is introduced.

Closure determines required membership, not runtime invocation order. P02-F09 will later execute
confidence inputs in canonical policy order after earlier adapter stages.

Selectors already participate transitively in semantic-profile fingerprints and tagged
serialization. Frame-role changes therefore continue to change the profile fingerprint without
changing the closure identity set unless the selector rule itself changes. P02-F10 and P02-F11 are
unchanged.

P01 and A07 remain frozen. P03 supplies no dynamic identities, P04 later chooses concrete
selectors and rules, and P05 retains MTF aggregation semantics. P02-F09 remains blocked until the
narrow P02-F13 implementation is closed and separately reviewed.
