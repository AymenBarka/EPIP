"""Component tests for A04-E06 deterministic declarative orchestration."""

from __future__ import annotations

from dataclasses import replace
from inspect import getmembers, isfunction
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError
from epip.evidence.graph import DependencyGraphBuilder
from epip.evidence.model import (
    DependencyType,
    DiagnosticCode,
    DiagnosticReason,
    EvidenceRequirement,
    ResolutionProfile,
)
from epip.evidence.orchestration import (
    ExecutionOrchestrator,
    ExecutionSchedule,
    OrchestrationDiagnostics,
)
from epip.evidence.resolution import ResolutionPlan, ResolutionPlanner
from epip.evidence.selection import SelectionDiagnostics
from epip.governance import GovernanceEpoch, RegistryEntry, RegistrySnapshot


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


def _snapshot(*entries: RegistryEntry) -> RegistrySnapshot:
    return RegistrySnapshot(
        "snapshot-1",
        "manifest-1",
        GovernanceEpoch(4),
        entries,
        ("action-1",),
        (("compatibility", "1.0.0"),),
    )


def _requirement(identity: str, **changes: object) -> EvidenceRequirement:
    values: dict[str, object] = {
        "requirement_id": identity,
        "evidence_type": "market.structure",
        "semantic_version": "1.0.0",
        "subject": "EURUSD",
        "scope": "H1",
        "dependency_type": DependencyType.MANDATORY,
    }
    values.update(changes)
    return EvidenceRequirement(**values)  # type: ignore[arg-type]


def _selection(entry: RegistryEntry) -> SelectionDiagnostics:
    return SelectionDiagnostics(
        "snapshot-1", "manifest-1", GovernanceEpoch(4), (entry,), (entry,), ()
    )


def _profile() -> ResolutionProfile:
    return ResolutionProfile("profile-1", "1.0.0")


def _plan(
    bindings: tuple[tuple[EvidenceRequirement, SelectionDiagnostics], ...] | None = None,
    edges: tuple[tuple[str, str], ...] | None = None,
) -> tuple[ResolutionPlan, RegistrySnapshot, ResolutionProfile]:
    actual_bindings = bindings or (
        (_requirement("requirement-c"), _selection(_entry("producer-c"))),
        (_requirement("requirement-a"), _selection(_entry("producer-a"))),
        (_requirement("requirement-b"), _selection(_entry("producer-b"))),
    )
    actual_edges = (
        edges
        if edges is not None
        else (
            ("requirement-c", "requirement-b"),
            ("requirement-b", "requirement-a"),
        )
    )
    entries = tuple(selection.selected_candidates[0] for _, selection in actual_bindings)
    snapshot = _snapshot(*entries)
    profile = _profile()
    graph = DependencyGraphBuilder.build(snapshot, actual_bindings, actual_edges)
    return ResolutionPlanner.plan(graph, profile, snapshot), snapshot, profile


def test_public_production_inventory_is_exact() -> None:
    from epip.evidence import orchestration

    public_classes = {
        name
        for name, value in vars(orchestration).items()
        if isinstance(value, type)
        if value.__module__ == orchestration.__name__ and not name.startswith("_")
    }
    assert public_classes == {
        "ExecutionOrchestrator",
        "ExecutionSchedule",
        "OrchestrationDiagnostics",
    }


def test_constructs_canonical_barrier_preserving_schedule() -> None:
    plan, snapshot, profile = _plan()
    schedule = ExecutionOrchestrator.orchestrate(plan, snapshot, profile)
    assert schedule.dependency_ordering == plan.dependency_ordering
    assert schedule.execution_layers == plan.execution_layers
    assert schedule.execution_barriers == (
        (0, (("requirement-a", "producer-a@1.0.0"),)),
        (1, (("requirement-b", "producer-b@1.0.0"),)),
        (2, (("requirement-c", "producer-c@1.0.0"),)),
    )
    assert schedule.scheduled_executions == (
        ("requirement-a", "producer-a@1.0.0"),
        ("requirement-b", "producer-b@1.0.0"),
        ("requirement-c", "producer-c@1.0.0"),
    )


