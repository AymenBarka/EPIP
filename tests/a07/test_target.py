from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

from epip.a07.direction import DirectionalDecision, DirectionalFacts, DirectionValidation
from epip.a07.entry import EntryFacts, EntryPrice, EntryValidation
from epip.a07.evidence import EvidenceBinding, EvidenceValidation
from epip.a07.foundation import StrategyDirection, StrategyIdentity
from epip.a07.policy import StrategyPolicy
from epip.a07.target import TakeProfit, TargetDiagnostics, TargetFacts, TargetValidation
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
def test_target_facts_preserve_valid_price(value: float) -> None:
    facts = TargetFacts(value)
    assert facts._values() == (value,)
    assert facts == TargetFacts(value) and hash(facts) == hash(TargetFacts(value))


@pytest.mark.parametrize(
    "bad",
    [None, True, 1, "1", Decimal(1), 0.0, -0.0, -1.0, float("nan"), float("inf"), -float("inf")],
)
def test_target_facts_reject_invalid_exact_types_and_values(bad: object) -> None:
    with pytest.raises(DataIntegrityError):
        TargetFacts(bad)


@pytest.mark.parametrize(
    "direction,precision,raw,expected",
    [
        (StrategyDirection.BUY, 0, 21.5, 22.0),
        (StrategyDirection.BUY, 1, 20.25, 20.2),
        (StrategyDirection.BUY, 2, 20.225, 20.22),
        (StrategyDirection.BUY, 2, 20.235, 20.24),
        (StrategyDirection.BUY, 6, 20.1234564, 20.123456),
        (StrategyDirection.SELL, 0, 8.5, 8.0),
        (StrategyDirection.SELL, 1, 9.25, 9.2),
        (StrategyDirection.SELL, 2, 9.225, 9.22),
        (StrategyDirection.SELL, 2, 9.235, 9.24),
        (StrategyDirection.SELL, 6, 9.1234564, 9.123456),
    ],
)
def test_target_uses_final_price_and_half_even(
    direction: StrategyDirection, precision: int, raw: float, expected: float
) -> None:
    assert (
        TakeProfit(entry_validation(direction, precision=precision), TargetFacts(raw)).price
        == expected
    )


@pytest.mark.parametrize("raw", [20.0, 19.0])
def test_buy_rejects_equal_and_wrong_side(raw: float) -> None:
    with pytest.raises(DataIntegrityError):
        TakeProfit(entry_validation(), TargetFacts(raw))


@pytest.mark.parametrize("raw", [10.0, 11.0])
def test_sell_rejects_equal_and_wrong_side(raw: float) -> None:
    with pytest.raises(DataIntegrityError):
        TakeProfit(entry_validation(StrategyDirection.SELL), TargetFacts(raw))


def test_precision_collapse_and_normalization_to_zero_fail_closed() -> None:
    with pytest.raises(DataIntegrityError):
        TakeProfit(entry_validation(precision=2), TargetFacts(20.001))
    with pytest.raises(DataIntegrityError):
        TakeProfit(entry_validation(StrategyDirection.SELL, precision=0), TargetFacts(0.1))


@pytest.mark.parametrize("bad", [None, object(), "entry"])
def test_target_rejects_wrong_entry_validation_type(bad: object) -> None:
    with pytest.raises(DataIntegrityError):
        TakeProfit(bad, TargetFacts(21.0))


@pytest.mark.parametrize("bad", [None, object(), 21.0])
def test_target_rejects_wrong_fact_type(bad: object) -> None:
    with pytest.raises(DataIntegrityError):
        TakeProfit(entry_validation(), bad)


def test_target_rejects_forged_nonactionable_predecessor_states() -> None:
    invalid = entry_validation()
    object.__setattr__(invalid, "valid", False)
    with pytest.raises(DataIntegrityError):
        TakeProfit(invalid, TargetFacts(21.0))
    invalid = entry_validation()
    object.__setattr__(invalid, "diagnostics", object())
    with pytest.raises(DataIntegrityError):
        TakeProfit(invalid, TargetFacts(21.0))
    invalid = entry_validation()
    object.__setattr__(
        invalid.entry.direction_validation.decision, "direction", StrategyDirection.NO_TRADE
    )
    with pytest.raises(DataIntegrityError):
        TakeProfit(invalid, TargetFacts(21.0))


