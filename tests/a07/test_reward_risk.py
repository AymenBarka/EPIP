from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

from epip.a07.direction import DirectionalDecision, DirectionalFacts, DirectionValidation
from epip.a07.entry import EntryFacts, EntryPrice, EntryValidation
from epip.a07.evidence import EvidenceBinding, EvidenceValidation
from epip.a07.foundation import StrategyDirection, StrategyIdentity
from epip.a07.policy import StrategyPolicy
from epip.a07.reward_risk import (
    RewardRiskDiagnostics,
    RewardRiskOutcome,
    RewardRiskValidation,
)
from epip.a07.stop import StopFacts, StopLoss, StopValidation
from epip.a07.target import TakeProfit, TargetFacts, TargetValidation
from epip.core.integrity import DataIntegrityError


def entry_validation(
    direction: StrategyDirection = StrategyDirection.BUY,
    *,
    minimum_rr: float = 3.0,
    precision: int = 13,
    entry: float = 100.0,
) -> EntryValidation:
    policy = StrategyPolicy(
        "strategy",
        "1",
        StrategyIdentity("strategy", "1"),
        (StrategyDirection.BUY, StrategyDirection.SELL),
        minimum_rr,
        0.5,
        (),
        (),
        60,
        precision,
        (),
    )
    evidence = EvidenceValidation(EvidenceBinding(policy, ()))
    facts = DirectionalFacts(direction, direction, direction, direction, direction, direction)
    directional = DirectionValidation(DirectionalDecision(policy, evidence, facts))
    return EntryValidation(EntryPrice(directional, EntryFacts(entry, entry)))


def outcome(
    direction: StrategyDirection = StrategyDirection.BUY,
    *,
    minimum_rr: float = 3.0,
    precision: int = 13,
    entry: float = 100.0,
    stop: float = 95.0,
    target: float = 115.0,
    predecessor: EntryValidation | None = None,
) -> RewardRiskOutcome:
    canonical_entry = predecessor or entry_validation(
        direction, minimum_rr=minimum_rr, precision=precision, entry=entry
    )
    stop_validation = StopValidation(StopLoss(canonical_entry, StopFacts(stop)))
    target_validation = TargetValidation(TakeProfit(canonical_entry, TargetFacts(target)))
    return RewardRiskOutcome(canonical_entry, stop_validation, target_validation)


@pytest.mark.parametrize(
    "direction,stop,target,expected",
    [
        (StrategyDirection.BUY, 95.0, 115.0, (5.0, 15.0, 3.0)),
        (StrategyDirection.BUY, 99.9, 100.3, (0.1, 0.3, 3.0)),
        (StrategyDirection.SELL, 105.0, 85.0, (5.0, 15.0, 3.0)),
        (StrategyDirection.SELL, 100.1, 99.7, (0.1, 0.3, 3.0)),
    ],
)
def test_directional_decimal_formulas(
    direction: StrategyDirection,
    stop: float,
    target: float,
    expected: tuple[float, float, float],
) -> None:
    assert outcome(direction, stop=stop, target=target)._values()[3:] == expected


@pytest.mark.parametrize(
    "minimum,stop,target,valid,codes",
    [
        (3.0, 95.0, 114.0, False, ("RR_BELOW_MINIMUM",)),
        (3.0, 95.0, 115.0, True, ()),
        (2.9, 95.0, 115.0, True, ()),
    ],
)
def test_threshold_below_equal_and_above(
    minimum: float, stop: float, target: float, valid: bool, codes: tuple[str, ...]
) -> None:
    validation = RewardRiskValidation(outcome(minimum_rr=minimum, stop=stop, target=target))
    assert validation.valid is valid
    assert validation.diagnostics.diagnostics == codes


@pytest.mark.parametrize(
    "raw_rr,expected,valid",
    [
        (2.9999999999996, 3.0, True),
        (2.9999999999994, 2.999999999999, False),
        (2.1234567890125, 2.123456789012, False),
        (2.1234567890135, 2.123456789014, False),
    ],
)
def test_twelve_decimal_half_even_and_post_canonical_threshold(
    raw_rr: float, expected: float, valid: bool
) -> None:
    value = outcome(
        minimum_rr=3.0,
        precision=13,
        entry=10.0,
        stop=9.0,
        target=10.0 + raw_rr,
    )
    assert value.rr == expected
    assert RewardRiskValidation(value).valid is valid


