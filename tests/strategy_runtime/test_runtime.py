from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Any

import pytest

import epip.strategy_runtime.runtime as runtime_module
from epip.a07.direction import DirectionalFacts
from epip.a07.entry import EntryFacts
from epip.a07.evidence import StrategyEvidenceSnapshot
from epip.a07.foundation import StrategyDirection, StrategyEvidenceIdentity, StrategyIdentity
from epip.a07.policy import StrategyPolicy
from epip.a07.stop import StopFacts
from epip.a07.target import TargetFacts
from epip.strategy_runtime import (
    AnalyticalInputBundle,
    DiagnosticSeverity,
    EvaluationContext,
    FactAdapterIdentity,
    FactAdapterResult,
    FactAdapterState,
    MultiTimeframeInputSet,
    RuntimeDiagnostic,
    RuntimeDiagnosticCode,
    RuntimeDiagnosticStage,
    StrategyFactBundle,
    StrategyProfile,
    StrategyProfileIdentity,
    StrategyRuntime,
    StrategyRuntimeOptions,
    StrategyRuntimeRequest,
    StrategyRuntimeState,
    TimeframeInput,
)
from epip.strategy_runtime._base import CONTRACT_VERSION, digest
from epip.strategy_runtime.provenance import ProvenanceManifest
from epip.strategy_runtime.serialization import from_json, to_json


class Registry:
    def __init__(self, profile: StrategyProfile, *, fail: bool = False) -> None:
        self.profile = profile
        self.fail = fail
        self.calls = 0

    def resolve(self, identity: object) -> StrategyProfile:
        self.calls += 1
        if self.fail:
            raise LookupError("missing profile")
        del identity
        return self.profile


class Adapter:
    def __init__(
        self,
        identity: FactAdapterIdentity,
        result: FactAdapterResult | None = None,
        *,
        error: Exception | None = None,
        trace: list[str] | None = None,
    ) -> None:
        self._identity = identity
        self.result = result
        self.error = error
        self.calls = 0
        self.trace = trace
        self._lock = Lock()

    @property
    def identity(self) -> FactAdapterIdentity:
        return self._identity

    def adapt(self, *args: object) -> FactAdapterResult:
        assert len(args) == 4
        with self._lock:
            self.calls += 1
            if self.trace is not None:
                self.trace.append("adapter")
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


