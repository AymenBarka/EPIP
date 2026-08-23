"""A06-E06 immutable projection-result contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a06.authority import ProjectionAuthority
from epip.a06.compatibility import ProjectionCompatibility
from epip.a06.eligibility import ProjectionEligibility
from epip.a06.foundation import ProjectionRequest
from epip.a06.planning import ProjectionPlan
from epip.a06.scope import ProjectionScope
from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text

__all__ = ["ProjectionDiagnostics", "ProjectionResult", "ProjectionResultValidation"]


class _Immutable:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("immutable projection result model")

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


def _lineage(value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError("lineage must be an immutable tuple")
    result = tuple(_text(item, "lineage") for item in value)
    if not result:
        raise MissingFieldError("lineage must not be empty")
    if len(set(result)) != len(result):
        raise DataIntegrityError("lineage must not contain duplicates")
    return tuple(sorted(result))


class ProjectionResult(_Immutable):
    """Immutable derived projection result and complete predecessor lineage."""

    __slots__ = (
        "authority_identity",
        "compatible",
        "eligible",
        "lineage",
        "plan_identity",
        "request_identity",
        "result_identity",
    )
    _field_names = __slots__
    authority_identity: str
    compatible: bool
    eligible: bool
    lineage: tuple[str, ...]
    plan_identity: str
    request_identity: str
    result_identity: str

    def __init__(
        self,
        result_identity: object,
        compatibility: ProjectionCompatibility,
        eligibility: ProjectionEligibility,
        plan: ProjectionPlan,
        request: ProjectionRequest,
        authority: ProjectionAuthority,
        scope: ProjectionScope,
        lineage: object,
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
        if not isinstance(result_identity, str) or not result_identity.strip():
            raise DataIntegrityError("result_identity must be non-empty text")
        if compatibility.plan_identity != plan.plan_identity:
            raise DataIntegrityError("compatibility plan identity mismatch")
        if compatibility.authority_identity != authority.authority_identity:
            raise DataIntegrityError("compatibility authority identity mismatch")
        if eligibility.plan_identity != plan.plan_identity:
            raise DataIntegrityError("eligibility plan identity mismatch")
        if eligibility.authority_identity != authority.authority_identity:
            raise DataIntegrityError("eligibility authority identity mismatch")
        if set(scope.target_artifacts) != set(request.target_scope):
            raise DataIntegrityError("scope and request target mismatch")
        self._init(
            {
                "authority_identity": authority.authority_identity,
                "compatible": compatibility.compatible,
                "eligible": eligibility.eligible,
                "lineage": _lineage(lineage),
                "plan_identity": plan.plan_identity,
                "request_identity": request.request_identity,
                "result_identity": result_identity.strip(),
            }
        )


class ProjectionResultValidation(_Immutable):
    """Immutable validation outcome for a projection result."""

    __slots__ = ("authority_identity", "plan_identity", "request_identity", "valid")
    _field_names = __slots__
    authority_identity: str
    plan_identity: str
    request_identity: str
    valid: bool

    def __init__(
        self,
        result: ProjectionResult,
        compatibility: ProjectionCompatibility,
        eligibility: ProjectionEligibility,
        plan: ProjectionPlan,
        request: ProjectionRequest,
        authority: ProjectionAuthority,
        scope: ProjectionScope,
    ) -> None:
        for obj, typ, name in (
            (result, ProjectionResult, "result"),
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
            result.authority_identity == authority.authority_identity
            and result.plan_identity == plan.plan_identity
            and result.request_identity == request.request_identity
            and result.compatible == compatibility.compatible
            and result.eligible == eligibility.eligible
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


class ProjectionDiagnostics(_Immutable):
    """Deterministically ordered immutable projection diagnostics."""

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
