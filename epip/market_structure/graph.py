"""Immutable graph views over market-structure snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epip.market_structure.models import MarketStructure, MarketStructureSnapshot


class StructureRelation(StrEnum):
    """Supported navigation relationships between structure nodes."""

    PARENT_CHILD = "PARENT_CHILD"
    CHRONOLOGICAL = "CHRONOLOGICAL"


@dataclass(frozen=True, slots=True)
class StructureNode:
    """A stable graph node consuming, but never altering, a structure."""

    node_id: str
    structure: MarketStructure
    version: int
    timestamp: str

    @classmethod
    def from_snapshot(cls, snapshot: MarketStructureSnapshot) -> StructureNode:
        return cls(
            node_id=f"{snapshot.structure.uuid}:v{snapshot.version}",
            structure=snapshot.structure,
            version=snapshot.version,
            timestamp=snapshot.timestamp,
        )


@dataclass(frozen=True, slots=True)
class StructureEdge:
    """A directed, immutable relationship between two structure nodes."""

    source_id: str
    target_id: str
    relation: StructureRelation


@dataclass(frozen=True, slots=True)
class StructureGraph:
    """Immutable graph supporting hierarchy and chronological traversal."""

    nodes: tuple[StructureNode, ...] = ()
    edges: tuple[StructureEdge, ...] = ()

    @classmethod
    def from_snapshots(cls, snapshots: tuple[MarketStructureSnapshot, ...]) -> StructureGraph:
        graph = cls()
        for snapshot in snapshots:
            graph = graph.append(snapshot)
        return graph

    def append(
        self,
        snapshot: MarketStructureSnapshot,
        *,
        parent_id: str | None = None,
    ) -> StructureGraph:
        node = StructureNode.from_snapshot(snapshot)
        if self.node(node.node_id) is not None:
            return self
        edges = list(self.edges)
        previous = self.nodes[-1] if self.nodes else None
        if previous is not None:
            edges.append(
                StructureEdge(previous.node_id, node.node_id, StructureRelation.CHRONOLOGICAL)
            )
        if parent_id is not None:
            if self.node(parent_id) is None:
                raise KeyError(f"unknown parent node: {parent_id}")
            edges.append(StructureEdge(parent_id, node.node_id, StructureRelation.PARENT_CHILD))
        return StructureGraph(nodes=(*self.nodes, node), edges=tuple(edges))

    def node(self, node_id: str) -> StructureNode | None:
        return next((node for node in self.nodes if node.node_id == node_id), None)

    def children(self, node_id: str) -> tuple[StructureNode, ...]:
        ids = {
            edge.target_id
            for edge in self.edges
            if edge.source_id == node_id and edge.relation == StructureRelation.PARENT_CHILD
        }
        return tuple(node for node in self.nodes if node.node_id in ids)

    def parent(self, node_id: str) -> StructureNode | None:
        edge = next(
            (
                edge
                for edge in self.edges
                if edge.target_id == node_id and edge.relation == StructureRelation.PARENT_CHILD
            ),
            None,
        )
        return self.node(edge.source_id) if edge else None

    def previous(self, node_id: str) -> StructureNode | None:
        edge = next(
            (
                edge
                for edge in self.edges
                if edge.target_id == node_id and edge.relation == StructureRelation.CHRONOLOGICAL
            ),
            None,
        )
        return self.node(edge.source_id) if edge else None

    def next(self, node_id: str) -> StructureNode | None:
        edge = next(
            (
                edge
                for edge in self.edges
                if edge.source_id == node_id and edge.relation == StructureRelation.CHRONOLOGICAL
            ),
            None,
        )
        return self.node(edge.target_id) if edge else None
