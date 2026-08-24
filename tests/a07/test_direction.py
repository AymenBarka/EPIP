from dataclasses import FrozenInstanceError
from enum import Enum
from pathlib import Path

import pytest

from epip.a07.direction import (
    DirectionalDecision,
    DirectionalFacts,
    DirectionDiagnostics,
    DirectionValidation,
)
from epip.a07.evidence import EvidenceBinding, EvidenceValidation
from epip.a07.foundation import StrategyDirection, StrategyIdentity
from epip.a07.policy import StrategyPolicy
from epip.core.integrity import DataIntegrityError


def policy(*directions: StrategyDirection) -> StrategyPolicy:
    return StrategyPolicy(
        "strategy",
        "1",
        StrategyIdentity("strategy", "1"),
        directions,
        2.0,
        0.5,
        (),
        (),
        60,
        2,
        (),
    )


def evidence(value: StrategyPolicy, *, valid: bool = True) -> EvidenceValidation:
    binding = EvidenceBinding(value, ())
    result = EvidenceValidation(binding)
    if valid:
        return result
    required = StrategyPolicy(
        value.identity.policy_id,
        value.identity.policy_version,
        value.strategy_identity,
        value.enabled_directions,
        value.minimum_rr,
        value.minimum_confidence,
        ("required",),
        (),
        value.expiration_seconds,
        value.numeric_precision,
        value.elliott_policy,
    )
    return EvidenceValidation(EvidenceBinding(required, ()))


def facts(direction: StrategyDirection, **changes: StrategyDirection) -> DirectionalFacts:
    values = dict.fromkeys(
        (
            "elliott_direction",
            "trend_direction",
            "structure_direction",
            "mtf_direction",
            "primary_direction",
            "alternate_direction",
        ),
        direction,
    )
    values.update(changes)
    return DirectionalFacts(**values)


def decision(
    direction: StrategyDirection = StrategyDirection.BUY,
    *,
    enabled: tuple[StrategyDirection, ...] = (StrategyDirection.BUY, StrategyDirection.SELL),
    valid_evidence: bool = True,
    **changes: StrategyDirection,
) -> DirectionalDecision:
    configured = policy(*enabled)
    validation = evidence(configured)
    if not valid_evidence:
        invalid_policy = StrategyPolicy(
            "strategy",
            "1",
            configured.strategy_identity,
            enabled,
            2.0,
            0.5,
            ("required",),
            (),
            60,
            2,
            (),
        )
        validation = EvidenceValidation(EvidenceBinding(invalid_policy, ()))
        configured = invalid_policy
    return DirectionalDecision(configured, validation, facts(direction, **changes))


@pytest.mark.parametrize("direction", tuple(StrategyDirection))
def test_directional_facts_preserve_exact_fixed_fields(direction: StrategyDirection) -> None:
    value = facts(direction)
    assert value._values() == (direction,) * 6
    assert value == DirectionalFacts(*value._values())
    assert hash(value) == hash(DirectionalFacts(*value._values()))


class ForeignDirection(Enum):
    BUY = "BUY"


@pytest.mark.parametrize("bad", [None, "BUY", 1, ForeignDirection.BUY, object()])
@pytest.mark.parametrize("field", range(6))
def test_directional_facts_reject_every_wrong_exact_type(bad: object, field: int) -> None:
    values: list[object] = [StrategyDirection.BUY] * 6
    values[field] = bad
    with pytest.raises(DataIntegrityError):
        DirectionalFacts(*values)


def test_public_objects_are_immutable_and_hashable() -> None:
    values = [
        facts(StrategyDirection.BUY),
        decision(),
        DirectionValidation(decision()),
        DirectionDiagnostics(()),
    ]
    for value in values:
        hash(value)
        with pytest.raises(FrozenInstanceError):
            value.changed = True
    assert facts(StrategyDirection.BUY) != object()


@pytest.mark.parametrize("direction", [StrategyDirection.BUY, StrategyDirection.SELL])
def test_unanimous_enabled_direction_is_actionable(direction: StrategyDirection) -> None:
    result = decision(direction)
    validation = DirectionValidation(result)
    assert result.direction is direction
    assert validation.valid is True
    assert validation.diagnostics == DirectionDiagnostics(())