@pytest.mark.parametrize("field", [0, 1, 2])
@pytest.mark.parametrize("bad", [None, object(), "validation"])
def test_wrong_predecessor_types_fail_closed(field: int, bad: object) -> None:
    canonical = outcome()
    values = list(canonical._values()[:3])
    values[field] = bad
    with pytest.raises(DataIntegrityError):
        RewardRiskOutcome(*values)


def test_value_equal_reconstructed_predecessors_are_accepted() -> None:
    direct = entry_validation()
    rebuilt = EntryValidation.reconstruct(*direct._values())
    stop = StopValidation(StopLoss(rebuilt, StopFacts(95.0)))
    target = TargetValidation(TakeProfit(rebuilt, TargetFacts(115.0)))
    value = RewardRiskOutcome(direct, stop, target)
    assert rebuilt == direct and rebuilt is not direct
    assert value.rr == 3.0


@pytest.mark.parametrize("kind", ["stop", "target"])
def test_value_unequal_entry_continuity_is_rejected(kind: str) -> None:
    direct = entry_validation()
    other = entry_validation(minimum_rr=2.0)
    stop_entry = other if kind == "stop" else direct
    target_entry = other if kind == "target" else direct
    stop = StopValidation(StopLoss(stop_entry, StopFacts(95.0)))
    target = TargetValidation(TakeProfit(target_entry, TargetFacts(115.0)))
    with pytest.raises(DataIntegrityError):
        RewardRiskOutcome(direct, stop, target)


@pytest.mark.parametrize("field", ["entry", "stop", "target"])
def test_invalid_predecessor_validation_is_rejected(field: str) -> None:
    value = outcome()
    predecessor = {
        "entry": value.entry_validation,
        "stop": value.stop_validation,
        "target": value.target_validation,
    }[field]
    object.__setattr__(predecessor, "valid", False)
    with pytest.raises(DataIntegrityError):
        RewardRiskOutcome(value.entry_validation, value.stop_validation, value.target_validation)
    value = outcome()
    object.__setattr__(value.stop_validation, "diagnostics", object())
    with pytest.raises(DataIntegrityError):
        RewardRiskOutcome(value.entry_validation, value.stop_validation, value.target_validation)


def test_no_trade_and_malformed_predecessor_states_are_rejected() -> None:
    value = outcome()
    object.__setattr__(
        value.entry_validation.entry.direction_validation.decision,
        "direction",
        StrategyDirection.NO_TRADE,
    )
    with pytest.raises(DataIntegrityError):
        RewardRiskOutcome(value.entry_validation, value.stop_validation, value.target_validation)


def test_nonempty_predecessor_diagnostics_are_rejected() -> None:
    value = outcome()
    object.__setattr__(value.stop_validation.diagnostics, "diagnostics", ("FORGED",))
    with pytest.raises(DataIntegrityError):
        RewardRiskOutcome(value.entry_validation, value.stop_validation, value.target_validation)


def test_defensive_decimal_conversion_and_operation_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import epip.a07.reward_risk as module

    with pytest.raises(DataIntegrityError):
        module._public_positive(Decimal("1e-10000"), "risk")
    value = outcome()
    monkeypatch.setattr(module, "_RR_QUANTUM", Decimal("1e-10000"))
    with pytest.raises(DataIntegrityError):
        RewardRiskOutcome(value.entry_validation, value.stop_validation, value.target_validation)


@pytest.mark.parametrize(
    "direction,field,price",
    [
        (StrategyDirection.BUY, "stop", 100.0),
        (StrategyDirection.BUY, "stop", 101.0),
        (StrategyDirection.BUY, "target", 100.0),
        (StrategyDirection.BUY, "target", 99.0),
        (StrategyDirection.SELL, "stop", 100.0),
        (StrategyDirection.SELL, "stop", 99.0),
        (StrategyDirection.SELL, "target", 100.0),
        (StrategyDirection.SELL, "target", 101.0),
    ],
)
def test_non_positive_derived_distances_are_rejected(
    direction: StrategyDirection, field: str, price: float
) -> None:
    value = outcome(
        direction,
        stop=95.0 if direction is StrategyDirection.BUY else 105.0,
        target=115.0 if direction is StrategyDirection.BUY else 85.0,
    )
    geometry = value.stop_validation.stop if field == "stop" else value.target_validation.target
    object.__setattr__(geometry, "price", price)
    with pytest.raises(DataIntegrityError):
        RewardRiskOutcome(value.entry_validation, value.stop_validation, value.target_validation)


