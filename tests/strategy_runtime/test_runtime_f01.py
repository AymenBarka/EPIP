from __future__ import annotations

import inspect
from dataclasses import replace

import pytest

import epip.strategy_runtime as public
from epip.a07.foundation import StrategyDirection, StrategyEvidenceIdentity, StrategyIdentity
from epip.a07.policy import StrategyPolicy
from epip.strategy_runtime import (
    AnalyticalInputBundle,
    EvaluationContext,
    FactAdapterIdentity,
    FactAdapterResult,
    FactAdapterState,
    MultiTimeframeInputSet,
    ProvenanceManifest,
    RuntimeDiagnosticCode,
    RuntimeDiagnosticStage,
    StrategyFactBundle,
    StrategyProfile,
    StrategyProfileIdentity,
    StrategyRuntime,
    StrategyRuntimeProtocol,
    StrategyRuntimeResult,
    StrategyRuntimeState,
)
from tests.strategy_runtime.test_runtime import (
    Adapter,
    Registry,
    accepted_adapter,
    make_bundle,
    make_request,
)


@pytest.fixture
def policy(profile: StrategyProfile) -> StrategyPolicy:
    return StrategyPolicy(
        "policy",
        "1",
        profile.strategy_identity,
        (StrategyDirection.BUY, StrategyDirection.SELL),
        2.0,
        0.5,
        ("context",),
        ("elliott",),
        90,
        6,
        (),
    )


@pytest.fixture
def inputs(
    mtf: MultiTimeframeInputSet,
    provenance: ProvenanceManifest,
) -> AnalyticalInputBundle:
    return AnalyticalInputBundle(None, None, None, None, None, None, None, None, mtf, provenance)


def _assert_invalid(
    result: StrategyRuntimeResult,
    stage: RuntimeDiagnosticStage,
    *,
    bundle: StrategyFactBundle | None = None,
) -> None:
    assert result.state is StrategyRuntimeState.INVALID_INPUT
    assert result.signal_envelope is None
    assert result.fact_bundle_id == (None if bundle is None else bundle.bundle_id)
    assert result.diagnostics.final_state is StrategyRuntimeState.INVALID_INPUT
    assert result.diagnostics.last_completed_stage is stage
    assert len(result.diagnostics.entries) == 1
    diagnostic = result.diagnostics.entries[0]
    assert diagnostic.code is RuntimeDiagnosticCode.INVALID_REQUEST
    assert diagnostic.stage is stage
    assert diagnostic.subject_ref == result.request_id
    assert diagnostic.source_refs == ()


def _inputs(
    inputs: AnalyticalInputBundle,
    *,
    mtf: MultiTimeframeInputSet | None = None,
    provenance: ProvenanceManifest | None = None,
) -> AnalyticalInputBundle:
    return replace(
        inputs,
        mtf_context=inputs.mtf_context if mtf is None else mtf,
        provenance=inputs.provenance if provenance is None else provenance,
    )


def _manifest(
    manifest: ProvenanceManifest,
    *,
    evaluation_id: str | None = None,
    profile_identity: StrategyProfileIdentity | None = None,
    adapter_identity: FactAdapterIdentity | None = None,
    source_digest: str | None = None,
) -> ProvenanceManifest:
    profile = profile_identity or manifest.profile_identity
    adapter = adapter_identity or manifest.adapter_identity
    sources = manifest.sources
    if source_digest is not None:
        sources = (replace(sources[0], source_digest=source_digest), *sources[1:])
    facts = tuple(
        replace(
            item,
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            adapter_id=adapter.adapter_id,
            adapter_version=adapter.adapter_version,
        )
        for item in manifest.facts
    )
    return ProvenanceManifest.create(
        sources,
        facts,
        profile,
        adapter,
        evaluation_id or manifest.evaluation_id,
    )


def _profile_like(profile: StrategyProfile, profile_id: str) -> StrategyProfile:
    return StrategyProfile.create(
        profile_id=profile_id,
        profile_version=profile.identity.profile_version,
        strategy_identity=profile.strategy_identity,
        compatible_runtime_contract_versions=profile.compatible_runtime_contract_versions,
        compatible_adapter_contract_versions=profile.compatible_adapter_contract_versions,
        required_source_domains=profile.required_source_domains,
        optional_source_domains=profile.optional_source_domains,
        required_evidence_keys=profile.required_evidence_keys,
        optional_evidence_keys=profile.optional_evidence_keys,
        enabled_direction_facts=profile.enabled_direction_facts,
        enabled_geometry_sources=profile.enabled_geometry_sources,
        confidence_model_reference=profile.confidence_model_reference,
        evidence_taxonomy_reference=profile.evidence_taxonomy_reference,
        mtf_requirement=profile.mtf_requirement,
        mapping_rules_reference=profile.mapping_rules_reference,
    )


