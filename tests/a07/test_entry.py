from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

from epip.a07.direction import DirectionalDecision, DirectionalFacts, DirectionValidation
from epip.a07.entry import EntryDiagnostics, EntryFacts, EntryPrice, EntryValidation
from epip.a07.evidence import EvidenceBinding, EvidenceValidation
from epip.a07.foundation import StrategyDirection, StrategyIdentity
from epip.a07.policy import StrategyPolicy
from epip.core.integrity import DataIntegrityError


def direction_validation(
    direction: StrategyDirection = StrategyDirection.BUY,
    *,
    precision: int = 2,
    actionable: bool = True,
) -> DirectionValidation:
    enabled = (StrategyDirection.BUY, StrategyDirection.SELL)
    policy = StrategyPolicy(
        "strategy",
        "1",
        StrategyIdentity("strategy", "1"),
        enabled,
        2.0,
        0.5,
        () if actionable else ("missing",),
        (),
        60,
        precision,
        (),
    )
    evidence = EvidenceValidation(EvidenceBinding(policy, ()))
    facts = DirectionalFacts(direction, direction, direction, direction, direction, direction)
    return DirectionValidation(DirectionalDecision(policy, evidence, facts))


@pytest.mark.parametrize("lower,upper", [(1.0, 2.0), (1.0, 1.0), (0.1, 999.9)])
def test_entry_facts_preserve_valid_raw_floats(lower: float, upper: float) -> None:
    value = EntryFacts(lower, upper)
    assert value._values() == (lower, upper)
    assert value == EntryFacts(lower, upper)
    assert hash(value) == hash(EntryFacts(lower, upper))


@pytest.mark.parametrize(
    "bad", [None, True, 1, "1", Decimal(1), 0.0, -1.0, float("nan"), float("inf"), -float("inf")]
)
@pytest.mark.parametrize("field", [0, 1])
def test_entry_facts_reject_invalid_exact_numeric_inputs(bad: object, field: int) -> None:
    values: list[object] = [1.0, 2.0]
    values[field] = bad
    with pytest.raises(DataIntegrityError):
        EntryFacts(*values)


def test_entry_facts_reject_reversed_zone() -> None:
    with pytest.raises(DataIntegrityError):
        EntryFacts(2.0, 1.0)


@pytest.mark.parametrize(
    "direction,precision,lower,upper,expected",
    [
        (StrategyDirection.BUY, 0, 1.1, 2.5, 2.0),
        (StrategyDirection.BUY, 2, 1.111, 2.345, 2.34),
        (StrategyDirection.BUY, 2, 1.111, 2.355, 2.36),
        (StrategyDirection.SELL, 0, 1.5, 3.1, 2.0),
        (StrategyDirection.SELL, 2, 1.225, 3.111, 1.22),
        (StrategyDirection.SELL, 2, 1.235, 3.111, 1.24),
        (StrategyDirection.BUY, 6, 1.1234561, 2.1234564, 2.123456),
    ],
)
def test_entry_uses_exact_directional_boundary_and_half_even(
    direction: StrategyDirection, precision: int, lower: float, upper: float, expected: float
) -> None:
    entry = EntryPrice(
        direction_validation(direction, precision=precision), EntryFacts(lower, upper)
    )
    assert entry.price == expected


def test_equal_raw_zone_is_supported() -> None:
    assert EntryPrice(direction_validation(), EntryFacts(1.234, 1.234)).price == 1.23


def test_distinct_bounds_collapsing_at_precision_fail_closed() -> None:
    with pytest.raises(DataIntegrityError):
        EntryPrice(direction_validation(precision=2), EntryFacts(1.231, 1.232))


def test_normalization_to_zero_fails_closed() -> None:
    with pytest.raises(DataIntegrityError):
        EntryPrice(direction_validation(precision=0), EntryFacts(0.1, 0.2))


def test_defensive_normalized_order_check_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    import epip.a07.entry as module

    results = iter((2.0, 1.0))
    monkeypatch.setattr(module, "_normalize", lambda value, precision: next(results))
    with pytest.raises(DataIntegrityError):
        EntryPrice(direction_validation(), EntryFacts(1.0, 2.0))