@pytest.mark.parametrize("field", ["stop", "target"])
@pytest.mark.parametrize("price", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_derived_state_is_rejected(field: str, price: float) -> None:
    value = outcome()
    geometry = value.stop_validation.stop if field == "stop" else value.target_validation.target
    object.__setattr__(geometry, "price", price)
    with pytest.raises(DataIntegrityError):
        RewardRiskOutcome(value.entry_validation, value.stop_validation, value.target_validation)


def test_outcome_fields_equality_hash_immutability_and_constructor() -> None:
    first = outcome()
    second = outcome()
    assert first._values()[3:] == (5.0, 15.0, 3.0)
    assert first == second and hash(first) == hash(second)
    assert first != object()
    with pytest.raises(FrozenInstanceError):
        first.risk = 1.0
    with pytest.raises(TypeError):
        RewardRiskOutcome(*first._values())


def test_outcome_reconstruction_round_trip_and_contradictions() -> None:
    original = outcome()
    rebuilt = RewardRiskOutcome.reconstruct(*original._values())
    assert rebuilt == original and hash(rebuilt) == hash(original)
    for field, bad in (
        (3, 4.0),
        (4, 14.0),
        (5, 2.0),
        (3, 5),
        (4, float("nan")),
        (5, 0.0),
    ):
        values = list(original._values())
        values[field] = bad
        with pytest.raises(DataIntegrityError):
            RewardRiskOutcome.reconstruct(*values)


def test_diagnostics_canonical_states_hash_and_immutability() -> None:
    for codes in ((), ("RR_BELOW_MINIMUM",)):
        value = RewardRiskDiagnostics(codes)
        assert value.diagnostics == codes
        assert value == RewardRiskDiagnostics(codes)
        assert hash(value) == hash(RewardRiskDiagnostics(codes))
        with pytest.raises(FrozenInstanceError):
            value.diagnostics = ()


@pytest.mark.parametrize(
    "bad",
    [
        ["RR_BELOW_MINIMUM"],
        {"RR_BELOW_MINIMUM"},
        ("UNKNOWN",),
        ("RR_BELOW_MINIMUM", "RR_BELOW_MINIMUM"),
        (1,),
        ("RR_BELOW_MINIMUM", "UNKNOWN"),
    ],
)
def test_diagnostics_reject_every_noncanonical_state(bad: object) -> None:
    with pytest.raises(DataIntegrityError):
        RewardRiskDiagnostics(bad)


def test_validation_fields_equality_hash_immutability_and_reconstruction() -> None:
    original = RewardRiskValidation(outcome())
    rebuilt = RewardRiskValidation.reconstruct(*original._values())
    assert original.valid is True and original.diagnostics == RewardRiskDiagnostics(())
    assert rebuilt == original and hash(rebuilt) == hash(original)
    assert original != object()
    with pytest.raises(FrozenInstanceError):
        original.valid = False


def test_rejected_validation_and_reconstruction_contradictions() -> None:
    original = RewardRiskValidation(outcome(target=114.0))
    assert original.valid is False
    assert original.diagnostics == RewardRiskDiagnostics(("RR_BELOW_MINIMUM",))
    for args in (
        (None, False, original.diagnostics),
        (original.outcome, 0, original.diagnostics),
        (original.outcome, True, original.diagnostics),
        (original.outcome, False, None),
        (original.outcome, False, RewardRiskDiagnostics(())),
    ):
        with pytest.raises(DataIntegrityError):
            RewardRiskValidation.reconstruct(*args)


def test_determinism_reconstruction_and_external_state_independence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = outcome(stop=96.0, target=113.0)
    monkeypatch.setenv("TZ", "different")
    monkeypatch.setenv("MINIMUM_RR", "999")
    repeated = outcome(stop=96.0, target=113.0)
    assert repeated == first and hash(repeated) == hash(first)
    assert RewardRiskValidation(repeated) == RewardRiskValidation(first)
    assert RewardRiskOutcome.reconstruct(*first._values()) == first


def test_public_api_dependency_and_successor_isolation_are_exact() -> None:
    import epip.a07.reward_risk as module

    assert module.__all__ == [
        "RewardRiskDiagnostics",
        "RewardRiskOutcome",
        "RewardRiskValidation",
    ]
    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    for forbidden in (
        "epip.a07.policy",
        "epip.a07.evidence",
        "epip.a07.direction",
        "epip.a05",
        "epip.a06",
        "epip.a07.confidence",
        "epip.a07.signal",
        "datetime",
        "random",
        "filesystem",
        "network",
        "broker",
        "mt5",
    ):
        assert forbidden not in source
