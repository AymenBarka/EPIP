"""Component tests for A04-E05 deterministic dependency-resolution planning."""

from __future__ import annotations

from dataclasses import replace
from inspect import getmembers, isfunction
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError
from epip.evidence.graph import DependencyGraph, DependencyGraphBuilder
from epip.evidence.model import (
    DependencyType,
    DiagnosticCode,
    DiagnosticReason,
    EvidenceRequirement,
    ResolutionProfile,
)
from epip.evidence.resolution import ResolutionDiagnostics, ResolutionPlan, ResolutionPlanner
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
        "snapshot-1",
        "manifest-1",
        GovernanceEpoch(4),
        (entry,),
        (entry,),
        (),
    )


def _profile() -> ResolutionProfile:
    return ResolutionProfile("profile-1", "1.0.0")


def _graph(
    bindings: tuple[tuple[EvidenceRequirement, SelectionDiagnostics], ...],
    edges: tuple[tuple[str, str], ...] = (),
) -> tuple[DependencyGraph, RegistrySnapshot]:
    entries = tuple(selection.selected_candidates[0] for _, selection in bindings)
    snapshot = _snapshot(*entries)
    return DependencyGraphBuilder.build(snapshot, bindings, edges), snapshot


def _chain() -> tuple[DependencyGraph, RegistrySnapshot]:
    return _graph(
        (
            (_requirement("requirement-c"), _selection(_entry("producer-c"))),
            (_requirement("requirement-a"), _selection(_entry("producer-a"))),
            (_requirement("requirement-b"), _selection(_entry("producer-b"))),
        ),
        (("requirement-c", "requirement-b"), ("requirement-b", "requirement-a")),
    )


def test_public_production_inventory_is_exact() -> None:
    from epip.evidence import resolution

    public_classes = {
        name
        for name, value in vars(resolution).items()
        if isinstance(value, type)
        if value.__module__ == resolution.__name__ and not name.startswith("_")
    }
    assert public_classes == {"ResolutionPlanner", "ResolutionPlan", "ResolutionDiagnostics"}


def test_plans_dependency_safe_canonical_layers() -> None:
    graph, snapshot = _chain()
    plan = ResolutionPlanner.plan(graph, _profile(), snapshot)
    assert plan.dependency_ordering == (
        "requirement-a",
        "requirement-b",
        "requirement-c",
    )
    assert plan.execution_layers == (
        (("requirement-a", "producer-a@1.0.0"),),
        (("requirement-b", "producer-b@1.0.0"),),
        (("requirement-c", "producer-c@1.0.0"),),
    )


def test_independent_requirements_share_one_sorted_layer() -> None:
    graph, snapshot = _graph(
        (
            (_requirement("requirement-b"), _selection(_entry("producer-b"))),
            (_requirement("requirement-a"), _selection(_entry("producer-a"))),
        )
    )
    plan = ResolutionPlanner.plan(graph, _profile(), snapshot)
    assert plan.dependency_ordering == ("requirement-a", "requirement-b")
    assert plan.execution_layers == (
        (
            ("requirement-a", "producer-a@1.0.0"),
            ("requirement-b", "producer-b@1.0.0"),
        ),
    )


def test_graph_and_every_planning_context_are_preserved() -> None:
    graph, snapshot = _chain()
    profile = _profile()
    plan = ResolutionPlanner.plan(graph, profile, snapshot)
    assert plan[:5] == (
        "snapshot-1",
        "manifest-1",
        GovernanceEpoch(4),
        profile,
        graph,
    )
    assert plan.selected_candidates == graph.selected_candidates
    assert plan.diagnostics.dependency_graph == graph
    assert plan.diagnostics.requirement_identities == graph.diagnostics.requirement_identities
    assert plan.diagnostics.selected_candidate_identities == graph.selected_candidates
    assert plan.diagnostics.dependency_ordering == plan.dependency_ordering
    assert plan.diagnostics.execution_layers == plan.execution_layers


