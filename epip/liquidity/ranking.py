"""Deterministic liquidity ranking."""

from enum import StrEnum


class LiquidityRanking(StrEnum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"

    @classmethod
    def from_score(cls, score: float) -> "LiquidityRanking":
        value = max(0.0, min(1.0, score))
        if value >= 0.85:
            return cls.VERY_HIGH
        if value >= 0.65:
            return cls.HIGH
        if value >= 0.4:
            return cls.MEDIUM
        if value >= 0.2:
            return cls.LOW
        return cls.VERY_LOW
