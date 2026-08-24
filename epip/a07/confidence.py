"""A07-E08 immutable confidence and expiration contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import isfinite
from typing import ClassVar

from epip.a07.direction import DirectionValidation
from epip.a07.evidence import EvidenceValidation
from epip.a07.foundation import StrategyDirection, StrategyEvaluationRequest
from epip.a07.reward_risk import RewardRiskValidation
from epip.core.integrity import DataIntegrityError

__all__ = [
    "ConfidenceDiagnostics",
    "ConfidenceValidation",
    "SignalExpiration",
    "StrategyConfidence",
]


class _Record:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable strategy confidence model")

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


def _confidence(value: object) -> float:
    if type(value) is not float or not isfinite(value):
        raise DataIntegrityError("confidence must be a finite built-in float")
    assert isinstance(value, float)
    if value < 0.0 or value > 1.0:
        raise DataIntegrityError("confidence must be within the inclusive range 0.0..1.0")
    return 0.0 if value == 0.0 else value


def _require_predecessors(
    evidence: EvidenceValidation,
    direction: DirectionValidation,
    reward_risk: RewardRiskValidation,
) -> None:
    try:
        if evidence.valid is not True or evidence.diagnostics.diagnostics:
            raise DataIntegrityError("confidence requires valid canonical evidence")
        if direction.valid is not True or direction.diagnostics.diagnostics:
            raise DataIntegrityError("confidence requires valid canonical direction")
        if reward_risk.valid is not True or reward_risk.diagnostics.diagnostics:
            raise DataIntegrityError("confidence requires valid canonical reward-risk")
        if direction.decision.direction not in (StrategyDirection.BUY, StrategyDirection.SELL):
            raise DataIntegrityError("confidence requires an actionable BUY or SELL direction")
        if direction.decision.evidence_validation != evidence:
            raise DataIntegrityError("direction evidence does not match canonical evidence")
        rr_direction = reward_risk.outcome.entry_validation.entry.direction_validation
        if rr_direction != direction:
            raise DataIntegrityError("reward-risk direction does not match canonical direction")
    except AttributeError as exc:
        raise DataIntegrityError("confidence predecessor state is malformed") from exc


class StrategyConfidence(_Record):
    """Caller-supplied confidence bound to accepted E02, E03, and E07 results."""

    __slots__ = (  # noqa: RUF023 - normative field and equality order
        "evidence_validation",
        "direction_validation",
        "reward_risk_validation",
        "confidence",
    )
    _field_names = __slots__
    evidence_validation: EvidenceValidation
    direction_validation: DirectionValidation
    reward_risk_validation: RewardRiskValidation
    confidence: float

    def __init__(
        self,
        evidence_validation: object,
        direction_validation: object,
        reward_risk_validation: object,
        confidence: object,
    ) -> None:
        if type(evidence_validation) is not EvidenceValidation:
            raise DataIntegrityError("evidence_validation must be an EvidenceValidation")
        if type(direction_validation) is not DirectionValidation:
            raise DataIntegrityError("direction_validation must be a DirectionValidation")
        if type(reward_risk_validation) is not RewardRiskValidation:
            raise DataIntegrityError("reward_risk_validation must be a RewardRiskValidation")
        assert isinstance(evidence_validation, EvidenceValidation)
        assert isinstance(direction_validation, DirectionValidation)
        assert isinstance(reward_risk_validation, RewardRiskValidation)
        _require_predecessors(evidence_validation, direction_validation, reward_risk_validation)
        self._init(
            {
                "evidence_validation": evidence_validation,
                "direction_validation": direction_validation,
                "reward_risk_validation": reward_risk_validation,
                "confidence": _confidence(confidence),
            }
        )

    @classmethod
    def reconstruct(
        cls,
        evidence_validation: object,
        direction_validation: object,
        reward_risk_validation: object,
        confidence: object,
    ) -> StrategyConfidence:
        return cls(
            evidence_validation,
            direction_validation,
            reward_risk_validation,
            confidence,
        )


def _canonical_timestamp(value: str) -> tuple[datetime, str]:
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise DataIntegrityError("evaluation timestamp must include a timezone")
        normalized = parsed.astimezone(timezone.utc)  # noqa: UP017 - normative formula
        canonical = normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")
    except (OverflowError, ValueError) as exc:
        raise DataIntegrityError("evaluation timestamp must be valid ISO-8601") from exc
    return normalized, canonical


class SignalExpiration(_Record):
    """Canonical UTC expiration metadata derived without reading a clock."""

    __slots__ = (  # noqa: RUF023 - normative field and equality order
        "request",
        "strategy_confidence",
        "evaluation_timestamp",
        "expiration_seconds",
        "expires_at",
    )
    _field_names = __slots__
    request: StrategyEvaluationRequest
    strategy_confidence: StrategyConfidence
    evaluation_timestamp: str
    expiration_seconds: int
    expires_at: str

    def __init__(self, request: object, strategy_confidence: object) -> None:
        if type(request) is not StrategyEvaluationRequest:
            raise DataIntegrityError("request must be a StrategyEvaluationRequest")
        if type(strategy_confidence) is not StrategyConfidence:
            raise DataIntegrityError("strategy_confidence must be a StrategyConfidence")
        assert isinstance(request, StrategyEvaluationRequest)
        assert isinstance(strategy_confidence, StrategyConfidence)
        try:
            policy = strategy_confidence.direction_validation.decision.policy
            snapshots = strategy_confidence.evidence_validation.binding.available_evidence
            if request.strategy_identity != policy.strategy_identity:
                raise DataIntegrityError("request strategy does not match confidence policy")
            if request.policy_reference != policy.identity.reference:
                raise DataIntegrityError(
                    "request policy reference does not match confidence policy"
                )
            if any(item.evidence_identity != request.evidence_identity for item in snapshots):
                raise DataIntegrityError(
                    "request evidence identity does not match confidence evidence"
                )
            duration = policy.expiration_seconds
            evaluation_utc, evaluation_timestamp = _canonical_timestamp(
                request.evaluation_timestamp
            )
            expires_utc = evaluation_utc + timedelta(seconds=duration)
            expires_at = expires_utc.isoformat(timespec="microseconds").replace("+00:00", "Z")
        except (AttributeError, OverflowError) as exc:
            raise DataIntegrityError("expiration predecessor state is malformed") from exc
        self._init(
            {
                "request": request,
                "strategy_confidence": strategy_confidence,
                "evaluation_timestamp": evaluation_timestamp,
                "expiration_seconds": duration,
                "expires_at": expires_at,
            }
        )

    @classmethod
    def reconstruct(
        cls,
        request: object,
        strategy_confidence: object,
        evaluation_timestamp: object,
        expiration_seconds: object,
        expires_at: object,
    ) -> SignalExpiration:
        result = cls(request, strategy_confidence)
        supplied = (evaluation_timestamp, expiration_seconds, expires_at)
        if result._values()[2:] != supplied:
            raise DataIntegrityError("expiration fields do not match canonical derivation")
        return result


class ConfidenceDiagnostics(_Record):
    """Canonical E08 diagnostics for confidence-threshold rejection."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if type(diagnostics) is not tuple:
            raise DataIntegrityError("diagnostics must be an immutable tuple")
        if diagnostics not in ((), ("CONFIDENCE_BELOW_MINIMUM",)):
            raise DataIntegrityError("diagnostics contains a non-canonical E08 state")
        self._init({"diagnostics": diagnostics})

    @classmethod
    def reconstruct(cls, diagnostics: object) -> ConfidenceDiagnostics:
        return cls(diagnostics)