def test_repeated_execution_and_input_permutations_are_identical() -> None:
    bindings = (
        (_requirement("requirement-a"), _selection(_entry("producer-a"))),
        (_requirement("requirement-b"), _selection(_entry("producer-b"))),
        (_requirement("requirement-c"), _selection(_entry("producer-c"))),
    )
    edges = (("requirement-c", "requirement-b"), ("requirement-b", "requirement-a"))
    expected: ResolutionPlan | None = None
    for binding_order in permutations(bindings):
        for edge_order in permutations(edges):
            graph, snapshot = _graph(binding_order, edge_order)
            actual = ResolutionPlanner.plan(graph, _profile(), snapshot)
            if expected is None:
                expected = actual
            else:
                assert actual == expected
                assert hash(actual) == hash(expected)
    graph, snapshot = _graph(bindings, edges)
    assert ResolutionPlanner.plan(graph, _profile(), snapshot) == expected


def test_plan_diagnostics_and_inputs_are_immutable_and_hashable() -> None:
    graph, snapshot = _chain()
    profile = _profile()
    inputs = (graph, snapshot, profile)
    hashes = tuple(hash(item) for item in inputs)
    plan = ResolutionPlanner.plan(graph, profile, snapshot)
    with pytest.raises(AttributeError):
        plan.execution_layers = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        plan.diagnostics.reasons = ()  # type: ignore[misc]
    assert hash(plan)
    assert hash(plan.diagnostics)
    assert hashes == tuple(hash(item) for item in inputs)


def test_optional_empty_requirement_does_not_create_an_execution_binding() -> None:
    requirement = _requirement(
        "requirement-a",
        dependency_type=DependencyType.OPTIONAL,
        min_cardinality=0,
        absence_semantics="explicit-absence",
    )
    selection = SelectionDiagnostics("snapshot-1", "manifest-1", GovernanceEpoch(4), (), (), ())
    snapshot = _snapshot()
    graph = DependencyGraphBuilder.build(snapshot, ((requirement, selection),))
    plan = ResolutionPlanner.plan(graph, _profile(), snapshot)
    assert plan.dependency_ordering == ("requirement-a",)
    assert plan.execution_layers == ()


def test_invalid_e04_graph_is_rejected_and_diagnostics_are_preserved() -> None:
    binding = (_requirement("requirement-a"), _selection(_entry("producer-a")))
    graph, snapshot = _graph((binding,), (("requirement-a", "requirement-a"),))
    plan = ResolutionPlanner.plan(graph, _profile(), snapshot)
    assert plan.dependency_ordering == ()
    assert plan.execution_layers == ()
    assert graph.diagnostics.reasons[0] in plan.diagnostics.reasons
    assert plan.diagnostics.reasons[-1].code is DiagnosticCode.CYCLIC_DEPENDENCY


