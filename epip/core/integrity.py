"""Shared fail-fast data-integrity policy for EPIP business objects."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from functools import wraps
from inspect import signature
from math import isfinite
from types import MappingProxyType
from typing import ParamSpec, Protocol, TypeVar, runtime_checkable

P = ParamSpec("P")
R = TypeVar("R")


class DataIntegrityError(ValueError):
    """Base exception raised when business data violates an invariant."""


class MissingFieldError(DataIntegrityError):
    """Raised when a mandatory value is absent or empty."""


class NumericIntegrityError(DataIntegrityError):
    """Raised when a numeric value is non-finite or outside its domain."""


class VersionIntegrityError(DataIntegrityError):
    """Raised when a schema or snapshot version is invalid."""


class RelationshipIntegrityError(DataIntegrityError):
    """Raised when related business values contradict one another."""


class SerializationIntegrityError(DataIntegrityError):
    """Raised when serialized input is missing, corrupted, or incompatible."""


class EventIntegrityError(DataIntegrityError):
    """Raised when an invalid object is submitted to the EventBus."""


class IntegrityContractError(DataIntegrityError):
    """Raised when an object does not participate in the integrity contract."""


@runtime_checkable
class IntegrityValidatable(Protocol):
    """Protocol implemented by objects exposing explicit invariant validation."""

    def validate_integrity(self) -> None:
        """Raise a domain exception when an invariant is violated."""


def deep_freeze(value: object) -> object:
    """Return a recursively immutable copy suitable for business state."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: deep_freeze(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(deep_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(deep_freeze(item) for item in value)
    if isinstance(value, bytearray):
        return bytes(value)
    return value