@pytest.fixture
def policy(strategy_identity: StrategyIdentity) -> StrategyPolicy:
    return StrategyPolicy(
        "policy",
        "1",
        strategy_identity,
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
def inputs(mtf: MultiTimeframeInputSet, provenance: ProvenanceManifest) -> AnalyticalInputBundle:
    return AnalyticalInputBundle(None, None, None, None, None, None, None, None, mtf, provenance)


def make_request(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
    **changes: object,
) -> StrategyRuntimeRequest:
    values: dict[str, object] = {
        "contract_version": CONTRACT_VERSION,
        "context": context,
        "inputs": inputs,
        "policy": policy,
        "profile_identity": profile.identity,
        "adapter_identity": adapter_identity,
        "runtime_contract_version": CONTRACT_VERSION,
        "options": StrategyRuntimeOptions(),
    }
    values.update(changes)
    candidate = object.__new__(StrategyRuntimeRequest)
    object.__setattr__(candidate, "request_id", "")
    for name, value in values.items():
        object.__setattr__(candidate, name, value)
    request_id = digest(candidate, exclude=frozenset({"request_id"}))
    return StrategyRuntimeRequest(request_id=request_id, **values)  # type: ignore[arg-type]


def make_bundle(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    *,
    directions: tuple[StrategyDirection, ...] | None = None,
    target: float = 115.0,
    stop: float = 95.0,
    confidence: float = 0.75,
    evidence_fresh: bool = True,
    policy_reference: str | None = None,
) -> StrategyFactBundle:
    set_identity = StrategyEvidenceIdentity("set-zeta-alpha", inputs.provenance.manifest_id)
    evidence = (
        StrategyEvidenceSnapshot(
            policy.strategy_identity,
            StrategyEvidenceIdentity("item-zeta", inputs.provenance.manifest_id),
            "elliott",
            evidence_fresh,
            True,
        ),
        StrategyEvidenceSnapshot(
            policy.strategy_identity,
            StrategyEvidenceIdentity("item-alpha", inputs.provenance.manifest_id),
            "context",
            True,
            True,
        ),
    )
    facts = directions or ((StrategyDirection.BUY,) * 6)
    return StrategyFactBundle.create(
        evaluation_id=context.evaluation_id,
        strategy_identity=policy.strategy_identity,
        policy_reference=policy_reference or policy.identity.reference,
        profile_identity=profile.identity,
        evidence_identity=set_identity,
        evidence=evidence,
        directional_facts=DirectionalFacts(*facts),
        entry_facts=EntryFacts(100.0, 100.0),
        stop_facts=StopFacts(stop),
        target_facts=TargetFacts(target),
        confidence=confidence,
        mtf_context_id=inputs.mtf_context.context_id,
        provenance=inputs.provenance,
    )


def accepted_adapter(
    adapter_identity: FactAdapterIdentity,
    bundle: StrategyFactBundle,
    trace: list[str] | None = None,
) -> Adapter:
    return Adapter(
        adapter_identity,
        FactAdapterResult(FactAdapterState.ACCEPTED, bundle, ()),
        trace=trace,
    )


def instrument_a07(
    monkeypatch: pytest.MonkeyPatch,
    trace: list[str],
) -> dict[str, Any]:
    captured: dict[str, Any] = {}
    stages = (
        ("StrategyEvaluationRequest", "E00"),
        ("PolicyValidation", "E01"),
        ("EvidenceBinding", "E02"),
        ("DirectionalDecision", "E03"),
        ("EntryPrice", "E04"),
        ("StopLoss", "E05"),
        ("TakeProfit", "E06"),
        ("RewardRiskOutcome", "E07"),
        ("StrategyConfidence", "E08"),
        ("StrategySignal", "E09"),
    )
    for name, label in stages:
        original = getattr(runtime_module, name)

        def wrapper(
            *args: object,
            _original: Any = original,
            _label: str = label,
            **kwargs: object,
        ) -> object:
            trace.append(_label)
            result: Any = _original(*args, **kwargs)
            if _label == "E00":
                captured["request"] = result
            elif _label == "E02":
                captured["evidence"] = result.available_evidence
            return result

        monkeypatch.setattr(runtime_module, name, wrapper)
    return captured


def test_accepted_signal_preserves_exact_evidence_handoff_and_stage_order(
    monkeypatch: pytest.MonkeyPatch,
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    bundle = make_bundle(context, inputs, policy, profile)
    trace: list[str] = []
    captured = instrument_a07(monkeypatch, trace)
    adapter = accepted_adapter(adapter_identity, bundle, trace)
    request = make_request(context, inputs, policy, profile, adapter_identity)

    result = StrategyRuntime(Registry(profile), adapter).evaluate(request)

    assert result.state is StrategyRuntimeState.ACCEPTED_SIGNAL
    assert result.signal_envelope is not None
    assert result.fact_bundle_id == bundle.bundle_id
    assert result.signal_envelope.evaluation_id == context.evaluation_id
    assert result.signal_envelope.profile_identity == profile.identity
    assert result.signal_envelope.adapter_identity == adapter_identity
    assert result.signal_envelope.provenance_manifest_id == inputs.provenance.manifest_id
    assert captured["request"].evidence_identity is bundle.evidence_identity
    assert captured["evidence"] is bundle.evidence
    assert tuple(item.evidence_identity for item in captured["evidence"]) == tuple(
        item.evidence_identity for item in bundle.evidence
    )
    assert trace == ["adapter", *(f"E{i:02}" for i in range(10))]
    assert adapter.calls == 1


@pytest.mark.parametrize(
    ("adapter_state", "runtime_state"),
    (
        (FactAdapterState.REJECTED, StrategyRuntimeState.REJECTED),
        (FactAdapterState.INVALID_INPUT, StrategyRuntimeState.INVALID_INPUT),
        (FactAdapterState.FAILED, StrategyRuntimeState.ADAPTER_FAILURE),
    ),
)
def test_terminal_adapter_states_map_once_without_a07(
    adapter_state: FactAdapterState,
    runtime_state: StrategyRuntimeState,
    monkeypatch: pytest.MonkeyPatch,
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    trace: list[str] = []
    instrument_a07(monkeypatch, trace)
    diagnostic = RuntimeDiagnostic(
        RuntimeDiagnosticCode.ADAPTER_REJECTED,
        RuntimeDiagnosticStage.ADAPTER,
        DiagnosticSeverity.ERROR,
        "adapter",
        (),
        "governed adapter diagnostic",
    )
    adapter = Adapter(
        adapter_identity,
        FactAdapterResult(adapter_state, None, (diagnostic,)),
        trace=trace,
    )
    request = make_request(context, inputs, policy, profile, adapter_identity)

    result = StrategyRuntime(Registry(profile), adapter).evaluate(request)

    assert result.state is runtime_state
    assert result.diagnostics.entries == (diagnostic,)
    assert result.signal_envelope is None
    assert trace == ["adapter"]
    assert adapter.calls == 1


def test_pre_adapter_structural_failures_make_zero_adapter_and_a07_calls(
    monkeypatch: pytest.MonkeyPatch,
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    trace: list[str] = []
    instrument_a07(monkeypatch, trace)
    terminal = FactAdapterResult(FactAdapterState.FAILED, None, ())
    request = make_request(context, inputs, policy, profile, adapter_identity)

    cases: list[tuple[object, Registry, Adapter]] = []
    wrong_adapter = FactAdapterIdentity("other", "1", CONTRACT_VERSION, "d" * 64)
    cases.append((request, Registry(profile), Adapter(wrong_adapter, terminal, trace=trace)))
    cases.append(
        (request, Registry(profile, fail=True), Adapter(adapter_identity, terminal, trace=trace))
    )
    forged = object.__new__(StrategyRuntimeRequest)
    for name in StrategyRuntimeRequest.__dataclass_fields__:
        object.__setattr__(forged, name, getattr(request, name))
    object.__setattr__(forged, "request_id", "forged")
    cases.append((forged, Registry(profile), Adapter(adapter_identity, terminal, trace=trace)))
    cases.append((object(), Registry(profile), Adapter(adapter_identity, terminal, trace=trace)))

    for invalid, registry, adapter in cases:
        result = StrategyRuntime(registry, adapter).evaluate(invalid)  # type: ignore[arg-type]
        assert result.state is StrategyRuntimeState.INVALID_INPUT
        assert result.signal_envelope is None
        assert adapter.calls == 0
    assert trace == []


def test_temporal_and_strategy_mismatches_fail_before_adapter(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    frame: TimeframeInput = inputs.mtf_context.frames[0]
    changed_mtf = MultiTimeframeInputSet.create(
        inputs.mtf_context.primary_timeframe,
        "2026-08-24T12:31:15.123456Z",
        (frame,),
    )
    changed_inputs = AnalyticalInputBundle(
        None, None, None, None, None, None, None, None, changed_mtf, inputs.provenance
    )
    other_policy = StrategyPolicy(
        "other",
        "1",
        StrategyIdentity("other", "1"),
        (StrategyDirection.BUY,),
        2.0,
        0.5,
        ("context",),
        (),
        90,
        6,
        (),
    )
    requests = (
        make_request(context, changed_inputs, policy, profile, adapter_identity),
        make_request(context, inputs, other_policy, profile, adapter_identity),
    )
    for request in requests:
        adapter = Adapter(
            adapter_identity,
            FactAdapterResult(FactAdapterState.FAILED, None, ()),
        )
        result = StrategyRuntime(Registry(profile), adapter).evaluate(request)
        assert result.state is StrategyRuntimeState.INVALID_INPUT
        assert adapter.calls == 0


def test_remaining_dependency_and_provenance_mismatches_fail_before_adapter(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    malformed_profiles: list[StrategyProfile] = []
    for field in (
        "compatible_runtime_contract_versions",
        "compatible_adapter_contract_versions",
    ):
        malformed = object.__new__(StrategyProfile)
        for name in StrategyProfile.__dataclass_fields__:
            object.__setattr__(malformed, name, getattr(profile, name))
        object.__setattr__(malformed, field, ("unsupported",))
        malformed_profiles.append(malformed)

    wrong_identity = object.__new__(StrategyProfile)
    for name in StrategyProfile.__dataclass_fields__:
        object.__setattr__(wrong_identity, name, getattr(profile, name))
    object.__setattr__(
        wrong_identity,
        "identity",
        StrategyProfileIdentity("wrong", "1", CONTRACT_VERSION, "e" * 64),
    )
    malformed_profiles.append(wrong_identity)

    frame = inputs.mtf_context.frames[0]
    different_primary = TimeframeInput(
        "M5",
        frame.role,
        frame.window_open,
        frame.window_close,
        frame.as_of_timestamp,
        frame.closed,
        frame.source_refs,
        frame.provenance_refs,
    )
    wrong_mtf = MultiTimeframeInputSet.create(
        "M5", inputs.mtf_context.alignment_timestamp, (different_primary,)
    )
    wrong_mtf_inputs = AnalyticalInputBundle(
        None, None, None, None, None, None, None, None, wrong_mtf, inputs.provenance
    )

    wrong_provenance = object.__new__(ProvenanceManifest)
    for name in ProvenanceManifest.__dataclass_fields__:
        object.__setattr__(wrong_provenance, name, getattr(inputs.provenance, name))
    object.__setattr__(wrong_provenance, "evaluation_id", "wrong-evaluation")
    wrong_provenance_inputs = AnalyticalInputBundle(
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        inputs.mtf_context,
        wrong_provenance,
    )

    cases = [
        (Registry(item), make_request(context, inputs, policy, profile, adapter_identity))
        for item in malformed_profiles
    ]
    cases.extend(
        (
            (
                Registry(profile),
                make_request(context, wrong_mtf_inputs, policy, profile, adapter_identity),
            ),
            (
                Registry(profile),
                make_request(context, wrong_provenance_inputs, policy, profile, adapter_identity),
            ),
        )
    )
    for registry, request in cases:
        adapter = Adapter(adapter_identity, FactAdapterResult(FactAdapterState.FAILED, None, ()))
        assert StrategyRuntime(registry, adapter).evaluate(request).state is (
            StrategyRuntimeState.INVALID_INPUT
        )
        assert adapter.calls == 0


def test_malformed_adapter_result_fails_closed(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    class MalformedAdapter(Adapter):
        def adapt(self, *args: object) -> FactAdapterResult:
            self.calls += 1
            return object()  # type: ignore[return-value]

    adapter = MalformedAdapter(adapter_identity)
    request = make_request(context, inputs, policy, profile, adapter_identity)
    result = StrategyRuntime(Registry(profile), adapter).evaluate(request)
    assert result.state is StrategyRuntimeState.ADAPTER_FAILURE
    assert adapter.calls == 1


def test_unexpected_adapter_exception_is_sanitized_and_not_retried(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    secret = r"C:\private\key.txt SECRET_TOKEN=abc object at 0x1234"
    adapter = Adapter(adapter_identity, error=RuntimeError(secret))
    request = make_request(context, inputs, policy, profile, adapter_identity)

    result = StrategyRuntime(Registry(profile), adapter).evaluate(request)

    assert result.state is StrategyRuntimeState.ADAPTER_FAILURE
    assert adapter.calls == 1
    rendered = repr(result.diagnostics)
    assert secret not in rendered
    assert "SECRET_TOKEN" not in rendered
    assert "0x1234" not in rendered


def test_accepted_bundle_coherence_failure_stops_before_a07(
    monkeypatch: pytest.MonkeyPatch,
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    trace: list[str] = []
    instrument_a07(monkeypatch, trace)
    bundle = make_bundle(
        context,
        inputs,
        policy,
        profile,
        policy_reference="different-policy-reference",
    )
    adapter = accepted_adapter(adapter_identity, bundle, trace)
    request = make_request(context, inputs, policy, profile, adapter_identity)

    result = StrategyRuntime(Registry(profile), adapter).evaluate(request)

    assert result.state is StrategyRuntimeState.INVALID_INPUT
    assert result.signal_envelope is None
    assert trace == ["adapter"]


def test_no_signal_stops_after_direction(
    monkeypatch: pytest.MonkeyPatch,
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    trace: list[str] = []
    instrument_a07(monkeypatch, trace)
    mixed = (
        StrategyDirection.BUY,
        StrategyDirection.SELL,
        StrategyDirection.BUY,
        StrategyDirection.SELL,
        StrategyDirection.BUY,
        StrategyDirection.SELL,
    )
    bundle = make_bundle(context, inputs, policy, profile, directions=mixed)
    adapter = accepted_adapter(adapter_identity, bundle, trace)
    request = make_request(context, inputs, policy, profile, adapter_identity)

    result = StrategyRuntime(Registry(profile), adapter).evaluate(request)

    assert result.state is StrategyRuntimeState.NO_SIGNAL
    assert result.signal_envelope is None
    assert trace == ["adapter", "E00", "E01", "E02", "E03"]


def test_early_evidence_rejection_stops_at_e02(
    monkeypatch: pytest.MonkeyPatch,
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    trace: list[str] = []
    instrument_a07(monkeypatch, trace)
    bundle = make_bundle(context, inputs, policy, profile, evidence_fresh=False)
    adapter = accepted_adapter(adapter_identity, bundle, trace)
    request = make_request(context, inputs, policy, profile, adapter_identity)
    result = StrategyRuntime(Registry(profile), adapter).evaluate(request)
    assert result.state is StrategyRuntimeState.A07_REJECTION
    assert trace == ["adapter", "E00", "E01", "E02"]


def test_a07_construction_exception_is_sanitized_and_fail_fast(
    monkeypatch: pytest.MonkeyPatch,
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    trace: list[str] = []
    instrument_a07(monkeypatch, trace)
    bundle = make_bundle(context, inputs, policy, profile, stop=105.0)
    adapter = accepted_adapter(adapter_identity, bundle, trace)
    request = make_request(context, inputs, policy, profile, adapter_identity)
    result = StrategyRuntime(Registry(profile), adapter).evaluate(request)
    assert result.state is StrategyRuntimeState.A07_REJECTION
    assert trace == ["adapter", "E00", "E01", "E02", "E03", "E04", "E05"]
    assert "105" not in repr(result.diagnostics)


@pytest.mark.parametrize(
    ("target", "confidence", "last_stage"),
    ((105.0, 0.75, "E07"), (115.0, 0.25, "E08")),
)
def test_a07_rejection_is_fail_fast(
    target: float,
    confidence: float,
    last_stage: str,
    monkeypatch: pytest.MonkeyPatch,
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    trace: list[str] = []
    instrument_a07(monkeypatch, trace)
    bundle = make_bundle(
        context,
        inputs,
        policy,
        profile,
        target=target,
        confidence=confidence,
    )
    adapter = accepted_adapter(adapter_identity, bundle, trace)
    request = make_request(context, inputs, policy, profile, adapter_identity)

    result = StrategyRuntime(Registry(profile), adapter).evaluate(request)

    assert result.state is StrategyRuntimeState.A07_REJECTION
    assert result.signal_envelope is None
    assert trace[-1] == last_stage
    assert len(trace) == int(last_stage[1:]) + 2


def test_repeated_and_concurrent_evaluations_are_value_equal(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    bundle = make_bundle(context, inputs, policy, profile)
    adapter = accepted_adapter(adapter_identity, bundle)
    runtime = StrategyRuntime(Registry(profile), adapter)
    request = make_request(context, inputs, policy, profile, adapter_identity)

    serial = (runtime.evaluate(request), runtime.evaluate(request))
    with ThreadPoolExecutor(max_workers=4) as pool:
        concurrent = tuple(pool.map(runtime.evaluate, (request,) * 8))

    assert serial[0] == serial[1]
    assert all(result == serial[0] for result in concurrent)
    assert adapter.calls == 10
    assert from_json(type(serial[0]), to_json(serial[0])) == serial[0]


def test_runtime_has_no_p02_identity_or_successor_dependencies() -> None:
    path = Path("epip/strategy_runtime/runtime.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    forbidden = (
        "epip.strategy_mapping",
        "epip.backtest",
        "epip.execution",
        "epip.portfolio",
        "epip.observability",
    )
    assert not any(module.startswith(forbidden) for module in imports)
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not calls & {"now", "utcnow", "time", "uuid4"}
