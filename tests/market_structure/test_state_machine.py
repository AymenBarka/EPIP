from __future__ import annotations

from epip.market_structure.exceptions import IllegalStructureTransitionError
from epip.market_structure.models import StructureState
from epip.market_structure.state_machine import StructureStateMachine


def test_state_machine_valid_transitions() -> None:
    machine = StructureStateMachine()

    assert (
        machine.transition(StructureState.UNKNOWN, StructureState.ACCUMULATION)
        == StructureState.ACCUMULATION
    )
    assert (
        machine.transition(StructureState.ACCUMULATION, StructureState.UPTREND)
        == StructureState.UPTREND
    )
    assert (
        machine.transition(StructureState.UPTREND, StructureState.DISTRIBUTION)
        == StructureState.DISTRIBUTION
    )
    assert (
        machine.transition(StructureState.DISTRIBUTION, StructureState.DOWNTREND)
        == StructureState.DOWNTREND
    )
    assert (
        machine.transition(StructureState.DOWNTREND, StructureState.RANGE) == StructureState.RANGE
    )


def test_state_machine_invalid_transition_raises() -> None:
    machine = StructureStateMachine()

    try:
        machine.transition(StructureState.UPTREND, StructureState.DOWNTREND)
        assert False
    except IllegalStructureTransitionError:
        assert True
