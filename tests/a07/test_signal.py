from dataclasses import FrozenInstanceError
from inspect import signature
from pathlib import Path
from types import SimpleNamespace

import pytest

from epip.a07.confidence import ConfidenceValidation, SignalExpiration, StrategyConfidence
from epip.a07.direction import DirectionalDecision, DirectionalFacts, DirectionValidation
from epip.a07.entry import EntryFacts, EntryPrice, EntryValidation
from epip.a07.evidence import EvidenceBinding, EvidenceValidation
from epip.a07.foundation import (
    StrategyDirection,
    StrategyEvaluationRequest,
    StrategyEvidenceIdentity,
    StrategyIdentity,
)
from epip.a07.policy import StrategyPolicy
from epip.a07.reward_risk import RewardRiskOutcome, RewardRiskValidation
from epip.a07.signal import SignalDiagnostics, SignalValidation, StrategySignal
from epip.a07.stop import StopFacts, StopLoss, StopValidation
from epip.a07.target import TakeProfit, TargetFacts, TargetValidation
from epip.core.integrity import DataIntegrityError


def confidence_validation(
    direction: StrategyDirection = StrategyDirection.BUY,
    *,
    confidence: float = 0.75,
    minimum_confidence: float = 0.5,
) -> ConfidenceValidation:
    identity = StrategyIdentity("strategy", "1")
    evidence_identity = StrategyEvidenceIdentity("evidence", "source")
    policy = StrategyPolicy(
        "strategy",
        "1",
        identity,
        (StrategyDirection.BUY, StrategyDirection.SELL),
        2.0,
        minimum_confidence,
        (),
        (),
        90,
        6,
        (),
    )
    evidence = EvidenceValidation(EvidenceBinding(policy, ()))
    facts = DirectionalFacts(direction, direction, direction, direction, direction, direction)
    directional = DirectionValidation(DirectionalDecision(policy, evidence, facts))
    entry = EntryValidation(EntryPrice(directional, EntryFacts(100.0, 100.0)))
    stop_price, target_price = (
        (95.0, 115.0) if direction is StrategyDirection.BUY else (105.0, 85.0)
    )
    reward_risk = RewardRiskValidation(
        RewardRiskOutcome(
            entry,
            StopValidation(StopLoss(entry, StopFacts(stop_price))),
            TargetValidation(TakeProfit(entry, TargetFacts(target_price))),
        )
    )
    strategy_confidence = StrategyConfidence(evidence, directional, reward_risk, confidence)
    request = StrategyEvaluationRequest(
        identity,
        evidence_identity,
        "2026-08-24T14:30:15.123456+02:00",
        "baseline",
        policy.identity.reference,
    )
    expiration = SignalExpiration(request, strategy_confidence)
    return ConfidenceValidation(strategy_confidence, expiration)


