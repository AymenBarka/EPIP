"""Immutable execution graph."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epip.core.integrity import RelationshipIntegrityError
from epip.execution.models import ExecutionSnapshot


class ExecutionRelation(StrEnum):
    NEXT = "NEXT"
    CHILD = "CHILD"
    LINKED_POSITION_PLAN = "LINKED_POSITION_PLAN"


@dataclass(frozen=True, slots=True)
class ExecutionNode:
    node_id: str
    snapshot: ExecutionSnapshot
    linked_position_plan: str


@dataclass(frozen=True, slots=True)
class ExecutionEdge:
    source_id: str
    target_id: str
    relation: ExecutionRelation


@dataclass(frozen=True, slots=True)
class ExecutionGraph:
    nodes: tuple[ExecutionNode, ...] = ()
    edges: tuple[ExecutionEdge, ...] = ()

    def append(self, snapshot: ExecutionSnapshot, parent_id: str | None = None) -> ExecutionGraph:
        node_id = f"{snapshot.symbol}:v{snapshot.version}"
        node = ExecutionNode(node_id, snapshot, snapshot.position_plan_id)
        edges = list(self.edges)
        if self.nodes:
            edges.append(ExecutionEdge(self.nodes[-1].node_id, node_id, ExecutionRelation.NEXT))
        if parent_id is not None:
            if self.node(parent_id) is None:
                raise RelationshipIntegrityError(f"unknown parent node: {parent_id}")
            edges.append(ExecutionEdge(parent_id, node_id, ExecutionRelation.CHILD))
        edges.append(
            ExecutionEdge(
                node_id, node.linked_position_plan, ExecutionRelation.LINKED_POSITION_PLAN
            )
        )
        return ExecutionGraph((*self.nodes, node), tuple(edges))

    def node(self, node_id: str) -> ExecutionNode | None:
        return next((item for item in self.nodes if item.node_id == node_id), None)

    def _related(
        self, node_id: str, relation: ExecutionRelation, reverse: bool
    ) -> ExecutionNode | None:
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

    def previous(self, node_id: str) -> ExecutionNode | None:
        return self._related(node_id, ExecutionRelation.NEXT, True)

    def next(self, node_id: str) -> ExecutionNode | None:
        return self._related(node_id, ExecutionRelation.NEXT, False)

    def parent(self, node_id: str) -> ExecutionNode | None:
        return self._related(node_id, ExecutionRelation.CHILD, True)

    def children(self, node_id: str) -> tuple[ExecutionNode, ...]:
        ids = {
            edge.target_id
            for edge in self.edges
            if edge.source_id == node_id and edge.relation == ExecutionRelation.CHILD
        }
        return tuple(node for node in self.nodes if node.node_id in ids)

    def linked_position_plan(self, node_id: str) -> str | None:
        edge = next(
            (
                item
                for item in self.edges
                if item.source_id == node_id
                and item.relation == ExecutionRelation.LINKED_POSITION_PLAN
            ),
            None,
        )
        return edge.target_id if edge else None
