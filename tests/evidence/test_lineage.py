"""Component tests for A04-E09 deterministic lineage verification."""

from __future__ import annotations

from dataclasses import replace
from inspect import getmembers, isfunction
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError
from epip.evidence.execution import ExecutionDiagnostics, ExecutionResult
from epip.evidence.graph import DependencyGraphBuilder
from epip.evidence.lineage import LineageDiagnostics, LineageReport, LineageVerifier
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
from epip.evidence.tracking import ExecutionTrace, ExecutionTracker
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


def _fixture() -> tuple[
    ExecutionTrace,
    ExecutionResult,
    ExecutionSchedule,
    RegistrySnapshot,
    ResolutionProfile,
]:
    entries = tuple(_entry(f"producer-{suffix}") for suffix in ("a", "b", "c"))
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
    execution_diagnostics = ExecutionDiagnostics(
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
        execution_diagnostics,
    )
    trace = ExecutionTracker.track(result, schedule, snapshot, profile)
    return trace, result, schedule, snapshot, profile


def test_public_production_inventory_is_exact() -> None:
    from epip.evidence import lineage

    assert {
        name
        for name, value in vars(lineage).items()
        if isinstance(value, type)
        and value.__module__ == lineage.__name__
        and not name.startswith("_")
    } == {"LineageVerifier", "LineageReport", "LineageDiagnostics"}


def test_verifies_and_preserves_complete_lineage_context() -> None:
    trace, result, schedule, snapshot, profile = _fixture()
    report = LineageVerifier.verify(trace, result, schedule, snapshot, profile)
    assert report.verified
    assert all(verified for _, verified in report.verification_results)
    assert report.execution_trace == trace
    assert report.diagnostics.execution_schedule == schedule
    assert report.diagnostics.execution_ordering == trace.execution_ordering
    assert report.diagnostics.execution_barriers == trace.execution_barriers
    assert report.diagnostics.producer_identities == trace.producer_identities
    assert report.diagnostics.requirement_identities == trace.requirement_identities
    assert report.diagnostics.dependency_identities == trace.diagnostics.dependency_identities
    assert report.diagnostics.execution_history == trace.execution_history
    assert report.diagnostics.execution_trace == trace
    assert report.diagnostics.reasons == ()


def test_repeated_verification_and_registry_permutations_are_identical() -> None:
    trace, result, schedule, snapshot, profile = _fixture()
    expected = LineageVerifier.verify(trace, result, schedule, snapshot, profile)
    permuted = replace(snapshot, entries=tuple(reversed(snapshot.entries)))
    actual = LineageVerifier.verify(trace, result, schedule, permuted, profile)
    assert actual == expected
    assert actual == LineageVerifier.verify(trace, result, schedule, permuted, profile)
    assert hash(actual) == hash(expected)


def test_report_diagnostics_and_inputs_are_immutable_and_hashable() -> None:
    trace, result, schedule, snapshot, profile = _fixture()
    inputs = (trace, result, schedule, snapshot, profile)
    hashes = tuple(hash(value) for value in inputs)
    report = LineageVerifier.verify(trace, result, schedule, snapshot, profile)
    with pytest.raises(AttributeError):
        report.verified = False  # type: ignore[misc]
    with pytest.raises(AttributeError):
        report.diagnostics.reasons = ()  # type: ignore[misc]
    assert hash(report) and hash(report.diagnostics)
    assert hashes == tuple(hash(value) for value in inputs)


def _replace_dependencies(
    trace: ExecutionTrace,
    result: ExecutionResult,
    schedule: ExecutionSchedule,
    identities: tuple[tuple[str, str], ...],
) -> tuple[ExecutionTrace, ExecutionResult, ExecutionSchedule]:
    plan = schedule.resolution_plan
    graph = plan.dependency_graph
    graph = graph._replace(diagnostics=graph.diagnostics._replace(dependency_identities=identities))
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
    trace = trace._replace(
        execution_schedule=schedule,
        diagnostics=trace.diagnostics._replace(
            execution_schedule=schedule,
            dependency_identities=tuple(sorted(set(identities))),
        ),
    )
    return trace, result, schedule


