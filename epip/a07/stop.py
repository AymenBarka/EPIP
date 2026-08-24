"""A07-E05 immutable stop-geometry contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import ROUND_HALF_EVEN, Decimal
from math import isfinite
from typing import ClassVar

from epip.a07.entry import EntryValidation
from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError

__all__ = ["StopDiagnostics", "StopFacts", "StopLoss", "StopValidation"]


class _Record:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable strategy stop model")

    def _init(self, values: dict[str, object]) -> None:
        for name in self._field_names:
            object.__setattr__(self, name, values[name])

    def _values(self) -> tuple[object, ...]:
        return tuple(getattr(self, name) for name in self._field_names)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        assert isinstance(other, _Record)
        return self._values() == other._values()

    def __hash__(self) -> int:
        return hash((type(self), self._values()))


def _price(value: object, field: str) -> float:
    if type(value) is not float or not isfinite(value):
        raise DataIntegrityError(f"{field} must be a finite float")
    assert isinstance(value, float)
    if value <= 0.0:
        raise DataIntegrityError(f"{field} must be strictly positive")
    return value


def _normalize(value: float, precision: int) -> float:
    quantum = Decimal(1).scaleb(-precision)
    result = float(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_EVEN))
    if result == 0.0:
        result = 0.0
    if not isfinite(result) or result <= 0.0:
        raise DataIntegrityError("normalized stop price must be finite and strictly positive")
    return result


class StopFacts(_Record):
    """Final caller-authorized immutable invalidation geometry."""

    __slots__ = ("invalidation_price",)
    _field_names = __slots__
    invalidation_price: float

    def __init__(self, invalidation_price: object) -> None:
        self._init({"invalidation_price": _price(invalidation_price, "invalidation_price")})


class StopLoss(_Record):
    """Canonical executable stop derived from E04 and one invalidation fact."""

    __slots__ = ("entry_validation", "stop_facts", "price")  # noqa: RUF023
    _field_names = __slots__
    entry_validation: EntryValidation
    stop_facts: StopFacts
    price: float

    def __init__(self, entry_validation: object, stop_facts: object) -> None:
        if type(entry_validation) is not EntryValidation:
            raise DataIntegrityError("entry_validation must be an EntryValidation")
        if type(stop_facts) is not StopFacts:
            raise DataIntegrityError("stop_facts must be StopFacts")
        assert isinstance(entry_validation, EntryValidation)
        assert isinstance(stop_facts, StopFacts)
        if not entry_validation.valid or entry_validation.diagnostics.diagnostics:
            raise DataIntegrityError("stop requires a canonical actionable entry validation")
        entry = entry_validation.entry
        direction = entry.direction_validation.decision.direction
        if direction not in (StrategyDirection.BUY, StrategyDirection.SELL):
            raise DataIntegrityError("stop requires an actionable BUY or SELL direction")
        precision = entry.direction_validation.decision.policy.numeric_precision
        price = _normalize(stop_facts.invalidation_price, precision)
        if direction is StrategyDirection.BUY and price >= entry.price:
            raise DataIntegrityError("BUY stop must be strictly below entry")
        if direction is StrategyDirection.SELL and price <= entry.price:
            raise DataIntegrityError("SELL stop must be strictly above entry")
        self._init({"entry_validation": entry_validation, "stop_facts": stop_facts, "price": price})

    @classmethod
    def reconstruct(cls, entry_validation: object, stop_facts: object, price: object) -> StopLoss:
        supplied = _price(price, "price")
        result = cls(entry_validation, stop_facts)
        if result.price != supplied:
            raise DataIntegrityError("price does not match canonical stop derivation")
        return result


class StopDiagnostics(_Record):
    """Canonical E05 diagnostics with an intentionally empty vocabulary."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if not isinstance(diagnostics, tuple):
            raise DataIntegrityError("diagnostics must be an immutable tuple")
        if diagnostics:
            raise DataIntegrityError("E05 diagnostics vocabulary is empty")
        self._init({"diagnostics": ()})


class StopValidation(_Record):
    """Immutable integrity validation of canonical executable stop geometry."""

    __slots__ = ("stop", "valid", "diagnostics")  # noqa: RUF023
    _field_names = __slots__
    stop: StopLoss
    valid: bool
    diagnostics: StopDiagnostics

    def __init__(self, stop: object) -> None:
        if type(stop) is not StopLoss:
            raise DataIntegrityError("stop must be a StopLoss")
        assert isinstance(stop, StopLoss)
        if StopLoss(stop.entry_validation, stop.stop_facts) != stop:
            raise DataIntegrityError("stop is not canonical")
        self._init({"stop": stop, "valid": True, "diagnostics": StopDiagnostics(())})

    @classmethod
    def reconstruct(cls, stop: object, valid: object, diagnostics: object) -> StopValidation:
        if type(valid) is not bool:
            raise DataIntegrityError("valid must be a bool")
        if type(diagnostics) is not StopDiagnostics:
            raise DataIntegrityError("diagnostics must be StopDiagnostics")
        result = cls(stop)
        if result.valid is not valid or result.diagnostics != diagnostics:
            raise DataIntegrityError("validation fields do not match canonical stop validation")
        return result
