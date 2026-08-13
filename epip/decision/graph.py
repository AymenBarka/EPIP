"""Deterministic, immutable decision dependency graph for EPIP-016."""

from __future__ import annotations

import hashlib
import heapq
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from epip.core.integrity import RelationshipIntegrityError
from epip.decision.models import DecisionSnapshot


class DecisionNodeType(StrEnum):
    """Structural role of a decision-graph node."""

    EVIDENCE = "evidence"
    HYPOTHESIS = "hypothesis"
    SCENARIO = "scenario"
    CONSTRAINT = "constraint"
    AGGREGATION = "aggregation"
    CANDIDATE = "candidate"


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True, slots=True, order=True)
class DecisionDependency:
    """Explicit dependency declared by a node."""

    node_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", _text(self.node_id, "node_id"))


@dataclass(frozen=True, slots=True)
class DecisionGraphNode:
    """Immutable structural node; its payload remains external to the graph."""

    node_id: str
    node_type: DecisionNodeType
    dependencies: tuple[DecisionDependency, ...] = ()
    label: str = ""
    reference: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", _text(self.node_id, "node_id"))
        object.__setattr__(self, "node_type", DecisionNodeType(self.node_type))
        object.__setattr__(self, "dependencies", tuple(sorted(self.dependencies)))
        if not isinstance(self.label, str) or not isinstance(self.reference, str):
            raise TypeError("label and reference must be strings")


@dataclass(frozen=True, slots=True, order=True)
class DecisionGraphEdge:
    """Directed dependency edge from prerequisite to dependent node."""

    source_id: str
    target_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id"))
        object.__setattr__(self, "target_id", _text(self.target_id, "target_id"))


def _node_payload(node: DecisionGraphNode) -> dict[str, Any]:
    return {
        "dependencies": [item.node_id for item in node.dependencies],
        "label": node.label,
        "node_id": node.node_id,
        "node_type": node.node_type.value,
        "reference": node.reference,
    }


def _graph_payload(
    nodes: tuple[DecisionGraphNode, ...], edges: tuple[DecisionGraphEdge, ...]
) -> dict[str, Any]:
    return {
        "edges": [{"source_id": edge.source_id, "target_id": edge.target_id} for edge in edges],
        "nodes": [_node_payload(node) for node in nodes],
        "version": 1,
    }


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