def test_public_protocol_exports_signature_and_result_behavior(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    adapter = Adapter(
        adapter_identity,
        FactAdapterResult(FactAdapterState.REJECTED, None, ()),
    )
    runtime: StrategyRuntimeProtocol = StrategyRuntime(Registry(profile), adapter)
    request = make_request(context, inputs, policy, profile, adapter_identity)

    result = runtime.evaluate(request)

    assert type(result) is StrategyRuntimeResult
    assert result.state is StrategyRuntimeState.REJECTED
    assert inspect.signature(StrategyRuntime.evaluate).parameters.keys() == {"self", "request"}
    assert inspect.signature(StrategyRuntimeProtocol.evaluate).parameters.keys() == {
        "self",
        "request",
    }
    assert public.StrategyRuntime is StrategyRuntime
    assert public.StrategyRuntimeProtocol is StrategyRuntimeProtocol
    assert {"StrategyRuntime", "StrategyRuntimeProtocol"} <= set(public.__all__)
    assert not hasattr(runtime, "__dict__")


@pytest.mark.parametrize(
    ("dependency", "stage", "registry_calls"),
    (
        ("adapter", RuntimeDiagnosticStage.ADAPTER, 0),
        ("profile", RuntimeDiagnosticStage.COHERENCE, 1),
    ),
)
def test_dependency_failures_expose_exact_public_diagnostics(
    dependency: str,
    stage: RuntimeDiagnosticStage,
    registry_calls: int,
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    registry = Registry(profile, fail=dependency == "profile")
    actual_identity = adapter_identity
    if dependency == "adapter":
        actual_identity = FactAdapterIdentity("other", "1", "p01-v1", "d" * 64)
    adapter = Adapter(actual_identity, FactAdapterResult(FactAdapterState.FAILED, None, ()))
    request = make_request(context, inputs, policy, profile, adapter_identity)

    result = StrategyRuntime(registry, adapter).evaluate(request)

    _assert_invalid(result, stage)
    assert registry.calls == registry_calls
    assert adapter.calls == 0


@pytest.mark.parametrize("axis", ("primary", "alignment"))
def test_temporal_coherence_axes_fail_before_adapter(
    axis: str,
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    frame = inputs.mtf_context.frames[0]
    if axis == "primary":
        changed_frame = replace(frame, timeframe="M5")
        mtf = MultiTimeframeInputSet.create(
            "M5",
            inputs.mtf_context.alignment_timestamp,
            (changed_frame,),
        )
    else:
        mtf = MultiTimeframeInputSet.create(
            inputs.mtf_context.primary_timeframe,
            "2026-08-24T12:31:15.123456Z",
            (frame,),
        )
    request = make_request(
        context,
        _inputs(inputs, mtf=mtf),
        policy,
        profile,
        adapter_identity,
    )
    adapter = Adapter(adapter_identity, FactAdapterResult(FactAdapterState.FAILED, None, ()))

    result = StrategyRuntime(Registry(profile), adapter).evaluate(request)

    _assert_invalid(result, RuntimeDiagnosticStage.TEMPORAL)
    assert adapter.calls == 0


def test_evaluation_provenance_mismatch_is_a_pre_adapter_coherence_failure(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    provenance = _manifest(inputs.provenance, evaluation_id="other-evaluation")
    request = make_request(
        context,
        _inputs(inputs, provenance=provenance),
        policy,
        profile,
        adapter_identity,
    )
    adapter = Adapter(adapter_identity, FactAdapterResult(FactAdapterState.FAILED, None, ()))

    result = StrategyRuntime(Registry(profile), adapter).evaluate(request)

    _assert_invalid(result, RuntimeDiagnosticStage.COHERENCE)
    assert adapter.calls == 0


@pytest.mark.parametrize(
    "axis",
    ("evaluation", "strategy", "policy", "profile", "mtf", "provenance", "manifest"),
)
def test_accepted_bundle_continuity_axes_stop_before_a07(
    axis: str,
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    bundle_context = context
    bundle_inputs = inputs
    bundle_policy = policy
    bundle_profile = profile
    policy_reference: str | None = None

    if axis == "evaluation":
        bundle_context = EvaluationContext.create(
            instrument_id=context.instrument_id,
            symbol=context.symbol,
            primary_timeframe=context.primary_timeframe,
            evaluation_timestamp=context.evaluation_timestamp,
            event_timestamp=context.event_timestamp,
            receipt_timestamp=context.receipt_timestamp,
            runtime_mode=context.runtime_mode,
            profile_identity=context.profile_identity,
            source_set_id=context.source_set_id,
            run_id="other-run",
        )
        provenance = _manifest(inputs.provenance, evaluation_id=bundle_context.evaluation_id)
        bundle_inputs = _inputs(inputs, provenance=provenance)
    elif axis == "strategy":
        bundle_policy = StrategyPolicy(
            policy.identity.policy_id,
            policy.identity.policy_version,
            StrategyIdentity("other", "1"),
            policy.enabled_directions,
            policy.minimum_rr,
            policy.minimum_confidence,
            policy.required_evidence,
            policy.optional_evidence,
            policy.expiration_seconds,
            policy.numeric_precision,
            policy.elliott_policy,
        )
    elif axis == "policy":
        policy_reference = "other-policy:1"
    elif axis == "profile":
        bundle_profile = _profile_like(profile, "other-profile")
        provenance = _manifest(inputs.provenance, profile_identity=bundle_profile.identity)
        bundle_inputs = _inputs(inputs, provenance=provenance)
    elif axis == "mtf":
        frame = inputs.mtf_context.frames[0]
        other_mtf = MultiTimeframeInputSet.create(
            inputs.mtf_context.primary_timeframe,
            "2026-08-24T12:31:15.123456Z",
            (frame,),
        )
        bundle_inputs = _inputs(inputs, mtf=other_mtf)
    elif axis == "provenance":
        provenance = _manifest(inputs.provenance, source_digest="e" * 64)
        bundle_inputs = _inputs(inputs, provenance=provenance)

    bundle = make_bundle(
        bundle_context,
        bundle_inputs,
        bundle_policy,
        bundle_profile,
        policy_reference=policy_reference,
    )
    if axis == "manifest":
        bundle = StrategyFactBundle.create(
            evaluation_id=bundle.evaluation_id,
            strategy_identity=bundle.strategy_identity,
            policy_reference=bundle.policy_reference,
            profile_identity=bundle.profile_identity,
            evidence_identity=StrategyEvidenceIdentity("other-set", "f" * 64),
            evidence=bundle.evidence,
            directional_facts=bundle.directional_facts,
            entry_facts=bundle.entry_facts,
            stop_facts=bundle.stop_facts,
            target_facts=bundle.target_facts,
            confidence=bundle.confidence,
            mtf_context_id=bundle.mtf_context_id,
            provenance=bundle.provenance,
        )
    adapter = accepted_adapter(adapter_identity, bundle)
    registry = Registry(profile)
    request = make_request(context, inputs, policy, profile, adapter_identity)

    result = StrategyRuntime(registry, adapter).evaluate(request)

    _assert_invalid(result, RuntimeDiagnosticStage.COHERENCE, bundle=bundle)
    assert registry.calls == 1
    assert adapter.calls == 1


def test_evaluation_preserves_all_caller_supplied_immutable_inputs(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    bundle = make_bundle(context, inputs, policy, profile)
    request = make_request(context, inputs, policy, profile, adapter_identity)
    before = (
        request,
        context,
        inputs,
        policy,
        profile.identity,
        adapter_identity,
        hash(request),
        hash(context),
        hash(inputs),
        hash(policy),
        hash(profile.identity),
        hash(adapter_identity),
    )

    result = StrategyRuntime(
        Registry(profile), accepted_adapter(adapter_identity, bundle)
    ).evaluate(request)

    after = (
        request,
        context,
        inputs,
        policy,
        profile.identity,
        adapter_identity,
        hash(request),
        hash(context),
        hash(inputs),
        hash(policy),
        hash(profile.identity),
        hash(adapter_identity),
    )
    assert result.state is StrategyRuntimeState.ACCEPTED_SIGNAL
    assert before == after
