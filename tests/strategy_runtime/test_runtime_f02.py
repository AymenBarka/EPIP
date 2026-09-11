from __future__ import annotations

import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier, Lock

import pytest

import epip.strategy_runtime as public
import epip.strategy_runtime.runtime as runtime_module
from epip.a07.foundation import StrategyDirection
from epip.a07.policy import StrategyPolicy
from epip.strategy_runtime import (
    AnalyticalInputBundle,
    EvaluationContext,
    FactAdapterIdentity,
    FactAdapterResult,
    FactAdapterState,
    ProvenanceManifest,
    StrategyFactBundle,
    StrategyProfile,
    StrategyRuntime,
    StrategyRuntimeProtocol,
    StrategyRuntimeRequest,
    StrategyRuntimeResult,
    StrategyRuntimeState,
)
from tests.strategy_runtime.test_runtime import Registry, make_bundle, make_request


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
    mtf: public.MultiTimeframeInputSet,
    provenance: ProvenanceManifest,
) -> AnalyticalInputBundle:
    return AnalyticalInputBundle(None, None, None, None, None, None, None, None, mtf, provenance)


class RoutingAdapter:
    def __init__(
        self,
        identity: FactAdapterIdentity,
        bundles: tuple[StrategyFactBundle, ...],
    ) -> None:
        self._identity = identity
        self._bundles = {item.evaluation_id: item for item in bundles}
        self._calls: Counter[str] = Counter()
        self._lock = Lock()
        self._barrier: Barrier | None = None

    @property
    def identity(self) -> FactAdapterIdentity:
        return self._identity

    @property
    def calls(self) -> Counter[str]:
        with self._lock:
            return self._calls.copy()

    def reset_for_concurrent_pair(self) -> None:
        with self._lock:
            self._calls.clear()
        self._barrier = Barrier(2)

    def adapt(
        self,
        context: EvaluationContext,
        inputs: AnalyticalInputBundle,
        profile: StrategyProfile,
        policy: StrategyPolicy,
    ) -> FactAdapterResult:
        del inputs, profile, policy
        with self._lock:
            self._calls[context.evaluation_id] += 1
        barrier = self._barrier
        if barrier is not None:
            barrier.wait()
        return FactAdapterResult(
            FactAdapterState.ACCEPTED,
            self._bundles[context.evaluation_id],
            (),
        )


