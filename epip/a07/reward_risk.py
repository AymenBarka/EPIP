"""A07-E07 immutable reward-risk contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import ROUND_HALF_EVEN, Decimal, DecimalException, localcontext
from math import isfinite
from typing import ClassVar

from epip.a07.entry import EntryValidation
from epip.a07.foundation import StrategyDirection
from epip.a07.stop import StopValidation
from epip.a07.target import TargetValidation
from epip.core.integrity import DataIntegrityError

__all__ = ["RewardRiskDiagnostics", "RewardRiskOutcome", "RewardRiskValidation"]

_RR_QUANTUM = Decimal("0.000000000001")
_DECIMAL_PRECISION = 1000


class _Record:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable strategy reward-risk model")

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


def _public_positive(value: Decimal, field: str) -> float:
    if not value.is_finite() or value <= 0:
        raise DataIntegrityError(f"{field} must be finite and strictly positive")
    result = float(value)
    if result == 0.0:
        result = 0.0
    if not isfinite(result) or result <= 0.0:
        raise DataIntegrityError(f"{field} must be finite and strictly positive")
    return result


def _supplied_positive(value: object, field: str) -> float:
    if type(value) is not float or not isfinite(value):
        raise DataIntegrityError(f"{field} must be a finite float")
    assert isinstance(value, float)
    if value <= 0.0:
        raise DataIntegrityError(f"{field} must be strictly positive")
    return value


def _derive(
    entry_validation: EntryValidation,
    stop_validation: StopValidation,
    target_validation: TargetValidation,
) -> tuple[float, float, float]:
    try:
        if (
            entry_validation.valid is not True
            or stop_validation.valid is not True
            or target_validation.valid is not True
        ):
            raise DataIntegrityError("reward-risk requires actionable predecessor validations")
        if (
            entry_validation.diagnostics.diagnostics
            or stop_validation.diagnostics.diagnostics
            or target_validation.diagnostics.diagnostics
        ):
            raise DataIntegrityError("reward-risk requires canonical predecessor validations")
        if stop_validation.stop.entry_validation != entry_validation:
            raise DataIntegrityError("stop entry does not match the canonical entry")
        if target_validation.target.entry_validation != entry_validation:
            raise DataIntegrityError("target entry does not match the canonical entry")
        entry = entry_validation.entry.price
        stop = stop_validation.stop.price
        target = target_validation.target.price
        direction = entry_validation.entry.direction_validation.decision.direction
    except AttributeError as exc:
        raise DataIntegrityError("reward-risk predecessor state is malformed") from exc
    if direction not in (StrategyDirection.BUY, StrategyDirection.SELL):
        raise DataIntegrityError("reward-risk requires an actionable BUY or SELL direction")
    try:
        with localcontext() as context:
            context.prec = _DECIMAL_PRECISION
            entry_decimal = Decimal(str(entry))
            stop_decimal = Decimal(str(stop))
            target_decimal = Decimal(str(target))
            if direction is StrategyDirection.BUY:
                risk_decimal = entry_decimal - stop_decimal
                reward_decimal = target_decimal - entry_decimal
            else:
                risk_decimal = stop_decimal - entry_decimal
                reward_decimal = entry_decimal - target_decimal
            risk = _public_positive(risk_decimal, "risk")
            reward = _public_positive(reward_decimal, "reward")
            rr_decimal = reward_decimal / risk_decimal
            rr_canonical = rr_decimal.quantize(_RR_QUANTUM, rounding=ROUND_HALF_EVEN)
            rr = _public_positive(rr_canonical, "rr")
    except DecimalException as exc:
        raise DataIntegrityError("reward-risk decimal derivation failed") from exc
    return risk, reward, rr


class RewardRiskOutcome(_Record):
    """Canonical risk, reward, and ratio over converged geometry."""

    __slots__ = (  # noqa: RUF023 - normative field and equality order
        "entry_validation",
        "stop_validation",
        "target_validation",
        "risk",
        "reward",
        "rr",
    )
    _field_names = __slots__
    entry_validation: EntryValidation
    stop_validation: StopValidation
    target_validation: TargetValidation
    risk: float
    reward: float
    rr: float

    def __init__(
        self,
        entry_validation: object,
        stop_validation: object,
        target_validation: object,
    ) -> None:
        if type(entry_validation) is not EntryValidation:
            raise DataIntegrityError("entry_validation must be an EntryValidation")
        if type(stop_validation) is not StopValidation:
            raise DataIntegrityError("stop_validation must be a StopValidation")
        if type(target_validation) is not TargetValidation:
            raise DataIntegrityError("target_validation must be a TargetValidation")
        assert isinstance(entry_validation, EntryValidation)
        assert isinstance(stop_validation, StopValidation)
        assert isinstance(target_validation, TargetValidation)
        risk, reward, rr = _derive(entry_validation, stop_validation, target_validation)
        self._init(
            {
                "entry_validation": entry_validation,
                "stop_validation": stop_validation,
                "target_validation": target_validation,
                "risk": risk,
                "reward": reward,
                "rr": rr,
            }
        )

    @classmethod
    def reconstruct(
        cls,
        entry_validation: object,
        stop_validation: object,
        target_validation: object,
        risk: object,
        reward: object,
        rr: object,
    ) -> RewardRiskOutcome:
        supplied = (
            _supplied_positive(risk, "risk"),
            _supplied_positive(reward, "reward"),
            _supplied_positive(rr, "rr"),
        )
        result = cls(entry_validation, stop_validation, target_validation)
        if (result.risk, result.reward, result.rr) != supplied:
            raise DataIntegrityError("derived fields do not match canonical reward-risk values")
        return result


class RewardRiskDiagnostics(_Record):
    """Canonical E07 diagnostics for minimum-ratio rejection."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if type(diagnostics) is not tuple:
            raise DataIntegrityError("diagnostics must be an immutable tuple")
        if diagnostics not in ((), ("RR_BELOW_MINIMUM",)):
            raise DataIntegrityError("diagnostics contains a non-canonical E07 state")
        self._init({"diagnostics": diagnostics})


def _accepted(outcome: RewardRiskOutcome) -> bool:
    minimum = outcome.entry_validation.entry.direction_validation.decision.policy.minimum_rr
    return Decimal(str(outcome.rr)) >= Decimal(str(minimum))


class RewardRiskValidation(_Record):
    """Immutable E07 minimum-ratio acceptance result."""

    __slots__ = ("outcome", "valid", "diagnostics")  # noqa: RUF023
    _field_names = __slots__
    outcome: RewardRiskOutcome
    valid: bool
    diagnostics: RewardRiskDiagnostics

    def __init__(self, outcome: object) -> None:
        if type(outcome) is not RewardRiskOutcome:
            raise DataIntegrityError("outcome must be a RewardRiskOutcome")
        assert isinstance(outcome, RewardRiskOutcome)
        valid = _accepted(outcome)
        diagnostics = RewardRiskDiagnostics(() if valid else ("RR_BELOW_MINIMUM",))
        self._init({"outcome": outcome, "valid": valid, "diagnostics": diagnostics})

    @classmethod
    def reconstruct(
        cls, outcome: object, valid: object, diagnostics: object
    ) -> RewardRiskValidation:
        if type(valid) is not bool:
            raise DataIntegrityError("valid must be a bool")
        if type(diagnostics) is not RewardRiskDiagnostics:
            raise DataIntegrityError("diagnostics must be RewardRiskDiagnostics")
        result = cls(outcome)
        if result.valid is not valid or result.diagnostics != diagnostics:
            raise DataIntegrityError("validation fields do not match canonical reward-risk state")
        return result
