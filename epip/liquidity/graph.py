"""Immutable liquidity relationship graph."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.integrity import RelationshipIntegrityError
from epip.liquidity.models import LiquiditySnapshot


@dataclass(frozen=True, slots=True)
class LiquidityNode:
    node_id: str
    snapshot: LiquiditySnapshot
    linked_structure_version: int


@dataclass(frozen=True, slots=True)
class LiquidityEdge:
    source_id: str
    target_id: str
    relation: str = "NEXT"


@dataclass(frozen=True, slots=True)
class LiquidityGraph:
    nodes: tuple[LiquidityNode, ...] = ()
    edges: tuple[LiquidityEdge, ...] = ()

    def append(
        self, snapshot: LiquiditySnapshot, *, parent_id: str | None = None
    ) -> LiquidityGraph:
        node = LiquidityNode(
            f"{snapshot.symbol}:{snapshot.timeframe}:v{snapshot.version}",
            snapshot,
            snapshot.structure_version,
        )
        edges = list(self.edges)
        if self.nodes:
            edges.append(LiquidityEdge(self.nodes[-1].node_id, node.node_id))
        if parent_id is not None:
            if self.node(parent_id) is None:
                raise RelationshipIntegrityError(f"unknown parent node: {parent_id}")
            edges.append(LiquidityEdge(parent_id, node.node_id, "CHILD"))
        return LiquidityGraph((*self.nodes, node), tuple(edges))

    def node(self, node_id: str) -> LiquidityNode | None:
        return next((x for x in self.nodes if x.node_id == node_id), None)

    def parent(self, node_id: str) -> LiquidityNode | None:
        edge = next(
            (x for x in self.edges if x.target_id == node_id and x.relation == "CHILD"), None
        )
        return self.node(edge.source_id) if edge else None

    def children(self, node_id: str) -> tuple[LiquidityNode, ...]:
        children: list[LiquidityNode] = []
        for edge in self.edges:
            child = self.node(edge.target_id)
            if edge.source_id == node_id and edge.relation == "CHILD" and child is not None:
                children.append(child)
        return tuple(children)

    def previous(self, node_id: str) -> LiquidityNode | None:
        edge = next(
            (x for x in self.edges if x.target_id == node_id and x.relation == "NEXT"), None
        )
        return self.node(edge.source_id) if edge else None

    def next(self, node_id: str) -> LiquidityNode | None:
        edge = next(
            (x for x in self.edges if x.source_id == node_id and x.relation == "NEXT"), None
        )
        return self.node(edge.target_id) if edge else None
