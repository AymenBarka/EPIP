"""Domain exceptions for Market Structure Engine."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType


class MarketStructureError(Exception):
    """Base error type for market structure domain failures."""

    def __init__(self, message: str, *, metadata: Mapping[str, object] | None = None) -> None:
        super().__init__(message)
        self.metadata = MappingProxyType(dict(metadata or {}))


class InvalidStructureInputError(MarketStructureError):
    """Raised when input data is invalid or insufficient."""


class IllegalStructureTransitionError(MarketStructureError):
    """Raised when a state-machine transition is not allowed."""


class InvalidStructureError(MarketStructureError):
    """Raised when a market structure violates domain invariants."""


class InvalidTrendError(InvalidStructureError):
    """Raised when a trend payload is invalid."""


class InvalidBOSError(InvalidStructureError):
    """Raised when a break-of-structure payload is invalid."""


class InvalidCHOCHError(InvalidStructureError):
    """Raised when a change-of-character payload is invalid."""


class InvalidRangeError(InvalidStructureError):
    """Raised when a range payload is invalid."""


class StructureVersionError(MarketStructureError):
    """Raised when a structure version is missing, duplicated, or invalid."""


class HistoryError(MarketStructureError):
    """Raised when structure history cannot satisfy an operation."""