def test_exact_public_api_fields_and_signatures() -> None:
    import epip.a07.signal as module

    assert module.__all__ == ["SignalDiagnostics", "SignalValidation", "StrategySignal"]
    assert StrategySignal._field_names == (
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
    assert SignalValidation._field_names == ("signal", "valid", "diagnostics")
    assert SignalDiagnostics._field_names == ("diagnostics",)
    assert tuple(signature(StrategySignal).parameters) == ("confidence_validation",)
    assert tuple(signature(SignalValidation).parameters) == ("signal",)


@pytest.mark.parametrize(
    "direction,stop,target",
    [(StrategyDirection.BUY, 95.0, 115.0), (StrategyDirection.SELL, 105.0, 85.0)],
)
def test_buy_and_sell_copy_all_canonical_sources(
    direction: StrategyDirection, stop: float, target: float
) -> None:
    validation = confidence_validation(direction)
    signal = StrategySignal(validation)
    policy = validation.strategy_confidence.direction_validation.decision.policy
    assert signal._values() == (
        policy.strategy_identity,
        policy.identity.reference,
        direction,
        100.0,
        stop,
        target,
        5.0,
        15.0,
        3.0,
        0.75,
        "2026-08-24T12:30:15.123456Z",
        "2026-08-24T12:31:45.123456Z",
    )


@pytest.mark.parametrize("bad", [None, object(), "confidence"])
def test_wrong_predecessor_type_fails_closed(bad: object) -> None:
    with pytest.raises(DataIntegrityError):
        StrategySignal(bad)


def test_rejected_e08_fails_closed() -> None:
    rejected = confidence_validation(confidence=0.49)
    assert rejected.valid is False
    with pytest.raises(DataIntegrityError):
        StrategySignal(rejected)


def test_malformed_e08_fails_closed() -> None:
    value = confidence_validation()
    object.__setattr__(value, "diagnostics", None)
    with pytest.raises(DataIntegrityError):
        StrategySignal(value)


@pytest.mark.parametrize("mutation", ["valid", "diagnostics", "continuity"])
def test_noncanonical_e08_fails_closed(mutation: str) -> None:
    value = confidence_validation()
    if mutation == "valid":
        object.__setattr__(value, "valid", False)
    elif mutation == "diagnostics":
        object.__setattr__(value.diagnostics, "diagnostics", ("FORGED",))
    else:
        object.__setattr__(value.signal_expiration, "strategy_confidence", object())
    with pytest.raises(DataIntegrityError):
        StrategySignal(value)


def test_no_trade_fails_closed() -> None:
    value = confidence_validation()
    object.__setattr__(
        value.strategy_confidence.direction_validation.decision,
        "direction",
        StrategyDirection.NO_TRADE,
    )
    with pytest.raises(DataIntegrityError):
        StrategySignal(value)


@pytest.mark.parametrize(
    "path",
    ["stop", "target", "entry", "request_strategy", "request_policy", "missing"],
)
def test_continuity_and_malformed_chains_fail_closed(path: str) -> None:
    value = confidence_validation()
    confidence = value.strategy_confidence
    outcome = confidence.reward_risk_validation.outcome
    if path == "stop":
        object.__setattr__(outcome.stop_validation.stop, "entry_validation", object())
    elif path == "target":
        object.__setattr__(outcome.target_validation.target, "entry_validation", object())
    elif path == "entry":
        object.__setattr__(outcome.entry_validation.entry, "direction_validation", object())
    elif path == "request_strategy":
        object.__setattr__(
            value.signal_expiration.request, "strategy_identity", StrategyIdentity("other", "1")
        )
    elif path == "request_policy":
        object.__setattr__(value.signal_expiration.request, "policy_reference", "wrong")
    else:
        object.__setattr__(confidence.reward_risk_validation, "outcome", None)
    with pytest.raises(DataIntegrityError):
        StrategySignal(value)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("strategy_identity", object()),
        ("policy_reference", 1),
        ("direction", "BUY"),
        ("entry_price", 100),
        ("stop_price", 95),
        ("target_price", 115),
        ("risk", 5),
        ("reward", 15),
        ("rr", 3),
        ("confidence", 1),
        ("evaluation_timestamp", object()),
        ("expires_at", object()),
    ],
)
def test_wrong_source_runtime_type_fails_closed(field: str, bad: object) -> None:
    value = confidence_validation()
    confidence = value.strategy_confidence
    outcome = confidence.reward_risk_validation.outcome
    sources = {
        "strategy_identity": confidence.direction_validation.decision.policy,
        "policy_reference": confidence.direction_validation.decision.policy.identity,
        "direction": confidence.direction_validation.decision,
        "entry_price": outcome.entry_validation.entry,
        "stop_price": outcome.stop_validation.stop,
        "target_price": outcome.target_validation.target,
        "risk": outcome,
        "reward": outcome,
        "rr": outcome,
        "confidence": confidence,
        "evaluation_timestamp": value.signal_expiration,
        "expires_at": value.signal_expiration,
    }
    attribute = {
        "strategy_identity": "strategy_identity",
        "policy_reference": "reference",
        "direction": "direction",
        "entry_price": "price",
        "stop_price": "price",
        "target_price": "price",
        "risk": "risk",
        "reward": "reward",
        "rr": "rr",
        "confidence": "confidence",
        "evaluation_timestamp": "evaluation_timestamp",
        "expires_at": "expires_at",
    }[field]
    if field == "policy_reference":
        policy = confidence.direction_validation.decision.policy
        object.__setattr__(policy, "identity", SimpleNamespace(reference=bad))
    else:
        object.__setattr__(sources[field], attribute, bad)
    with pytest.raises(DataIntegrityError):
        StrategySignal(value)


