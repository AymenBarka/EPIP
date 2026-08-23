"""A06-E02 immutable projection-scope contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a06.authority import ProjectionAuthority
from epip.a06.foundation import ProjectionRequest
from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text

__all__ = ["ProjectionScope", "ScopeDiagnostics", "ScopeValidation"]


class _ImmutableRecord:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable scope model")

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


def _items(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field} must be an immutable tuple")
    result = tuple(sorted(require_text(item, field).strip() for item in value))
    if not result:
        raise MissingFieldError(f"{field} must not be empty")
    if len(set(result)) != len(result):
        raise DataIntegrityError(f"{field} must not contain duplicates")
    return result


class ProjectionScope(_ImmutableRecord):
    """Immutable target artifacts and temporal dimensions of a projection."""

    __slots__ = ("target_artifacts", "temporal_dimensions")
    _field_names = __slots__
    target_artifacts: tuple[str, ...]
    temporal_dimensions: tuple[str, ...]

    def __init__(self, target_artifacts: object, temporal_dimensions: object) -> None:
        self._initialize(
            {
                "temporal_dimensions": _items(temporal_dimensions, "temporal_dimensions"),
                "target_artifacts": _items(target_artifacts, "target_artifacts"),
            }
        )


class ScopeValidation(_ImmutableRecord):
    """Immutable scope validation outcome."""

    __slots__ = ("authority_identity", "request_identity", "valid")
    _field_names = __slots__
    authority_identity: str
    request_identity: str
    valid: bool

    def __init__(
        self,
        scope: ProjectionScope,
        request: ProjectionRequest,
        authority: ProjectionAuthority,
    ) -> None:
        if not isinstance(scope, ProjectionScope):
            raise DataIntegrityError("scope must be a ProjectionScope")
        if not isinstance(request, ProjectionRequest):
            raise DataIntegrityError("request must be a ProjectionRequest")
        if not isinstance(authority, ProjectionAuthority):
            raise DataIntegrityError("authority must be a ProjectionAuthority")
        valid = set(scope.target_artifacts).issubset(authority.permitted_scope) and set(
            scope.target_artifacts
        ) == set(request.target_scope)
        self._initialize(
            {
                "authority_identity": authority.authority_identity,
                "request_identity": request.request_identity,
                "valid": valid,
            }
        )


class ScopeDiagnostics(_ImmutableRecord):
    """Immutable deterministic scope diagnostics."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        values = () if diagnostics == () else _items(diagnostics, "diagnostics")
        self._initialize({"diagnostics": values})
