import pytest

from epip.liquidity.clusters import LiquidityCluster
from epip.liquidity.exceptions import LiquidityError
from epip.liquidity.fvg import BearishFVG, BullishFVG, FairValueGapDetector
from epip.liquidity.models import (
    EqualHigh,
    LiquidityPool,
    LiquidityScope,
    LiquiditySide,
    LiquiditySnapshot,
)
from epip.liquidity.ranking import LiquidityRanking
from epip.liquidity.serialization import from_json, to_json
from epip.liquidity.state_machine import LiquidityState, LiquidityStateMachine
from epip.liquidity.strength import LiquidityStrength
from epip.liquidity.tree import MultiTimeFrameLiquidityTree
from epip.liquidity.voids import LiquidityVoid, LiquidityVoidDetector


def test_state_machine_explicit_transitions() -> None:
    machine = LiquidityStateMachine()
    assert (
        machine.transition(LiquidityState.CREATED, LiquidityState.ACTIVE) == LiquidityState.ACTIVE
    )
    assert (
        machine.transition(LiquidityState.ACTIVE, LiquidityState.PARTIALLY_CONSUMED)
        == LiquidityState.PARTIALLY_CONSUMED
    )
    assert (
        machine.transition(LiquidityState.PARTIALLY_CONSUMED, LiquidityState.CONSUMED)
        == LiquidityState.CONSUMED
    )
    with pytest.raises(LiquidityError):
        machine.transition(LiquidityState.CONSUMED, LiquidityState.ACTIVE)


def test_strength_and_ranking_are_deterministic() -> None:
    value = LiquidityStrength.calculate(4, 2, 3, 0.1)
    assert value.confidence == LiquidityStrength.calculate(4, 2, 3, 0.1).confidence
    assert value.strength_level == LiquidityRanking.from_score(value.confidence)
    assert LiquidityRanking.from_score(2) == LiquidityRanking.VERY_HIGH
    assert LiquidityRanking.from_score(-1) == LiquidityRanking.VERY_LOW


def test_fvg_void_cluster_and_placeholders() -> None:
    bullish = BullishFVG(
        "EURUSD", "M1", "t", 1.1, 1.2, LiquidityScope.INTERNAL, confluence_score=0.7
    )
    bearish = BearishFVG("EURUSD", "M1", "t", 1.0, 1.1, LiquidityScope.EXTERNAL)
    void = LiquidityVoid("EURUSD", "M1", "t", 1.1, 1.3, LiquidityScope.EXTERNAL)
    high = EqualHigh("EURUSD", "M1", 1.2, (1, 2), ("a", "b"))
    pool = LiquidityPool(
        "p", "EURUSD", "M1", 1.2, LiquiditySide.BUY_SIDE, LiquidityScope.EXTERNAL, 2, (1, 2)
    )
    cluster = LiquidityCluster(
        "c",
        equal_highs=(high,),
        pools=(pool,),
        fair_value_gaps=(bullish, bearish),
        voids=(void,),
        confluence_score=0.8,
    )
    assert cluster.confluence_score == 0.8
    assert not FairValueGapDetector().detect()
    assert not LiquidityVoidDetector().detect()


def test_tree_hierarchy_and_serialization() -> None:
    h1 = LiquiditySnapshot("1", "EURUSD", "H1", 1)
    m5 = LiquiditySnapshot("2", "EURUSD", "M5", 1)
    tree = MultiTimeFrameLiquidityTree().add(h1)
    tree = tree.add(m5, tree.nodes[0].node_id)
    assert tree.parent(tree.nodes[1].node_id) == tree.nodes[0]
    assert tree.children(tree.nodes[0].node_id) == (tree.nodes[1],)
    restored = from_json(MultiTimeFrameLiquidityTree, to_json(tree))
    assert restored == tree
    with pytest.raises(ValueError):
        tree.add(LiquiditySnapshot("3", "EURUSD", "W1", 1))


def test_new_object_serialization() -> None:
    strength = LiquidityStrength.calculate(3, 1, 2, 0.2)
    assert from_json(LiquidityStrength, to_json(strength)) == strength
    gap = BullishFVG("EURUSD", "M1", "t", 1.0, 2.0, LiquidityScope.INTERNAL)
    assert from_json(BullishFVG, to_json(gap)) == gap
    void = LiquidityVoid("EURUSD", "M1", "t", 1.0, 2.0, LiquidityScope.EXTERNAL)
    assert from_json(LiquidityVoid, to_json(void)) == void
