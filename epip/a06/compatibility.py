"""A06-E05 immutable compatibility contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a06.authority import ProjectionAuthority
from epip.a06.eligibility import ProjectionEligibility
from epip.a06.foundation import ProjectionRequest
from epip.a06.planning import ProjectionPlan
from epip.a06.scope import ProjectionScope
from epip.core.integrity import DataIntegrityError, require_text

__all__ = ["CompatibilityDiagnostics", "CompatibilityValidation", "ProjectionCompatibility"]


class _Immutable:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("immutable compatibility model")

    def _init(self, values: dict[str, object]) -> None:
        for name in self._field_names:
            object.__setattr__(self, name, values[name])

    def _values(self) -> tuple[object, ...]:
        return tuple(getattr(self, name) for name in self._field_names)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        assert isinstance(other, _Immutable)
        return self._values() == other._values()

    def __hash__(self) -> int:
        return hash((type(self), self._values()))


def _text(value: object, field: str) -> str:
    return require_text(value, field).strip()


class ProjectionCompatibility(_Immutable):
    __slots__ = ("authority_identity", "compatible", "plan_identity")
    _field_names = __slots__
    authority_identity: str
    compatible: bool
    plan_identity: str

    def __init__(
        self, plan: ProjectionPlan, authority: ProjectionAuthority, compatible: object
    ) -> None:
        if not isinstance(plan, ProjectionPlan):
            raise DataIntegrityError("plan must be a ProjectionPlan")
        if not isinstance(authority, ProjectionAuthority):
            raise DataIntegrityError("authority must be a ProjectionAuthority")
        if not isinstance(compatible, bool):
            raise DataIntegrityError("compatible must be boolean")
        self._init(
            {
                "authority_identity": authority.authority_identity,
                "compatible": compatible,
                "plan_identity": plan.plan_identity,
            }
        )


class CompatibilityValidation(_Immutable):
    __slots__ = ("authority_identity", "plan_identity", "request_identity", "valid")
    _field_names = __slots__
    authority_identity: str
    plan_identity: str
    request_identity: str
    valid: bool

    def __init__(
        self,
        compatibility: ProjectionCompatibility,
        eligibility: ProjectionEligibility,
        plan: ProjectionPlan,
        request: ProjectionRequest,
        authority: ProjectionAuthority,
        scope: ProjectionScope,
    ) -> None:
        for obj, typ, name in (
            (compatibility, ProjectionCompatibility, "compatibility"),
            (eligibility, ProjectionEligibility, "eligibility"),
            (plan, ProjectionPlan, "plan"),
            (request, ProjectionRequest, "request"),
            (authority, ProjectionAuthority, "authority"),
            (scope, ProjectionScope, "scope"),
        ):
            if not isinstance(obj, typ):
                raise DataIntegrityError(f"{name} has invalid type")
        valid = (
            compatibility.plan_identity == plan.plan_identity
            and compatibility.authority_identity == authority.authority_identity
            and compatibility.compatible
            and eligibility.eligible
            and set(scope.target_artifacts) == set(request.target_scope)
        )
        self._init(
            {
                "authority_identity": authority.authority_identity,
                "plan_identity": plan.plan_identity,
                "request_identity": request.request_identity,
                "valid": valid,
            }
        )


class CompatibilityDiagnostics(_Immutable):
    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if diagnostics == ():
            values: tuple[str, ...] = ()
        else:
            if not isinstance(diagnostics, tuple):
                raise DataIntegrityError("diagnostics must be tuple")
            values = tuple(sorted(_text(item, "diagnostics") for item in diagnostics))
        self._init({"diagnostics": values})
