"""A06-E07 immutable deterministic replay contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a06.projection import ProjectionResult
from epip.core.integrity import DataIntegrityError, require_text

__all__ = ["ProjectionReplay", "ReplayDiagnostics", "ReplayValidation"]


class _Immutable:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("immutable replay model")

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


class ProjectionReplay(_Immutable):
    """Immutable replay inputs, mode and projection lineage."""

    __slots__ = (
        "authority_identity",
        "baseline_tag",
        "lineage",
        "mode",
        "projection_identity",
        "result_identity",
        "temporal_basis",
    )
    _field_names = __slots__
    lineage: tuple[str, ...]
    mode: str
    result_identity: str
    projection_identity: str
    baseline_tag: str
    authority_identity: str
    temporal_basis: str

    def __init__(self, result: ProjectionResult, mode: object, lineage: object) -> None:
        if not isinstance(result, ProjectionResult):
            raise DataIntegrityError("result must be a ProjectionResult")
        if not isinstance(lineage, tuple):
            raise DataIntegrityError("lineage must be an immutable tuple")
        canonical = tuple(sorted(_text(item, "lineage") for item in lineage))
        if canonical != result.lineage:
            raise DataIntegrityError("replay lineage mismatch")
        self._init(
            {
                "authority_identity": result.authority_identity,
                "baseline_tag": result.baseline_tag,
                "lineage": result.lineage,
                "mode": _text(mode, "mode"),
                "projection_identity": result.projection_identity,
                "result_identity": result.result_identity,
                "temporal_basis": result.temporal_basis,
            }
        )


class ReplayValidation(_Immutable):
    """Immutable replay validation outcome."""

    __slots__ = (
        "baseline_tag",
        "lineage",
        "mode",
        "projection_identity",
        "result_identity",
        "valid",
    )
    _field_names = __slots__
    result_identity: str
    valid: bool
    baseline_tag: str
    lineage: tuple[str, ...]
    mode: str
    projection_identity: str

    def __init__(self, replay: ProjectionReplay, result: ProjectionResult) -> None:
        if not isinstance(replay, ProjectionReplay):
            raise DataIntegrityError("replay must be a ProjectionReplay")
        if not isinstance(result, ProjectionResult):
            raise DataIntegrityError("result must be a ProjectionResult")
        self._init(
            {
                "baseline_tag": replay.baseline_tag,
                "lineage": replay.lineage,
                "mode": replay.mode,
                "projection_identity": replay.projection_identity,
                "result_identity": result.result_identity,
                "valid": replay.result_identity == result.result_identity
                and replay.projection_identity == result.projection_identity
                and replay.baseline_tag == result.baseline_tag
                and replay.temporal_basis == result.temporal_basis
                and replay.lineage == result.lineage,
            }
        )


class ReplayDiagnostics(_Immutable):
    """Deterministically ordered immutable replay diagnostics."""

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