def deep_thaw(value: object) -> object:
    """Return a serialization-safe copy of recursively immutable state."""
    if isinstance(value, Mapping):
        return {key: deep_thaw(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [deep_thaw(item) for item in value]
    return value


def require_text(value: object, field: str) -> str:
    """Require a non-empty string without coercing corrupted input."""
    if not isinstance(value, str) or not value.strip():
        raise MissingFieldError(f"{field} must be a non-empty string")
    return value


def require_finite(value: object, field: str) -> float:
    """Require a finite real number while rejecting booleans and coercion."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NumericIntegrityError(f"{field} must be a real number")
    result = float(value)
    if not isfinite(result):
        raise NumericIntegrityError(f"{field} must be finite")
    return result


def require_non_negative(value: object, field: str) -> float:
    """Require a finite value greater than or equal to zero."""
    result = require_finite(value, field)
    if result < 0.0:
        raise NumericIntegrityError(f"{field} must be non-negative")
    return result


def require_positive(value: object, field: str) -> float:
    """Require a finite value strictly greater than zero."""
    result = require_finite(value, field)
    if result <= 0.0:
        raise NumericIntegrityError(f"{field} must be positive")
    return result


def require_unit_interval(value: object, field: str) -> float:
    """Require a probability, percentage, or score in the closed unit interval."""
    result = require_finite(value, field)
    if not 0.0 <= result <= 1.0:
        raise NumericIntegrityError(f"{field} must be between 0.0 and 1.0")
    return result


def require_signed_unit_interval(value: object, field: str) -> float:
    """Require a signed score in the closed interval from -1.0 to 1.0."""
    result = require_finite(value, field)
    if not -1.0 <= result <= 1.0:
        raise NumericIntegrityError(f"{field} must be between -1.0 and 1.0")
    return result


def require_percentage(value: object, field: str) -> float:
    """Require a score expressed on the inclusive 0-to-100 scale."""
    result = require_finite(value, field)
    if not 0.0 <= result <= 100.0:
        raise NumericIntegrityError(f"{field} must be between 0.0 and 100.0")
    return result


def require_version(value: object, field: str = "version") -> int:
    """Require a positive, non-boolean integer version."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise VersionIntegrityError(f"{field} must be a positive integer")
    return value


def _validate_named_value(value: object, field: str) -> None:
    """Apply conservative, name-based invariants shared by pipeline DTOs."""
    name = field.rsplit(".", 1)[-1]
    if value is None or isinstance(value, (str, bytes, bool, Enum)):
        return
    if isinstance(value, (int, float)):
        require_finite(value, field)
        if any(token in name for token in ("probability", "confidence", "confluence")):
            require_unit_interval(value, field)
        elif not name.startswith("net_") and any(
            token in name
            for token in (
                "quantity",
                "allocation",
                "drawdown",
                "leverage",
                "margin",
                "exposure",
                "commission",
                "volume",
            )
        ):
            require_non_negative(value, field)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _validate_named_value(item, f"{field}[{key!r}]")
        return
    if isinstance(value, (tuple, frozenset)):
        for index, item in enumerate(value):
            _validate_named_value(item, f"{field}[{index}]")
        return
    if isinstance(value, (list, dict, set, bytearray)):
        raise RelationshipIntegrityError(f"{field} must be deeply immutable")
    if is_dataclass(value):
        validate_dataclass_integrity(value, field)


def validate_dataclass_integrity(value: object, field: str = "object") -> None:
    """Validate every stored field of an immutable pipeline dataclass."""
    if not is_dataclass(value) or isinstance(value, type):
        raise IntegrityContractError(f"{field} must be an integrity-aware dataclass")
    parameters = getattr(type(value), "__dataclass_params__", None)
    if parameters is None or not parameters.frozen:
        raise IntegrityContractError(f"{field} must be immutable")
    for item in fields(value):
        current = getattr(value, item.name)
        if item.name in {"schema_version", "snapshot_version", "version"} and isinstance(
            current, int
        ):
            require_version(current, f"{field}.{item.name}")
        _validate_named_value(current, f"{field}.{item.name}")


def validate_object(value: object, field: str = "object", *, explicit: bool = False) -> None:
    """Validate an explicit contract or an immutable pipeline dataclass."""
    if value is None:
        raise MissingFieldError(f"{field} must not be None")
    if isinstance(value, IntegrityValidatable):
        value.validate_integrity()
        validate_dataclass_integrity(value, field)
        return
    if explicit:
        raise IntegrityContractError(f"{field} does not implement IntegrityValidatable")
    validate_dataclass_integrity(value, field)


def integrity_deserializer(function: Callable[P, R]) -> Callable[P, R]:  # noqa: UP047
    """Translate malformed payload failures into the public integrity hierarchy."""

    @wraps(function)
    def guarded(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return function(*args, **kwargs)
        except DataIntegrityError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise SerializationIntegrityError(f"corrupted serialized payload: {exc}") from exc

    return guarded


def integrity_boundary(function: Callable[P, R]) -> Callable[P, R]:  # noqa: UP047
    """Validate immutable business inputs and outputs at an engine boundary."""

    parameters = tuple(signature(function).parameters)

    @wraps(function)
    def guarded(*args: P.args, **kwargs: P.kwargs) -> R:
        for name, value in zip(parameters, args, strict=False):
            if name == "self" or value is None:
                continue
            if is_dataclass(value) and not isinstance(value, type):
                validate_object(value, f"input.{name}")
            elif isinstance(value, tuple):
                for index, item in enumerate(value):
                    if is_dataclass(item) and not isinstance(item, type):
                        validate_object(item, f"input.{name}[{index}]")
        for name, value in kwargs.items():
            if value is not None and is_dataclass(value) and not isinstance(value, type):
                validate_object(value, f"input.{name}")
        result = function(*args, **kwargs)
        if result is not None and is_dataclass(result) and not isinstance(result, type):
            validate_object(result, "output")
        elif isinstance(result, tuple):
            for index, item in enumerate(result):
                if is_dataclass(item) and not isinstance(item, type):
                    validate_object(item, f"output[{index}]")
        return result

    setattr(guarded, "__integrity_boundary__", True)  # noqa: B010
    return guarded
