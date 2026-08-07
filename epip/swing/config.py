"""Immutable configuration for Swing Engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SwingConfig:
    """Tunable parameters for swing detection."""

    left_bars: int = 2
    right_bars: int = 2
    minimum_distance: int = 1
    minimum_price_move: float = 0.0
    minimum_atr: float = 0.0
    adaptive_window: bool = False
    equal_high_threshold: float = 0.0
    equal_low_threshold: float = 0.0
    atr_period: int = 14
    trend_bias: str = "NEUTRAL"

    def __post_init__(self) -> None:
        if self.left_bars <= 0:
            raise ValueError("left_bars must be greater than zero")
        if self.right_bars <= 0:
            raise ValueError("right_bars must be greater than zero")
        if self.minimum_distance < 0:
            raise ValueError("minimum_distance must be non-negative")
        if self.minimum_price_move < 0:
            raise ValueError("minimum_price_move must be non-negative")
        if self.minimum_atr < 0:
            raise ValueError("minimum_atr must be non-negative")
        if self.equal_high_threshold < 0:
            raise ValueError("equal_high_threshold must be non-negative")
        if self.equal_low_threshold < 0:
            raise ValueError("equal_low_threshold must be non-negative")
        if self.atr_period <= 0:
            raise ValueError("atr_period must be greater than zero")