def test_take_profit_fields_constructor_and_reconstruction() -> None:
    predecessor = entry_validation()
    facts = TargetFacts(21.225)
    original = TakeProfit(predecessor, facts)
    assert original._values() == (predecessor, facts, 21.22)
    rebuilt = TakeProfit.reconstruct(*original._values())
    assert rebuilt == original and hash(rebuilt) == hash(original)
    with pytest.raises(TypeError):
        TakeProfit(predecessor, facts, 21.22)  # type: ignore[call-arg]
    for bad in (21.23, 21, "21.22", None, float("nan"), 0.0):
        with pytest.raises(DataIntegrityError):
            TakeProfit.reconstruct(predecessor, facts, bad)


def test_diagnostics_only_accept_empty_tuple() -> None:
    value = TargetDiagnostics(())
    assert value.diagnostics == () and TargetDiagnostics(value.diagnostics) == value
    assert hash(value) == hash(TargetDiagnostics(()))
    for bad in ([], ["X"], {"X"}, {"X": True}, ("X",), ("X", "X"), (1,)):
        with pytest.raises(DataIntegrityError):
            TargetDiagnostics(bad)


def test_validation_is_canonical_and_reconstructable() -> None:
    target = TakeProfit(entry_validation(), TargetFacts(21.0))
    value = TargetValidation(target)
    assert value._values() == (target, True, TargetDiagnostics(()))
    rebuilt = TargetValidation.reconstruct(*value._values())
    assert rebuilt == value and hash(rebuilt) == hash(value)
    for args in (
        (None, True, value.diagnostics),
        (value.target, 1, value.diagnostics),
        (value.target, False, value.diagnostics),
        (value.target, True, None),
    ):
        with pytest.raises(DataIntegrityError):
            TargetValidation.reconstruct(*args)


def test_validation_rejects_wrong_and_forged_noncanonical_target() -> None:
    with pytest.raises(DataIntegrityError):
        TargetValidation(None)
    target = TakeProfit(entry_validation(), TargetFacts(21.0))
    object.__setattr__(target, "price", 22.0)
    with pytest.raises(DataIntegrityError):
        TargetValidation(target)


def test_public_objects_are_immutable_hashable_and_exact_type_equal() -> None:
    target = TakeProfit(entry_validation(), TargetFacts(21.0))
    values = [TargetFacts(21.0), target, TargetValidation(target), TargetDiagnostics(())]
    for value in values:
        hash(value)
        assert value != object()
        with pytest.raises(FrozenInstanceError):
            value.changed = True


def test_determinism_and_external_state_independence(monkeypatch: pytest.MonkeyPatch) -> None:
    predecessor = entry_validation(precision=3)
    facts = TargetFacts(21.1236)
    first = TakeProfit(predecessor, facts)
    monkeypatch.setenv("TZ", "different")
    monkeypatch.setenv("TARGET_PRICE", "1")
    assert TakeProfit(predecessor, facts) == first
    assert hash(TakeProfit(predecessor, facts)) == hash(first)
    assert TakeProfit.reconstruct(*first._values()) == first


def test_public_api_dependencies_and_successor_isolation_are_exact() -> None:
    import epip.a07.target as module

    assert module.__all__ == [
        "TakeProfit",
        "TargetDiagnostics",
        "TargetFacts",
        "TargetValidation",
    ]
    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    for forbidden in (
        "epip.a05",
        "epip.a06",
        "epip.a07.policy",
        "epip.a07.evidence",
        "epip.a07.direction",
        "epip.a07.stop",
        "epip.a07.reward_risk",
        "stoploss",
        "stopvalidation",
        "stopfacts",
        "minimum_rr",
        "fibonacci",
        "elliott",
        "liquidity",
        "candidate",
        "broker",
        "mt5",
    ):
        assert forbidden not in source
