"""Explicit state machine for Market Structure transitions."""

from __future__ import annotations

from epip.market_structure.exceptions import IllegalStructureTransitionError
from epip.market_structure.models import StructureState

_ALLOWED_TRANSITIONS: dict[StructureState, tuple[StructureState, ...]] = {
    StructureState.UNKNOWN: (
        StructureState.UNKNOWN,
        StructureState.ACCUMULATION,
        StructureState.DISTRIBUTION,
        StructureState.UPTREND,
        StructureState.DOWNTREND,
        StructureState.RANGE,
    ),
    StructureState.ACCUMULATION: (
        StructureState.ACCUMULATION,
        StructureState.UPTREND,
        StructureState.DOWNTREND,
        StructureState.RANGE,
    ),
    StructureState.UPTREND: (
        StructureState.UPTREND,
        StructureState.DISTRIBUTION,
        StructureState.RANGE,
    ),
    StructureState.DISTRIBUTION: (
        StructureState.DISTRIBUTION,
        StructureState.DOWNTREND,
        StructureState.UPTREND,
        StructureState.RANGE,
    ),
    StructureState.DOWNTREND: (
        StructureState.DOWNTREND,
        StructureState.ACCUMULATION,
        StructureState.RANGE,
    ),
    StructureState.RANGE: (
        StructureState.RANGE,
        StructureState.ACCUMULATION,
        StructureState.DISTRIBUTION,
        StructureState.UPTREND,
        StructureState.DOWNTREND,
    ),
}


class StructureStateMachine:
    """Transition guard for market structure phases."""

    def transition(self, current: StructureState, target: StructureState) -> StructureState:
        allowed = _ALLOWED_TRANSITIONS.get(current, ())
        if target not in allowed:
            raise IllegalStructureTransitionError(
                f"illegal structure transition: {current.value} -> {target.value}"
            )
        return target
