"""A06-E09 integrated immutable closure contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a06.audit import AuditPreparation, ProjectionAudit
from epip.core.integrity import DataIntegrityError, require_text

__all__ = [
    "IntegratedProjectionClosure",
    "ProjectionClosureDiagnostics",
    "ProjectionClosureVerifier",
]


class _Immutable:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("immutable closure model")

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


class IntegratedProjectionClosure(_Immutable):
    __slots__ = (
        "audit_identity",
        "baseline_tag",
        "closed",
        "lineage",
        "mode",
        "projection_identity",
    )
    _field_names = __slots__
    audit_identity: str
    baseline_tag: str
    lineage: tuple[str, ...]
    mode: str
    projection_identity: str
    closed: bool

    def __init__(self, audit: ProjectionAudit, preparation: AuditPreparation) -> None:
        if not isinstance(audit, ProjectionAudit) or not isinstance(preparation, AuditPreparation):
            raise DataIntegrityError("closure inputs have invalid type")
        if preparation.audit_identity != audit.result_identity or not preparation.complete:
            raise DataIntegrityError("closure preparation mismatch")
        self._init(
            {
                "audit_identity": audit.result_identity,
                "baseline_tag": audit.baseline_tag,
                "lineage": audit.lineage,
                "mode": audit.mode,
                "projection_identity": audit.projection_identity,
                "closed": True,
            }
        )


class ProjectionClosureVerifier(_Immutable):
    __slots__ = ("valid",)
    _field_names = __slots__
    valid: bool

    def __init__(self, closure: IntegratedProjectionClosure) -> None:
        if not isinstance(closure, IntegratedProjectionClosure):
            raise DataIntegrityError("closure has invalid type")
        self._init({"valid": closure.closed})


class ProjectionClosureDiagnostics(_Immutable):
    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if diagnostics == ():
            values: tuple[str, ...] = ()
        else:
            if not isinstance(diagnostics, tuple):
                raise DataIntegrityError("diagnostics must be tuple")
            values = tuple(
                sorted(require_text(item, "diagnostics").strip() for item in diagnostics)
            )
        self._init({"diagnostics": values})
