"""Shared validation helpers for the additive mapping foundation."""

from __future__ import annotations

from typing import TypeVar

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime._base import (
    digest,
    finite,
    instant,
    require_digest,
    text,
    timestamp,
    unique_texts,
)

FOUNDATION_SCHEMA_VERSION = "p02-f00-v1"
T = TypeVar("T")


def exact(value: object, expected: type[T], field: str) -> T:  # noqa: UP047
    if type(value) is not expected:
        raise DataIntegrityError(f"{field} must be a {expected.__name__}")
    return value


def exact_tuple(  # noqa: UP047
    value: object, expected: type[T], field: str, *, empty: bool = True
) -> tuple[T, ...]:
    if type(value) is not tuple or any(type(item) is not expected for item in value):
        raise DataIntegrityError(f"{field} must be a tuple of {expected.__name__}")
    if not empty and not value:
        raise DataIntegrityError(f"{field} must not be empty")
    return value


def boolean(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise DataIntegrityError(f"{field} must be a bool")
    return value


def non_negative_int(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise DataIntegrityError(f"{field} must be a non-negative int")
    return value


def version(value: object, field: str = "schema_version") -> str:
    result = text(value, field)
    if result != FOUNDATION_SCHEMA_VERSION:
        raise DataIntegrityError(f"unsupported {field}")
    return result


__all__ = [
    "FOUNDATION_SCHEMA_VERSION",
    "boolean",
    "digest",
    "exact",
    "exact_tuple",
    "finite",
    "instant",
    "non_negative_int",
    "require_digest",
    "text",
    "timestamp",
    "unique_texts",
    "version",
]
