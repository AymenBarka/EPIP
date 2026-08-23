"""A06-E04 immutable provisional eligibility contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a06.authority import ProjectionAuthority
from epip.a06.foundation import ProjectionRequest
from epip.a06.planning import ProjectionPlan
from epip.a06.scope import ProjectionScope
from epip.core.integrity import DataIntegrityError, require_text

__all__ = ["EligibilityDiagnostics", "EligibilityValidation", "ProjectionEligibility"]


class _Immutable:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, n: str, v: object) -> None:
        del n, v
        raise FrozenInstanceError("immutable eligibility model")

    def _init(self, d: dict[str, object]) -> None:
        for n in self._field_names:
            object.__setattr__(self, n, d[n])

    def _vals(self) -> tuple[object, ...]:
        return tuple(getattr(self, n) for n in self._field_names)

    def __eq__(self, o: object) -> bool:
        if type(self) is not type(o):
            return NotImplemented
        assert isinstance(o, _Immutable)
        return self._vals() == o._vals()

    def __hash__(self) -> int:
        return hash((type(self), self._vals()))


def _text(v: object, f: str) -> str:
    return require_text(v, f).strip()


class ProjectionEligibility(_Immutable):
    __slots__ = ("authority_identity", "eligible", "knowledge_boundary", "plan_identity")
    _field_names = __slots__
    authority_identity: str
    eligible: bool
    knowledge_boundary: int
    plan_identity: str

    def __init__(
        self,
        plan: ProjectionPlan,
        authority: ProjectionAuthority,
        knowledge_boundary: object,
        eligible: object,
    ) -> None:
        if not isinstance(plan, ProjectionPlan):
            raise DataIntegrityError("plan must be a ProjectionPlan")
        if not isinstance(authority, ProjectionAuthority):
            raise DataIntegrityError("authority must be a ProjectionAuthority")
        if (
            isinstance(knowledge_boundary, bool)
            or not isinstance(knowledge_boundary, int)
            or knowledge_boundary < 1
        ):
            raise DataIntegrityError("knowledge_boundary must be positive")
        if not isinstance(eligible, bool):
            raise DataIntegrityError("eligible must be boolean")
        self._init(
            {
                "authority_identity": authority.authority_identity,
                "eligible": eligible,
                "knowledge_boundary": knowledge_boundary,
                "plan_identity": plan.plan_identity,
            }
        )


class EligibilityValidation(_Immutable):
    __slots__ = ("authority_identity", "plan_identity", "request_identity", "valid")
    _field_names = __slots__
    authority_identity: str
    plan_identity: str
    request_identity: str
    valid: bool

    def __init__(
        self,
        eligibility: ProjectionEligibility,
        plan: ProjectionPlan,
        request: ProjectionRequest,
        authority: ProjectionAuthority,
        scope: ProjectionScope,
    ) -> None:
        for obj, typ, name in (
            (eligibility, ProjectionEligibility, "eligibility"),
            (plan, ProjectionPlan, "plan"),
            (request, ProjectionRequest, "request"),
            (authority, ProjectionAuthority, "authority"),
            (scope, ProjectionScope, "scope"),
        ):
            if not isinstance(obj, typ):
                raise DataIntegrityError(f"{name} has invalid type")
        valid = (
            eligibility.plan_identity == plan.plan_identity
            and eligibility.authority_identity == authority.authority_identity
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


class EligibilityDiagnostics(_Immutable):
    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        vals: tuple[str, ...]
        if diagnostics == ():
            vals = ()
        else:
            if not isinstance(diagnostics, tuple):
                raise DataIntegrityError("diagnostics must be tuple")
            vals = tuple(sorted(_text(x, "diagnostics") for x in diagnostics))
        self._init({"diagnostics": vals})