@pytest.mark.parametrize("direction", [StrategyDirection.BUY, StrategyDirection.SELL])
def test_unanimous_disabled_direction_is_no_trade(direction: StrategyDirection) -> None:
    other = StrategyDirection.SELL if direction is StrategyDirection.BUY else StrategyDirection.BUY
    result = decision(direction, enabled=(other,))
    validation = DirectionValidation(result)
    assert result.direction is StrategyDirection.NO_TRADE
    assert validation.diagnostics.diagnostics == ("DIRECTION_DISABLED_BY_POLICY",)


def test_invalid_evidence_is_domain_no_trade_without_e02_code_propagation() -> None:
    result = decision(valid_evidence=False)
    assert result.direction is StrategyDirection.NO_TRADE
    assert DirectionValidation(result).diagnostics.diagnostics == ("EVIDENCE_INVALID",)


@pytest.mark.parametrize(
    "field",
    [
        "elliott_direction",
        "trend_direction",
        "structure_direction",
        "mtf_direction",
        "primary_direction",
        "alternate_direction",
    ],
)
def test_each_neutral_fact_prevents_consensus(field: str) -> None:
    result = decision(**{field: StrategyDirection.NO_TRADE})  # type: ignore[arg-type]
    codes = DirectionValidation(result).diagnostics.diagnostics
    assert result.direction is StrategyDirection.NO_TRADE
    assert "NO_DIRECTIONAL_CONSENSUS" in codes
    assert ("PRIMARY_ALTERNATE_CONFLICT" in codes) is (
        field in {"primary_direction", "alternate_direction"}
    )


@pytest.mark.parametrize(
    ("primary", "alternate"),
    [(a, b) for a in StrategyDirection for b in StrategyDirection if a is not b],
)
def test_every_primary_alternate_conflict_is_no_trade(
    primary: StrategyDirection, alternate: StrategyDirection
) -> None:
    result = decision(primary_direction=primary, alternate_direction=alternate)
    codes = DirectionValidation(result).diagnostics.diagnostics
    assert result.direction is StrategyDirection.NO_TRADE
    assert "PRIMARY_ALTERNATE_CONFLICT" in codes
    assert "NO_DIRECTIONAL_CONSENSUS" in codes


def test_buy_sell_disagreement_has_all_applicable_sorted_codes() -> None:
    result = decision(
        valid_evidence=False,
        trend_direction=StrategyDirection.SELL,
        alternate_direction=StrategyDirection.SELL,
    )
    assert DirectionValidation(result).diagnostics.diagnostics == (
        "DIRECTIONAL_CONFLICT",
        "EVIDENCE_INVALID",
        "NO_DIRECTIONAL_CONSENSUS",
        "PRIMARY_ALTERNATE_CONFLICT",
    )


@pytest.mark.parametrize("sell_positions", [(5,), (4, 5), (3, 4, 5), (1, 2, 3, 4, 5)])
def test_no_majority_or_precedence(sell_positions: tuple[int, ...]) -> None:
    values = [StrategyDirection.BUY] * 6
    for position in sell_positions:
        values[position] = StrategyDirection.SELL
    configured = policy(StrategyDirection.BUY, StrategyDirection.SELL)
    result = DirectionalDecision(configured, evidence(configured), DirectionalFacts(*values))
    assert result.direction is StrategyDirection.NO_TRADE


def test_all_neutral_is_no_consensus_without_directional_conflict() -> None:
    validation = DirectionValidation(decision(StrategyDirection.NO_TRADE))
    assert validation.diagnostics.diagnostics == ("NO_DIRECTIONAL_CONSENSUS",)


@pytest.mark.parametrize("bad,field", [(None, "policy"), (None, "evidence"), (None, "facts")])
def test_decision_rejects_wrong_predecessor_types(bad: object, field: str) -> None:
    configured = policy(StrategyDirection.BUY)
    values = [configured, evidence(configured), facts(StrategyDirection.BUY)]
    values[{"policy": 0, "evidence": 1, "facts": 2}[field]] = bad
    with pytest.raises(DataIntegrityError):
        DirectionalDecision(*values)


