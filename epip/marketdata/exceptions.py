"""Exceptions for the Market Data Layer."""

from __future__ import annotations


class MarketDataError(Exception):
    """Base error for market data operations."""


class ConnectionError(MarketDataError):
    """Raised when provider connection fails."""


class ProviderError(MarketDataError):
    """Raised when a provider operation fails."""


class TimeoutError(MarketDataError):
    """Raised when an operation exceeds timeout."""


class RateLimitError(MarketDataError):
    """Raised when provider rate limits are exceeded."""


class InvalidRequestError(MarketDataError):
    """Raised when a request payload is invalid."""
