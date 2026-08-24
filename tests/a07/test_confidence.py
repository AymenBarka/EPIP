from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

from epip.a07.confidence import (
    ConfidenceDiagnostics,
    ConfidenceValidation,
    SignalExpiration,
    StrategyConfidence,
)
from epip.a07.direction import DirectionalDecision, DirectionalFacts, DirectionValidation
from epip.a07.entry import EntryFacts, EntryPrice, EntryValidation
from epip.a07.evidence import (
    EvidenceBinding,
    EvidenceValidation,
    StrategyEvidenceSnapshot,
)
from epip.a07.foundation import (
    StrategyDirection,
    StrategyEvaluationRequest,
    StrategyEvidenceIdentity,
    StrategyIdentity,
)
from epip.a07.policy import StrategyPolicy
from epip.a07.reward_risk import RewardRiskOutcome, RewardRiskValidation
from epip.a07.stop import StopFacts, StopLoss, StopValidation
from epip.a07.target import TakeProfit, TargetFacts, TargetValidation
from epip.core.integrity import DataIntegrityError


def inputs(
    confidence: float = 0.75,
    *,
    minimum_confidence: float = 0.5,
    timestamp: str = "2026-08-24T14:30:15.123456+02:00",
    expiration_seconds: int = 90,
    direction: StrategyDirection = StrategyDirection.BUY,
    with_evidence: bool = False,
) -> tuple[StrategyConfidence, SignalExpiration]:
    identity = StrategyIdentity("strategy", "1")
    evidence_identity = StrategyEvidenceIdentity("evidence", "source")
    keys = ("required",) if with_evidence else ()
    policy = StrategyPolicy(
        "strategy",
        "1",
        identity,
        (StrategyDirection.BUY, StrategyDirection.SELL),
        2.0,
        minimum_confidence,
        keys,
        (),
        expiration_seconds,
        6,
        (),
    )
    available = (
        (StrategyEvidenceSnapshot(identity, evidence_identity, "required", True, True),)
        if with_evidence
        else ()
    )
    evidence = EvidenceValidation(EvidenceBinding(policy, available))
    facts = DirectionalFacts(direction, direction, direction, direction, direction, direction)
    directional = DirectionValidation(DirectionalDecision(policy, evidence, facts))
    entry = EntryValidation(EntryPrice(directional, EntryFacts(100.0, 100.0)))
    if direction is StrategyDirection.BUY:
        stop, target = 95.0, 115.0
    else:
        stop, target = 105.0, 85.0
    reward_risk = RewardRiskValidation(
        RewardRiskOutcome(
            entry,
            StopValidation(StopLoss(entry, StopFacts(stop))),
            TargetValidation(TakeProfit(entry, TargetFacts(target))),
        )
    )
    value = StrategyConfidence(evidence, directional, reward_risk, confidence)
    request = StrategyEvaluationRequest(
        identity,
        evidence_identity,
        timestamp,
        "baseline",
        policy.identity.reference,
    )
    return value, SignalExpiration(request, value)


def test_public_api_and_exact_fields() -> None:
    import epip.a07.confidence as module

    value, expiration = inputs()
    validation = ConfidenceValidation(value, expiration)
    assert module.__all__ == [
        "ConfidenceDiagnostics",
        "ConfidenceValidation",
        "SignalExpiration",
        "StrategyConfidence",
    ]
    assert value._field_names == (
        "evidence_validation",
        "direction_validation",
        "reward_risk_validation",
        "confidence",
    )
    assert expiration._field_names == (
        "request",
        "strategy_confidence",
        "evaluation_timestamp",
        "expiration_seconds",
        "expires_at",
    )
    assert validation._field_names == (
        "strategy_confidence",
        "signal_expiration",
        "valid",
        "diagnostics",
    )


@pytest.mark.parametrize("confidence", [0.0, -0.0, 0.25, 0.5, 0.75, 1.0])
def test_confidence_exact_float_range_and_negative_zero(confidence: float) -> None:
    value, _ = inputs(confidence)
    assert type(value.confidence) is float
    assert value.confidence == confidence
    if confidence == 0.0:
        assert str(value.confidence) == "0.0"


@pytest.mark.parametrize(
    "bad",
    [
        True,
        False,
        0,
        1,
        Decimal("0.5"),
        "0.5",
        None,
        float("nan"),
        float("inf"),
        -float("inf"),
        -0.1,
        1.1,
    ],
)
def test_invalid_confidence_fails_closed(bad: object) -> None:
    value, _ = inputs()
    with pytest.raises(DataIntegrityError):
        StrategyConfidence(
            value.evidence_validation,
            value.direction_validation,
            value.reward_risk_validation,
            bad,
        )


@pytest.mark.parametrize(
    "confidence,minimum,valid,codes",
    [
        (0.4999999999999999, 0.5, False, ("CONFIDENCE_BELOW_MINIMUM",)),
        (0.5, 0.5, True, ()),
        (0.5000000000000001, 0.5, True, ()),
    ],
)
def test_threshold_below_equal_above(
    confidence: float, minimum: float, valid: bool, codes: tuple[str, ...]
) -> None:
    value, expiration = inputs(confidence, minimum_confidence=minimum)
    result = ConfidenceValidation(value, expiration)
    assert result.valid is valid
    assert result.diagnostics.diagnostics == codes