def test_schedule_and_diagnostics_preserve_every_context() -> None:
    plan, snapshot, profile = _plan()
    schedule = ExecutionOrchestrator.orchestrate(plan, snapshot, profile)
    assert schedule[:5] == (
        "snapshot-1",
        "manifest-1",
        GovernanceEpoch(4),
        profile,
        plan,
    )
    diagnostics = schedule.diagnostics
    assert diagnostics.resolution_plan == plan
    assert diagnostics.dependency_graph == plan.dependency_graph
    assert diagnostics.execution_layers == plan.execution_layers
    assert diagnostics.execution_schedule == schedule.execution_barriers
    assert diagnostics.selected_candidates == plan.selected_candidates


def test_repeated_execution_and_input_permutations_are_identical() -> None:
    bindings = (
        (_requirement("requirement-a"), _selection(_entry("producer-a"))),
        (_requirement("requirement-b"), _selection(_entry("producer-b"))),
        (_requirement("requirement-c"), _selection(_entry("producer-c"))),
    )
    edges = (("requirement-c", "requirement-b"), ("requirement-b", "requirement-a"))
    expected: ExecutionSchedule | None = None
    for binding_order in permutations(bindings):
        for edge_order in permutations(edges):
            plan, snapshot, profile = _plan(binding_order, edge_order)
            actual = ExecutionOrchestrator.orchestrate(plan, snapshot, profile)
            if expected is None:
                expected = actual
            else:
                assert actual == expected
                assert hash(actual) == hash(expected)
    plan, snapshot, profile = _plan(bindings, edges)
    assert ExecutionOrchestrator.orchestrate(plan, snapshot, profile) == expected


def test_schedule_diagnostics_and_inputs_are_immutable_and_hashable() -> None:
    plan, snapshot, profile = _plan()
    inputs = (plan, snapshot, profile)
    hashes = tuple(hash(item) for item in inputs)
    schedule = ExecutionOrchestrator.orchestrate(plan, snapshot, profile)
    with pytest.raises(AttributeError):
        schedule.execution_barriers = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        schedule.diagnostics.reasons = ()  # type: ignore[misc]
    assert hash(schedule)
    assert hash(schedule.diagnostics)
    assert hashes == tuple(hash(item) for item in inputs)


def test_empty_optional_plan_remains_declarative() -> None:
    requirement = _requirement(
        "requirement-a",
        dependency_type=DependencyType.OPTIONAL,
        min_cardinality=0,
        absence_semantics="explicit-absence",
    )
    selection = SelectionDiagnostics("snapshot-1", "manifest-1", GovernanceEpoch(4), (), (), ())
    snapshot = _snapshot()
    profile = _profile()
    graph = DependencyGraphBuilder.build(snapshot, ((requirement, selection),))
    plan = ResolutionPlanner.plan(graph, profile, snapshot)
    schedule = ExecutionOrchestrator.orchestrate(plan, snapshot, profile)
    assert schedule.dependency_ordering == ("requirement-a",)
    assert schedule.execution_layers == ()
    assert schedule.execution_barriers == ()
    assert schedule.diagnostics.reasons == ()


