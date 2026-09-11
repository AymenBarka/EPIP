# ADR-0029: Caller-Bound Primary Timeframe

- **Status:** Accepted
- **Milestone:** P02-R02 / P04-F00-R02
- **Decision scope:** Additive P02 timeframe binding

## Context

`MtfDirectionPolicyRef.required_timeframes` admits only concrete strings, and the canonical adapter
selects frames by exact string membership. A timeframe-agnostic profile therefore cannot request
the concrete PRIMARY timeframe supplied by its caller without hard-coding a market timeframe.
`EvaluationContext.primary_timeframe` and `MultiTimeframeInputSet.primary_timeframe` already carry
and validate that caller authority.

## Decision

Add `bind_primary_timeframe: bool = False` as the final field of
`MtfDirectionPolicyRef`. The two legal, mutually exclusive modes are:

- `False`: `required_timeframes` remains non-empty and retains its exact existing behavior.
- `True`: `required_roles` is exactly `(TimeframeRole.PRIMARY,)` and
  `required_timeframes` is exactly empty. At evaluation, P02 derives the sole effective timeframe
  from `EvaluationContext.primary_timeframe`, requires equality with
  `MultiTimeframeInputSet.primary_timeframe`, and selects exactly the frame with that timeframe and
  PRIMARY role.

The flag must be an exact `bool`. No wildcard, sentinel, default timeframe, environment lookup, or
P05 aggregation semantics exists. Zero or multiple PRIMARY frames, a mismatching primary
timeframe, an absent selected frame, duplicate concrete timeframes, and malformed frame metadata
remain fail-closed conditions at their existing owning boundary.

## Compatibility and implementation

Concrete profiles are unchanged because the new field defaults to `False`. Existing tagged JSON
without the final field reconstructs through the dataclass default; new payloads encode the field
canonically. P02-R02-I00 changes only `epip/strategy_mapping/direction_policy.py` and
`epip/strategy_mapping/adapter.py`, with tests in
`tests/strategy_mapping/test_caller_bound_primary_timeframe.py` and additive serialization tests in
`tests/strategy_mapping/test_source_and_serialization.py`.

This changes an existing frozen dataclass rather than adding a public type. Compliance inventory is
forecast to remain 606 and its digest unchanged because the scanner records class identity and
integrity mode, not fields. Implementation must verify both values.