@pytest.mark.parametrize(
    "change",
    [
        "context",
        "diagnostic_context",
        "nodes",
        "edges",
        "selection_order",
        "diagnostic_nodes",
        "diagnostic_edges",
        "diagnostic_candidates",
        "requirements",
        "dependency_order",
        "topology_nodes",
        "topology_edges",
        "dependency_endpoint",
        "registry_binding",
        "cycle",
    ],
)
def test_incomplete_or_invalid_graphs_fail_closed(change: str) -> None:
    graph, snapshot = _chain()
    diagnostics = graph.diagnostics
    if change == "context":
        snapshot = replace(snapshot, snapshot_identity="other")
    elif change == "diagnostic_context":
        diagnostics = diagnostics._replace(manifest_reference="other")
    elif change == "nodes":
        graph = graph._replace(nodes=tuple(reversed(graph.nodes)))
    elif change == "edges":
        graph = graph._replace(edges=(*graph.edges, graph.edges[0]))
    elif change == "selection_order":
        graph = graph._replace(selected_candidates=tuple(reversed(graph.selected_candidates)))
    elif change == "diagnostic_nodes":
        diagnostics = diagnostics._replace(graph_nodes=())
    elif change == "diagnostic_edges":
        diagnostics = diagnostics._replace(graph_edges=())
    elif change == "diagnostic_candidates":
        diagnostics = diagnostics._replace(selected_candidate_identities=())
    elif change == "requirements":
        diagnostics = diagnostics._replace(requirement_identities=("missing",))
    elif change == "dependency_order":
        diagnostics = diagnostics._replace(
            dependency_identities=tuple(reversed(diagnostics.dependency_identities))
        )
    elif change == "topology_nodes":
        graph = graph._replace(nodes=graph.nodes[:-1])
        diagnostics = diagnostics._replace(graph_nodes=graph.nodes)
    elif change == "topology_edges":
        graph = graph._replace(edges=graph.edges[:-1])
        diagnostics = diagnostics._replace(graph_edges=graph.edges)
    elif change == "dependency_endpoint":
        diagnostics = diagnostics._replace(dependency_identities=(("requirement-a", "missing"),))
    elif change == "registry_binding":
        snapshot = _snapshot()
    elif change == "cycle":
        cycle_edges = (
            ("requirement-a", "requirement-b"),
            ("requirement-b", "requirement-a"),
            ("requirement-c", "requirement-b"),
        )
        graph_edges = tuple(
            sorted(
                {
                    edge
                    for edge in graph.edges
                    if not (
                        edge[0].startswith("requirement:") and edge[1].startswith("requirement:")
                    )
                }
                | {
                    (f"requirement:{source}", f"requirement:{target}")
                    for source, target in cycle_edges
                }
            )
        )
        diagnostics = diagnostics._replace(
            dependency_identities=cycle_edges,
            graph_edges=graph_edges,
        )
        graph = graph._replace(edges=graph_edges)
    graph = graph._replace(diagnostics=diagnostics)
    plan = ResolutionPlanner.plan(graph, _profile(), snapshot)
    assert plan.dependency_ordering == ()
    assert plan.execution_layers == ()
    assert plan.diagnostics.reasons[-1].code in {
        DiagnosticCode.INVALID_DEPENDENCY,
        DiagnosticCode.INELIGIBLE_PROVIDER,
        DiagnosticCode.CYCLIC_DEPENDENCY,
    }


@pytest.mark.parametrize(
    "call",
    [
        lambda: ResolutionPlanner.plan(cast(Any, object()), _profile(), _snapshot()),
        lambda: ResolutionPlanner.plan(_chain()[0], cast(Any, object()), _chain()[1]),
        lambda: ResolutionPlanner.plan(_chain()[0], _profile(), cast(Any, object())),
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
        "canonical_identity",
        "orchestrate",
        "execute",
        "schedule",
        "replay",
        "track_execution",
        "integrate_lifecycle",
    }
    methods = {
        name
        for owner in (ResolutionPlanner, ResolutionPlan, ResolutionDiagnostics)
        for name, value in getmembers(owner)
        if isfunction(value) or callable(value)
    }
    assert forbidden.isdisjoint(methods)


def test_resolution_imports_no_forbidden_services() -> None:
    from epip.evidence import resolution

    names = vars(resolution)
    for forbidden in (
        "EvidenceClaim",
        "CandidateEnumerator",
        "CandidateFilter",
        "SelectionEngine",
        "DependencyGraphBuilder",
        "CompatibilityEvaluator",
        "SemanticValidator",
        "CertificationRecord",
    ):
        assert forbidden not in names


def test_resolution_uses_only_frozen_e00_diagnostics() -> None:
    graph, snapshot = _chain()
    invalid = graph._replace(nodes=())
    plan = ResolutionPlanner.plan(invalid, _profile(), snapshot)
    assert all(
        isinstance(reason, DiagnosticReason) and isinstance(reason.code, DiagnosticCode)
        for reason in plan.diagnostics.reasons
    )