@dataclass(frozen=True, slots=True)
class DecisionDependencyGraph:
    """Immutable deterministic directed acyclic decision graph."""

    nodes: tuple[DecisionGraphNode, ...]
    edges: tuple[DecisionGraphEdge, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodes", tuple(sorted(self.nodes, key=lambda item: item.node_id)))
        object.__setattr__(self, "edges", tuple(sorted(self.edges)))

    def node(self, node_id: str) -> DecisionGraphNode:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        raise KeyError(node_id)

    def to_json(self) -> str:
        return _canonical_json(_graph_payload(self.nodes, self.edges))

    @classmethod
    def from_json(cls, value: str) -> DecisionDependencyGraph:
        payload = json.loads(value)
        if payload.get("version") != 1:
            raise ValueError("unsupported decision graph version")
        nodes = tuple(
            DecisionGraphNode(
                node_id=item["node_id"],
                node_type=DecisionNodeType(item["node_type"]),
                dependencies=tuple(DecisionDependency(node_id) for node_id in item["dependencies"]),
                label=item["label"],
                reference=item["reference"],
            )
            for item in payload["nodes"]
        )
        edges = tuple(DecisionGraphEdge(**item) for item in payload["edges"])
        graph = cls(nodes=nodes, edges=edges)
        DecisionGraphValidator.validate(graph)
        return graph


def _index(graph: DecisionDependencyGraph) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    outgoing: dict[str, set[str]] = {node.node_id: set() for node in graph.nodes}
    incoming: dict[str, set[str]] = {node.node_id: set() for node in graph.nodes}
    for edge in graph.edges:
        if edge.source_id in outgoing and edge.target_id in incoming:
            outgoing[edge.source_id].add(edge.target_id)
            incoming[edge.target_id].add(edge.source_id)
    return outgoing, incoming


def _walk(seed: str, adjacency: Mapping[str, set[str]]) -> tuple[str, ...]:
    seen: set[str] = set()
    pending = sorted(adjacency.get(seed, ()), reverse=True)
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(sorted(adjacency.get(current, ()), reverse=True))
    return tuple(sorted(seen))


@dataclass(frozen=True, slots=True)
class DecisionTopology:
    """Immutable topology derived solely from graph edges."""

    roots: tuple[str, ...]
    leaves: tuple[str, ...]
    dependencies: Mapping[str, tuple[str, ...]] = field(hash=False, compare=False)
    dependents: Mapping[str, tuple[str, ...]] = field(hash=False, compare=False)

    @classmethod
    def from_graph(cls, graph: DecisionDependencyGraph) -> DecisionTopology:
        outgoing, incoming = _index(graph)
        return cls(
            roots=tuple(sorted(key for key, value in incoming.items() if not value)),
            leaves=tuple(sorted(key for key, value in outgoing.items() if not value)),
            dependencies=MappingProxyType(
                {key: tuple(sorted(value)) for key, value in sorted(incoming.items())}
            ),
            dependents=MappingProxyType(
                {key: tuple(sorted(value)) for key, value in sorted(outgoing.items())}
            ),
        )

    def ancestors(self, node_id: str) -> tuple[str, ...]:
        return _walk(node_id, {key: set(value) for key, value in self.dependencies.items()})

    def descendants(self, node_id: str) -> tuple[str, ...]:
        return _walk(node_id, {key: set(value) for key, value in self.dependents.items()})

    def dependency_closure(self, node_ids: Iterable[str]) -> tuple[str, ...]:
        values = set(node_ids)
        for node_id in tuple(values):
            values.update(self.ancestors(node_id))
        return tuple(sorted(values))

    def reverse_lookup(self, node_id: str) -> tuple[str, ...]:
        return self.dependents.get(node_id, ())


@dataclass(frozen=True, slots=True)
class DecisionExecutionPlan:
    """Stable topological sequence for deterministic graph execution."""

    node_ids: tuple[str, ...]

    @classmethod
    def from_graph(cls, graph: DecisionDependencyGraph) -> DecisionExecutionPlan:
        DecisionGraphValidator.validate(graph)
        outgoing, incoming = _index(graph)
        degrees = {key: len(value) for key, value in incoming.items()}
        ready = [key for key, value in degrees.items() if value == 0]
        heapq.heapify(ready)
        ordered: list[str] = []
        while ready:
            current = heapq.heappop(ready)
            ordered.append(current)
            for target in sorted(outgoing[current]):
                degrees[target] -= 1
                if degrees[target] == 0:
                    heapq.heappush(ready, target)
        return cls(tuple(ordered))


@dataclass(frozen=True, slots=True)
class DecisionGraphDigest:
    """Canonical SHA-256 digest of graph content and execution order."""

    value: str

    @classmethod
    def from_graph(cls, graph: DecisionDependencyGraph) -> DecisionGraphDigest:
        plan = DecisionExecutionPlan.from_graph(graph)
        payload = _graph_payload(graph.nodes, graph.edges)
        payload["execution_order"] = list(plan.node_ids)
        return cls(hashlib.sha256(_canonical_json(payload).encode()).hexdigest())


@dataclass(frozen=True, slots=True)
class DecisionGraphSnapshot:
    """Replay-compatible immutable graph capture."""

    graph: DecisionDependencyGraph
    execution_plan: DecisionExecutionPlan
    digest: DecisionGraphDigest
    version: int = 1

    @classmethod
    def capture(cls, graph: DecisionDependencyGraph) -> DecisionGraphSnapshot:
        return cls(
            graph, DecisionExecutionPlan.from_graph(graph), DecisionGraphDigest.from_graph(graph)
        )

    def to_json(self) -> str:
        return _canonical_json(
            {
                "digest": self.digest.value,
                "execution_plan": list(self.execution_plan.node_ids),
                "graph": _graph_payload(self.graph.nodes, self.graph.edges),
                "version": self.version,
            }
        )

    @classmethod
    def from_json(cls, value: str) -> DecisionGraphSnapshot:
        payload = json.loads(value)
        if payload.get("version") != 1:
            raise ValueError("unsupported decision graph snapshot version")
        graph = DecisionDependencyGraph.from_json(_canonical_json(payload["graph"]))
        snapshot = cls.capture(graph)
        if (
            snapshot.digest.value != payload["digest"]
            or list(snapshot.execution_plan.node_ids) != payload["execution_plan"]
        ):
            raise ValueError("decision graph snapshot integrity mismatch")
        return snapshot


@dataclass(frozen=True, slots=True)
class DecisionGraphDiagnostics:
    """Complete, read-only validation diagnostics without repair."""

    duplicate_nodes: tuple[str, ...] = ()
    duplicate_edges: tuple[str, ...] = ()
    self_edges: tuple[str, ...] = ()
    invalid_references: tuple[str, ...] = ()
    missing_dependencies: tuple[str, ...] = ()
    orphan_nodes: tuple[str, ...] = ()
    cycles: tuple[str, ...] = ()
    root_errors: tuple[str, ...] = ()

    @property
    def errors(self) -> tuple[str, ...]:
        return tuple(
            item
            for group in (
                self.duplicate_nodes,
                self.duplicate_edges,
                self.self_edges,
                self.invalid_references,
                self.missing_dependencies,
                self.orphan_nodes,
                self.cycles,
                self.root_errors,
            )
            for item in group
        )

    @property
    def valid(self) -> bool:
        return not self.errors


class DecisionGraphValidator:
    """Deterministic graph integrity validator."""

    @staticmethod
    def diagnose(
        graph: DecisionDependencyGraph, *, require_single_root: bool = False
    ) -> DecisionGraphDiagnostics:
        ids = [node.node_id for node in graph.nodes]
        known = set(ids)
        duplicate_nodes = tuple(sorted({value for value in ids if ids.count(value) > 1}))
        edge_pairs = [(edge.source_id, edge.target_id) for edge in graph.edges]
        duplicate_edges = tuple(
            f"{source}->{target}"
            for source, target in sorted(
                {pair for pair in edge_pairs if edge_pairs.count(pair) > 1}
            )
        )
        self_edges = tuple(
            f"{source}->{target}" for source, target in edge_pairs if source == target
        )
        invalid_references = tuple(
            f"{source}->{target}"
            for source, target in edge_pairs
            if source not in known or target not in known
        )
        missing: set[str] = set()
        declared: set[tuple[str, str]] = set()
        for node in graph.nodes:
            for dependency in node.dependencies:
                pair = (dependency.node_id, node.node_id)
                declared.add(pair)
                if dependency.node_id not in known or pair not in edge_pairs:
                    missing.add(f"{dependency.node_id}->{node.node_id}")
        for pair in edge_pairs:
            target_node = next((node for node in graph.nodes if node.node_id == pair[1]), None)
            if target_node is not None and pair not in declared:
                missing.add(f"undeclared:{pair[0]}->{pair[1]}")
        outgoing, incoming = _index(graph)
        orphan_nodes: tuple[str, ...] = ()
        if len(graph.nodes) > 1:
            orphan_nodes = tuple(
                sorted(key for key in known if not outgoing[key] and not incoming[key])
            )
        cycle_nodes: tuple[str, ...] = ()
        if not invalid_references and not duplicate_nodes:
            degrees = {key: len(value) for key, value in incoming.items()}
            ready = [key for key, value in degrees.items() if value == 0]
            while ready:
                current = ready.pop()
                for dependent_id in outgoing[current]:
                    degrees[dependent_id] -= 1
                    if degrees[dependent_id] == 0:
                        ready.append(dependent_id)
            cycle_nodes = tuple(sorted(key for key, value in degrees.items() if value > 0))
        roots = tuple(key for key, value in incoming.items() if not value)
        root_errors = (
            ("graph must have exactly one root",) if require_single_root and len(roots) != 1 else ()
        )
        return DecisionGraphDiagnostics(
            duplicate_nodes=duplicate_nodes,
            duplicate_edges=duplicate_edges,
            self_edges=tuple(sorted(self_edges)),
            invalid_references=tuple(sorted(invalid_references)),
            missing_dependencies=tuple(sorted(missing)),
            orphan_nodes=orphan_nodes,
            cycles=cycle_nodes,
            root_errors=root_errors,
        )

    @classmethod
    def validate(cls, graph: DecisionDependencyGraph, *, require_single_root: bool = False) -> None:
        diagnostics = cls.diagnose(graph, require_single_root=require_single_root)
        if not diagnostics.valid:
            raise ValueError("invalid decision graph: " + "; ".join(diagnostics.errors))


@dataclass(frozen=True, slots=True)
class DecisionGraphStatistics:
    """Structural graph statistics."""

    node_count: int
    edge_count: int
    root_count: int
    leaf_count: int


@dataclass(frozen=True, slots=True)
class DecisionGraphAudit:
    """Read-only graph audit report."""

    statistics: DecisionGraphStatistics
    roots: tuple[str, ...]
    leaves: tuple[str, ...]
    validation_failures: tuple[str, ...]
    execution_plan: DecisionExecutionPlan | None

    @classmethod
    def inspect(cls, graph: DecisionDependencyGraph) -> DecisionGraphAudit:
        diagnostics = DecisionGraphValidator.diagnose(graph)
        topology = DecisionTopology.from_graph(graph)
        plan = None if diagnostics.errors else DecisionExecutionPlan.from_graph(graph)
        return cls(
            statistics=DecisionGraphStatistics(
                len(graph.nodes), len(graph.edges), len(topology.roots), len(topology.leaves)
            ),
            roots=topology.roots,
            leaves=topology.leaves,
            validation_failures=diagnostics.errors,
            execution_plan=plan,
        )


class DecisionGraphBuilder:
    """Explicit deterministic graph builder with no runtime discovery."""

    def __init__(self) -> None:
        self._nodes: list[DecisionGraphNode] = []
        self._edges: list[DecisionGraphEdge] = []

    def add_node(self, node: DecisionGraphNode) -> DecisionGraphBuilder:
        self._nodes.append(node)
        return self

    def add_edge(self, edge: DecisionGraphEdge) -> DecisionGraphBuilder:
        self._edges.append(edge)
        return self

    def connect(self, source_id: str, target_id: str) -> DecisionGraphBuilder:
        return self.add_edge(DecisionGraphEdge(source_id, target_id))

    def build(self, *, require_single_root: bool = False) -> DecisionDependencyGraph:
        graph = DecisionDependencyGraph(tuple(self._nodes), tuple(self._edges))
        DecisionGraphValidator.validate(graph, require_single_root=require_single_root)
        return graph


class DecisionRelation(StrEnum):
    """Backward-compatible relationship type for decision history graphs."""

    NEXT = "NEXT"
    CHILD = "CHILD"
    LINKED_CONTEXT = "LINKED_CONTEXT"
    LINKED_ELLIOTT = "LINKED_ELLIOTT"


@dataclass(frozen=True, slots=True)
class DecisionNode:
    """Backward-compatible node used by the EPIP-012 decision history graph."""

    node_id: str
    snapshot: DecisionSnapshot
    linked_context: str
    linked_elliott: str


@dataclass(frozen=True, slots=True)
class DecisionEdge:
    """Backward-compatible edge used by the EPIP-012 decision history graph."""

    source_id: str
    target_id: str
    relation: DecisionRelation


@dataclass(frozen=True, slots=True)
class DecisionGraph:
    """Backward-compatible immutable EPIP-012 decision history graph."""

    nodes: tuple[DecisionNode, ...] = ()
    edges: tuple[DecisionEdge, ...] = ()

    def append(self, snapshot: DecisionSnapshot, parent_id: str | None = None) -> DecisionGraph:
        node_id = f"{snapshot.symbol}:{snapshot.timeframe}:v{snapshot.version}"
        node = DecisionNode(
            node_id,
            snapshot,
            f"context:v{snapshot.context_version}",
            f"elliott:v{snapshot.elliott_version}",
        )
        edges = list(self.edges)
        if self.nodes:
            edges.append(DecisionEdge(self.nodes[-1].node_id, node_id, DecisionRelation.NEXT))
        if parent_id is not None:
            if self.node(parent_id) is None:
                raise RelationshipIntegrityError(f"unknown parent node: {parent_id}")
            edges.append(DecisionEdge(parent_id, node_id, DecisionRelation.CHILD))
        edges.extend(
            (
                DecisionEdge(node_id, node.linked_context, DecisionRelation.LINKED_CONTEXT),
                DecisionEdge(node_id, node.linked_elliott, DecisionRelation.LINKED_ELLIOTT),
            )
        )
        return DecisionGraph((*self.nodes, node), tuple(edges))

    def node(self, node_id: str) -> DecisionNode | None:
        return next((node for node in self.nodes if node.node_id == node_id), None)

    def _related(
        self, node_id: str, relation: DecisionRelation, reverse: bool
    ) -> DecisionNode | None:
        edge = next(
            (
                edge
                for edge in self.edges
                if edge.relation == relation
                and (edge.target_id if reverse else edge.source_id) == node_id
            ),
            None,
        )
        if edge is None:
            return None
        return self.node(edge.source_id if reverse else edge.target_id)

    def previous(self, node_id: str) -> DecisionNode | None:
        return self._related(node_id, DecisionRelation.NEXT, True)

    def next(self, node_id: str) -> DecisionNode | None:
        return self._related(node_id, DecisionRelation.NEXT, False)

    def parent(self, node_id: str) -> DecisionNode | None:
        return self._related(node_id, DecisionRelation.CHILD, True)

    def children(self, node_id: str) -> tuple[DecisionNode, ...]:
        child_ids = {
            edge.target_id
            for edge in self.edges
            if edge.source_id == node_id and edge.relation == DecisionRelation.CHILD
        }
        return tuple(node for node in self.nodes if node.node_id in child_ids)

    def linked_context(self, node_id: str) -> str | None:
        edge = next(
            (
                edge
                for edge in self.edges
                if edge.source_id == node_id and edge.relation == DecisionRelation.LINKED_CONTEXT
            ),
            None,
        )
        return edge.target_id if edge else None

    def linked_elliott(self, node_id: str) -> str | None:
        edge = next(
            (
                edge
                for edge in self.edges
                if edge.source_id == node_id and edge.relation == DecisionRelation.LINKED_ELLIOTT
            ),
            None,
        )
        return edge.target_id if edge else None


__all__ = [
    "DecisionDependency",
    "DecisionDependencyGraph",
    "DecisionEdge",
    "DecisionExecutionPlan",
    "DecisionGraph",
    "DecisionGraphAudit",
    "DecisionGraphBuilder",
    "DecisionGraphDiagnostics",
    "DecisionGraphDigest",
    "DecisionGraphEdge",
    "DecisionGraphNode",
    "DecisionGraphSnapshot",
    "DecisionGraphStatistics",
    "DecisionGraphValidator",
    "DecisionNode",
    "DecisionNodeType",
    "DecisionRelation",
    "DecisionTopology",
]
