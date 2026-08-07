"""Validation of official Decision Engine inputs."""

from epip.context import MarketContextSnapshot
from epip.elliott import WaveSnapshot


class DecisionInputValidator:
    def validate(self, context: MarketContextSnapshot, elliott: WaveSnapshot) -> bool:
        return (
            context.symbol == elliott.symbol
            and context.timeframe == elliott.timeframe
            and context.version.context == elliott.context_version
            and elliott.version > 0
        )
