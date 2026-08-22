"""Component tests for A04-E08 deterministic execution tracking."""

from __future__ import annotations

from dataclasses import replace
from inspect import getmembers, isfunction
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError
from epip.evidence.execution import ExecutionDiagnostics, ExecutionResult
from epip.evidence.graph import DependencyGraphBuilder
from epip.evidence.model import (
    DependencyType,
    DiagnosticCode,
    DiagnosticReason,
    EvidenceRequirement,
    ResolutionProfile,
)
from epip.evidence.orchestration import ExecutionOrchestrator, ExecutionSchedule
from epip.evidence.resolution import ResolutionPlanner
from epip.evidence.selection import SelectionDiagnostics
from epip.evidence.tracking import ExecutionTrace, ExecutionTracker, TrackingDiagnostics
from epip.governance import GovernanceEpoch, RegistryEntry, RegistrySnapshot
from epip.producer import ProducerExecutionOutput


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


def _fixture() -> tuple[ExecutionResult, ExecutionSchedule, RegistrySnapshot, ResolutionProfile]:
    entries = (_entry("producer-a"), _entry("producer-b"), _entry("producer-c"))
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
        for suffix in ("a", "b", "c")
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
        snapshot,
        selections,
        (("requirement-c", "requirement-b"), ("requirement-b", "requirement-a")),
    )
    plan = ResolutionPlanner.plan(graph, profile, snapshot)
    schedule = ExecutionOrchestrator.orchestrate(plan, snapshot, profile)
    outcomes = tuple(
        (
            requirement,
            identity,
            ProducerExecutionOutput(
                "manifest-1",
                identity.split("@")[0],
                "1.0.0",
                "1.0.0",
                (("market.structure", "1.0.0"),),
                "1",
                "1",
                "1",
                "success",
                (("market.structure", identity),),
            ),
        )
        for requirement, identity in schedule.scheduled_executions
    )
    diagnostics = ExecutionDiagnostics(
        "snapshot-1",
        "manifest-1",
        GovernanceEpoch(4),
        schedule,
        schedule.execution_layers,
        tuple(identity for _, identity in schedule.scheduled_executions),
        schedule.scheduled_executions,
        schedule.execution_barriers,
        outcomes,
        (),
    )
    result = ExecutionResult(
        "snapshot-1",
        "manifest-1",
        GovernanceEpoch(4),
        profile,
        schedule,
        schedule.scheduled_executions,
        schedule.execution_barriers,
        outcomes,
        diagnostics,
    )
    return result, schedule, snapshot, profile


def test_public_production_inventory_is_exact() -> None:
    from epip.evidence import tracking

    assert {
        name
        for name, value in vars(tracking).items()
        if isinstance(value, type)
        and value.__module__ == tracking.__name__
        and not name.startswith("_")
    } == {"ExecutionTracker", "ExecutionTrace", "TrackingDiagnostics"}


def test_tracks_complete_execution_history_and_context() -> None:
    result, schedule, snapshot, profile = _fixture()
    trace = ExecutionTracker.track(result, schedule, snapshot, profile)
    assert trace.execution_history == result.outcomes
    assert trace.execution_ordering == schedule.scheduled_executions
    assert trace.execution_barriers == schedule.execution_barriers
    assert trace.dependency_ordering == schedule.dependency_ordering
    assert trace.producer_identities == tuple(identity for _, identity in trace.execution_ordering)
    assert trace.requirement_identities == tuple(
        requirement for requirement, _ in trace.execution_ordering
    )
    assert trace.diagnostics.execution_schedule == schedule
    assert trace.diagnostics.execution_trace == trace.execution_history
    assert trace.diagnostics.execution_outcomes == result.outcomes
    assert trace.diagnostics.dependency_identities == (
        ("requirement-b", "requirement-a"),
        ("requirement-c", "requirement-b"),
    )
    assert trace.diagnostics.reasons == ()


