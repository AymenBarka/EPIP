from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

from epip.a07.direction import DirectionalDecision, DirectionalFacts, DirectionValidation
from epip.a07.entry import EntryFacts, EntryPrice, EntryValidation
from epip.a07.evidence import EvidenceBinding, EvidenceValidation
from epip.a07.foundation import StrategyDirection, StrategyIdentity
from epip.a07.policy import StrategyPolicy
from epip.a07.stop import StopDiagnostics, StopFacts, StopLoss, StopValidation
from epip.core.integrity import DataIntegrityError


def entry_validation(
    direction: StrategyDirection = StrategyDirection.BUY, *, precision: int = 2
) -> EntryValidation:
    policy = StrategyPolicy(
        "strategy",
        "1",
        StrategyIdentity("strategy", "1"),
        (StrategyDirection.BUY, StrategyDirection.SELL),
        2.0,
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
    return EntryValidation(EntryPrice(directional, EntryFacts(10.0, 20.0)))


@pytest.mark.parametrize("value", [0.1, 1.0, 999.9])
def test_stop_facts_preserve_valid_price(value: float) -> None:
    facts = StopFacts(value)
    assert facts.invalidation_price == value
    assert facts == StopFacts(value) and hash(facts) == hash(StopFacts(value))


@pytest.mark.parametrize(
    "bad", [None, True, 1, "1", Decimal(1), 0.0, -1.0, float("nan"), float("inf"), -float("inf")]
)
def test_stop_facts_reject_invalid_exact_types_and_values(bad: object) -> None:
    with pytest.raises(DataIntegrityError):
        StopFacts(bad)


@pytest.mark.parametrize(
    "direction,precision,raw,expected",
    [
        (StrategyDirection.BUY, 0, 9.5, 10.0),
        (StrategyDirection.BUY, 2, 9.225, 9.22),
        (StrategyDirection.BUY, 2, 9.235, 9.24),
        (StrategyDirection.SELL, 0, 21.5, 22.0),
        (StrategyDirection.SELL, 2, 20.225, 20.22),
        (StrategyDirection.SELL, 2, 20.235, 20.24),
        (StrategyDirection.SELL, 6, 20.1234564, 20.123456),
    ],
)
def test_stop_uses_exact_invalidation_and_half_even(
    direction: StrategyDirection, precision: int, raw: float, expected: float
) -> None:
    assert (
        StopLoss(entry_validation(direction, precision=precision), StopFacts(raw)).price == expected
    )


@pytest.mark.parametrize("raw", [20.0, 21.0])
def test_buy_rejects_equal_and_wrong_side(raw: float) -> None:
    with pytest.raises(DataIntegrityError):
        StopLoss(entry_validation(), StopFacts(raw))


@pytest.mark.parametrize("raw", [10.0, 9.0])
def test_sell_rejects_equal_and_wrong_side(raw: float) -> None:
    with pytest.raises(DataIntegrityError):
        StopLoss(entry_validation(StrategyDirection.SELL), StopFacts(raw))


def test_precision_collapse_and_normalization_to_zero_fail_closed() -> None:
    with pytest.raises(DataIntegrityError):
        StopLoss(entry_validation(precision=2), StopFacts(19.999))
    with pytest.raises(DataIntegrityError):
        StopLoss(entry_validation(precision=0), StopFacts(0.1))


@pytest.mark.parametrize("bad", [None, object(), "entry"])
def test_stop_rejects_wrong_entry_validation_type(bad: object) -> None:
    with pytest.raises(DataIntegrityError):
        StopLoss(bad, StopFacts(1.0))


def test_stop_rejects_wrong_fact_type() -> None:
    with pytest.raises(DataIntegrityError):
        StopLoss(entry_validation(), None)


def test_stop_rejects_forged_nonactionable_predecessor_states() -> None:
    invalid = entry_validation()
    object.__setattr__(invalid, "valid", False)
    with pytest.raises(DataIntegrityError):
        StopLoss(invalid, StopFacts(9.0))
    invalid = entry_validation()
    object.__setattr__(
        invalid.entry.direction_validation.decision, "direction", StrategyDirection.NO_TRADE
    )
    with pytest.raises(DataIntegrityError):
        StopLoss(invalid, StopFacts(9.0))


def test_stop_reconstruction_round_trip_and_failures() -> None:
    original = StopLoss(entry_validation(), StopFacts(9.225))
    rebuilt = StopLoss.reconstruct(*original._values())
    assert rebuilt == original and hash(rebuilt) == hash(original)
    for bad in (9.23, 9, "9.22", None, float("nan"), 0.0):
        with pytest.raises(DataIntegrityError):
            StopLoss.reconstruct(original.entry_validation, original.stop_facts, bad)


def test_diagnostics_only_accept_empty_tuple() -> None:
    value = StopDiagnostics(())
    assert value.diagnostics == () and StopDiagnostics(value.diagnostics) == value
    for bad in ([], ["X"], ("X",), ("X", "X"), (1,)):
        with pytest.raises(DataIntegrityError):
            StopDiagnostics(bad)


def test_validation_is_canonical_and_reconstructable() -> None:
    value = StopValidation(StopLoss(entry_validation(), StopFacts(9.0)))
    assert value.valid is True and value.diagnostics == StopDiagnostics(())
    rebuilt = StopValidation.reconstruct(*value._values())
    assert rebuilt == value and hash(rebuilt) == hash(value)
    for args in (
        (None, True, value.diagnostics),
        (value.stop, 1, value.diagnostics),
        (value.stop, False, value.diagnostics),
        (value.stop, True, None),
    ):
        with pytest.raises(DataIntegrityError):
            StopValidation.reconstruct(*args)


def test_validation_rejects_forged_noncanonical_stop() -> None:
    stop = StopLoss(entry_validation(), StopFacts(9.0))
    object.__setattr__(stop, "price", 8.0)
    with pytest.raises(DataIntegrityError):
        StopValidation(stop)


def test_public_objects_are_immutable_hashable_and_exact_type_equal() -> None:
    stop = StopLoss(entry_validation(), StopFacts(9.0))
    values = [StopFacts(9.0), stop, StopValidation(stop), StopDiagnostics(())]
    for value in values:
        hash(value)
        assert value != object()
        with pytest.raises(FrozenInstanceError):
            value.changed = True


def test_determinism_and_external_state_independence(monkeypatch: pytest.MonkeyPatch) -> None:
    entry = entry_validation(precision=3)
    facts = StopFacts(9.1236)
    first = StopLoss(entry, facts)
    monkeypatch.setenv("TZ", "different")
    monkeypatch.setenv("STOP_PRICE", "999")
    assert StopLoss(entry, facts) == first
    assert hash(StopLoss(entry, facts)) == hash(first)


def test_public_api_and_successor_isolation_are_exact() -> None:
    import epip.a07.stop as module

    assert module.__all__ == ["StopDiagnostics", "StopFacts", "StopLoss", "StopValidation"]
    source = Path(module.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "epip.a05",
        "epip.a06",
        "epip.a07.target",
        "ATR",
        "fibonacci",
        "minimum_rr",
        "confidence",
        "expiration",
        "broker",
        "MT5",
    ):
        assert forbidden not in source
