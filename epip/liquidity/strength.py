"""Immutable liquidity strength assessment."""

from dataclasses import dataclass

from epip.liquidity.ranking import LiquidityRanking


@dataclass(frozen=True, slots=True)
class LiquidityStrength:
    touch_count: int
    age: int
    reaction_count: int
    consumption_ratio: float
    confidence: float
    strength_level: LiquidityRanking

    @classmethod
    def calculate(
        cls, touch_count: int, age: int, reaction_count: int, consumption_ratio: float
    ) -> "LiquidityStrength":
        ratio = max(0.0, min(1.0, consumption_ratio))
        confidence = max(
            0.0,
            min(
                1.0,
                0.15 * min(touch_count, 4)
                + 0.1 * min(reaction_count, 3)
                + 0.1 / (1 + max(age, 0))
                - 0.3 * ratio,
            ),
        )
        return cls(
            touch_count,
            max(age, 0),
            reaction_count,
            ratio,
            confidence,
            LiquidityRanking.from_score(confidence),
        )