@pytest.mark.parametrize(
    "change",
    [
        "snapshot",
        "profile",
        "diagnostic_context",
        "graph",
        "ordering_binding",
        "layer_binding",
        "candidate_binding",
        "requirements",
        "ordering_duplicate",
        "ordering_missing",
        "layer_order",
        "empty_layer",
        "schedule_duplicate",
        "schedule_missing",
        "dependency_order",
        "barrier_order",
        "fatal_reason",
    ],
)
def test_invalid_or_incomplete_plans_fail_closed(change: str) -> None:
    plan, snapshot, profile = _plan()
    diagnostics = plan.diagnostics
    if change == "snapshot":
        snapshot = replace(snapshot, manifest_reference="other")
    elif change == "profile":
        profile = ResolutionProfile("other", "1.0.0")
    elif change == "diagnostic_context":
        diagnostics = diagnostics._replace(snapshot_identity="other")
    elif change == "graph":
        diagnostics = diagnostics._replace(dependency_graph=cast(Any, object()))
    elif change == "ordering_binding":
        diagnostics = diagnostics._replace(dependency_ordering=())
    elif change == "layer_binding":
        diagnostics = diagnostics._replace(execution_layers=())
    elif change == "candidate_binding":
        diagnostics = diagnostics._replace(selected_candidate_identities=())
    elif change == "requirements":
        plan = plan._replace(selected_candidates=tuple(reversed(plan.selected_candidates)))
    elif change == "ordering_duplicate":
        plan = plan._replace(dependency_ordering=(*plan.dependency_ordering, "requirement-a"))
    elif change == "ordering_missing":
        plan = plan._replace(dependency_ordering=plan.dependency_ordering[:-1])
    elif change == "layer_order":
        plan = plan._replace(execution_layers=(tuple(reversed(plan.execution_layers[0])),))
    elif change == "empty_layer":
        plan = plan._replace(execution_layers=((), *plan.execution_layers))
    elif change == "schedule_duplicate":
        plan = plan._replace(execution_layers=(plan.execution_layers[0], *plan.execution_layers))
    elif change == "schedule_missing":
        plan = plan._replace(execution_layers=plan.execution_layers[:-1])
    elif change == "dependency_order":
        plan = plan._replace(dependency_ordering=tuple(reversed(plan.dependency_ordering)))
    elif change == "barrier_order":
        plan = plan._replace(execution_layers=tuple(reversed(plan.execution_layers)))
    elif change == "fatal_reason":
        diagnostics = diagnostics._replace(
            reasons=(
                DiagnosticReason(
                    DiagnosticCode.INVALID_DEPENDENCY,
                    "graph",
                    "invalid plan",
                ),
            )
        )
    if change in {
        "requirements",
        "ordering_duplicate",
        "ordering_missing",
        "layer_order",
        "empty_layer",
        "schedule_duplicate",
        "schedule_missing",
        "dependency_order",
        "barrier_order",
    }:
        diagnostics = diagnostics._replace(
            dependency_ordering=plan.dependency_ordering,
            execution_layers=plan.execution_layers,
            selected_candidate_identities=plan.selected_candidates,
        )
    plan = plan._replace(diagnostics=diagnostics)
    schedule = ExecutionOrchestrator.orchestrate(plan, snapshot, profile)
    assert schedule.dependency_ordering == ()
    assert schedule.execution_layers == ()
    assert schedule.execution_barriers == ()
    assert schedule.scheduled_executions == ()
    assert schedule.diagnostics.reasons[-1].code is DiagnosticCode.INVALID_DEPENDENCY


@pytest.mark.parametrize(
    "call",
    [
        lambda: ExecutionOrchestrator.orchestrate(cast(Any, object()), _snapshot(), _profile()),
        lambda: ExecutionOrchestrator.orchestrate(_plan()[0], cast(Any, object()), _profile()),
        lambda: ExecutionOrchestrator.orchestrate(_plan()[0], _plan()[1], cast(Any, object())),
    ],
)
def test_invalid_input_models_fail_closed(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


def test_no_predecessor_or_successor_responsibility_is_present() -> None:
    forbidden = {
        "enumerate",
        "filter",
        "select",
        "validate",
        "certify",
        "build",
        "execute",
        "aggregate",
        "canonical_identity",
        "replay",
        "track_execution",
        "integrate_lifecycle",
    }
    methods = {
        name
        for owner in (ExecutionOrchestrator, ExecutionSchedule, OrchestrationDiagnostics)
        for name, value in getmembers(owner)
        if isfunction(value) or callable(value)
    }
    assert forbidden.isdisjoint(methods)


def test_orchestration_imports_no_forbidden_services() -> None:
    from epip.evidence import orchestration

    names = vars(orchestration)
    for forbidden in (
        "EvidenceClaim",
        "CandidateEnumerator",
        "CandidateFilter",
        "SelectionEngine",
        "DependencyGraphBuilder",
        "ResolutionPlanner",
        "CompatibilityEvaluator",
        "SemanticValidator",
        "CertificationRecord",
    ):
        assert forbidden not in names


def test_orchestration_uses_only_frozen_e00_diagnostics() -> None:
    plan, snapshot, profile = _plan()
    invalid = plan._replace(dependency_ordering=())
    schedule = ExecutionOrchestrator.orchestrate(invalid, snapshot, profile)
    assert all(
        isinstance(reason, DiagnosticReason) and isinstance(reason.code, DiagnosticCode)
        for reason in schedule.diagnostics.reasons
    )