@pytest.mark.parametrize("direction", [StrategyDirection.BUY, StrategyDirection.SELL])
def test_buy_and_sell_actionable_chains(direction: StrategyDirection) -> None:
    value, expiration = inputs(direction=direction)
    assert value.direction_validation.decision.direction is direction
    assert ConfidenceValidation(value, expiration).valid is True


@pytest.mark.parametrize("field", [0, 1, 2])
@pytest.mark.parametrize("bad", [None, object(), "validation"])
def test_wrong_predecessor_types(field: int, bad: object) -> None:
    value, _ = inputs()
    parts = list(value._values())
    parts[field] = bad
    with pytest.raises(DataIntegrityError):
        StrategyConfidence(*parts)


@pytest.mark.parametrize("field", [0, 1, 2])
def test_invalid_predecessor_gates_fail_closed(field: int) -> None:
    value, _ = inputs()
    parts = list(value._values())
    object.__setattr__(parts[field], "valid", False)
    with pytest.raises(DataIntegrityError):
        StrategyConfidence(*parts)


def test_value_equal_reconstructed_predecessors_are_accepted() -> None:
    value, _ = inputs()
    evidence = EvidenceValidation.reconstruct(*value.evidence_validation._values())
    direction = DirectionValidation.reconstruct(*value.direction_validation._values())
    reward_risk = RewardRiskValidation.reconstruct(*value.reward_risk_validation._values())
    rebuilt = StrategyConfidence(evidence, direction, reward_risk, 0.75)
    assert rebuilt == value and rebuilt is not value


@pytest.mark.parametrize("field", ["evidence", "direction"])
def test_predecessor_continuity_mismatch(field: str) -> None:
    value, _ = inputs()
    other, _ = inputs(minimum_confidence=0.6)
    evidence = other.evidence_validation if field == "evidence" else value.evidence_validation
    direction = other.direction_validation if field == "direction" else value.direction_validation
    with pytest.raises(DataIntegrityError):
        StrategyConfidence(evidence, direction, value.reward_risk_validation, 0.75)


def test_reward_risk_continuity_mismatch_and_malformed_state() -> None:
    value, _ = inputs()
    other, _ = inputs(minimum_confidence=0.6)
    with pytest.raises(DataIntegrityError):
        StrategyConfidence(
            value.evidence_validation,
            value.direction_validation,
            other.reward_risk_validation,
            0.75,
        )
    object.__setattr__(value.reward_risk_validation, "outcome", None)
    with pytest.raises(DataIntegrityError):
        StrategyConfidence(*value._values())


def test_non_actionable_direction_fails_closed() -> None:
    value, _ = inputs()
    object.__setattr__(value.direction_validation.decision, "direction", StrategyDirection.NO_TRADE)
    with pytest.raises(DataIntegrityError):
        StrategyConfidence(*value._values())


@pytest.mark.parametrize(
    "timestamp,canonical,expires",
    [
        ("2026-08-24T12:30:15Z", "2026-08-24T12:30:15.000000Z", "2026-08-24T12:31:45.000000Z"),
        (
            "2026-08-24T14:30:15.123456+02:00",
            "2026-08-24T12:30:15.123456Z",
            "2026-08-24T12:31:45.123456Z",
        ),
        (
            "2026-08-24T07:30:15.1-05:00",
            "2026-08-24T12:30:15.100000Z",
            "2026-08-24T12:31:45.100000Z",
        ),
    ],
)
def test_utc_normalization_and_expiration_formula(
    timestamp: str, canonical: str, expires: str
) -> None:
    _, expiration = inputs(timestamp=timestamp)
    assert expiration.evaluation_timestamp == canonical
    assert expiration.expiration_seconds == 90
    assert expiration.expires_at == expires


@pytest.mark.parametrize("bad", [None, object(), "request"])
def test_wrong_request_type(bad: object) -> None:
    value, _ = inputs()
    with pytest.raises(DataIntegrityError):
        SignalExpiration(bad, value)


def test_wrong_strategy_confidence_type() -> None:
    _, expiration = inputs()
    with pytest.raises(DataIntegrityError):
        SignalExpiration(expiration.request, object())


@pytest.mark.parametrize("timestamp", ["not-a-time", "2026-08-24T12:30:15"])
def test_malformed_or_naive_forged_request_rejected(timestamp: str) -> None:
    value, expiration = inputs()
    object.__setattr__(expiration.request, "evaluation_timestamp", timestamp)
    with pytest.raises(DataIntegrityError):
        SignalExpiration(expiration.request, value)


