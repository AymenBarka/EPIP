"""A07-E09 immutable final strategy-signal contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a07.confidence import ConfidenceValidation
from epip.a07.foundation import StrategyDirection, StrategyIdentity
from epip.core.integrity import DataIntegrityError

__all__ = ["SignalDiagnostics", "SignalValidation", "StrategySignal"]


class _Record:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable strategy signal model")

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


def _canonical_confidence(value: object) -> ConfidenceValidation:
    if type(value) is not ConfidenceValidation:
        raise DataIntegrityError("confidence_validation must be a ConfidenceValidation")
    assert isinstance(value, ConfidenceValidation)
    try:
        if value.valid is not True or value.diagnostics.diagnostics != ():
            raise DataIntegrityError("signal requires valid canonical confidence")
        rebuilt = ConfidenceValidation.reconstruct(
            value.strategy_confidence,
            value.signal_expiration,
            value.valid,
            value.diagnostics,
        )
        if rebuilt != value:  # pragma: no cover - frozen E08 reconstruct guarantees equality
            raise DataIntegrityError("confidence validation is not canonical")
        if (  # pragma: no cover - frozen E08 reconstruct enforces this continuity
            value.signal_expiration.strategy_confidence != value.strategy_confidence
        ):
            raise DataIntegrityError("expiration confidence continuity is invalid")
    except AttributeError as exc:
        raise DataIntegrityError("confidence predecessor state is malformed") from exc
    return value


def _signal_values(value: ConfidenceValidation) -> dict[str, object]:
    try:
        confidence = value.strategy_confidence
        expiration = value.signal_expiration
        direction_validation = confidence.direction_validation
        outcome = confidence.reward_risk_validation.outcome
        entry_validation = outcome.entry_validation
        stop_validation = outcome.stop_validation
        target_validation = outcome.target_validation
        policy = direction_validation.decision.policy
        direction = direction_validation.decision.direction
        values: dict[str, object] = {
            "strategy_identity": policy.strategy_identity,
            "policy_reference": policy.identity.reference,
            "direction": direction,
            "entry_price": entry_validation.entry.price,
            "stop_price": stop_validation.stop.price,
            "target_price": target_validation.target.price,
            "risk": outcome.risk,
            "reward": outcome.reward,
            "rr": outcome.rr,
            "confidence": confidence.confidence,
            "evaluation_timestamp": expiration.evaluation_timestamp,
            "expires_at": expiration.expires_at,
        }
        expected_types = (
            StrategyIdentity,
            str,
            StrategyDirection,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            str,
            str,
        )
        if any(
            type(item) is not expected for item, expected in zip(values.values(), expected_types)
        ):
            raise DataIntegrityError("signal source field has an invalid runtime type")
        if direction not in (StrategyDirection.BUY, StrategyDirection.SELL):
            raise DataIntegrityError("signal requires an actionable BUY or SELL direction")
        if stop_validation.stop.entry_validation != entry_validation:
            raise DataIntegrityError("stop and entry continuity is invalid")
        if target_validation.target.entry_validation != entry_validation:
            raise DataIntegrityError("target and entry continuity is invalid")
        if entry_validation.entry.direction_validation != direction_validation:
            raise DataIntegrityError("entry and direction continuity is invalid")
        if (  # pragma: no cover - checked by canonical E08 reconstruction above
            expiration.strategy_confidence != confidence
        ):
            raise DataIntegrityError("expiration and confidence continuity is invalid")
        if expiration.request.strategy_identity != policy.strategy_identity:
            raise DataIntegrityError("request and strategy identity continuity is invalid")
        if expiration.request.policy_reference != policy.identity.reference:
            raise DataIntegrityError("request and policy reference continuity is invalid")
    except AttributeError as exc:
        raise DataIntegrityError("signal predecessor state is malformed") from exc
    return values


class StrategySignal(_Record):
    """Final immutable actionable signal copied from a canonical E08 result."""

    __slots__ = (  # noqa: RUF023 - normative field and equality order
        "strategy_identity",
        "policy_reference",
        "direction",
        "entry_price",
        "stop_price",
        "target_price",
        "risk",
        "reward",
        "rr",
        "confidence",
        "evaluation_timestamp",
        "expires_at",
    )
    _field_names = __slots__
    strategy_identity: StrategyIdentity
    policy_reference: str
    direction: StrategyDirection
    entry_price: float
    stop_price: float
    target_price: float
    risk: float
    reward: float
    rr: float
    confidence: float
    evaluation_timestamp: str
    expires_at: str

    def __init__(self, confidence_validation: object) -> None:
        self._init(_signal_values(_canonical_confidence(confidence_validation)))

    @classmethod
    def reconstruct(
        cls,
        confidence_validation: object,
        strategy_identity: object,
        policy_reference: object,
        direction: object,
        entry_price: object,
        stop_price: object,
        target_price: object,
        risk: object,
        reward: object,
        rr: object,
        confidence: object,
        evaluation_timestamp: object,
        expires_at: object,
    ) -> StrategySignal:
        result = cls(confidence_validation)
        supplied = (
            strategy_identity,
            policy_reference,
            direction,
            entry_price,
            stop_price,
            target_price,
            risk,
            reward,
            rr,
            confidence,
            evaluation_timestamp,
            expires_at,
        )
        if result._values() != supplied:
            raise DataIntegrityError("signal fields do not match canonical predecessor state")
        return result


class SignalDiagnostics(_Record):
    """Empty diagnostics for the success-only E09 boundary."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if type(diagnostics) is not tuple:
            raise DataIntegrityError("diagnostics must be an immutable tuple")
        if diagnostics != ():
            raise DataIntegrityError("diagnostics must be the canonical empty state")
        self._init({"diagnostics": diagnostics})

    @classmethod
    def reconstruct(cls, diagnostics: object) -> SignalDiagnostics:
        return cls(diagnostics)


class SignalValidation(_Record):
    """Success-only structural validation of a canonical final signal."""

    __slots__ = ("signal", "valid", "diagnostics")  # noqa: RUF023
    _field_names = __slots__
    signal: StrategySignal
    valid: bool
    diagnostics: SignalDiagnostics

    def __init__(self, signal: object) -> None:
        if type(signal) is not StrategySignal:
            raise DataIntegrityError("signal must be a StrategySignal")
        assert isinstance(signal, StrategySignal)
        self._init({"signal": signal, "valid": True, "diagnostics": SignalDiagnostics(())})

    @classmethod
    def reconstruct(cls, signal: object, valid: object, diagnostics: object) -> SignalValidation:
        if type(valid) is not bool:
            raise DataIntegrityError("valid must be a bool")
        if type(diagnostics) is not SignalDiagnostics:
            raise DataIntegrityError("diagnostics must be SignalDiagnostics")
        result = cls(signal)
        if result.valid is not valid or result.diagnostics != diagnostics:
            raise DataIntegrityError("validation fields do not match canonical signal state")
        return result