def _second_request(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> tuple[StrategyRuntimeRequest, StrategyFactBundle]:
    second_context = EvaluationContext.create(
        instrument_id=context.instrument_id,
        symbol=context.symbol,
        primary_timeframe=context.primary_timeframe,
        evaluation_timestamp=context.evaluation_timestamp,
        event_timestamp=context.event_timestamp,
        receipt_timestamp=context.receipt_timestamp,
        runtime_mode=context.runtime_mode,
        profile_identity=context.profile_identity,
        source_set_id="sources:2",
        run_id="run:2",
    )
    second_provenance = ProvenanceManifest.create(
        inputs.provenance.sources,
        inputs.provenance.facts,
        inputs.provenance.profile_identity,
        inputs.provenance.adapter_identity,
        second_context.evaluation_id,
    )
    second_inputs = replace(inputs, provenance=second_provenance)
    second_request = make_request(
        second_context,
        second_inputs,
        policy,
        profile,
        adapter_identity,
    )
    return second_request, make_bundle(second_context, second_inputs, policy, profile)


def _assert_request_specific_result(
    request: StrategyRuntimeRequest,
    bundle: StrategyFactBundle,
    result: StrategyRuntimeResult,
) -> None:
    assert result.request_id == request.request_id
    assert result.state is StrategyRuntimeState.ACCEPTED_SIGNAL
    assert result.fact_bundle_id == bundle.bundle_id
    assert result.signal_envelope is not None
    assert result.signal_envelope.evaluation_id == request.context.evaluation_id
    assert result.signal_envelope.source_set_id == request.context.source_set_id
    assert result.diagnostics.final_state is result.state


def test_mixed_requests_are_deterministic_and_isolated_on_one_shared_runtime(
    context: EvaluationContext,
    inputs: AnalyticalInputBundle,
    policy: StrategyPolicy,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> None:
    first_request = make_request(context, inputs, policy, profile, adapter_identity)
    first_bundle = make_bundle(context, inputs, policy, profile)
    second_request, second_bundle = _second_request(
        context,
        inputs,
        policy,
        profile,
        adapter_identity,
    )
    requests = (first_request, second_request)
    bundles = (first_bundle, second_bundle)
    adapter = RoutingAdapter(adapter_identity, bundles)
    runtime: StrategyRuntimeProtocol = StrategyRuntime(Registry(profile), adapter)

    first_serial = tuple(runtime.evaluate(request) for request in requests)
    second_serial = tuple(runtime.evaluate(request) for request in requests)

    assert first_serial == second_serial
    assert len({result.result_id for result in first_serial}) == 2
    assert len({result.fact_bundle_id for result in first_serial}) == 2
    for request, bundle, result in zip(requests, bundles, first_serial, strict=True):
        _assert_request_specific_result(request, bundle, result)
    assert adapter.calls == Counter(
        {first_request.context.evaluation_id: 2, second_request.context.evaluation_id: 2}
    )

    adapter.reset_for_concurrent_pair()
    with ThreadPoolExecutor(max_workers=2) as pool:
        concurrent = tuple(pool.map(runtime.evaluate, requests))

    assert concurrent == first_serial
    for request, bundle, result in zip(requests, bundles, concurrent, strict=True):
        _assert_request_specific_result(request, bundle, result)
    assert adapter.calls == Counter(
        {first_request.context.evaluation_id: 1, second_request.context.evaluation_id: 1}
    )
    assert not hasattr(runtime, "__dict__")


def test_canonical_runtime_package_is_publicly_stable_pure_and_successor_isolated() -> None:
    package_root = Path("epip/strategy_runtime")
    runtime_path = package_root / "runtime.py"
    parsed = {
        path: ast.parse(path.read_text(encoding="utf-8"))
        for path in sorted(package_root.glob("*.py"))
    }
    strategy_runtime_defs = tuple(
        (path, node.name)
        for path, tree in parsed.items()
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and node.name in {"StrategyRuntime", "StrategyRuntimeProtocol"}
    )
    assert strategy_runtime_defs == (
        (runtime_path, "StrategyRuntimeProtocol"),
        (runtime_path, "StrategyRuntime"),
    )
    assert runtime_module.__all__ == ["StrategyRuntime", "StrategyRuntimeProtocol"]
    assert public.StrategyRuntime is runtime_module.StrategyRuntime
    assert public.StrategyRuntimeProtocol is runtime_module.StrategyRuntimeProtocol
    assert not {"_entry", "_result"} & set(public.__all__)

    tree = parsed[runtime_path]
    imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)} | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    forbidden_imports = (
        "epip.strategy_mapping",
        "epip.elliott",
        "epip.fibonacci",
        "epip.backtest",
        "epip.replay",
        "epip.execution",
        "epip.portfolio",
        "epip.persistence",
        "epip.observability",
        "epip.dashboard",
        "epip.scheduler",
        "pathlib",
        "os",
        "random",
        "uuid",
        "socket",
        "urllib",
        "http",
        "requests",
        "subprocess",
        "importlib",
        "pickle",
    )
    assert not any(
        name == root or name.startswith(f"{root}.")
        for name in imports
        for root in forbidden_imports
    )

    direct_calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    attribute_calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not direct_calls & {"open", "eval", "exec", "__import__"}
    assert not attribute_calls & {"now", "utcnow", "time", "uuid1", "uuid4"}
    assert not any(
        isinstance(node, ast.Attribute) and node.attr == "environ" for node in ast.walk(tree)
    )

    module_assignments = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
    }
    assert module_assignments <= {"RUNTIME_VERSION", "__all__"}
