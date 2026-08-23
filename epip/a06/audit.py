"""A06-E08 immutable audit evidence preparation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a06.projection import ProjectionResult
from epip.a06.replay import ProjectionReplay
from epip.core.integrity import DataIntegrityError, require_text

__all__ = ["AuditDiagnostics", "AuditPreparation", "ProjectionAudit"]


class _Immutable:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("immutable audit model")

    def _init(self, values: dict[str, object]) -> None:
        for name in self._field_names:
            object.__setattr__(self, name, values[name])

    def _values(self) -> tuple[object, ...]:
        return tuple(getattr(self, n) for n in self._field_names)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        assert isinstance(other, _Immutable)
        return self._values() == other._values()

    def __hash__(self) -> int:
        return hash((type(self), self._values()))


class ProjectionAudit(_Immutable):
    __slots__ = ("baseline_tag", "lineage", "mode", "projection_identity", "result_identity")
    _field_names = __slots__
    result_identity: str
    baseline_tag: str
    lineage: tuple[str, ...]
    mode: str
    projection_identity: str

    def __init__(self, result: ProjectionResult, replay: ProjectionReplay) -> None:
        if not isinstance(result, ProjectionResult) or not isinstance(replay, ProjectionReplay):
            raise DataIntegrityError("audit inputs have invalid type")
        if replay.result_identity != result.result_identity or replay.lineage != result.lineage:
            raise DataIntegrityError("audit context mismatch")
        self._init(
            {
                "baseline_tag": result.baseline_tag,
                "lineage": result.lineage,
                "mode": replay.mode,
                "projection_identity": result.projection_identity,
                "result_identity": result.result_identity,
            }
        )


class AuditPreparation(_Immutable):
    __slots__ = ("audit_identity", "complete")
    _field_names = __slots__
    audit_identity: str
    complete: bool

    def __init__(self, audit: ProjectionAudit) -> None:
        if not isinstance(audit, ProjectionAudit):
            raise DataIntegrityError("audit has invalid type")
        self._init({"audit_identity": audit.result_identity, "complete": True})


class AuditDiagnostics(_Immutable):
    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if diagnostics == ():
            values: tuple[str, ...] = ()
        else:
            if not isinstance(diagnostics, tuple):
                raise DataIntegrityError("diagnostics must be tuple")
            values = tuple(sorted(require_text(x, "diagnostics").strip() for x in diagnostics))
        self._init({"diagnostics": values})
