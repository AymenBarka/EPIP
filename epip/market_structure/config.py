"""Immutable configuration for EPIP-007 Market Structure Engine."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.integrity import DataIntegrityError


@dataclass(frozen=True, slots=True)
class MarketStructureConfig:
    """Tunable rules for structure inference from swing sequences."""

    minimum_swings: int = 4
    equal_threshold: float = 0.0
    confirmation_required: bool = True
    range_touch_count: int = 2
    enable_bos: bool = True
    enable_choch: bool = True
    enable_range: bool = True

    def __post_init__(self) -> None:
        if self.minimum_swings < 2:
            raise DataIntegrityError("minimum_swings must be >= 2")
        if self.equal_threshold < 0.0:
            raise DataIntegrityError("equal_threshold must be non-negative")
        if self.range_touch_count < 1:
            raise DataIntegrityError("range_touch_count must be >= 1")