@pytest.mark.parametrize("bad", [None, object(), "validation"])
def test_entry_rejects_wrong_direction_validation_type(bad: object) -> None:
    with pytest.raises(DataIntegrityError):
        EntryPrice(bad, EntryFacts(1.0, 2.0))


def test_entry_rejects_wrong_facts_type_and_non_actionable_predecessors() -> None:
    with pytest.raises(DataIntegrityError):
        EntryPrice(direction_validation(), None)
    with pytest.raises(DataIntegrityError):
        EntryPrice(direction_validation(StrategyDirection.NO_TRADE), EntryFacts(1.0, 2.0))
    with pytest.raises(DataIntegrityError):
        EntryPrice(direction_validation(actionable=False), EntryFacts(1.0, 2.0))


def test_entry_reconstruction_round_trip_and_failures() -> None:
    original = EntryPrice(direction_validation(), EntryFacts(1.111, 2.345))
    rebuilt = EntryPrice.reconstruct(*original._values())
    assert rebuilt == original and hash(rebuilt) == hash(original)
    for bad in (2.35, 2, "2.34", None, float("nan"), 0.0):
        with pytest.raises(DataIntegrityError):
            EntryPrice.reconstruct(original.direction_validation, original.entry_facts, bad)


def test_diagnostics_only_accept_empty_tuple() -> None:
    value = EntryDiagnostics(())
    assert value.diagnostics == () and EntryDiagnostics(value.diagnostics) == value
    for bad in ([], ["X"], ("X",), ("X", "X"), (1,)):
        with pytest.raises(DataIntegrityError):
            EntryDiagnostics(bad)


def test_entry_validation_is_canonical_and_reconstructable() -> None:
    value = EntryValidation(EntryPrice(direction_validation(), EntryFacts(1.0, 2.0)))
    assert value.valid is True and value.diagnostics == EntryDiagnostics(())
    rebuilt = EntryValidation.reconstruct(*value._values())
    assert rebuilt == value and hash(rebuilt) == hash(value)
    for args in (
        (None, True, value.diagnostics),
        (value.entry, 1, value.diagnostics),
        (value.entry, False, value.diagnostics),
        (value.entry, True, None),
    ):
        with pytest.raises(DataIntegrityError):
            EntryValidation.reconstruct(*args)


def test_validation_rejects_forged_noncanonical_entry() -> None:
    entry = EntryPrice(direction_validation(), EntryFacts(1.0, 2.0))
    object.__setattr__(entry, "price", 1.5)
    with pytest.raises(DataIntegrityError):
        EntryValidation(entry)


def test_public_objects_are_immutable_hashable_and_exact_type_equal() -> None:
    values = [
        EntryFacts(1.0, 2.0),
        EntryPrice(direction_validation(), EntryFacts(1.0, 2.0)),
        EntryValidation(EntryPrice(direction_validation(), EntryFacts(1.0, 2.0))),
        EntryDiagnostics(()),
    ]
    for value in values:
        hash(value)
        assert value != object()
        with pytest.raises(FrozenInstanceError):
            value.changed = True


def test_determinism_and_external_state_independence(monkeypatch: pytest.MonkeyPatch) -> None:
    predecessor = direction_validation(precision=3)
    facts = EntryFacts(1.1114, 2.2226)
    first = EntryPrice(predecessor, facts)
    monkeypatch.setenv("TZ", "different")
    monkeypatch.setenv("ENTRY_PRICE", "999")
    assert EntryPrice(predecessor, facts) == first
    assert hash(EntryPrice(predecessor, facts)) == hash(first)


def test_public_api_and_successor_isolation_are_exact() -> None:
    import epip.a07.entry as module

    assert module.__all__ == ["EntryDiagnostics", "EntryFacts", "EntryPrice", "EntryValidation"]
    source = Path(module.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "epip.a05",
        "epip.a06",
        "epip.a07.stop",
        "epip.a07.target",
        "fibonacci",
        "minimum_rr",
        "confidence",
        "expiration",
        "broker",
        "MT5",
    ):
        assert forbidden not in source
