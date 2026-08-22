"""Deterministic replay and historical compatibility validation (A05-E07)."""

from __future__ import annotations

__all__ = [
    "ReplayCompatibilityValidator",
    "ReplayCompatibilityValidation",
    "ReplayCompatibilityDiagnostics",
]

from dataclasses import FrozenInstanceError
from typing import ClassVar, NoReturn

from epip.core.integrity import DataIntegrityError, require_text
from epip.temporal.model import (
    CanonicalInstant,
    TemporalBoundary,
    TemporalDiagnosticCode,
    TemporalDiagnosticReason,
)


class _Immutable:
    __slots__ = ()
    _fields: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable replay model")

    def _init(self, values: dict[str, object]) -> None:
        for name in self._fields:
            object.__setattr__(self, name, values[name])

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        assert isinstance(other, _Immutable)
        return self._values() == other._values()

    def __hash__(self) -> int:
        return hash((type(self), self._values()))

    def _values(self) -> tuple[object, ...]:
        return tuple(getattr(self, name) for name in self._fields)


def _key(value: CanonicalInstant) -> tuple[object, ...]:
    return (
        value.value,
        value.precision,
        value.time_scale,
        value.timezone_basis,
        value.authority_identity,
    )


def _basis(left: CanonicalInstant, right: CanonicalInstant) -> bool:
    return _key(left)[1:] == _key(right)[1:]


def _fail(reason: str) -> NoReturn:
    raise DataIntegrityError(f"{TemporalDiagnosticCode.HISTORICAL_AMBIGUITY.value}: {reason}")


class ReplayCompatibilityValidation(_Immutable):
    __slots__ = (
        "validation_identity",
        "boundary_identity",
        "replay_time",
        "historical_time",
        "knowledge_boundary",
        "historical_visible",
        "exposure_valid",
        "mode",
        "predecessor_context",
        "historical_mode",
        "revision_mode",
    )
    _fields = __slots__
    validation_identity: str
    boundary_identity: str
    replay_time: CanonicalInstant
    historical_time: CanonicalInstant
    knowledge_boundary: CanonicalInstant
    historical_visible: bool
    exposure_valid: bool
    mode: str
    predecessor_context: tuple[tuple[str, str], ...]
    historical_mode: str
    revision_mode: str

    def __init__(
        self,
        validation_identity: str,
        boundary_identity: str,
        replay_time: CanonicalInstant,
        historical_time: CanonicalInstant,
        knowledge_boundary: CanonicalInstant,
        historical_visible: bool,
        exposure_valid: bool,
        mode: str,
        predecessor_context: tuple[tuple[str, str], ...] | None = None,
        historical_mode: str = "historical_recomputation",
        revision_mode: str = "original_historical",
    ) -> None:
        self._init({name: value for name, value in locals().items() if name != "self"})
        require_text(self.validation_identity, "replay.validation_identity")
        require_text(self.boundary_identity, "replay.boundary_identity")
        require_text(self.mode, "replay.mode")
        require_text(self.historical_mode, "replay.historical_mode")
        require_text(self.revision_mode, "replay.revision_mode")
        if not isinstance(self.predecessor_context, tuple):
            raise DataIntegrityError("replay predecessor context must be immutable")
        for item in self.predecessor_context:
            if not isinstance(item, tuple) or len(item) != 2:
                raise DataIntegrityError("replay predecessor context is invalid")
            require_text(item[0], "replay predecessor context identity")
            require_text(item[1], "replay predecessor context value")
        if len(set(self.predecessor_context)) != len(self.predecessor_context):
            raise DataIntegrityError("replay predecessor context must be unique")
        object.__setattr__(self, "predecessor_context", tuple(sorted(self.predecessor_context)))
        for name in ("replay_time", "historical_time", "knowledge_boundary"):
            if not isinstance(getattr(self, name), CanonicalInstant):
                raise DataIntegrityError(f"replay.{name} is invalid")
        if not _basis(self.replay_time, self.knowledge_boundary) or not _basis(
            self.historical_time, self.knowledge_boundary
        ):
            _fail("replay temporal basis is incompatible")
        if not isinstance(self.historical_visible, bool) or not isinstance(
            self.exposure_valid, bool
        ):
            raise DataIntegrityError("replay outcomes must be boolean")


