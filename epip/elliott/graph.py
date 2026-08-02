"""Immutable Elliott graph for Decision traversal."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epip.elliott.models import WaveSnapshot


class WaveRelation(StrEnum):
    NEXT = "NEXT"
    CHILD = "CHILD"
    ALTERNATE = "ALTERNATE"
    PROJECTION = "PROJECTION"


@dataclass(frozen=True, slots=True)
class WaveNode:
    node_id: str
    snapshot: WaveSnapshot


@dataclass(frozen=True, slots=True)
class WaveEdge:
    source_id: str
    target_id: str
    relation: WaveRelation


@dataclass(frozen=True, slots=True)
class WaveGraph:
    nodes: tuple[WaveNode, ...] = ()
    edges: tuple[WaveEdge, ...] = ()

    def append(self, snapshot: WaveSnapshot, parent_id: str | None = None) -> WaveGraph:
        node_id = f"{snapshot.symbol}:{snapshot.timeframe}:v{snapshot.version}"
        node = WaveNode(node_id, snapshot)
        edges = list(self.edges)
        if self.nodes:
            edges.append(WaveEdge(self.nodes[-1].node_id, node_id, WaveRelation.NEXT))
        if parent_id is not None:
            if self.node(parent_id) is None:
                raise KeyError(parent_id)
            edges.append(WaveEdge(parent_id, node_id, WaveRelation.CHILD))
        if snapshot.analysis.alternates:
            edges.append(WaveEdge(node_id, f"{node_id}:alternate", WaveRelation.ALTERNATE))
        if snapshot.analysis.projection is not None:
            edges.append(WaveEdge(node_id, f"{node_id}:projection", WaveRelation.PROJECTION))
        return WaveGraph((*self.nodes, node), tuple(edges))

    def node(self, node_id: str) -> WaveNode | None:
        return next((node for node in self.nodes if node.node_id == node_id), None)

    def _related(self, node_id: str, relation: WaveRelation, reverse: bool) -> WaveNode | None:
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

    def previous(self, node_id: str) -> WaveNode | None:
        return self._related(node_id, WaveRelation.NEXT, True)

    def next(self, node_id: str) -> WaveNode | None:
        return self._related(node_id, WaveRelation.NEXT, False)

    def parent(self, node_id: str) -> WaveNode | None:
        return self._related(node_id, WaveRelation.CHILD, True)

    def children(self, node_id: str) -> tuple[WaveNode, ...]:
        ids = {
            edge.target_id
            for edge in self.edges
            if edge.source_id == node_id and edge.relation == WaveRelation.CHILD
        }
        return tuple(node for node in self.nodes if node.node_id in ids)

    def alternates(self, node_id: str) -> tuple[WaveEdge, ...]:
        return tuple(
            edge
            for edge in self.edges
            if edge.source_id == node_id and edge.relation == WaveRelation.ALTERNATE
        )

    def projections(self, node_id: str) -> tuple[WaveEdge, ...]:
        return tuple(
            edge
            for edge in self.edges
            if edge.source_id == node_id and edge.relation == WaveRelation.PROJECTION
        )