@pytest.mark.parametrize(
    "change",
    [
        "trace_context",
        "result_context",
        "schedule_context",
        "diagnostic_context",
        "diagnostic_schedule",
        "diagnostic_ordering",
        "diagnostic_barriers",
        "diagnostic_producers",
        "diagnostic_requirements",
        "diagnostic_history",
        "diagnostic_trace",
        "fatal_reason",
        "ordering",
        "barriers",
        "dependency_ordering",
        "requirements",
        "producers",
        "history",
        "result_ordering",
        "result_barriers",
        "result_outcomes",
        "dependency_binding",
        "broken_dependency",
        "registry",
        "output_type",
        "output_manifest",
        "output_producer",
        "output_version",
        "output_contract",
        "output_failure",
    ],
)
def test_incomplete_or_inconsistent_lineage_fails_closed(change: str) -> None:
    trace, result, schedule, snapshot, profile = _fixture()
    if change == "trace_context":
        trace = trace._replace(manifest_reference="other")
    elif change == "result_context":
        result = result._replace(snapshot_identity="other")
    elif change == "schedule_context":
        schedule = schedule._replace(governance_epoch=GovernanceEpoch(5))
    elif change == "diagnostic_context":
        trace = trace._replace(diagnostics=trace.diagnostics._replace(manifest_reference="other"))
    elif change == "diagnostic_schedule":
        trace = trace._replace(
            diagnostics=trace.diagnostics._replace(execution_schedule=cast(Any, object()))
        )
    elif change == "diagnostic_ordering":
        trace = trace._replace(diagnostics=trace.diagnostics._replace(execution_ordering=()))
    elif change == "diagnostic_barriers":
        trace = trace._replace(diagnostics=trace.diagnostics._replace(execution_barriers=()))
    elif change == "diagnostic_producers":
        trace = trace._replace(diagnostics=trace.diagnostics._replace(producer_identities=()))
    elif change == "diagnostic_requirements":
        trace = trace._replace(diagnostics=trace.diagnostics._replace(requirement_identities=()))
    elif change == "diagnostic_history":
        trace = trace._replace(diagnostics=trace.diagnostics._replace(execution_outcomes=()))
    elif change == "diagnostic_trace":
        trace = trace._replace(diagnostics=trace.diagnostics._replace(execution_trace=()))
    elif change == "fatal_reason":
        trace = trace._replace(
            diagnostics=trace.diagnostics._replace(
                reasons=(
                    DiagnosticReason(
                        DiagnosticCode.INVALID_DEPENDENCY,
                        "tracking",
                        "invalid execution trace",
                    ),
                )
            )
        )
    elif change == "ordering":
        trace = trace._replace(execution_ordering=())
    elif change == "barriers":
        trace = trace._replace(execution_barriers=())
    elif change == "dependency_ordering":
        trace = trace._replace(dependency_ordering=())
    elif change == "requirements":
        trace = trace._replace(requirement_identities=())
    elif change == "producers":
        trace = trace._replace(producer_identities=())
    elif change == "history":
        trace = trace._replace(execution_history=trace.execution_history[:-1])
    elif change == "result_ordering":
        result = result._replace(execution_ordering=())
    elif change == "result_barriers":
        result = result._replace(execution_barriers=())
    elif change == "result_outcomes":
        result = result._replace(outcomes=())
    elif change == "dependency_binding":
        trace = trace._replace(diagnostics=trace.diagnostics._replace(dependency_identities=()))
    elif change == "broken_dependency":
        trace, result, schedule = _replace_dependencies(
            trace, result, schedule, (("requirement-a", "requirement-b"),)
        )
    elif change == "registry":
        snapshot = replace(snapshot, entries=snapshot.entries[:-1])
    elif change == "output_type":
        trace = trace._replace(
            execution_history=(
                (trace.execution_history[0][0], trace.execution_history[0][1], cast(Any, object())),
                *trace.execution_history[1:],
            )
        )
    elif change.startswith("output_"):
        output = trace.execution_history[0][2]
        if change == "output_manifest":
            output = replace(output, input_manifest_reference="other")
        elif change == "output_producer":
            output = replace(output, producer_identity="other")
        elif change == "output_version":
            output = replace(output, producer_version="2.0.0")
        elif change == "output_contract":
            output = replace(output, contract_version="2.0.0")
        elif change == "output_failure":
            output = replace(
                output,
                outcome="analytical_execution_failure",
                evidence_outputs=(),
                semantic_diagnostics=(("failure", "declared"),),
            )
        trace = trace._replace(
            execution_history=(
                (trace.execution_history[0][0], trace.execution_history[0][1], output),
                *trace.execution_history[1:],
            )
        )
    if change in {
        "ordering",
        "barriers",
        "dependency_ordering",
        "requirements",
        "producers",
        "history",
        "output_type",
        "output_manifest",
        "output_producer",
        "output_version",
        "output_contract",
        "output_failure",
    }:
        trace = trace._replace(
            diagnostics=trace.diagnostics._replace(
                execution_ordering=trace.execution_ordering,
                execution_barriers=trace.execution_barriers,
                producer_identities=trace.producer_identities,
                requirement_identities=trace.requirement_identities,
                execution_outcomes=trace.execution_history,
                execution_trace=trace.execution_history,
            )
        )
    report = LineageVerifier.verify(trace, result, schedule, snapshot, profile)
    assert not report.verified
    assert all(not verified for _, verified in report.verification_results)
    assert report.diagnostics.reasons[-1].code is DiagnosticCode.INVALID_DEPENDENCY


@pytest.mark.parametrize(
    "call",
    [
        lambda: LineageVerifier.verify(cast(Any, object()), *_fixture()[1:]),
        lambda: LineageVerifier.verify(_fixture()[0], cast(Any, object()), *_fixture()[2:]),
        lambda: LineageVerifier.verify(
            _fixture()[0], _fixture()[1], cast(Any, object()), *_fixture()[3:]
        ),
        lambda: LineageVerifier.verify(
            _fixture()[0], _fixture()[1], _fixture()[2], cast(Any, object()), _fixture()[4]
        ),
        lambda: LineageVerifier.verify(*_fixture()[:4], cast(Any, object())),
    ],
)
def test_invalid_input_models_fail_closed(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


def test_terminal_boundary_contains_no_forbidden_responsibilities() -> None:
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
        "track",
        "replay",
        "integrate_lifecycle",
    }
    methods = {
        name
        for owner in (LineageVerifier, LineageReport, LineageDiagnostics)
        for name, value in getmembers(owner)
        if isfunction(value) or callable(value)
    }
    assert forbidden.isdisjoint(methods)