def _permute_dependency_identities(
    result: ExecutionResult, schedule: ExecutionSchedule
) -> tuple[ExecutionResult, ExecutionSchedule]:
    plan = schedule.resolution_plan
    graph = plan.dependency_graph
    graph_diagnostics = graph.diagnostics._replace(
        dependency_identities=tuple(reversed(graph.diagnostics.dependency_identities))
    )
    graph = graph._replace(diagnostics=graph_diagnostics)
    plan = plan._replace(
        dependency_graph=graph,
        diagnostics=plan.diagnostics._replace(dependency_graph=graph),
    )
    schedule = schedule._replace(
        resolution_plan=plan,
        diagnostics=schedule.diagnostics._replace(
            resolution_plan=plan,
            dependency_graph=graph,
        ),
    )
    result = result._replace(
        execution_schedule=schedule,
        diagnostics=result.diagnostics._replace(execution_schedule=schedule),
    )
    return result, schedule


def test_dependency_identities_are_independent_canonical_and_hashable() -> None:
    result, schedule, snapshot, profile = _fixture()
    expected = ExecutionTracker.track(result, schedule, snapshot, profile).diagnostics
    permuted_result, permuted_schedule = _permute_dependency_identities(result, schedule)
    actual = ExecutionTracker.track(
        permuted_result, permuted_schedule, snapshot, profile
    ).diagnostics
    repeated = ExecutionTracker.track(
        permuted_result, permuted_schedule, snapshot, profile
    ).diagnostics
    assert actual.dependency_identities == expected.dependency_identities
    assert actual == repeated
    assert hash(actual) == hash(repeated)
    assert actual.dependency_identities is not (
        permuted_schedule.resolution_plan.dependency_graph.diagnostics.dependency_identities
    )


def test_repeated_tracking_and_registry_permutations_are_identical() -> None:
    result, schedule, snapshot, profile = _fixture()
    expected = ExecutionTracker.track(result, schedule, snapshot, profile)
    permuted = replace(snapshot, entries=tuple(reversed(snapshot.entries)))
    assert ExecutionTracker.track(result, schedule, snapshot, profile) == expected
    assert ExecutionTracker.track(result, schedule, permuted, profile) == expected
    assert hash(ExecutionTracker.track(result, schedule, permuted, profile)) == hash(expected)


def test_trace_diagnostics_and_inputs_are_immutable_and_hashable() -> None:
    result, schedule, snapshot, profile = _fixture()
    inputs = (result, schedule, snapshot, profile)
    hashes = tuple(hash(value) for value in inputs)
    trace = ExecutionTracker.track(result, schedule, snapshot, profile)
    with pytest.raises(AttributeError):
        trace.execution_history = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        trace.diagnostics.reasons = ()  # type: ignore[misc]
    assert hash(trace) and hash(trace.diagnostics)
    assert hashes == tuple(hash(value) for value in inputs)