@pytest.mark.parametrize("index", range(12))
def test_reconstruction_rejects_each_tampered_field(index: int) -> None:
    value = confidence_validation()
    signal = StrategySignal(value)
    fields = list(signal._values())
    fields[index] = object()
    with pytest.raises(DataIntegrityError):
        StrategySignal.reconstruct(value, *fields)


def test_signal_reconstruction_round_trip_and_value_equal_predecessor() -> None:
    value = confidence_validation()
    rebuilt_e08 = ConfidenceValidation.reconstruct(*value._values())
    signal = StrategySignal(value)
    rebuilt = StrategySignal.reconstruct(rebuilt_e08, *signal._values())
    assert rebuilt == signal and rebuilt is not signal and hash(rebuilt) == hash(signal)


@pytest.mark.parametrize("bad", [("UNKNOWN",), ("A", "A"), ["A"], {"A"}, {"a": 1}, (1,)])
def test_diagnostics_reject_every_nonempty_or_mutable_state(bad: object) -> None:
    with pytest.raises(DataIntegrityError):
        SignalDiagnostics(bad)
    with pytest.raises(DataIntegrityError):
        SignalDiagnostics.reconstruct(bad)


def test_empty_diagnostics_are_canonical_hashable_and_reconstructable() -> None:
    value = SignalDiagnostics(())
    rebuilt = SignalDiagnostics.reconstruct(())
    assert value.diagnostics == () and rebuilt == value and hash(rebuilt) == hash(value)


@pytest.mark.parametrize("bad", [None, object(), "signal"])
def test_validation_rejects_wrong_signal_type(bad: object) -> None:
    with pytest.raises(DataIntegrityError):
        SignalValidation(bad)


def test_validation_is_success_only_and_reconstructable() -> None:
    signal = StrategySignal(confidence_validation())
    value = SignalValidation(signal)
    rebuilt = SignalValidation.reconstruct(signal, True, SignalDiagnostics(()))
    assert value._values() == (signal, True, SignalDiagnostics(()))
    assert rebuilt == value and hash(rebuilt) == hash(value)


@pytest.mark.parametrize(
    "valid,diagnostics",
    [(False, SignalDiagnostics(())), (1, SignalDiagnostics(())), (True, object())],
)
def test_validation_reconstruction_rejects_contradictions(
    valid: object, diagnostics: object
) -> None:
    with pytest.raises(DataIntegrityError):
        SignalValidation.reconstruct(StrategySignal(confidence_validation()), valid, diagnostics)


@pytest.mark.parametrize("kind", ["signal", "validation", "diagnostics"])
def test_public_objects_are_immutable(kind: str) -> None:
    signal = StrategySignal(confidence_validation())
    value = {
        "signal": signal,
        "validation": SignalValidation(signal),
        "diagnostics": SignalDiagnostics(()),
    }[kind]
    with pytest.raises(FrozenInstanceError):
        value.changed = True


def test_exact_type_equality_and_determinism() -> None:
    first = StrategySignal(confidence_validation())
    second = StrategySignal(confidence_validation())
    assert first == second and hash(first) == hash(second)
    assert SignalValidation(first) == SignalValidation(second)
    assert first.__eq__(first._values()) is NotImplemented


def test_module_has_no_external_state_or_successor_dependencies() -> None:
    source = Path("epip/a07/signal.py").read_text(encoding="utf-8")
    forbidden_imports = ("datetime", "time", "random", "os", "pathlib", "requests", "mt5")
    import_lines = tuple(
        line.lower() for line in source.splitlines() if line.startswith(("import ", "from "))
    )
    assert all(token not in line for token in forbidden_imports for line in import_lines)
    assert "uuid" not in source.lower()
