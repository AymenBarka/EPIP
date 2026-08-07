"""EPIP-009 configuration."""

from dataclasses import dataclass

DEFAULT_LEVELS = (
    0.0,
    0.236,
    0.382,
    0.5,
    0.618,
    0.705,
    0.786,
    0.886,
    1.0,
    1.13,
    1.272,
    1.414,
    1.618,
    2.0,
    2.618,
    4.236,
)


@dataclass(frozen=True, slots=True)
class FibonacciConfig:
    levels: tuple[float, ...] = DEFAULT_LEVELS
    ote_low: float = 0.618
    ote_high: float = 0.786
    golden_low: float = 0.618
    golden_high: float = 0.705

    def __post_init__(self) -> None:
        if not self.levels or any(x < 0 for x in self.levels):
            raise ValueError("levels must be non-empty and non-negative")
        if not 0 <= self.ote_low <= self.ote_high <= 1:
            raise ValueError("invalid OTE range")
