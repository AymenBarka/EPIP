# mypy: disable-error-code="arg-type,attr-defined,no-untyped-call,var-annotated"
"""P02-R02-I00 caller-bound PRIMARY timeframe proofs."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import (
    DirectionFactName,
    MtfDirectionPolicyRef,
    NonAcceptanceAction,
    StrategySemanticMappingProfile,
)
from epip.strategy_mapping.adapter import CanonicalFactAdapter
from epip.strategy_mapping.invocation_binding import AdapterInvocationBinding
from epip.strategy_runtime._base import digest
from epip.strategy_runtime.context import EvaluationContext
from epip.strategy_runtime.mtf import TimeframeRole
from epip.strategy_runtime.protocols import FactAdapterState
from tests.strategy_mapping.test_canonical_fact_adapter import _fixture


def _policy(
    *,
    roles: tuple[TimeframeRole, ...] = (TimeframeRole.PRIMARY,),
    timeframes: tuple[str, ...] = ("H1",),
    bind: bool = False,
) -> MtfDirectionPolicyRef:
    base = _fixture()[0]._profile.mtf_direction_policy
    return MtfDirectionPolicyRef(
        roles,
        timeframes,
        DirectionFactName.PRIMARY,
        base.rule_identity,
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
        bind,
    )


def _caller_fixture() -> tuple[object, ...]:
    adapter, context, inputs, parent, policy, calls = _fixture()
    current = adapter._profile
    semantic = StrategySemanticMappingProfile.create(
        semantic_profile_id=current.identity.semantic_profile_id,
        semantic_profile_version=current.identity.semantic_profile_version,
        parent_profile=parent,
        direction_policies=current.direction_policies,
        mtf_direction_policy=replace(
            current.mtf_direction_policy,
            required_roles=(TimeframeRole.PRIMARY,),
            required_timeframes=(),
            bind_primary_timeframe=True,
        ),
        entry_policy=current.entry_policy,
        stop_policy=current.stop_policy,
        target_policy=current.target_policy,
        confidence_policy=current.confidence_policy,
        evidence_taxonomy=current.evidence_taxonomy,
        global_conflict_action=current.global_conflict_action,
    )
    binding = AdapterInvocationBinding.create(
        adapter_identity=adapter.identity,
        semantic_profile_identity=semantic.identity,
        resolved_rule_set_id=adapter._rules.manifest.rule_set_id,
        typed_bundle_id=adapter._typed_bundle.bundle_id,
        analytical_input_digest=digest(inputs),
        provenance_manifest_id=inputs.provenance.manifest_id,
        instrument_binding_id=adapter._typed_bundle.instrument.binding_id,
    )
    return (
        CanonicalFactAdapter(
            adapter.identity, semantic, adapter._rules, adapter._typed_bundle, binding
        ),
        context,
        inputs,
        parent,
        policy,
        calls,
    )


def test_default_false_preserves_historical_positional_and_keyword_construction() -> None:
    positional = _policy()
    keyword = replace(positional, bind_primary_timeframe=False)
    assert positional.bind_primary_timeframe is False
    assert positional == keyword
    assert positional.required_timeframes == ("H1",)


def test_caller_primary_mode_is_exact_and_immutable() -> None:
    caller = _policy(timeframes=(), bind=True)
    assert caller.required_roles == (TimeframeRole.PRIMARY,)
    assert caller.required_timeframes == ()
    assert caller.bind_primary_timeframe is True
    assert caller != _policy()
    assert hash(caller) != hash(_policy())
    with pytest.raises(FrozenInstanceError):
        caller.bind_primary_timeframe = False  # type: ignore[misc]


@pytest.mark.parametrize(
    ("roles", "timeframes", "bind"),
    (
        ((TimeframeRole.PRIMARY,), ("H1",), True),
        ((TimeframeRole.HIGHER,), (), True),
        ((TimeframeRole.PRIMARY, TimeframeRole.HIGHER), (), True),
        ((TimeframeRole.PRIMARY,), (), False),
        ((TimeframeRole.PRIMARY,), ("*",), True),
        ((TimeframeRole.PRIMARY,), ("PRIMARY",), True),
    ),
)
def test_ambiguous_or_sentinel_modes_are_rejected(
    roles: tuple[TimeframeRole, ...], timeframes: tuple[str, ...], bind: bool
) -> None:
    with pytest.raises(DataIntegrityError):
        _policy(roles=roles, timeframes=timeframes, bind=bind)


def test_bind_flag_requires_exact_bool() -> None:
    with pytest.raises(DataIntegrityError):
        _policy(timeframes=(), bind=1)


def test_caller_primary_selects_exact_context_timeframe_deterministically() -> None:
    adapter, context, inputs, profile, policy, calls = _caller_fixture()
    first = adapter.adapt(context, inputs, profile, policy)
    first_calls = tuple(calls)
    calls.clear()
    second = adapter.adapt(context, inputs, profile, policy)
    assert first == second
    assert first.state is FactAdapterState.ACCEPTED
    assert tuple(calls) == first_calls
    mtf_request = next(request for name, request in calls if name == "mtf")
    assert mtf_request.required_timeframes == (context.primary_timeframe,)
    assert tuple(item.timeframe for item in mtf_request.directions) == ("H1",)


def test_binding_mismatch_fails_before_any_semantic_rule_invocation() -> None:
    adapter, context, inputs, profile, policy, calls = _caller_fixture()
    mismatched = EvaluationContext.create(
        instrument_id=context.instrument_id,
        symbol=context.symbol,
        primary_timeframe="h1",
        evaluation_timestamp=context.evaluation_timestamp,
        event_timestamp=context.event_timestamp,
        receipt_timestamp=context.receipt_timestamp,
        runtime_mode=context.runtime_mode,
        profile_identity=context.profile_identity,
        source_set_id=context.source_set_id,
        run_id=context.run_id,
        correlation_id=context.correlation_id,
    )
    result = adapter.adapt(mismatched, inputs, profile, policy)
    assert result.state is FactAdapterState.INVALID_INPUT
    assert result.bundle is None
    assert calls == []


def test_caller_primary_reads_are_thread_safe() -> None:
    adapter, context, inputs, profile, policy, _ = _caller_fixture()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = tuple(
            pool.map(lambda _: adapter.adapt(context, inputs, profile, policy), range(8))
        )
    assert all(result == results[0] for result in results)
