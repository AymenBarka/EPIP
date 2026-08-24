"""Shared validation and canonical identity helpers for P01 contracts."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
from math import isfinite
from typing import Any

from epip.core.integrity import DataIntegrityError

CONTRACT_VERSION = "p01-v1"


def text(value: object, field: str) -> str:
    if type(value) is not str or not value.strip():
        raise DataIntegrityError(f"{field} must be non-empty text")
    return value


def optional_text(value: object, field: str) -> str | None:
    return None if value is None else text(value, field)


def timestamp(value: object, field: str) -> str:
    raw = text(value, field)
    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
    except (OverflowError, ValueError) as exc:
        raise DataIntegrityError(f"{field} must be timezone-aware ISO-8601") from exc
    return parsed.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value)


def finite(value: object, field: str, *, non_negative: bool = False) -> float:
    if type(value) not in (int, float):
        raise DataIntegrityError(f"{field} must be finite")
    assert isinstance(value, (int, float))
    result = float(value)
    if not isfinite(result):
        raise DataIntegrityError(f"{field} must be finite")
    if non_negative and result < 0.0:
        raise DataIntegrityError(f"{field} must be non-negative")
    return result


def unique_texts(value: object, field: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise DataIntegrityError(f"{field} must be a tuple")
    result = tuple(sorted(text(item, field) for item in value))
    if not allow_empty and not result:
        raise DataIntegrityError(f"{field} must not be empty")
    if len(set(result)) != len(result):
        raise DataIntegrityError(f"{field} must be unique")
    return result


def canonical(value: Any, *, exclude: frozenset[str] = frozenset()) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {
            item.name: canonical(getattr(value, item.name))
            for item in fields(value)
            if item.name not in exclude
        }
    if isinstance(value, tuple):
        return [canonical(item) for item in value]
    if isinstance(value, list):
        return [canonical(item) for item in value]
    if isinstance(value, dict):
        return {str(key): canonical(item) for key, item in sorted(value.items())}
    slots = getattr(type(value), "__slots__", ())
    if slots and not isinstance(value, (str, bytes)):
        return {name: canonical(getattr(value, name)) for name in slots if name not in exclude}
    if type(value) is float and not isfinite(value):
        raise DataIntegrityError("canonical values must not contain NaN or infinity")
    return value


def canonical_json(value: object, *, exclude: frozenset[str] = frozenset()) -> str:
    return json.dumps(canonical(value, exclude=exclude), sort_keys=True, separators=(",", ":"))


def digest(value: object, *, exclude: frozenset[str] = frozenset()) -> str:
    return sha256(canonical_json(value, exclude=exclude).encode("utf-8")).hexdigest()


def require_digest(value: object, field: str) -> str:
    result = text(value, field)
    if len(result) != 64 or any(char not in "0123456789abcdef" for char in result):
        raise DataIntegrityError(f"{field} must be a lowercase SHA-256 digest")
    return result
