"""Explicit lifecycle state machine for liquidity objects."""

from enum import StrEnum
from typing import ClassVar

from epip.liquidity.exceptions import LiquidityError


class LiquidityState(StrEnum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    PARTIALLY_CONSUMED = "PARTIALLY_CONSUMED"
    CONSUMED = "CONSUMED"
    INVALIDATED = "INVALIDATED"


class LiquidityStateMachine:
    _allowed: ClassVar[dict[LiquidityState, set[LiquidityState]]] = {
        LiquidityState.CREATED: {LiquidityState.ACTIVE, LiquidityState.INVALIDATED},
        LiquidityState.ACTIVE: {
            LiquidityState.PARTIALLY_CONSUMED,
            LiquidityState.CONSUMED,
            LiquidityState.INVALIDATED,
        },
        LiquidityState.PARTIALLY_CONSUMED: {
            LiquidityState.PARTIALLY_CONSUMED,
            LiquidityState.CONSUMED,
            LiquidityState.INVALIDATED,
        },
        LiquidityState.CONSUMED: set(),
        LiquidityState.INVALIDATED: set(),
    }

    def transition(self, current: LiquidityState, target: LiquidityState) -> LiquidityState:
        if target not in self._allowed[current]:
            raise LiquidityError(
                "illegal liquidity transition",
                metadata={"current": current.value, "target": target.value},
            )
        return target
