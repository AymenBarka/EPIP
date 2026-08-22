"""Component tests for A04-E07 deterministic provider execution."""

from __future__ import annotations

from dataclasses import replace
from inspect import getmembers, isfunction
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError
from epip.evidence.execution import ExecutionDiagnostics, ExecutionResult, ProviderExecutor
from epip.evidence.graph import DependencyGraphBuilder
from epip.evidence.model import (
    DependencyType,
    DiagnosticCode,
    EvidenceRequirement,
    ResolutionProfile,
)
from epip.evidence.orchestration import ExecutionOrchestrator
from epip.evidence.resolution import ResolutionPlanner
from epip.evidence.selection import SelectionDiagnostics
from epip.governance import GovernanceEpoch, RegistryEntry, RegistrySnapshot
from epip.producer import (
    ProducerCapability,
    ProducerContract,
    ProducerExecutionEnvironment,
    ProducerExecutionInput,
    ProducerExecutionOutput,
)


def _capability() -> ProducerCapability:
    return ProducerCapability(
        "market.structure",
        "1.0.0",
        "analytical",
        ("price.series",),
        ("market.structure",),
        (),
        (),
        ("symbol",),
        ("closed",),
        "1",
        True,
        (),
        ("determinism",),
    )


def _contract(identity: str, **changes: object) -> ProducerContract:
    values: dict[str, object] = {
        "producer_identity": identity,
        "owner": "owner-1",
        "producer_version": "1.0.0",
        "contract_version": "1.0.0",
        "implementation_identity": f"build-{identity}",
        "capabilities": (_capability(),),
        "configuration_schema_version": "1",
        "configuration_fields": (),
        "configuration_compatibility": ("exact",),
        "input_schema_version": "1",
        "output_schema_version": "1",
        "diagnostic_schema_version": "1",
        "failure_schema_version": "1",
        "supported_timeframes": ("H1",),
        "execution_profile": "bounded",
        "isolation_profile": "isolated",
        "resource_profile": "declared",
        "execution_properties": ("terminal",),
        "resource_requirements": ("bounded",),
        "isolation_properties": ("isolated",),
        "cancellation_properties": ("cooperative-cancellation",),
        "concurrency_properties": ("serial",),
        "idempotency_classification": "idempotent",
        "determinism_profile": "deterministic",
        "replay_profile": "historical",
        "security_classification": "least-privilege",
        "trust_classification": "approved",
        "failure_codes": (
            "input_validation_failure",
            "unsupported_contract_or_capability",
            "invalid_configuration",
            "invalid_context_projection",
            "dependency_unavailable",
            "dependency_semantically_invalid",
            "unsupported_temporal_boundary",
            "analytical_execution_failure",
            "deterministic_contract_violation",
            "cooperative_cancellation",
        ),
        "certification_requirements": ("execution",),
    }
    values.update(changes)
    return ProducerContract(**values)  # type: ignore[arg-type]


class _Producer:
    def __init__(
        self,
        identity: str,
        *,
        outcome: str = "success",
        fail: bool = False,
        invalid_output: bool = False,
    ) -> None:
        self._contract = _contract(identity)
        self.outcome = outcome
        self.fail = fail
        self.invalid_output = invalid_output
        self.calls: list[str] = []

    @property
    def producer_contract(self) -> ProducerContract:
        return self._contract

    def produce(
        self, execution_input: ProducerExecutionInput, environment: ProducerExecutionEnvironment
    ) -> ProducerExecutionOutput:
        del environment
        self.calls.append(execution_input.producer_identity)
        if self.fail:
            raise RuntimeError("provider failure")
        if self.invalid_output:
            return object()  # type: ignore[return-value]
        failure = self.outcome != "success"
        return ProducerExecutionOutput(
            execution_input.manifest_reference,
            execution_input.producer_identity,
            execution_input.producer_version,
            execution_input.contract_version,
            execution_input.selected_capabilities,
            "1",
            "1",
            "1",
            self.outcome,
            () if failure else (("market.structure", execution_input.producer_identity),),
            (),
            (("failure", "declared failure"),) if failure else (),
            (),
            (),
        )


