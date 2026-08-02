"""Immutable graph for Market Context and future Elliott traversal."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epip.context.snapshot import MarketContextSnapshot


class ContextRelation(StrEnum):
    NEXT = "NEXT"
    CHILD = "CHILD"
    LINKED = "LINKED"


@dataclass(frozen=True, slots=True)
class MarketContextNode:
    node_id: str
    snapshot: MarketContextSnapshot
    linked_snapshots: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MarketContextEdge:
    source_id: str
    target_id: str
    relation: ContextRelation


@dataclass(frozen=True, slots=True)
class MarketContextGraph:
    nodes: tuple[MarketContextNode, ...] = ()
    edges: tuple[MarketContextEdge, ...] = ()

    def append(
        self, snapshot: MarketContextSnapshot, parent_id: str | None = None
    ) -> MarketContextGraph:
        node_id = f"{snapshot.symbol}:{snapshot.timeframe}:v{snapshot.version.context}"
        node = MarketContextNode(
            node_id,
            snapshot,
            (
                f"structure:v{snapshot.version.structure}",
                f"liquidity:v{snapshot.version.liquidity}",
                f"fibonacci:v{snapshot.version.fibonacci}",
            ),
        )
        edges = list(self.edges)
        if self.nodes:
            edges.append(MarketContextEdge(self.nodes[-1].node_id, node_id, ContextRelation.NEXT))
        if parent_id is not None:
            if self.node(parent_id) is None:
                raise KeyError(parent_id)
            edges.append(MarketContextEdge(parent_id, node_id, ContextRelation.CHILD))
        return MarketContextGraph((*self.nodes, node), tuple(edges))

    def node(self, node_id: str) -> MarketContextNode | None:
        return next((node for node in self.nodes if node.node_id == node_id), None)

    def previous(self, node_id: str) -> MarketContextNode | None:
        edge = next(
            (
                edge
                for edge in self.edges
                if edge.target_id == node_id and edge.relation == ContextRelation.NEXT
            ),
            None,
        )
        return self.node(edge.source_id) if edge else None

    def next(self, node_id: str) -> MarketContextNode | None:
        edge = next(
            (
                edge
                for edge in self.edges
                if edge.source_id == node_id and edge.relation == ContextRelation.NEXT
            ),
            None,
        )
        return self.node(edge.target_id) if edge else None

    def parent(self, node_id: str) -> MarketContextNode | None:
        edge = next(
            (
                edge
                for edge in self.edges
                if edge.target_id == node_id and edge.relation == ContextRelation.CHILD
            ),
            None,
        )
        return self.node(edge.source_id) if edge else None

    def children(self, node_id: str) -> tuple[MarketContextNode, ...]:
        child_ids = {
            edge.target_id
            for edge in self.edges
            if edge.source_id == node_id and edge.relation == ContextRelation.CHILD
        }
        return tuple(node for node in self.nodes if node.node_id in child_ids)
