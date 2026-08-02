"""Deterministic Fibonacci strength assessment."""

from dataclasses import dataclass
from enum import StrEnum


class FibonacciQuality(StrEnum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


@dataclass(frozen=True, slots=True)
class FibonacciStrength:
    confidence: float
    quality: FibonacciQuality
    touches: int
    reactions: int
    probability: float

    @classmethod
    def calculate(cls, touches: int, reactions: int, confluence: float) -> "FibonacciStrength":
        bounded_confluence = max(0.0, min(1.0, confluence))
        confidence = max(
            0.0,
            min(
                1.0,
                0.15 * min(max(touches, 0), 4)
                + 0.15 * min(max(reactions, 0), 3)
                + 0.35 * bounded_confluence,
            ),
        )
        if confidence >= 0.85:
            quality = FibonacciQuality.VERY_HIGH
        elif confidence >= 0.65:
            quality = FibonacciQuality.HIGH
        elif confidence >= 0.4:
            quality = FibonacciQuality.MEDIUM
        elif confidence >= 0.2:
            quality = FibonacciQuality.LOW
        else:
            quality = FibonacciQuality.VERY_LOW
        probability = max(0.0, min(1.0, 0.6 * confidence + 0.4 * bounded_confluence))
        return cls(confidence, quality, max(touches, 0), max(reactions, 0), probability)
