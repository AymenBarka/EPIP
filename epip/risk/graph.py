"""Immutable risk graph."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epip.risk.models import RiskSnapshot


class RiskRelation(StrEnum):
    NEXT = "NEXT"
    CHILD = "CHILD"
    LINKED_DECISION = "LINKED_DECISION"


@dataclass(frozen=True, slots=True)
class RiskNode:
    node_id: str
    snapshot: RiskSnapshot
    linked_decision: str


@dataclass(frozen=True, slots=True)
class RiskEdge:
    source_id: str
    target_id: str
    relation: RiskRelation


@dataclass(frozen=True, slots=True)
class RiskGraph:
    nodes: tuple[RiskNode, ...] = ()
    edges: tuple[RiskEdge, ...] = ()

    def append(self, snapshot: RiskSnapshot, parent_id: str | None = None) -> RiskGraph:
        node_id = f"{snapshot.symbol}:{snapshot.timeframe}:v{snapshot.version}"
        node = RiskNode(node_id, snapshot, snapshot.plan.decision_id)
        edges = list(self.edges)
        if self.nodes:
            edges.append(RiskEdge(self.nodes[-1].node_id, node_id, RiskRelation.NEXT))
        if parent_id is not None:
            if self.node(parent_id) is None:
                raise KeyError(parent_id)
            edges.append(RiskEdge(parent_id, node_id, RiskRelation.CHILD))
        edges.append(RiskEdge(node_id, node.linked_decision, RiskRelation.LINKED_DECISION))
        return RiskGraph((*self.nodes, node), tuple(edges))

    def node(self, node_id: str) -> RiskNode | None:
        return next((item for item in self.nodes if item.node_id == node_id), None)

    def _related(self, node_id: str, relation: RiskRelation, reverse: bool) -> RiskNode | None:
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

    def previous(self, node_id: str) -> RiskNode | None:
        return self._related(node_id, RiskRelation.NEXT, True)

    def next(self, node_id: str) -> RiskNode | None:
        return self._related(node_id, RiskRelation.NEXT, False)

    def parent(self, node_id: str) -> RiskNode | None:
        return self._related(node_id, RiskRelation.CHILD, True)

    def children(self, node_id: str) -> tuple[RiskNode, ...]:
        ids = {
            edge.target_id
            for edge in self.edges
            if edge.source_id == node_id and edge.relation == RiskRelation.CHILD
        }
        return tuple(node for node in self.nodes if node.node_id in ids)

    def linked_trade_decision(self, node_id: str) -> str | None:
        edge = next(
            (
                item
                for item in self.edges
                if item.source_id == node_id and item.relation == RiskRelation.LINKED_DECISION
            ),
            None,
        )
        return edge.target_id if edge else None
