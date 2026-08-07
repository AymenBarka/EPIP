"""Liquidity domain errors."""

from collections.abc import Mapping
from types import MappingProxyType


class LiquidityError(Exception):
    def __init__(self, message: str, *, metadata: Mapping[str, object] | None = None) -> None:
        super().__init__(message)
        self.metadata = MappingProxyType(dict(metadata or {}))


class InvalidLiquidityInputError(LiquidityError):
    pass


class LiquidityVersionError(LiquidityError):
    pass


class LiquidityHistoryError(LiquidityError):
    pass
