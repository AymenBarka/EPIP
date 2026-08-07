"""Deterministic mapping from evidence to the official action."""

from epip.context import InstitutionalBias
from epip.decision.models import DecisionAction


class DecisionMatrix:
    def decide(
        self,
        bias: InstitutionalBias,
        score: float,
        threshold: float,
        *,
        invalid: bool,
        previous: DecisionAction | None = None,
    ) -> DecisionAction:
        if invalid:
            return DecisionAction.INVALID
        bullish = bias in (InstitutionalBias.BULLISH, InstitutionalBias.STRONGLY_BULLISH)
        bearish = bias in (InstitutionalBias.BEARISH, InstitutionalBias.STRONGLY_BEARISH)
        if previous in (DecisionAction.LONG, DecisionAction.ADD) and bearish:
            return DecisionAction.EXIT_LONG
        if previous == DecisionAction.SHORT and bullish:
            return DecisionAction.EXIT_SHORT
        if score < threshold or not (bullish or bearish):
            if previous in (DecisionAction.LONG, DecisionAction.SHORT, DecisionAction.ADD):
                return DecisionAction.REDUCE
            return DecisionAction.WAIT
        if bullish:
            return DecisionAction.ADD if previous == DecisionAction.LONG else DecisionAction.LONG
        return DecisionAction.SHORT
