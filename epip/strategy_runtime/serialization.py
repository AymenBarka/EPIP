"""Canonical tagged JSON serialization for immutable P01 contract graphs."""

from __future__ import annotations

import importlib
import json
from dataclasses import fields, is_dataclass
from enum import Enum
from math import isfinite
from typing import Any, TypeVar

from epip.core.integrity import DataIntegrityError

T = TypeVar("T")


def _qualified(value: type[object]) -> str:
    return f"{value.__module__}:{value.__qualname__}"


def _encode(value: Any) -> Any:
    if isinstance(value, Enum):
        return {"$enum": _qualified(type(value)), "value": value.value}
    if is_dataclass(value):
        return {
            "$type": _qualified(type(value)),
            "fields": {item.name: _encode(getattr(value, item.name)) for item in fields(value)},
        }
    slots = getattr(type(value), "__slots__", ())
    if slots and not isinstance(value, (str, bytes)):
        return {
            "$record": _qualified(type(value)),
            "fields": {name: _encode(getattr(value, name)) for name in slots},
        }
    if isinstance(value, tuple):
        return {"$tuple": [_encode(item) for item in value]}
    if isinstance(value, dict):
        return {"$dict": [[_encode(key), _encode(item)] for key, item in value.items()]}
    if type(value) is float and not isfinite(value):
        raise DataIntegrityError("NaN and infinity are not serializable")
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise DataIntegrityError(f"unsupported serialization type: {type(value).__name__}")


def _resolve(reference: object) -> type[Any]:
    if type(reference) is not str or not reference.startswith("epip.") or ":" not in reference:
        raise DataIntegrityError("serialized type reference is not an EPIP contract")
    module_name, qualified = reference.split(":", 1)
    value: Any = importlib.import_module(module_name)
    for part in qualified.split("."):
        value = getattr(value, part)
    if not isinstance(value, type):
        raise DataIntegrityError("serialized type reference does not resolve to a type")
    return value


def _decode(value: Any) -> Any:
    if not isinstance(value, dict):
        if type(value) is float and not isfinite(value):
            raise DataIntegrityError("NaN and infinity are not serializable")
        return value
    if "$tuple" in value:
        return tuple(_decode(item) for item in value["$tuple"])
    if "$dict" in value:
        return {_decode(key): _decode(item) for key, item in value["$dict"]}
    if "$enum" in value:
        return _resolve(value["$enum"])(_decode(value["value"]))
    if "$type" in value:
        cls = _resolve(value["$type"])
        kwargs = {name: _decode(item) for name, item in value["fields"].items()}
        try:
            return cls(**kwargs)
        except (TypeError, ValueError) as exc:
            raise DataIntegrityError("serialized dataclass failed reconstruction") from exc
    if "$record" in value:
        cls = _resolve(value["$record"])
        decoded = {name: _decode(item) for name, item in value["fields"].items()}
        instance = object.__new__(cls)
        initializer = getattr(instance, "_init", None)
        if initializer is None:
            raise DataIntegrityError("serialized record has no immutable reconstruction boundary")
        initializer(decoded)
        return instance
    raise DataIntegrityError("malformed tagged serialization payload")


def to_dict(value: object) -> dict[str, Any]:
    encoded = _encode(value)
    if not isinstance(encoded, dict):
        raise DataIntegrityError("root contract must serialize as an object")
    return encoded


def from_dict(expected: type[T], payload: dict[str, Any]) -> T:  # noqa: UP047
    result = _decode(payload)
    if type(result) is not expected:
        raise DataIntegrityError("serialized root type does not match expected contract")
    return result


def to_json(value: object) -> str:
    return json.dumps(to_dict(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def from_json(expected: type[T], payload: str) -> T:  # noqa: UP047
    try:
        decoded = json.loads(payload)
    except (TypeError, ValueError) as exc:
        raise DataIntegrityError("payload must be valid JSON") from exc
    if not isinstance(decoded, dict):
        raise DataIntegrityError("serialized root must be an object")
    return from_dict(expected, decoded)
