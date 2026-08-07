"""Immutable multi-timeframe liquidity tree."""

from __future__ import annotations

from dataclasses import dataclass

from epip.liquidity.models import LiquiditySnapshot

_ORDER = {"M1": 0, "M5": 1, "M15": 2, "H1": 3, "H4": 4, "D1": 5}


@dataclass(frozen=True, slots=True)
class LiquidityTreeNode:
    node_id: str
    timeframe: str
    snapshot: LiquiditySnapshot
    parent_id: str | None = None


@dataclass(frozen=True, slots=True)
class MultiTimeFrameLiquidityTree:
    nodes: tuple[LiquidityTreeNode, ...] = ()

    def add(
        self, snapshot: LiquiditySnapshot, parent_id: str | None = None
    ) -> MultiTimeFrameLiquidityTree:
        if snapshot.timeframe not in _ORDER:
            raise ValueError("unsupported timeframe")
        if parent_id is not None:
            parent = self.node(parent_id)
            if parent is None or _ORDER[parent.timeframe] <= _ORDER[snapshot.timeframe]:
                raise ValueError("parent must be a higher timeframe")
        node = LiquidityTreeNode(
            f"{snapshot.symbol}:{snapshot.timeframe}:v{snapshot.version}",
            snapshot.timeframe,
            snapshot,
            parent_id,
        )
        return MultiTimeFrameLiquidityTree((*self.nodes, node))

    def node(self, node_id: str) -> LiquidityTreeNode | None:
        return next((x for x in self.nodes if x.node_id == node_id), None)

    def parent(self, node_id: str) -> LiquidityTreeNode | None:
        node = self.node(node_id)
        return self.node(node.parent_id) if node and node.parent_id else None

    def children(self, node_id: str) -> tuple[LiquidityTreeNode, ...]:
        return tuple(x for x in self.nodes if x.parent_id == node_id)
