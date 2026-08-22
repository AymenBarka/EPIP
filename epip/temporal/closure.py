"""Deterministic terminal verification of the A05 temporal pipeline."""

from __future__ import annotations
from dataclasses import FrozenInstanceError
from typing import ClassVar
from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text

__all__ = ["ClosureDiagnostics", "IntegratedTemporalClosure", "TemporalClosureVerifier"]


class _Immutable:
    __slots__ = ()
    _fields: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable closure model")

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


class IntegratedTemporalClosure(_Immutable):
    __slots__ = ("closure_identity", "complete", "predecessor_facts")
    _fields = __slots__
    closure_identity: str
    complete: bool
    predecessor_facts: tuple[tuple[str, object], ...]

    def __init__(
        self,
        closure_identity: str,
        predecessor_facts: tuple[tuple[str, object], ...],
        complete: bool,
    ) -> None:
        self._init({k: v for k, v in locals().items() if k != "self"})
        require_text(self.closure_identity, "closure.closure_identity")
        if not isinstance(self.predecessor_facts, tuple) or not self.predecessor_facts:
            raise MissingFieldError("closure predecessor facts are required")
        labels: list[str] = []
        for item in self.predecessor_facts:
            if not isinstance(item, tuple) or len(item) != 2:
                raise DataIntegrityError("closure predecessor fact is invalid")
            label, fact = item
            require_text(label, "closure.predecessor_label")
            if fact is None:
                raise DataIntegrityError("closure predecessor fact is missing")
            try:
                hash(fact)
            except TypeError as exc:
                raise DataIntegrityError("closure predecessor fact is not immutable") from exc
            labels.append(label)
        if len(set(labels)) != len(labels):
            raise DataIntegrityError("closure predecessor labels must be unique")
        if not isinstance(self.complete, bool):
            raise DataIntegrityError("closure completeness must be boolean")
        object.__setattr__(self, "predecessor_facts", tuple(sorted(self.predecessor_facts)))


class ClosureDiagnostics(_Immutable):
    __slots__ = ("attributions", "closures", "context", "reasons")
    _fields = __slots__
    closures: tuple[IntegratedTemporalClosure, ...]
    reasons: tuple[str, ...]
    attributions: tuple[tuple[str, IntegratedTemporalClosure], ...]
    context: tuple[tuple[str, object], ...]

    def __init__(
        self,
        closures: tuple[IntegratedTemporalClosure, ...],
        reasons: tuple[str, ...] = (),
        attributions: tuple[tuple[str, IntegratedTemporalClosure], ...] = (),
        context: tuple[tuple[str, object], ...] = (),
    ) -> None:
        self._init(
            {
                "closures": closures,
                "reasons": reasons,
                "attributions": attributions,
                "context": context,
            }
        )
        if not isinstance(closures, tuple) or not closures:
            raise MissingFieldError("closure diagnostics require a closure")
        if any(not isinstance(item, IntegratedTemporalClosure) for item in closures):
            raise DataIntegrityError("closure diagnostics require immutable closures")
        if not isinstance(reasons, tuple) or any(
            not isinstance(item, str) or not item for item in reasons
        ):
            raise DataIntegrityError("closure diagnostics reasons are invalid")
        if not isinstance(attributions, tuple):
            raise DataIntegrityError("closure diagnostic attributions are invalid")
        if not isinstance(context, tuple):
            raise DataIntegrityError("closure diagnostic context is invalid")
        for identity, closure in attributions:
            require_text(identity, "closure.diagnostic_identity")
            if not isinstance(closure, IntegratedTemporalClosure) or closure not in closures:
                raise DataIntegrityError("closure diagnostic attribution is mismatched")
            if closure.predecessor_facts != context:
                raise DataIntegrityError("closure diagnostic context is mismatched")
        if len({identity for identity, _ in attributions}) != len(attributions):
            raise DataIntegrityError("closure diagnostic attributions are ambiguous")
        ordered = tuple(sorted(closures, key=lambda item: item._values()))
        if len(set(ordered)) != len(ordered):
            raise DataIntegrityError("closure diagnostics contain duplicates")
        object.__setattr__(self, "closures", ordered)
        object.__setattr__(self, "reasons", tuple(sorted(reasons)))
        object.__setattr__(
            self, "attributions", tuple(sorted(attributions, key=lambda item: item[0]))
        )
        object.__setattr__(self, "context", tuple(sorted(context)))


class TemporalClosureVerifier:
    __slots__ = ()
    REQUIRED_FACTS = ("E00", "E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08")

    @classmethod
    def verify(
        cls, closure_identity: str, predecessor_facts: tuple[tuple[str, object], ...]
    ) -> ClosureDiagnostics:
        if not isinstance(predecessor_facts, tuple):
            raise DataIntegrityError("closure predecessor facts must be immutable")
        labels = {label for label, _ in predecessor_facts if isinstance(label, str)}
        missing = tuple(item for item in cls.REQUIRED_FACTS if item not in labels)
        if missing:
            raise MissingFieldError(f"closure missing mandatory facts: {', '.join(missing)}")
        result = IntegratedTemporalClosure(closure_identity, predecessor_facts, True)
        return ClosureDiagnostics(
            (result,), attributions=((closure_identity, result),), context=result.predecessor_facts
        )
