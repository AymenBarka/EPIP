"""Decision graph determinism, topology, validation, and replay tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from epip.decision.graph import (
    DecisionDependency,
    DecisionDependencyGraph,
    DecisionExecutionPlan,
    DecisionGraphAudit,
    DecisionGraphBuilder,
    DecisionGraphDigest,
    DecisionGraphEdge,
    DecisionGraphNode,
    DecisionGraphSnapshot,
    DecisionGraphValidator,
    DecisionNodeType,
    DecisionTopology,
)
from epip.decision.graph import DecisionGraph as LegacyDecisionGraph


def node(
    node_id: str,
    node_type: DecisionNodeType,
    *dependencies: str,
) -> DecisionGraphNode:
    return DecisionGraphNode(
        node_id,
        node_type,
        tuple(DecisionDependency(value) for value in dependencies),
    )


def graph() -> DecisionDependencyGraph:
    return (
        DecisionGraphBuilder()
        .add_node(node("evidence-b", DecisionNodeType.EVIDENCE))
        .add_node(node("candidate", DecisionNodeType.CANDIDATE, "scenario"))
        .add_node(node("evidence-a", DecisionNodeType.EVIDENCE))
        .add_node(
            node(
                "hypothesis",
                DecisionNodeType.HYPOTHESIS,
                "evidence-a",
                "evidence-b",
            )
        )
        .add_node(node("scenario", DecisionNodeType.SCENARIO, "hypothesis"))
        .connect("evidence-b", "hypothesis")
        .connect("hypothesis", "scenario")
        .connect("evidence-a", "hypothesis")
        .connect("scenario", "candidate")
        .build()
    )


def test_graph_is_immutable_ordered_and_discoverable() -> None:
    value = graph()
    assert tuple(item.node_id for item in value.nodes) == (
        "candidate",
        "evidence-a",
        "evidence-b",
        "hypothesis",
        "scenario",
    )
    assert value.node("hypothesis").node_type is DecisionNodeType.HYPOTHESIS
    with pytest.raises(KeyError):
        value.node("missing")
    with pytest.raises(FrozenInstanceError):
        value.nodes = ()  # type: ignore[misc]


def test_value_validation_and_node_types() -> None:
    assert {item.value for item in DecisionNodeType} == {
        "evidence",
        "hypothesis",
        "scenario",
        "constraint",
        "aggregation",
        "candidate",
    }
    for factory in (
        lambda: DecisionDependency(" "),
        lambda: DecisionGraphEdge("", "x"),
        lambda: DecisionGraphEdge("x", ""),
        lambda: DecisionGraphNode("", DecisionNodeType.EVIDENCE),
    ):
        with pytest.raises(ValueError):
            factory()
    with pytest.raises(TypeError):
        DecisionGraphNode("x", DecisionNodeType.EVIDENCE, label=1)  # type: ignore[arg-type]


def test_topology_queries_are_stable_and_immutable() -> None:
    topology = DecisionTopology.from_graph(graph())
    assert topology.roots == ("evidence-a", "evidence-b")
    assert topology.leaves == ("candidate",)
    assert topology.ancestors("candidate") == (
        "evidence-a",
        "evidence-b",
        "hypothesis",
        "scenario",
    )
    assert topology.descendants("evidence-a") == (
        "candidate",
        "hypothesis",
        "scenario",
    )
    assert topology.dependency_closure(("scenario",)) == (
        "evidence-a",
        "evidence-b",
        "hypothesis",
        "scenario",
    )
    assert topology.reverse_lookup("hypothesis") == ("scenario",)
    assert topology.reverse_lookup("unknown") == ()
    with pytest.raises(TypeError):
        topology.dependencies["x"] = ()  # type: ignore[index]


def test_execution_is_topological_and_lexically_stable() -> None:
    expected = (
        "evidence-a",
        "evidence-b",
        "hypothesis",
        "scenario",
        "candidate",
    )
    assert DecisionExecutionPlan.from_graph(graph()).node_ids == expected
    assert DecisionExecutionPlan.from_graph(graph()).node_ids == expected


def test_digest_snapshot_and_serialization_are_byte_deterministic() -> None:
    first = graph()
    second = DecisionDependencyGraph(tuple(reversed(first.nodes)), tuple(reversed(first.edges)))
    assert first.to_json() == second.to_json()
    assert DecisionGraphDigest.from_graph(first) == DecisionGraphDigest.from_graph(second)
    restored = DecisionDependencyGraph.from_json(first.to_json())
    assert restored == first
    snapshot = DecisionGraphSnapshot.capture(first)
    assert DecisionGraphSnapshot.from_json(snapshot.to_json()) == snapshot
    assert DecisionGraphSnapshot.capture(restored).to_json() == snapshot.to_json()


def test_serialization_rejects_versions_and_tampering() -> None:
    with pytest.raises(ValueError, match="graph version"):
        DecisionDependencyGraph.from_json('{"version":2}')
    snapshot = DecisionGraphSnapshot.capture(graph())
    with pytest.raises(ValueError, match="snapshot version"):
        DecisionGraphSnapshot.from_json('{"version":2}')
    tampered = snapshot.to_json().replace(snapshot.digest.value, "0" * 64)
    with pytest.raises(ValueError, match="integrity mismatch"):
        DecisionGraphSnapshot.from_json(tampered)
    tampered_plan = snapshot.to_json().replace('"candidate"]', '"wrong"]', 1)
    with pytest.raises(ValueError, match="integrity mismatch"):
        DecisionGraphSnapshot.from_json(tampered_plan)


def test_diagnostics_report_all_structural_failures_without_repair() -> None:
    invalid = DecisionDependencyGraph(
        nodes=(
            node("a", DecisionNodeType.EVIDENCE, "missing"),
            node("a", DecisionNodeType.HYPOTHESIS),
            node("orphan", DecisionNodeType.CONSTRAINT),
        ),
        edges=(
            DecisionGraphEdge("a", "a"),
            DecisionGraphEdge("a", "a"),
            DecisionGraphEdge("unknown", "a"),
        ),
    )
    diagnostics = DecisionGraphValidator.diagnose(invalid, require_single_root=True)
    assert diagnostics.duplicate_nodes == ("a",)
    assert diagnostics.duplicate_edges == ("a->a",)
    assert diagnostics.self_edges == ("a->a", "a->a")
    assert diagnostics.invalid_references == ("unknown->a",)
    assert "missing->a" in diagnostics.missing_dependencies
    assert "undeclared:a->a" in diagnostics.missing_dependencies
    assert diagnostics.orphan_nodes == ("orphan",)
    assert diagnostics.root_errors == ()
    assert not diagnostics.valid
    with pytest.raises(ValueError, match="invalid decision graph"):
        DecisionGraphValidator.validate(invalid, require_single_root=True)


def test_cycles_are_detected_and_execution_rejected() -> None:
    cyclic = DecisionDependencyGraph(
        (
            node("a", DecisionNodeType.AGGREGATION, "b"),
            node("b", DecisionNodeType.AGGREGATION, "a"),
        ),
        (DecisionGraphEdge("a", "b"), DecisionGraphEdge("b", "a")),
    )
    assert DecisionGraphValidator.diagnose(cyclic).cycles == ("a", "b")
    with pytest.raises(ValueError, match="invalid decision graph"):
        DecisionExecutionPlan.from_graph(cyclic)


def test_topology_walk_deduplicates_converging_paths() -> None:
    diamond = DecisionDependencyGraph(
        (
            node("a", DecisionNodeType.EVIDENCE),
            node("b", DecisionNodeType.HYPOTHESIS, "a"),
            node("c", DecisionNodeType.SCENARIO, "a"),
            node("d", DecisionNodeType.CANDIDATE, "b", "c"),
        ),
        (
            DecisionGraphEdge("a", "b"),
            DecisionGraphEdge("a", "c"),
            DecisionGraphEdge("b", "d"),
            DecisionGraphEdge("c", "d"),
        ),
    )
    assert DecisionTopology.from_graph(diamond).descendants("a") == ("b", "c", "d")


def test_builder_rejects_duplicate_self_invalid_and_missing_dependencies() -> None:
    cases = (
        DecisionDependencyGraph((node("a", DecisionNodeType.EVIDENCE),) * 2),
        DecisionDependencyGraph(
            (node("a", DecisionNodeType.EVIDENCE),), (DecisionGraphEdge("a", "a"),)
        ),
        DecisionDependencyGraph(
            (node("a", DecisionNodeType.EVIDENCE),), (DecisionGraphEdge("a", "b"),)
        ),
        DecisionDependencyGraph((node("a", DecisionNodeType.EVIDENCE, "b"),)),
        DecisionDependencyGraph(
            (node("a", DecisionNodeType.EVIDENCE), node("b", DecisionNodeType.HYPOTHESIS)),
            (DecisionGraphEdge("a", "b"),),
        ),
    )
    for value in cases:
        with pytest.raises(ValueError):
            DecisionGraphValidator.validate(value)
    builder = DecisionGraphBuilder().add_node(node("one", DecisionNodeType.EVIDENCE))
    assert builder.build(require_single_root=True).nodes[0].node_id == "one"


def test_orphan_policy_allows_a_single_node_and_configures_multiple_roots() -> None:
    single = DecisionDependencyGraph((node("only", DecisionNodeType.EVIDENCE),))
    assert DecisionGraphValidator.diagnose(single).valid
    multi_root = graph()
    assert DecisionGraphValidator.diagnose(multi_root).valid
    assert not DecisionGraphValidator.diagnose(multi_root, require_single_root=True).valid


def test_audit_reports_valid_and_invalid_graphs() -> None:
    valid = DecisionGraphAudit.inspect(graph())
    assert valid.statistics.node_count == 5
    assert valid.statistics.edge_count == 4
    assert valid.statistics.root_count == 2
    assert valid.statistics.leaf_count == 1
    assert valid.validation_failures == ()
    assert valid.execution_plan is not None

    invalid_graph = DecisionDependencyGraph(
        (node("a", DecisionNodeType.EVIDENCE), node("b", DecisionNodeType.HYPOTHESIS)),
    )
    invalid = DecisionGraphAudit.inspect(invalid_graph)
    assert invalid.validation_failures == ("a", "b")
    assert invalid.execution_plan is None


def test_legacy_graph_returns_none_when_a_relation_is_absent() -> None:
    legacy = LegacyDecisionGraph()
    assert legacy.previous("missing") is None
