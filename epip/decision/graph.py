"""Immutable Decision graph with official snapshot links."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epip.decision.models import DecisionSnapshot


class DecisionRelation(StrEnum):
    NEXT = "NEXT"
    CHILD = "CHILD"
    LINKED_CONTEXT = "LINKED_CONTEXT"
    LINKED_ELLIOTT = "LINKED_ELLIOTT"


@dataclass(frozen=True, slots=True)
class DecisionNode:
    node_id: str
    snapshot: DecisionSnapshot
    linked_context: str
    linked_elliott: str


@dataclass(frozen=True, slots=True)
class DecisionEdge:
    source_id: str
    target_id: str
    relation: DecisionRelation


@dataclass(frozen=True, slots=True)
class DecisionGraph:
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
                raise KeyError(parent_id)
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
