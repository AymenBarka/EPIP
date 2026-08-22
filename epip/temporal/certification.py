"""Deterministic preparation of immutable A05 temporal certification evidence."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text
from epip.temporal.model import CanonicalInstant, TemporalDiagnosticCode, TemporalDiagnosticReason

__all__ = ["CertificationPreparer", "CertificationPreparation", "CertificationDiagnostics"]


class _Immutable:
    __slots__ = ()
    _fields: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable certification model")

    def _init(self, values: dict[str, object]) -> None:
        for name in self._fields:
            object.__setattr__(self, name, values[name])

    def _values(self) -> tuple[object, ...]:
        return tuple(getattr(self, name) for name in self._fields)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        assert isinstance(other, _Immutable)
        return self._values() == other._values()

    def __hash__(self) -> int:
        return hash((type(self), self._values()))


class CertificationPreparation(_Immutable):
    __slots__ = ("preparation_identity", "profile_identity", "facts", "complete")
    _fields = __slots__
    preparation_identity: str
    profile_identity: str
    facts: tuple[tuple[str, str], ...]
    complete: bool

    def __init__(
        self,
        preparation_identity: str,
        profile_identity: str,
        facts: tuple[tuple[str, str], ...],
        complete: bool,
    ) -> None:
        self._init({k: v for k, v in locals().items() if k != "self"})
        require_text(self.preparation_identity, "certification.preparation_identity")
        require_text(self.profile_identity, "certification.profile_identity")
        if not isinstance(self.facts, tuple) or not self.facts:
            raise MissingFieldError("certification facts are required")
        for fact in self.facts:
            if not isinstance(fact, tuple) or len(fact) != 2:
                raise DataIntegrityError("certification fact is invalid")
            require_text(fact[0], "certification.fact_identity")
            require_text(fact[1], "certification.fact_value")
        if len(set(self.facts)) != len(self.facts):
            raise DataIntegrityError("certification facts must be unique")
        if not isinstance(self.complete, bool):
            raise DataIntegrityError("certification completeness must be boolean")
        object.__setattr__(self, "facts", tuple(sorted(self.facts)))


class CertificationDiagnostics(_Immutable):
    __slots__ = ("preparations", "reasons")
    _fields = __slots__
    preparations: tuple[CertificationPreparation, ...]
    reasons: tuple[TemporalDiagnosticReason, ...]

    def __init__(
        self,
        preparations: tuple[CertificationPreparation, ...],
        reasons: tuple[TemporalDiagnosticReason, ...] = (),
    ) -> None:
        self._init({"preparations": preparations, "reasons": reasons})
        if not isinstance(preparations, tuple) or any(
            not isinstance(p, CertificationPreparation) for p in preparations
        ):
            raise DataIntegrityError("certification diagnostics require immutable preparations")
        if not isinstance(reasons, tuple) or any(
            not isinstance(r, TemporalDiagnosticReason) for r in reasons
        ):
            raise DataIntegrityError("certification diagnostics require immutable reasons")
        ordered = tuple(sorted(preparations, key=lambda p: p._values()))
        if len(set(ordered)) != len(ordered):
            raise DataIntegrityError("certification diagnostics contain duplicates")
        object.__setattr__(self, "preparations", ordered)
        object.__setattr__(
            self,
            "reasons",
            tuple(sorted(reasons, key=lambda r: (r.affected_evidence, r.reason, r.code.value))),
        )


class CertificationPreparer:
    __slots__ = ()

    @classmethod
    def prepare(
        cls,
        preparation_identity: str,
        profile_identity: str,
        facts: tuple[tuple[str, str], ...],
        complete: bool = True,
    ) -> CertificationDiagnostics:
        if not isinstance(facts, tuple):
            raise DataIntegrityError("certification facts must be immutable")
        result = CertificationPreparation(preparation_identity, profile_identity, facts, complete)
        reasons: tuple[TemporalDiagnosticReason, ...] = ()
        if not complete:
            reasons = (
                TemporalDiagnosticReason(
                    TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                    preparation_identity,
                    preparation_identity,
                    preparation_identity,
                    None,
                    None,
                    CanonicalInstant(0, "second", "UTC", "UTC", "certification"),
                    (),
                    profile_identity,
                    "certification preparation is incomplete",
                ),
            )
        return CertificationDiagnostics((result,), reasons)