def _accepted(value: StrategyConfidence) -> bool:
    minimum = value.direction_validation.decision.policy.minimum_confidence
    return Decimal(str(value.confidence)) >= Decimal(str(minimum))


class ConfidenceValidation(_Record):
    """Immutable E08 confidence-threshold acceptance result."""

    __slots__ = (  # noqa: RUF023 - normative field and equality order
        "strategy_confidence",
        "signal_expiration",
        "valid",
        "diagnostics",
    )
    _field_names = __slots__
    strategy_confidence: StrategyConfidence
    signal_expiration: SignalExpiration
    valid: bool
    diagnostics: ConfidenceDiagnostics

    def __init__(self, strategy_confidence: object, signal_expiration: object) -> None:
        if type(strategy_confidence) is not StrategyConfidence:
            raise DataIntegrityError("strategy_confidence must be a StrategyConfidence")
        if type(signal_expiration) is not SignalExpiration:
            raise DataIntegrityError("signal_expiration must be a SignalExpiration")
        assert isinstance(strategy_confidence, StrategyConfidence)
        assert isinstance(signal_expiration, SignalExpiration)
        if signal_expiration.strategy_confidence != strategy_confidence:
            raise DataIntegrityError("expiration confidence does not match canonical confidence")
        valid = _accepted(strategy_confidence)
        diagnostics = ConfidenceDiagnostics(() if valid else ("CONFIDENCE_BELOW_MINIMUM",))
        self._init(
            {
                "strategy_confidence": strategy_confidence,
                "signal_expiration": signal_expiration,
                "valid": valid,
                "diagnostics": diagnostics,
            }
        )

    @classmethod
    def reconstruct(
        cls,
        strategy_confidence: object,
        signal_expiration: object,
        valid: object,
        diagnostics: object,
    ) -> ConfidenceValidation:
        if type(valid) is not bool:
            raise DataIntegrityError("valid must be a bool")
        if type(diagnostics) is not ConfidenceDiagnostics:
            raise DataIntegrityError("diagnostics must be ConfidenceDiagnostics")
        result = cls(strategy_confidence, signal_expiration)
        if result.valid is not valid or result.diagnostics != diagnostics:
            raise DataIntegrityError("validation fields do not match canonical confidence state")
        return result
