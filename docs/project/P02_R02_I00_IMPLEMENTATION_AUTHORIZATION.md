# P02-R02-I00 Implementation Authorization

## Decision

P02-R02-I00 is **AUTHORIZED / READY FOR IMPLEMENTATION**. This record authorizes only the additive
caller-bound PRIMARY capability governed by ADR-0029 and P02-R02. It contains no implementation.

## Contract delta and compatibility

Add `bind_primary_timeframe: bool = False` as the final dataclass field of
`MtfDirectionPolicyRef`, after `conflict_action`. Final placement preserves every existing
six-argument positional construction and all keyword construction. The type remains frozen,
slotted and hashable. The field must be an exact `bool`.

Repository construction inventory contains three sites, all positional and all passing the
existing six fields: `tests/strategy_mapping/conftest.py`,
`tests/strategy_mapping/test_policy_contracts.py`, and
`tests/strategy_mapping/test_canonical_fact_adapter.py`. There is no production constructor.

The legal modes are mutually exclusive:

- `False`: existing validation remains unchanged; `required_timeframes` is a non-empty unique text
  tuple and concrete exact matching is unchanged.
- `True`: `required_timeframes == ()` and `required_roles == (TimeframeRole.PRIMARY,)` are required.
  Any non-empty timeframe tuple, another role, or mixed roles raises `DataIntegrityError`.

Role authority comes only from `TimeframeInput.role`. Concrete-timeframe authority comes only from
the already validated `EvaluationContext.primary_timeframe`, using existing case-sensitive exact
text equality without normalization or coercion.

## Serialization and identity

The existing tagged dataclass serializer emits every declared field. Consequently new False-mode
serialization includes `"bind_primary_timeframe": false`; True mode includes `true`. Both round
trip canonically. A historical payload without the field reconstructs with the dataclass default
`False`; no serializer change is required.

This is an explicitly governed additive schema evolution, not byte-preserving serialization.
Newly constructed False-mode `MtfDirectionPolicyRef` values compare and hash differently only when
the new field differs. Because `StrategySemanticMappingProfile.create` fingerprints the complete
record graph, profiles reconstructed under the evolved contract receive a canonical fingerprint
that includes `false` or `true`. No deployed concrete production profile exists, and no golden byte
snapshot is present. Existing exact rule, parent-profile, and mapping references remain unchanged.

The compliance scanner records only frozen dataclass qualified name and validation mode. The
inventory remains 606 and its digest remains
`2b2aa94b9f3a8fb7ebe305be5dc3697f645197df82f3d12bee598d8f08c0930b` because neither changes.

## Adapter behavior

Before any downstream MTF semantic-rule invocation, the adapter computes:

```text
effective_timeframes =
    (evaluation.primary_timeframe,)
    if policy.bind_primary_timeframe
    else policy.required_timeframes
```

The existing frame filter then requires both membership in `policy.required_roles` and exact
membership in `effective_timeframes`. Caller mode must yield exactly one matching PRIMARY frame;
otherwise the adapter uses the existing structural-invalid path and invokes no downstream rule.

`MultiTimeframeInputSet` already rejects zero or multiple PRIMARY frames, PRIMARY/timeframe
mismatch, duplicate concrete timeframes and malformed frame metadata. Typed bundle/context
validation rejects an absent or mismatched caller timeframe. I00 must retain those checks and add a
defensive exact-one match before MTF invocation. It adds no state, diagnostic, fallback, wildcard,
clock, I/O, cache or P05 aggregation behavior.

## Authorized implementation boundary

Production files are exactly:

- `epip/strategy_mapping/direction_policy.py`
- `epip/strategy_mapping/adapter.py`

Test files are exactly:

- `tests/strategy_mapping/test_caller_bound_primary_timeframe.py`
- additive changes to `tests/strategy_mapping/test_source_and_serialization.py`

Tests must prove default False construction; both validation modes; rejection of mixed mode;
historical missing-field decode; explicit False/True encoding and round trips; exact caller-primary
selection; case-sensitive equality; missing, multiple, mismatched and duplicate failures; zero
downstream calls on failure; unchanged one/many/unmatched concrete behavior; deterministic repeat;
immutability, concurrent reads, wildcard/sentinel rejection and P05 isolation.

Closure requires focused tests, full P02 and P03 suites, A07 and full repository regressions,
aggregate coverage at least 95%, changed-line coverage without meaningful gaps, EventBus stress,
Black, Ruff, strict MyPy, compliance, documentation gates, zero predecessor removals, one atomic
commit and exact-SHA Quality, CodeQL and Documentation success.

P03 and A07 require no change: P03 already passes the immutable context and analytical bundle into
the configured adapter, while A07 consumes only mapped facts. P04-F00 remains blocked until I00 is
implemented, validated, published and frozen. P05 remains excluded.
