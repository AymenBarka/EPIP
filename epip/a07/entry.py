"""A07-E04 immutable entry-geometry contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import ROUND_HALF_EVEN, Decimal
from math import isfinite
from typing import ClassVar

from epip.a07.direction import DirectionValidation
from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError

__all__ = ["EntryDiagnostics", "EntryFacts", "EntryPrice", "EntryValidation"]


class _Record:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable strategy entry model")

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
        raise DataIntegrityError("normalized entry price must be finite and strictly positive")
    return result


class EntryFacts(_Record):
    """Caller-supplied immutable authorized entry zone."""

    __slots__ = ("zone_lower", "zone_upper")
    _field_names = __slots__
    zone_lower: float
    zone_upper: float

    def __init__(self, zone_lower: object, zone_upper: object) -> None:
        lower = _price(zone_lower, "zone_lower")
        upper = _price(zone_upper, "zone_upper")
        if lower > upper:
            raise DataIntegrityError("zone_lower must not exceed zone_upper")
        self._init({"zone_lower": lower, "zone_upper": upper})


class EntryPrice(_Record):
    """Canonical executable entry derived from E03 and one authorized zone."""

    __slots__ = (
        "direction_validation",
        "entry_facts",
        "price",
    )
    _field_names = __slots__
    direction_validation: DirectionValidation
    entry_facts: EntryFacts
    price: float

    def __init__(self, direction_validation: object, entry_facts: object) -> None:
        if type(direction_validation) is not DirectionValidation:
            raise DataIntegrityError("direction_validation must be a DirectionValidation")
        if type(entry_facts) is not EntryFacts:
            raise DataIntegrityError("entry_facts must be EntryFacts")
        assert isinstance(direction_validation, DirectionValidation)
        assert isinstance(entry_facts, EntryFacts)
        direction = direction_validation.decision.direction
        if not direction_validation.valid or direction not in (
            StrategyDirection.BUY,
            StrategyDirection.SELL,
        ):
            raise DataIntegrityError("entry requires an actionable direction validation")
        precision = direction_validation.decision.policy.numeric_precision
        lower = _normalize(entry_facts.zone_lower, precision)
        upper = _normalize(entry_facts.zone_upper, precision)
        if lower > upper:
            raise DataIntegrityError("normalized zone_lower must not exceed zone_upper")
        if entry_facts.zone_lower != entry_facts.zone_upper and lower == upper:
            raise DataIntegrityError("entry zone bounds collapse at policy precision")
        price = upper if direction is StrategyDirection.BUY else lower
        self._init(
            {
                "direction_validation": direction_validation,
                "entry_facts": entry_facts,
                "price": price,
            }
        )

    @classmethod
    def reconstruct(
        cls,
        direction_validation: object,
        entry_facts: object,
        price: object,
    ) -> EntryPrice:
        supplied = _price(price, "price")
        result = cls(direction_validation, entry_facts)
        if result.price != supplied:
            raise DataIntegrityError("price does not match canonical entry derivation")
        return result


class EntryDiagnostics(_Record):
    """Canonical E04 diagnostics with an intentionally empty vocabulary."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if not isinstance(diagnostics, tuple):
            raise DataIntegrityError("diagnostics must be an immutable tuple")
        if diagnostics:
            raise DataIntegrityError("E04 diagnostics vocabulary is empty")
        self._init({"diagnostics": ()})


class EntryValidation(_Record):
    """Immutable integrity validation of canonical executable entry geometry."""

    __slots__ = ("entry", "valid", "diagnostics")  # noqa: RUF023
    _field_names = __slots__
    entry: EntryPrice
    valid: bool
    diagnostics: EntryDiagnostics

    def __init__(self, entry: object) -> None:
        if type(entry) is not EntryPrice:
            raise DataIntegrityError("entry must be an EntryPrice")
        assert isinstance(entry, EntryPrice)
        if EntryPrice(entry.direction_validation, entry.entry_facts) != entry:
            raise DataIntegrityError("entry is not canonical")
        self._init({"entry": entry, "valid": True, "diagnostics": EntryDiagnostics(())})

    @classmethod
    def reconstruct(cls, entry: object, valid: object, diagnostics: object) -> EntryValidation:
        if type(valid) is not bool:
            raise DataIntegrityError("valid must be a bool")
        if type(diagnostics) is not EntryDiagnostics:
            raise DataIntegrityError("diagnostics must be EntryDiagnostics")
        result = cls(entry)
        if result.valid is not valid or result.diagnostics != diagnostics:
            raise DataIntegrityError("validation fields do not match canonical entry validation")
        return result
