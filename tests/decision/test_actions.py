from dataclasses import replace

from epip.context import InstitutionalBias
from epip.core.event_bus import EventBus
from epip.decision import DecisionAction, DecisionConfig, DecisionEngine
from epip.decision.decision_matrix import DecisionMatrix
from epip.elliott import CountStatus
from epip.market_structure.models import StructureState, TrendDirection
from tests.decision.helpers import snapshots


def test_short_wait_exit_reduce_and_invalid_actions() -> None:
    short_context, short_elliott = snapshots(
        direction=TrendDirection.DOWNTREND, state=StructureState.DOWNTREND
    )
    assert (
        DecisionEngine(config=DecisionConfig(), event_bus=EventBus())
        .process(short_context, short_elliott)
        .decision.action
        == DecisionAction.SHORT
    )
    matrix = DecisionMatrix()
    assert matrix.decide(InstitutionalBias.NEUTRAL, 90, 50, invalid=False) == DecisionAction.WAIT


def test_matrix_covers_exit_reduce_and_invalid() -> None:
    matrix = DecisionMatrix()
    assert (
        matrix.decide(
            InstitutionalBias.BEARISH, 80, 50, invalid=False, previous=DecisionAction.LONG
        )
        == DecisionAction.EXIT_LONG
    )
    assert (
        matrix.decide(
            InstitutionalBias.BULLISH, 80, 50, invalid=False, previous=DecisionAction.SHORT
        )
        == DecisionAction.EXIT_SHORT
    )
    assert (
        matrix.decide(
            InstitutionalBias.BULLISH, 10, 50, invalid=False, previous=DecisionAction.LONG
        )
        == DecisionAction.REDUCE
    )
    assert matrix.decide(InstitutionalBias.BULLISH, 80, 50, invalid=True) == DecisionAction.INVALID


def test_invalid_elliott_count_produces_invalid_decision() -> None:
    context, elliott = snapshots()
    primary = replace(elliott.analysis.primary, status=CountStatus.INVALID)
    elliott = replace(elliott, analysis=replace(elliott.analysis, primary=primary))
    decision = DecisionEngine(config=DecisionConfig(), event_bus=EventBus()).process(
        context, elliott
    )
    assert decision.decision.action == DecisionAction.INVALID