class ReplayCompatibilityDiagnostics(_Immutable):
    __slots__ = ("validations", "reasons")
    _fields = __slots__
    validations: tuple[ReplayCompatibilityValidation, ...]
    reasons: tuple[TemporalDiagnosticReason, ...]

    def __init__(
        self,
        validations: tuple[ReplayCompatibilityValidation, ...],
        reasons: tuple[TemporalDiagnosticReason, ...] = (),
    ) -> None:
        self._init({"validations": validations, "reasons": reasons})
        if not isinstance(validations, tuple) or any(
            not isinstance(v, ReplayCompatibilityValidation) for v in validations
        ):
            raise DataIntegrityError("replay diagnostics require immutable validations")
        if not isinstance(reasons, tuple) or any(
            not isinstance(r, TemporalDiagnosticReason) for r in reasons
        ):
            raise DataIntegrityError("replay diagnostics require immutable reasons")
        vals = tuple(sorted(validations, key=lambda v: v._values()))
        if len(set(vals)) != len(vals):
            raise DataIntegrityError("replay diagnostics contain duplicate validations")
        object.__setattr__(self, "validations", vals)
        object.__setattr__(
            self,
            "reasons",
            tuple(sorted(reasons, key=lambda r: (r.affected_evidence, r.reason, r.code.value))),
        )
        for reason in self.reasons:
            matches = tuple(
                v
                for v in vals
                if v.boundary_identity == reason.affected_evidence
                and v.knowledge_boundary == reason.knowledge_boundary
                and reason.source_boundary == v.boundary_identity
                and reason.consumer_boundary == v.boundary_identity
                and (reason.timeframe_identity or "")
                == dict(v.predecessor_context).get("timeframe", "")
                and (reason.calendar_identity or "")
                == dict(v.predecessor_context).get("calendar", "")
                and ",".join(reason.revision_lineage)
                == dict(v.predecessor_context).get("revision", "")
                and reason.policy_version == "replay"
            )
            if len(matches) != 1:
                raise DataIntegrityError("replay diagnostic reason is orphaned or ambiguous")


class ReplayCompatibilityValidator:
    __slots__ = ()

    @classmethod
    def validate(
        cls,
        validation_identity: str,
        boundary: TemporalBoundary,
        replay_time: CanonicalInstant,
        historical_time: CanonicalInstant,
        knowledge_boundary: CanonicalInstant,
        mode: str = "historical",
        predecessor_context: tuple[tuple[str, str], ...] = (),
        historical_mode: str = "historical_recomputation",
        revision_mode: str = "original_historical",
    ) -> ReplayCompatibilityDiagnostics:
        if not isinstance(boundary, TemporalBoundary):
            raise DataIntegrityError("replay boundary is invalid")
        expected_context = (
            ("availability", str(boundary.availability.value)),
            ("calendar", boundary.calendar_identity or ""),
            ("closure", "closed" if boundary.validity is not None else "open"),
            ("mapping", boundary.timeframe_version or ""),
            ("revision", ",".join(boundary.revision_lineage)),
            ("timeframe", boundary.timeframe_identity or ""),
            ("watermark", str(boundary.knowledge.value)),
        )
        if predecessor_context is None or not predecessor_context:
            raise DataIntegrityError("replay predecessor context is missing or incomplete")
        if tuple(sorted(predecessor_context)) != expected_context:
            raise DataIntegrityError("replay predecessor context is inconsistent")
        for name, value in (
            ("replay_time", replay_time),
            ("historical_time", historical_time),
            ("knowledge_boundary", knowledge_boundary),
        ):
            if not isinstance(value, CanonicalInstant):
                raise DataIntegrityError(f"replay.{name} is invalid")
        for value in (replay_time, historical_time):
            if not _basis(value, knowledge_boundary):
                _fail("replay temporal basis is incompatible")
        if (
            historical_time.value > knowledge_boundary.value
            or replay_time.value > knowledge_boundary.value
        ):
            _fail("replay exposes future knowledge")
        visible = historical_time.value <= boundary.knowledge.value
        exposure = (
            replay_time.value >= historical_time.value
            and replay_time.value <= knowledge_boundary.value
        )
        result = ReplayCompatibilityValidation(
            validation_identity,
            boundary.boundary_identity,
            replay_time,
            historical_time,
            knowledge_boundary,
            visible,
            exposure,
            mode,
            predecessor_context,
            historical_mode,
            revision_mode,
        )
        reasons: tuple[TemporalDiagnosticReason, ...] = ()
        if not visible or not exposure:
            reasons = (
                TemporalDiagnosticReason(
                    TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                    boundary.boundary_identity,
                    boundary.boundary_identity,
                    boundary.boundary_identity,
                    boundary.timeframe_identity,
                    boundary.calendar_identity,
                    knowledge_boundary,
                    boundary.revision_lineage,
                    "replay",
                    "historical replay is not compatible",
                ),
            )
        return ReplayCompatibilityDiagnostics((result,), reasons)