@pytest.mark.parametrize("field", ["strategy", "policy", "evidence"])
def test_request_continuity_mismatch(field: str) -> None:
    value, expiration = inputs(with_evidence=True)
    request = expiration.request
    if field == "strategy":
        request = StrategyEvaluationRequest(
            StrategyIdentity("other", "1"),
            request.evidence_identity,
            request.evaluation_timestamp,
            "baseline",
            request.policy_reference,
        )
    elif field == "policy":
        request = StrategyEvaluationRequest(
            request.strategy_identity,
            request.evidence_identity,
            request.evaluation_timestamp,
            "baseline",
            "wrong-policy",
        )
    else:
        request = StrategyEvaluationRequest(
            request.strategy_identity,
            StrategyEvidenceIdentity("other", "source"),
            request.evaluation_timestamp,
            "baseline",
            request.policy_reference,
        )
    with pytest.raises(DataIntegrityError):
        SignalExpiration(request, value)


def test_expiration_overflow_fails_closed() -> None:
    with pytest.raises(DataIntegrityError):
        inputs(timestamp="9999-12-31T23:59:59+00:00", expiration_seconds=2)


@pytest.mark.parametrize("field,bad", [(2, "wrong"), (3, 91), (4, "wrong")])
def test_expiration_reconstruction_contradictions(field: int, bad: object) -> None:
    _, expiration = inputs()
    parts = list(expiration._values())
    parts[field] = bad
    with pytest.raises(DataIntegrityError):
        SignalExpiration.reconstruct(*parts)


def test_expiration_reconstruction_round_trip() -> None:
    _, expiration = inputs()
    rebuilt = SignalExpiration.reconstruct(*expiration._values())
    assert rebuilt == expiration and hash(rebuilt) == hash(expiration)


@pytest.mark.parametrize("codes", [(), ("CONFIDENCE_BELOW_MINIMUM",)])
def test_diagnostics_canonical_round_trip(codes: tuple[str, ...]) -> None:
    value = ConfidenceDiagnostics(codes)
    assert value.diagnostics == codes
    assert ConfidenceDiagnostics.reconstruct(*value._values()) == value
    assert hash(value) == hash(ConfidenceDiagnostics(codes))


@pytest.mark.parametrize(
    "bad",
    [
        [],
        ["CONFIDENCE_BELOW_MINIMUM"],
        ("UNKNOWN",),
        ("CONFIDENCE_BELOW_MINIMUM", "CONFIDENCE_BELOW_MINIMUM"),
        (1,),
    ],
)
def test_invalid_diagnostics(bad: object) -> None:
    with pytest.raises(DataIntegrityError):
        ConfidenceDiagnostics(bad)


def test_validation_types_continuity_and_reconstruction() -> None:
    value, expiration = inputs()
    result = ConfidenceValidation(value, expiration)
    assert ConfidenceValidation.reconstruct(*result._values()) == result
    with pytest.raises(DataIntegrityError):
        ConfidenceValidation(object(), expiration)
    with pytest.raises(DataIntegrityError):
        ConfidenceValidation(value, object())
    other, other_expiration = inputs(minimum_confidence=0.6)
    with pytest.raises(DataIntegrityError):
        ConfidenceValidation(value, other_expiration)
    del other


@pytest.mark.parametrize(
    "field,bad",
    [(2, False), (2, 1), (3, ConfidenceDiagnostics(("CONFIDENCE_BELOW_MINIMUM",))), (3, ())],
)
def test_validation_reconstruction_contradictions(field: int, bad: object) -> None:
    value, expiration = inputs()
    result = ConfidenceValidation(value, expiration)
    parts = list(result._values())
    parts[field] = bad
    with pytest.raises(DataIntegrityError):
        ConfidenceValidation.reconstruct(*parts)


@pytest.mark.parametrize("kind", ["confidence", "expiration", "validation", "diagnostics"])
def test_immutability_hashing_and_exact_type_equality(kind: str) -> None:
    value, expiration = inputs()
    objects = {
        "confidence": value,
        "expiration": expiration,
        "validation": ConfidenceValidation(value, expiration),
        "diagnostics": ConfidenceDiagnostics(()),
    }
    selected = objects[kind]
    assert hash(selected)
    assert selected != object()
    with pytest.raises(FrozenInstanceError):
        setattr(selected, selected._field_names[0], None)


def test_strategy_confidence_reconstruction_round_trip() -> None:
    value, _ = inputs()
    rebuilt = StrategyConfidence.reconstruct(*value._values())
    assert rebuilt == value and hash(rebuilt) == hash(value)


def test_determinism_and_external_state_independence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TZ", "Pacific/Auckland")
    first, first_expiration = inputs()
    monkeypatch.setenv("TZ", "America/New_York")
    second, second_expiration = inputs()
    assert (first, first_expiration, ConfidenceValidation(first, first_expiration)) == (
        second,
        second_expiration,
        ConfidenceValidation(second, second_expiration),
    )


def test_no_hidden_scoring_wall_clock_or_successor_semantics() -> None:
    source = Path("epip/a07/confidence.py").read_text(encoding="utf-8")
    for forbidden in (
        "datetime.now",
        "datetime.utcnow",
        "time.time",
        "epip.a07.signal",
        "epip.a05",
        "epip.a06",
        "broker",
        "MT5",
    ):
        assert forbidden not in source
    assert "numeric_precision" not in source
