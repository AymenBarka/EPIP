"""A06-E00 immutable projection-foundation contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text

__all__ = [
    "ProjectionFoundationDiagnostics",
    "ProjectionIdentity",
    "ProjectionRequest",
]


class _ImmutableRecord:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable projection foundation model")

    def _initialize(self, values: dict[str, object]) -> None:
        for name in self._field_names:
            object.__setattr__(self, name, values[name])

    def _values(self) -> tuple[object, ...]:
        return tuple(getattr(self, name) for name in self._field_names)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        assert isinstance(other, _ImmutableRecord)
        return self._values() == other._values()

    def __hash__(self) -> int:
        return hash((type(self), self._values()))


def _text(value: object, field: str) -> str:
    return require_text(value, field).strip()


def _version(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DataIntegrityError("policy_version must be a positive integer")
    return value


def _text_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field} must be an immutable tuple")
    result = tuple(sorted(_text(item, field) for item in value))
    if not result:
        raise MissingFieldError(f"{field} must not be empty")
    if len(set(result)) != len(result):
        raise DataIntegrityError(f"{field} must not contain duplicates")
    return result


class ProjectionIdentity(_ImmutableRecord):
    """Canonical identity of an A06 projection baseline."""

    __slots__ = ("authority_identity", "baseline_tag", "identity")
    _field_names = __slots__
    authority_identity: str
    baseline_tag: str
    identity: str

    def __init__(self, identity: object, baseline_tag: object, authority_identity: object) -> None:
        self._initialize(
            {
                "authority_identity": _text(authority_identity, "authority_identity"),
                "baseline_tag": _text(baseline_tag, "baseline_tag"),
                "identity": _text(identity, "identity"),
            }
        )


class ProjectionRequest(_ImmutableRecord):
    """Immutable request to derive a projection from an A05 baseline."""

    __slots__ = (
        "policy_version",
        "projection_mode",
        "request_identity",
        "target_scope",
        "temporal_basis",
    )
    _field_names = __slots__
    policy_version: int
    projection_mode: str
    request_identity: str
    target_scope: tuple[str, ...]
    temporal_basis: str

    def __init__(
        self,
        request_identity: object,
        target_scope: object,
        temporal_basis: object,
        projection_mode: object,
        policy_version: object,
    ) -> None:
        self._initialize(
            {
                "policy_version": _version(policy_version),
                "projection_mode": _text(projection_mode, "projection_mode"),
                "request_identity": _text(request_identity, "request_identity"),
                "target_scope": _text_tuple(target_scope, "target_scope"),
                "temporal_basis": _text(temporal_basis, "temporal_basis"),
            }
        )


class ProjectionFoundationDiagnostics(_ImmutableRecord):
    """Deterministically ordered immutable foundation diagnostics."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if diagnostics == ():
            canonical: tuple[str, ...] = ()
        else:
            canonical = _text_tuple(diagnostics, "diagnostics")
        self._initialize({"diagnostics": canonical})
