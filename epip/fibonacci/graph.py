from __future__ import annotations

from dataclasses import dataclass

from epip.core.integrity import RelationshipIntegrityError
from epip.fibonacci.models import FibonacciSnapshot


@dataclass(frozen=True, slots=True)
class FibonacciNode:
    node_id: str
    snapshot: FibonacciSnapshot
    linked_structure_version: int
    linked_liquidity_version: int
    linked_swing_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class FibonacciEdge:
    source_id: str
    target_id: str
    relation: str = "NEXT"


@dataclass(frozen=True, slots=True)
class FibonacciGraph:
    nodes: tuple[FibonacciNode, ...] = ()
    edges: tuple[FibonacciEdge, ...] = ()

    def append(
        self, s: FibonacciSnapshot, swing_indices: tuple[int, ...], parent_id: str | None = None
    ) -> FibonacciGraph:
        node = FibonacciNode(
            f"{s.symbol}:{s.timeframe}:v{s.version}",
            s,
            s.structure_version,
            s.liquidity_version,
            swing_indices,
        )
        edges = list(self.edges)
        if self.nodes:
            edges.append(FibonacciEdge(self.nodes[-1].node_id, node.node_id))
        if parent_id:
            if self.node(parent_id) is None:
                raise RelationshipIntegrityError(f"unknown parent node: {parent_id}")
            edges.append(FibonacciEdge(parent_id, node.node_id, "CHILD"))
        return FibonacciGraph((*self.nodes, node), tuple(edges))

    def node(self, i: str) -> FibonacciNode | None:
        return next((x for x in self.nodes if x.node_id == i), None)

    def previous(self, i: str) -> FibonacciNode | None:
        e = next((x for x in self.edges if x.target_id == i and x.relation == "NEXT"), None)
        return self.node(e.source_id) if e else None

    def next(self, i: str) -> FibonacciNode | None:
        e = next((x for x in self.edges if x.source_id == i and x.relation == "NEXT"), None)
        return self.node(e.target_id) if e else None

    def parent(self, i: str) -> FibonacciNode | None:
        e = next((x for x in self.edges if x.target_id == i and x.relation == "CHILD"), None)
        return self.node(e.source_id) if e else None

    def children(self, i: str) -> tuple[FibonacciNode, ...]:
        return tuple(
            x
            for x in self.nodes
            if any(
                e.source_id == i and e.target_id == x.node_id and e.relation == "CHILD"
                for e in self.edges
            )
        )
