"""A06-E03 immutable deterministic projection-planning contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a06.authority import ProjectionAuthority
from epip.a06.foundation import ProjectionRequest
from epip.a06.scope import ProjectionScope
from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text

__all__ = ["PlanDiagnostics", "PlanValidation", "ProjectionPlan"]


class _ImmutableRecord:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable planning model")

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


def _items(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field} must be an immutable tuple")
    result = tuple(sorted(_text(item, field) for item in value))
    if not result:
        raise MissingFieldError(f"{field} must not be empty")
    if len(set(result)) != len(result):
        raise DataIntegrityError(f"{field} must not contain duplicates")
    return result


class ProjectionPlan(_ImmutableRecord):
    """Canonical ordered derivation plan for a projection."""

    __slots__ = ("authority_identity", "plan_identity", "steps")
    _field_names = __slots__
    authority_identity: str
    plan_identity: str
    steps: tuple[str, ...]

    def __init__(
        self, plan_identity: object, steps: object, authority: ProjectionAuthority
    ) -> None:
        if not isinstance(authority, ProjectionAuthority):
            raise DataIntegrityError("authority must be a ProjectionAuthority")
        self._initialize(
            {
                "authority_identity": authority.authority_identity,
                "plan_identity": _text(plan_identity, "plan_identity"),
                "steps": _items(steps, "steps"),
            }
        )


class PlanValidation(_ImmutableRecord):
    """Immutable outcome of validating a plan against E00-E02 contracts."""

    __slots__ = ("authority_identity", "plan_identity", "request_identity", "valid")
    _field_names = __slots__
    authority_identity: str
    plan_identity: str
    request_identity: str
    valid: bool

    def __init__(
        self,
        plan: ProjectionPlan,
        request: ProjectionRequest,
        authority: ProjectionAuthority,
        scope: ProjectionScope,
    ) -> None:
        if not isinstance(plan, ProjectionPlan):
            raise DataIntegrityError("plan must be a ProjectionPlan")
        if not isinstance(request, ProjectionRequest):
            raise DataIntegrityError("request must be a ProjectionRequest")
        if not isinstance(authority, ProjectionAuthority):
            raise DataIntegrityError("authority must be a ProjectionAuthority")
        if not isinstance(scope, ProjectionScope):
            raise DataIntegrityError("scope must be a ProjectionScope")
        valid = (
            plan.authority_identity == authority.authority_identity
            and set(scope.target_artifacts) == set(request.target_scope)
            and set(scope.target_artifacts).issubset(authority.permitted_scope)
        )
        self._initialize(
            {
                "authority_identity": authority.authority_identity,
                "plan_identity": plan.plan_identity,
                "request_identity": request.request_identity,
                "valid": valid,
            }
        )


class PlanDiagnostics(_ImmutableRecord):
    """Immutable deterministic planning diagnostics."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        values = () if diagnostics == () else _items(diagnostics, "diagnostics")
        self._initialize({"diagnostics": values})