@pytest.mark.parametrize(
    "change",
    [
        "result_context",
        "schedule_context",
        "schedule_history",
        "diagnostic_context",
        "diagnostic_layers",
        "diagnostic_executed",
        "diagnostic_ordering",
        "diagnostic_barriers",
        "diagnostic_outcomes",
        "diagnostic_reasons",
        "ordering",
        "barriers",
        "missing_outcome",
        "outcome_order",
        "registry",
        "output_type",
        "output_manifest",
        "output_producer",
        "output_version",
        "output_contract",
        "failure_outcome",
    ],
)
def test_invalid_or_incomplete_execution_history_fails_closed(change: str) -> None:
    result, schedule, snapshot, profile = _fixture()
    diagnostics = result.diagnostics
    if change == "result_context":
        result = result._replace(manifest_reference="other")
    elif change == "schedule_context":
        schedule = schedule._replace(manifest_reference="other")
    elif change == "schedule_history":
        schedule = schedule._replace(scheduled_executions=())
    elif change == "diagnostic_context":
        diagnostics = diagnostics._replace(snapshot_identity="other")
    elif change == "diagnostic_layers":
        diagnostics = diagnostics._replace(execution_layers=())
    elif change == "diagnostic_executed":
        diagnostics = diagnostics._replace(executed_provider_identities=())
    elif change == "diagnostic_ordering":
        diagnostics = diagnostics._replace(execution_ordering=())
    elif change == "diagnostic_barriers":
        diagnostics = diagnostics._replace(execution_barriers=())
    elif change == "diagnostic_outcomes":
        diagnostics = diagnostics._replace(outcomes=())
    elif change == "diagnostic_reasons":
        diagnostics = diagnostics._replace(
            reasons=(DiagnosticReason(DiagnosticCode.INVALID_DEPENDENCY, "execution", "failed"),)
        )
    elif change == "ordering":
        result = result._replace(execution_ordering=tuple(reversed(result.execution_ordering)))
    elif change == "barriers":
        result = result._replace(execution_barriers=())
    elif change == "missing_outcome":
        result = result._replace(outcomes=result.outcomes[:-1])
    elif change == "outcome_order":
        result = result._replace(outcomes=tuple(reversed(result.outcomes)))
    elif change == "registry":
        snapshot = replace(snapshot, entries=snapshot.entries[:-1])
    elif change == "output_type":
        result = result._replace(
            outcomes=(
                (result.outcomes[0][0], result.outcomes[0][1], cast(Any, object())),
                *result.outcomes[1:],
            )
        )
    elif change == "output_manifest":
        output = replace(result.outcomes[0][2], input_manifest_reference="other")
        result = result._replace(
            outcomes=((result.outcomes[0][0], result.outcomes[0][1], output), *result.outcomes[1:])
        )
    elif change == "output_producer":
        output = replace(result.outcomes[0][2], producer_identity="other")
        result = result._replace(
            outcomes=((result.outcomes[0][0], result.outcomes[0][1], output), *result.outcomes[1:])
        )
    elif change == "output_version":
        output = replace(result.outcomes[0][2], producer_version="2.0.0")
        result = result._replace(
            outcomes=((result.outcomes[0][0], result.outcomes[0][1], output), *result.outcomes[1:])
        )
    elif change == "output_contract":
        output = replace(result.outcomes[0][2], contract_version="2.0.0")
        result = result._replace(
            outcomes=((result.outcomes[0][0], result.outcomes[0][1], output), *result.outcomes[1:])
        )
    elif change == "failure_outcome":
        output = replace(
            result.outcomes[0][2],
            outcome="analytical_execution_failure",
            evidence_outputs=(),
            semantic_diagnostics=(("failure", "declared"),),
        )
        result = result._replace(
            outcomes=((result.outcomes[0][0], result.outcomes[0][1], output), *result.outcomes[1:])
        )
    if change in {
        "diagnostic_context",
        "diagnostic_layers",
        "diagnostic_executed",
        "diagnostic_ordering",
        "diagnostic_barriers",
        "diagnostic_outcomes",
        "diagnostic_reasons",
    }:
        result = result._replace(diagnostics=diagnostics)
    elif change in {
        "ordering",
        "barriers",
        "missing_outcome",
        "outcome_order",
        "output_type",
        "output_manifest",
        "output_producer",
        "output_version",
        "output_contract",
        "failure_outcome",
    }:
        result = result._replace(
            diagnostics=result.diagnostics._replace(
                execution_ordering=result.execution_ordering,
                execution_barriers=result.execution_barriers,
                outcomes=result.outcomes,
            )
        )
    trace = ExecutionTracker.track(result, schedule, snapshot, profile)
    assert trace.execution_history == ()
    assert trace.execution_ordering == ()
    assert trace.execution_barriers == ()
    assert trace.diagnostics.reasons[-1].code is DiagnosticCode.INVALID_DEPENDENCY
    assert isinstance(trace.diagnostics.reasons[-1], DiagnosticReason)


@pytest.mark.parametrize(
    "call",
    [
        lambda: ExecutionTracker.track(
            cast(Any, object()), _fixture()[1], _fixture()[2], _fixture()[3]
        ),
        lambda: ExecutionTracker.track(
            _fixture()[0], cast(Any, object()), _fixture()[2], _fixture()[3]
        ),
        lambda: ExecutionTracker.track(
            _fixture()[0], _fixture()[1], cast(Any, object()), _fixture()[3]
        ),
        lambda: ExecutionTracker.track(
            _fixture()[0], _fixture()[1], _fixture()[2], cast(Any, object())
        ),
    ],
)
def test_invalid_input_models_fail_closed(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


def test_no_e09_or_predecessor_responsibilities_are_present() -> None:
    forbidden = {
        "enumerate",
        "filter",
        "validate",
        "build",
        "select",
        "plan",
        "orchestrate",
        "execute",
        "produce",
        "aggregate",
        "replay",
        "integrate_lifecycle",
    }
    methods = {
        name
        for owner in (ExecutionTracker, ExecutionTrace, TrackingDiagnostics)
        for name, value in getmembers(owner)
        if isfunction(value) or callable(value)
    }
    assert forbidden.isdisjoint(methods)
