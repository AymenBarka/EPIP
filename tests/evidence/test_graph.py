"""Component tests for A04-E04 deterministic dependency graphs."""

from __future__ import annotations

from inspect import getmembers, isfunction
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError
from epip.evidence.graph import DependencyDiagnostics, DependencyGraph, DependencyGraphBuilder
from epip.evidence.model import (
    DependencyType,
    DiagnosticCode,
    DiagnosticReason,
    EvidenceRequirement,
)
from epip.evidence.selection import SelectionDiagnostics
from epip.governance import GovernanceEpoch, RegistryEntry, RegistrySnapshot


def _entry(producer: str) -> RegistryEntry:
    return RegistryEntry(
        producer,
        "1.0.0",
        f"descriptor-{producer}",
        "owner-1",
        "1.0.0",
        f"build-{producer}",
        (("market.structure", "1.0.0"),),
        "Trusted",
        (),
        (),
        "Enabled",
        ("admission-1",),
    )


def _snapshot() -> RegistrySnapshot:
    return RegistrySnapshot(
        "snapshot-1",
        "manifest-1",
        GovernanceEpoch(4),
        (),
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


def _selection(
    *entries: RegistryEntry,
    diagnostics: tuple[DiagnosticReason, ...] = (),
    snapshot_identity: str = "snapshot-1",
    manifest_reference: str = "manifest-1",
    epoch: GovernanceEpoch | None = None,
) -> SelectionDiagnostics:
    ordered = tuple(sorted(entries, key=lambda item: item.producer_identity))
    return SelectionDiagnostics(
        snapshot_identity,
        manifest_reference,
        epoch or GovernanceEpoch(4),
        ordered,
        ordered,
        diagnostics,
    )


def _binding(
    identity: str, *entries: RegistryEntry, **changes: object
) -> tuple[EvidenceRequirement, SelectionDiagnostics]:
    return (_requirement(identity, **changes), _selection(*entries))


def test_public_production_inventory_is_exact() -> None:
    from epip.evidence import graph

    public_classes = {
        name
        for name, value in vars(graph).items()
        if isinstance(value, type)
        if value.__module__ == graph.__name__ and not name.startswith("_")
    }
    assert public_classes == {
        "DependencyGraphBuilder",
        "DependencyGraph",
        "DependencyDiagnostics",
    }


def test_builds_expanded_graph_with_canonical_order() -> None:
    first = _binding("requirement-a", _entry("producer-b"), _entry("producer-a"))
    second = _binding("requirement-b", _entry("producer-c"))
    graph = DependencyGraphBuilder.build(
        _snapshot(),
        (second, first),
        (("requirement-b", "requirement-a"),),
    )
    assert graph.nodes == (
        "provider:producer-a@1.0.0",
        "provider:producer-b@1.0.0",
        "provider:producer-c@1.0.0",
        "requirement:requirement-a",
        "requirement:requirement-b",
    )
    assert graph.edges == (
        ("requirement:requirement-a", "provider:producer-a@1.0.0"),
        ("requirement:requirement-a", "provider:producer-b@1.0.0"),
        ("requirement:requirement-b", "provider:producer-c@1.0.0"),
        ("requirement:requirement-b", "requirement:requirement-a"),
    )
    assert graph.selected_candidates == (
        ("requirement-a", ("producer-a@1.0.0", "producer-b@1.0.0")),
        ("requirement-b", ("producer-c@1.0.0",)),
    )
    assert graph.diagnostics.reasons == ()


def test_duplicate_edges_are_eliminated() -> None:
    binding = _binding("requirement-a", _entry("producer-a"))
    graph = DependencyGraphBuilder.build(
        _snapshot(),
        (binding,),
        (("requirement-a", "requirement-a"), ("requirement-a", "requirement-a")),
    )
    assert graph.edges == ()
    assert graph.diagnostics.reasons[-1].code is DiagnosticCode.CYCLIC_DEPENDENCY


def test_duplicate_provider_edges_are_eliminated_by_identity() -> None:
    selection = _selection(_entry("producer-a"), _entry("producer-a"))
    graph = DependencyGraphBuilder.build(_snapshot(), ((_requirement("requirement-a"), selection),))
    assert graph.edges == (("requirement:requirement-a", "provider:producer-a@1.0.0"),)


def test_cycle_detection_fails_closed_deterministically() -> None:
    bindings = (
        _binding("requirement-b", _entry("producer-b")),
        _binding("requirement-a", _entry("producer-a")),
    )
    edges = (("requirement-a", "requirement-b"), ("requirement-b", "requirement-a"))
    first = DependencyGraphBuilder.build(_snapshot(), bindings, edges)
    second = DependencyGraphBuilder.build(
        _snapshot(), tuple(reversed(bindings)), tuple(reversed(edges))
    )
    assert first == second
    assert first.nodes == ()
    assert first.edges == ()
    assert first.diagnostics.reasons[-1].code is DiagnosticCode.CYCLIC_DEPENDENCY
    assert first.diagnostics.reasons[-1].requirement_id == "requirement-a"


def test_missing_mandatory_dependency_fails_closed() -> None:
    graph = DependencyGraphBuilder.build(_snapshot(), (_binding("requirement-a"),))
    assert graph.nodes == ()
    assert graph.edges == ()
    assert graph.diagnostics.reasons[-1].code is DiagnosticCode.MISSING_MANDATORY_DEPENDENCY


def test_optional_absence_remains_declarative() -> None:
    graph = DependencyGraphBuilder.build(
        _snapshot(),
        (
            _binding(
                "requirement-a",
                dependency_type=DependencyType.OPTIONAL,
                min_cardinality=0,
                absence_semantics="explicit-absence",
            ),
        ),
    )
    assert graph.nodes == ("requirement:requirement-a",)
    assert graph.edges == ()


@pytest.mark.parametrize(
    "edge",
    [
        (("missing", "requirement-a"),),
        (("requirement-a", "missing"),),
        (("missing-left", "missing-right"),),
    ],
)
def test_missing_edge_endpoints_fail_closed(edge: tuple[tuple[str, str], ...]) -> None:
    graph = DependencyGraphBuilder.build(
        _snapshot(), (_binding("requirement-a", _entry("producer-a")),), edge
    )
    assert graph.nodes == ()
    assert graph.edges == ()
    assert graph.diagnostics.reasons[-1].code is DiagnosticCode.INVALID_DEPENDENCY


@pytest.mark.parametrize(
    "selection_changes",
    [
        {"snapshot_identity": "other-snapshot"},
        {"manifest_reference": "other-manifest"},
        {"epoch": GovernanceEpoch(3)},
    ],
)
def test_mismatched_selection_context_fails_closed(
    selection_changes: dict[str, object],
) -> None:
    selection = _selection(_entry("producer-a"), **selection_changes)  # type: ignore[arg-type]
    graph = DependencyGraphBuilder.build(_snapshot(), ((_requirement("requirement-a"), selection),))
    assert graph.nodes == ()
    assert graph.edges == ()
    assert graph.diagnostics.reasons[-1].code is DiagnosticCode.INVALID_DEPENDENCY


def test_prior_diagnostics_and_context_are_preserved() -> None:
    prior = DiagnosticReason(
        DiagnosticCode.INELIGIBLE_PROVIDER,
        "requirement-a",
        "prior rejection",
        "producer-z",
        "1.0.0",
    )
    selection = _selection(_entry("producer-a"), diagnostics=(prior,))
    graph = DependencyGraphBuilder.build(_snapshot(), ((_requirement("requirement-a"), selection),))
    assert graph[:3] == ("snapshot-1", "manifest-1", GovernanceEpoch(4))
    assert graph.diagnostics == DependencyDiagnostics(
        "snapshot-1",
        "manifest-1",
        GovernanceEpoch(4),
        ("requirement-a",),
        (("requirement-a", ("producer-a@1.0.0",)),),
        (),
        ("provider:producer-a@1.0.0", "requirement:requirement-a"),
        (("requirement:requirement-a", "provider:producer-a@1.0.0"),),
        (prior,),
    )


def test_diagnostics_are_independently_self_contained() -> None:
    graph = DependencyGraphBuilder.build(
        _snapshot(),
        (
            _binding("requirement-b", _entry("producer-b")),
            _binding("requirement-a", _entry("producer-a")),
        ),
        (("requirement-b", "requirement-a"),),
    )
    diagnostics = graph.diagnostics
    assert diagnostics.snapshot_identity == "snapshot-1"
    assert diagnostics.manifest_reference == "manifest-1"
    assert diagnostics.governance_epoch == GovernanceEpoch(4)
    assert diagnostics.requirement_identities == ("requirement-a", "requirement-b")
    assert diagnostics.selected_candidate_identities == graph.selected_candidates
    assert diagnostics.dependency_identities == (("requirement-b", "requirement-a"),)
    assert diagnostics.graph_nodes == graph.nodes
    assert diagnostics.graph_edges == graph.edges


def test_fail_closed_diagnostics_preserve_unconditional_context() -> None:
    graph = DependencyGraphBuilder.build(
        _snapshot(),
        (_binding("requirement-a", _entry("producer-a")),),
        (("missing", "requirement-a"),),
    )
    assert graph.nodes == ()
    assert graph.edges == ()
    assert graph.diagnostics.requirement_identities == ("requirement-a",)
    assert graph.diagnostics.selected_candidate_identities == (
        ("requirement-a", ("producer-a@1.0.0",)),
    )
    assert graph.diagnostics.dependency_identities == (("missing", "requirement-a"),)
    assert graph.diagnostics.graph_nodes == ()
    assert graph.diagnostics.graph_edges == ()


def test_graph_and_diagnostics_are_immutable_and_hashable() -> None:
    graph = DependencyGraphBuilder.build(
        _snapshot(), (_binding("requirement-a", _entry("producer-a")),)
    )
    with pytest.raises(AttributeError):
        graph.nodes = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        graph.diagnostics.reasons = ()  # type: ignore[misc]
    assert hash(graph)
    assert hash(graph.diagnostics)


def test_input_permutations_and_repeated_execution_are_identical() -> None:
    bindings = (
        _binding("requirement-a", _entry("producer-a")),
        _binding("requirement-b", _entry("producer-b")),
        _binding("requirement-c", _entry("producer-c")),
    )
    edges = (
        ("requirement-c", "requirement-b"),
        ("requirement-b", "requirement-a"),
    )
    expected: DependencyGraph | None = None
    for binding_order in permutations(bindings):
        for edge_order in permutations(edges):
            graph = DependencyGraphBuilder.build(_snapshot(), binding_order, edge_order)
            if expected is None:
                expected = graph
            else:
                assert graph == expected
    assert DependencyGraphBuilder.build(_snapshot(), bindings, edges) == expected


def test_diagnostics_are_permutation_invariant_and_hash_identical() -> None:
    bindings = (
        _binding("requirement-a", _entry("producer-a")),
        _binding("requirement-b", _entry("producer-b")),
        _binding("requirement-c", _entry("producer-c")),
    )
    edges = (
        ("requirement-c", "requirement-b"),
        ("requirement-b", "requirement-a"),
    )
    expected = DependencyGraphBuilder.build(_snapshot(), bindings, edges).diagnostics
    for binding_order in permutations(bindings):
        for edge_order in permutations(edges):
            actual = DependencyGraphBuilder.build(
                _snapshot(), binding_order, edge_order
            ).diagnostics
            assert actual == expected
            assert hash(actual) == hash(expected)


def test_shared_prerequisite_remains_acyclic() -> None:
    bindings = (
        _binding("requirement-a", _entry("producer-a")),
        _binding("requirement-b", _entry("producer-b")),
        _binding("requirement-c", _entry("producer-c")),
    )
    graph = DependencyGraphBuilder.build(
        _snapshot(),
        bindings,
        (
            ("requirement-b", "requirement-a"),
            ("requirement-c", "requirement-a"),
        ),
    )
    assert graph.diagnostics.reasons == ()
    assert graph.nodes


def test_every_immutable_input_is_preserved() -> None:
    snapshot = _snapshot()
    bindings = (_binding("requirement-a", _entry("producer-a")),)
    edges = (("requirement-a", "requirement-a"),)
    inputs = (snapshot, bindings, edges)
    hashes = tuple(hash(item) for item in inputs)
    DependencyGraphBuilder.build(snapshot, bindings, edges)
    assert hashes == tuple(hash(item) for item in inputs)


@pytest.mark.parametrize(
    "call",
    [
        lambda: DependencyGraphBuilder.build(cast(Any, object()), ()),
        lambda: DependencyGraphBuilder.build(_snapshot(), cast(Any, [])),
        lambda: DependencyGraphBuilder.build(_snapshot(), cast(Any, ((object(),),))),
        lambda: DependencyGraphBuilder.build(_snapshot(), (), cast(Any, [])),
        lambda: DependencyGraphBuilder.build(_snapshot(), (), cast(Any, (("", "x"),))),
        lambda: DependencyGraphBuilder.build(
            _snapshot(),
            (
                _binding("requirement-a", _entry("producer-a")),
                _binding("requirement-a", _entry("producer-b")),
            ),
        ),
    ],
)
def test_invalid_inputs_fail_closed(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


def test_no_predecessor_or_successor_responsibility_is_present() -> None:
    forbidden = {
        "enumerate",
        "filter",
        "select",
        "rank",
        "validate",
        "certify",
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
        for owner in (DependencyGraphBuilder, DependencyGraph, DependencyDiagnostics)
        for name, value in getmembers(owner)
        if isfunction(value) or callable(value)
    }
    assert forbidden.isdisjoint(methods)


def test_graph_imports_no_forbidden_services_or_evidence() -> None:
    from epip.evidence import graph

    names = vars(graph)
    for forbidden in (
        "EvidenceClaim",
        "CandidateFilter",
        "CandidateEnumerator",
        "SelectionEngine",
        "CompatibilityEvaluator",
        "SemanticValidator",
        "CertificationRecord",
        "CompatibilityDecision",
    ):
        assert forbidden not in names


def test_graph_uses_only_frozen_e00_diagnostics() -> None:
    graph = DependencyGraphBuilder.build(_snapshot(), (_binding("requirement-a"),))
    assert all(
        isinstance(reason, DiagnosticReason) and isinstance(reason.code, DiagnosticCode)
        for reason in graph.diagnostics.reasons
    )