def _entry(identity: str) -> RegistryEntry:
    return RegistryEntry(
        identity,
        "1.0.0",
        f"descriptor-{identity}",
        "owner-1",
        "1.0.0",
        f"build-{identity}",
        (("market.structure", "1.0.0"),),
        "Trusted",
        (),
        (),
        "Enabled",
        ("admission-1",),
    )


def _fixture() -> (
    tuple[
        Any, RegistrySnapshot, ResolutionProfile, tuple[Any, ...], tuple[Any, ...], tuple[Any, ...]
    ]
):
    entries = (_entry("producer-a"), _entry("producer-b"))
    snapshot = RegistrySnapshot(
        "snapshot-1",
        "manifest-1",
        GovernanceEpoch(4),
        entries,
        ("action-1",),
        (("compatibility", "1.0.0"),),
    )
    profile = ResolutionProfile("profile-1", "1.0.0")
    requirements = tuple(
        EvidenceRequirement(
            f"requirement-{suffix}",
            "market.structure",
            "1.0.0",
            "EURUSD",
            "H1",
            DependencyType.MANDATORY,
        )
        for suffix in ("a", "b")
    )
    selections = tuple(
        (
            requirement,
            SelectionDiagnostics(
                "snapshot-1", "manifest-1", GovernanceEpoch(4), (entry,), (entry,), ()
            ),
        )
        for requirement, entry in zip(requirements, entries, strict=True)
    )
    graph = DependencyGraphBuilder.build(
        snapshot, selections, (("requirement-b", "requirement-a"),)
    )
    plan = ResolutionPlanner.plan(graph, profile, snapshot)
    schedule = ExecutionOrchestrator.orchestrate(plan, snapshot, profile)
    producers = (_Producer("producer-a"), _Producer("producer-b"))
    bindings = tuple(
        (f"producer-{suffix}@1.0.0", producer)
        for suffix, producer in zip(("a", "b"), producers, strict=True)
    )
    inputs = tuple(
        (
            key,
            ProducerExecutionInput(
                "manifest-1",
                identity.split("@")[0],
                "1.0.0",
                "1.0.0",
                (("market.structure", "1.0.0"),),
                "1",
                "1",
                (),
                "1",
                "control-plane",
                (("symbol", "EURUSD"),),
                (),
                "EURUSD",
                "H1",
                "closed",
                "revision-1",
                "snapshot-1",
                "manifest-1",
            ),
        )
        for key in schedule.scheduled_executions
        for identity in (key[1],)
    )
    environment = ProducerExecutionEnvironment("bounded", "isolated", "declared", False)
    environments = tuple((key, environment) for key in schedule.scheduled_executions)
    return schedule, snapshot, profile, bindings, inputs, environments


def test_public_inventory_is_exact() -> None:
    from epip.evidence import execution

    assert {
        name
        for name, value in vars(execution).items()
        if isinstance(value, type)
        and value.__module__ == execution.__name__
        and not name.startswith("_")
    } == {"ProviderExecutor", "ExecutionResult", "ExecutionDiagnostics"}


def test_executes_in_schedule_order_and_preserves_context() -> None:
    schedule, snapshot, profile, bindings, inputs, environments = _fixture()
    result = ProviderExecutor.execute(schedule, snapshot, profile, bindings, inputs, environments)
    assert (
        tuple((requirement, identity) for requirement, identity, _ in result.outcomes)
        == schedule.scheduled_executions
    )
    assert result.execution_ordering == schedule.scheduled_executions
    assert result.execution_barriers == schedule.execution_barriers
    assert result.diagnostics.execution_schedule == schedule
    assert result.diagnostics.outcomes == result.outcomes
    assert result.diagnostics.reasons == ()


def test_repeated_execution_and_binding_permutations_are_identical() -> None:
    schedule, snapshot, profile, bindings, inputs, environments = _fixture()
    expected = ProviderExecutor.execute(schedule, snapshot, profile, bindings, inputs, environments)
    for binding_order in permutations(bindings):
        for input_order in permutations(inputs):
            actual = ProviderExecutor.execute(
                schedule,
                snapshot,
                profile,
                binding_order,
                input_order,
                tuple(reversed(environments)),
            )
            assert actual == expected
            assert hash(actual) == hash(expected)


