# P02-R02 Caller-Bound Primary Timeframe Reconciliation

## Decision

P02-R02 is **GOVERNANCE RECONCILED**. P02-R02-I00 is **READY FOR AUTHORIZATION**; no implementation
is performed here. ADR-0029 freezes the smallest additive contract change.

The caller-authority chain is:

```text
StrategyRuntimeRequest evaluation context
-> EvaluationContext.primary_timeframe
-> MultiTimeframeInputSet.primary_timeframe equality
-> unique closed PRIMARY TimeframeInput
-> P02 exact frame selection
-> semantic rule request
```

`MtfDirectionPolicyRef.bind_primary_timeframe=True` means caller binding. In this mode
`required_roles == (PRIMARY,)` and `required_timeframes == ()`; P02 computes the effective tuple
`(evaluation.primary_timeframe,)`. Concrete mode remains `False` with a non-empty exact timeframe
tuple.

No PRIMARY, multiple PRIMARY values, role/timeframe mismatch, absence of the caller timeframe,
duplicate timeframe frames, and malformed metadata are rejected before rule execution. Existing
structural validation and adapter `INVALID_INPUT` translation remain authoritative. No new state or
diagnostic is introduced.

## P02-R02-I00 boundary

Future production files are exactly `epip/strategy_mapping/direction_policy.py` and
`epip/strategy_mapping/adapter.py`. Future tests are exactly
`tests/strategy_mapping/test_caller_bound_primary_timeframe.py` plus additive regression in
`tests/strategy_mapping/test_source_and_serialization.py`.

The slice must preserve old constructors, concrete-timeframe behavior and old serialized payloads;
prove exact caller binding and every fail-closed case; keep P01/P03/A07 unchanged; and pass full
regression, coverage, compliance, static and exact-SHA remote gates. P05 voting, hierarchy,
confirmation and cross-frame interpretation remain excluded.
