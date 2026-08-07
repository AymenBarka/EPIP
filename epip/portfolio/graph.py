"""Immutable portfolio lineage graph."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epip.portfolio.models import PortfolioSnapshot


class PortfolioRelation(StrEnum):
    NEXT = "NEXT"
    CHILD = "CHILD"
    LINKED_EXECUTION = "LINKED_EXECUTION"


@dataclass(frozen=True, slots=True)
class PortfolioNode:
    node_id: str
    snapshot: PortfolioSnapshot
    linked_execution: str


@dataclass(frozen=True, slots=True)
class PortfolioEdge:
    source_id: str
    target_id: str
    relation: PortfolioRelation


@dataclass(frozen=True, slots=True)
class PortfolioGraph:
    nodes: tuple[PortfolioNode, ...] = ()
    edges: tuple[PortfolioEdge, ...] = ()

    def append(self, snapshot: PortfolioSnapshot, parent_id: str | None = None) -> PortfolioGraph:
        node_id = f"portfolio:v{snapshot.version}"
        node = PortfolioNode(node_id, snapshot, snapshot.execution_plan_id)
        edges = list(self.edges)
        if self.nodes:
            edges.append(PortfolioEdge(self.nodes[-1].node_id, node_id, PortfolioRelation.NEXT))
        if parent_id is not None:
            if self.node(parent_id) is None:
                raise KeyError(parent_id)
            edges.append(PortfolioEdge(parent_id, node_id, PortfolioRelation.CHILD))
        edges.append(
            PortfolioEdge(node_id, snapshot.execution_plan_id, PortfolioRelation.LINKED_EXECUTION)
        )
        return PortfolioGraph((*self.nodes, node), tuple(edges))

    def node(self, node_id: str) -> PortfolioNode | None:
        return next((item for item in self.nodes if item.node_id == node_id), None)

    def _related(
        self, node_id: str, relation: PortfolioRelation, reverse: bool
    ) -> PortfolioNode | None:
        edge = next(
            (
                item
                for item in self.edges
                if item.relation == relation
                and (item.target_id if reverse else item.source_id) == node_id
            ),
            None,
        )
        return None if edge is None else self.node(edge.source_id if reverse else edge.target_id)

    def previous(self, node_id: str) -> PortfolioNode | None:
        return self._related(node_id, PortfolioRelation.NEXT, True)

    def next(self, node_id: str) -> PortfolioNode | None:
        return self._related(node_id, PortfolioRelation.NEXT, False)

    def parent(self, node_id: str) -> PortfolioNode | None:
        return self._related(node_id, PortfolioRelation.CHILD, True)

    def children(self, node_id: str) -> tuple[PortfolioNode, ...]:
        ids = {
            edge.target_id
            for edge in self.edges
            if edge.source_id == node_id and edge.relation == PortfolioRelation.CHILD
        }
        return tuple(node for node in self.nodes if node.node_id in ids)

    def linked_execution(self, node_id: str) -> str | None:
        edge = next(
            (
                item
                for item in self.edges
                if item.source_id == node_id and item.relation == PortfolioRelation.LINKED_EXECUTION
            ),
            None,
        )
        return edge.target_id if edge else None