def test_decision_rejects_cross_predecessor_policy_mismatch() -> None:
    first = policy(StrategyDirection.BUY)
    second = policy(StrategyDirection.SELL)
    with pytest.raises(DataIntegrityError):
        DirectionalDecision(first, evidence(second), facts(StrategyDirection.BUY))


def test_decision_reconstruction_round_trip_and_contradiction() -> None:
    original = decision()
    rebuilt = DirectionalDecision.reconstruct(*original._values())
    assert rebuilt == original and hash(rebuilt) == hash(original)
    with pytest.raises(DataIntegrityError):
        DirectionalDecision.reconstruct(
            original.policy,
            original.evidence_validation,
            original.directional_facts,
            StrategyDirection.SELL,
        )
    with pytest.raises(DataIntegrityError):
        DirectionalDecision.reconstruct(
            original.policy, original.evidence_validation, original.directional_facts, "BUY"
        )


@pytest.mark.parametrize(
    "code",
    [
        "DIRECTIONAL_CONFLICT",
        "DIRECTION_DISABLED_BY_POLICY",
        "EVIDENCE_INVALID",
        "NO_DIRECTIONAL_CONSENSUS",
        "PRIMARY_ALTERNATE_CONFLICT",
    ],
)
def test_every_known_diagnostic_is_accepted(code: str) -> None:
    assert DirectionDiagnostics((code,)).diagnostics == (code,)


def test_diagnostics_are_canonical_reconstructable_and_fail_closed() -> None:
    value = DirectionDiagnostics(("PRIMARY_ALTERNATE_CONFLICT", "DIRECTIONAL_CONFLICT"))
    assert value.diagnostics == ("DIRECTIONAL_CONFLICT", "PRIMARY_ALTERNATE_CONFLICT")
    assert DirectionDiagnostics(value.diagnostics) == value
    for bad in (["EVIDENCE_INVALID"], ("UNKNOWN",), ("EVIDENCE_INVALID",) * 2, (1,)):
        with pytest.raises((DataIntegrityError, TypeError)):
            DirectionDiagnostics(bad)


def test_validation_reconstruction_round_trip_and_contradictions() -> None:
    original = DirectionValidation(decision())
    rebuilt = DirectionValidation.reconstruct(*original._values())
    assert rebuilt == original and hash(rebuilt) == hash(original)
    with pytest.raises(DataIntegrityError):
        DirectionValidation.reconstruct(original.decision, False, original.diagnostics)
    with pytest.raises(DataIntegrityError):
        DirectionValidation.reconstruct(
            original.decision, True, DirectionDiagnostics(("EVIDENCE_INVALID",))
        )
    for args in [
        (None, True, DirectionDiagnostics(())),
        (original.decision, 1, original.diagnostics),
        (original.decision, True, None),
    ]:
        with pytest.raises(DataIntegrityError):
            DirectionValidation.reconstruct(*args)


def test_validation_rejects_wrong_decision_type() -> None:
    with pytest.raises(DataIntegrityError):
        DirectionValidation(None)


def test_determinism_and_external_state_independence(monkeypatch: pytest.MonkeyPatch) -> None:
    original = decision()
    monkeypatch.setenv("TZ", "different")
    monkeypatch.setenv("A07_DIRECTION", "SELL")
    repeated = decision()
    assert repeated == original
    assert hash(repeated) == hash(original)
    assert DirectionValidation(repeated) == DirectionValidation(original)


def test_public_api_and_dependency_boundary_are_exact() -> None:
    import epip.a07.direction as module

    assert module.__all__ == [
        "DirectionDiagnostics",
        "DirectionValidation",
        "DirectionalDecision",
        "DirectionalFacts",
    ]
    source = Path(module.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "epip.a05",
        "epip.a06",
        "epip.a07.entry",
        "datetime",
        "random",
        "time.time",
        "MT5",
    ):
        assert forbidden not in source
