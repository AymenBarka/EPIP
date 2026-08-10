"""Configuration for the EPIP-008 Liquidity Engine."""

from dataclasses import dataclass

from epip.core.integrity import DataIntegrityError


@dataclass(frozen=True, slots=True)
class LiquidityConfig:
    equal_threshold: float = 0.0001
    minimum_pool_size: int = 2
    minimum_touches: int = 2
    minimum_distance: float = 0.0
    sweep_confirmation: bool = True
    internal_only: bool = False
    external_only: bool = False

    def __post_init__(self) -> None:
        if self.equal_threshold < 0 or self.minimum_distance < 0:
            raise DataIntegrityError("thresholds must be non-negative")
        if self.minimum_pool_size < 1 or self.minimum_touches < 2:
            raise DataIntegrityError("pool size must be positive and touches >= 2")
        if self.internal_only and self.external_only:
            raise DataIntegrityError("internal_only and external_only are mutually exclusive")
