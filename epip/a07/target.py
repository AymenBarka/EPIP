"""A07-E06 immutable target-geometry contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import ROUND_HALF_EVEN, Decimal
from math import isfinite
from typing import ClassVar

from epip.a07.entry import EntryValidation
from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError

__all__ = ["TakeProfit", "TargetDiagnostics", "TargetFacts", "TargetValidation"]


class _Record:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable strategy target model")

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
        raise DataIntegrityError("normalized target price must be finite and strictly positive")
    return result


class TargetFacts(_Record):
    """One final caller-authorized immutable target price."""

    __slots__ = ("target_price",)
    _field_names = __slots__
    target_price: float

    def __init__(self, target_price: object) -> None:
        self._init({"target_price": _price(target_price, "target_price")})


class TakeProfit(_Record):
    """Canonical executable target derived from E04 and one target fact."""

    __slots__ = ("entry_validation", "target_facts", "price")  # noqa: RUF023
    _field_names = __slots__
    entry_validation: EntryValidation
    target_facts: TargetFacts
    price: float

    def __init__(self, entry_validation: object, target_facts: object) -> None:
        if type(entry_validation) is not EntryValidation:
            raise DataIntegrityError("entry_validation must be an EntryValidation")
        if type(target_facts) is not TargetFacts:
            raise DataIntegrityError("target_facts must be TargetFacts")
        assert isinstance(entry_validation, EntryValidation)
        assert isinstance(target_facts, TargetFacts)
        try:
            if not entry_validation.valid or entry_validation.diagnostics.diagnostics:
                raise DataIntegrityError("target requires a canonical actionable entry validation")
            entry = entry_validation.entry
            direction = entry.direction_validation.decision.direction
        except AttributeError as exc:
            raise DataIntegrityError(
                "target requires a canonical actionable entry validation"
            ) from exc
        if direction not in (StrategyDirection.BUY, StrategyDirection.SELL):
            raise DataIntegrityError("target requires an actionable BUY or SELL direction")
        precision = entry.direction_validation.decision.policy.numeric_precision
        price = _normalize(target_facts.target_price, precision)
        if direction is StrategyDirection.BUY and price <= entry.price:
            raise DataIntegrityError("BUY target must be strictly above entry")
        if direction is StrategyDirection.SELL and price >= entry.price:
            raise DataIntegrityError("SELL target must be strictly below entry")
        self._init(
            {"entry_validation": entry_validation, "target_facts": target_facts, "price": price}
        )

    @classmethod
    def reconstruct(
        cls, entry_validation: object, target_facts: object, price: object
    ) -> TakeProfit:
        supplied = _price(price, "price")
        result = cls(entry_validation, target_facts)
        if result.price != supplied:
            raise DataIntegrityError("price does not match canonical target derivation")
        return result


class TargetDiagnostics(_Record):
    """Canonical E06 diagnostics with an intentionally empty vocabulary."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if not isinstance(diagnostics, tuple):
            raise DataIntegrityError("diagnostics must be an immutable tuple")
        if diagnostics:
            raise DataIntegrityError("E06 diagnostics vocabulary is empty")
        self._init({"diagnostics": ()})


class TargetValidation(_Record):
    """Immutable integrity validation of canonical executable target geometry."""

    __slots__ = ("target", "valid", "diagnostics")  # noqa: RUF023
    _field_names = __slots__
    target: TakeProfit
    valid: bool
    diagnostics: TargetDiagnostics

    def __init__(self, target: object) -> None:
        if type(target) is not TakeProfit:
            raise DataIntegrityError("target must be a TakeProfit")
        assert isinstance(target, TakeProfit)
        if TakeProfit(target.entry_validation, target.target_facts) != target:
            raise DataIntegrityError("target is not canonical")
        self._init({"target": target, "valid": True, "diagnostics": TargetDiagnostics(())})

    @classmethod
    def reconstruct(cls, target: object, valid: object, diagnostics: object) -> TargetValidation:
        if type(valid) is not bool:
            raise DataIntegrityError("valid must be a bool")
        if type(diagnostics) is not TargetDiagnostics:
            raise DataIntegrityError("diagnostics must be TargetDiagnostics")
        result = cls(target)
        if result.valid is not valid or result.diagnostics != diagnostics:
            raise DataIntegrityError("validation fields do not match canonical target validation")
        return result