def test_results_diagnostics_and_inputs_are_immutable() -> None:
    schedule, snapshot, profile, bindings, inputs, environments = _fixture()
    hashes = tuple(hash(value) for value in (schedule, snapshot, profile, inputs, environments))
    result = ProviderExecutor.execute(schedule, snapshot, profile, bindings, inputs, environments)
    with pytest.raises(AttributeError):
        result.outcomes = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.diagnostics.reasons = ()  # type: ignore[misc]
    assert hash(result) and hash(result.diagnostics)
    assert hashes == tuple(
        hash(value) for value in (schedule, snapshot, profile, inputs, environments)
    )


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "unauthorized",
        "inconsistent",
        "inputs",
        "environments",
        "cancelled",
        "schedule",
        "non_provider",
        "input_mismatch",
        "input_contract",
        "failure",
        "invalid_output",
        "outcome",
    ],
)
def test_execution_failures_fail_closed(change: str) -> None:
    schedule, snapshot, profile, bindings, inputs, environments = _fixture()
    if change == "missing":
        bindings = bindings[:-1]
    elif change == "duplicate":
        bindings = (*bindings, bindings[0])
    elif change == "unauthorized":
        bindings = (*bindings, ("producer-z@1.0.0", _Producer("producer-z")))
    elif change == "inconsistent":
        bindings = ((bindings[0][0], _Producer("producer-z")), bindings[1])
    elif change == "inputs":
        inputs = inputs[:-1]
    elif change == "environments":
        environments = environments[:-1]
    elif change == "cancelled":
        environments = tuple(
            (key, ProducerExecutionEnvironment("bounded", "isolated", "declared", True))
            for key, _ in environments
        )
    elif change == "schedule":
        schedule = schedule._replace(execution_barriers=())
    elif change == "non_provider":
        bindings = ((bindings[0][0], cast(Any, object())), bindings[1])
    elif change == "input_mismatch":
        inputs = ((inputs[0][0], replace(inputs[0][1], producer_version="2.0.0")), inputs[1])
    elif change == "input_contract":
        inputs = ((inputs[0][0], replace(inputs[0][1], configuration=(("bad", 1),))), inputs[1])
    elif change == "failure":
        cast(Any, bindings[0][1]).fail = True
    elif change == "invalid_output":
        cast(Any, bindings[0][1]).invalid_output = True
    elif change == "outcome":
        cast(Any, bindings[0][1]).outcome = "analytical_execution_failure"
    result = ProviderExecutor.execute(schedule, snapshot, profile, bindings, inputs, environments)
    assert result.execution_ordering == () and result.execution_barriers == ()
    assert result.diagnostics.reasons[-1].code is DiagnosticCode.INVALID_DEPENDENCY


@pytest.mark.parametrize(
    "call",
    [
        lambda: ProviderExecutor.execute(
            cast(Any, object()), cast(Any, object()), cast(Any, object()), (), (), ()
        ),
        lambda: ProviderExecutor.execute(
            _fixture()[0], cast(Any, object()), _fixture()[2], (), (), ()
        ),
        lambda: ProviderExecutor.execute(
            _fixture()[0], _fixture()[1], cast(Any, object()), (), (), ()
        ),
        lambda: ProviderExecutor.execute(
            _fixture()[0], _fixture()[1], _fixture()[2], cast(Any, []), (), ()
        ),
    ],
)
def test_invalid_outer_inputs_fail_closed(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


def test_no_e08_e09_or_predecessor_responsibilities() -> None:
    forbidden = {
        "enumerate",
        "filter",
        "select",
        "validate",
        "build",
        "plan",
        "orchestrate",
        "aggregate",
        "replay",
        "track_execution",
        "integrate_lifecycle",
    }
    methods = {
        name
        for owner in (ProviderExecutor, ExecutionResult, ExecutionDiagnostics)
        for name, value in getmembers(owner)
        if isfunction(value) or callable(value)
    }
    assert forbidden.isdisjoint(methods)
